import { Request, Response } from 'express';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import axios from 'axios';
import { db } from '../db';
import { config } from '../config';

// Ensure uploads directory exists
if (!fs.existsSync(config.uploadDir)) {
  fs.mkdirSync(config.uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => {
    cb(null, config.uploadDir);
  },
  filename: (_req, file, cb) => {
    const uniqueSuffix = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    const ext = path.extname(file.originalname);
    cb(null, `report-${uniqueSuffix}${ext}`);
  },
});

export const uploadMiddleware = multer({
  storage,
  limits: { fileSize: config.maxFileSizeMb * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    if (file.mimetype === 'application/pdf' || file.originalname.toLowerCase().endsWith('.pdf')) {
      cb(null, true);
    } else {
      cb(new Error('Only PDF files are supported'));
    }
  },
});

export const documentController = {
  async uploadDocument(req: Request, res: Response): Promise<void> {
    try {
      if (!req.file) {
        res.status(400).json({ error: 'No PDF file uploaded' });
        return;
      }

      const { company_id, fiscal_year, period_type, document_type } = req.body;
      if (!company_id || !fiscal_year) {
        res.status(400).json({ error: 'company_id and fiscal_year are required' });
        return;
      }

      const year = parseInt(fiscal_year, 10);
      const filePath = path.resolve(req.file.path);

      // 1. Create document record
      const docRecord = await db.createDocument({
        company_id,
        fiscal_year: year,
        period_type: period_type || 'FY',
        document_type: document_type || 'annual_report',
        original_filename: req.file.originalname,
        storage_path: filePath,
        status: 'processing',
      });

      // 2. Create ingestion job
      const job = await db.createJob(docRecord.id);

      // 3. Trigger asynchronous ingestion in FastAPI
      setImmediate(async () => {
        try {
          await db.updateJob(job.id, { stage: 'PARSING', progress_percent: 20 });

          const aiResp = await axios.post(`${config.aiServiceUrl}/internal/documents/process`, {
            file_path: filePath,
            company_id,
            fiscal_year: year,
            document_id: docRecord.id,
            period_type: period_type || 'FY',
            document_type: document_type || 'annual_report',
          });

          await db.updateJob(job.id, {
            stage: 'COMPLETED',
            progress_percent: 100,
          });
        } catch (err: any) {
          await db.updateJob(job.id, {
            stage: 'FAILED',
            error_message: err.message || 'Ingestion failed in AI service',
          });
        }
      });

      res.status(202).json({
        message: 'Document uploaded and processing job created',
        document: docRecord,
        job_id: job.id,
      });
    } catch (err: any) {
      res.status(500).json({ error: `Upload failed: ${err.message}` });
    }
  },

  async getDocumentStatus(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const job = await db.getJobByDocumentId(id);
      if (!job) {
        res.status(404).json({ error: 'Job not found for this document' });
        return;
      }
      res.json({
        document_id: id,
        stage: job.stage,
        progress_percent: job.progress_percent,
        error_message: job.error_message,
        updated_at: job.updated_at,
      });
    } catch (err: any) {
      res.status(500).json({ error: `Failed to fetch status: ${err.message}` });
    }
  },

  async listDocuments(req: Request, res: Response): Promise<void> {
    try {
      const { company_id } = req.query;
      const docs = await db.listDocuments(company_id as string | undefined);
      res.json(docs);
    } catch (err: any) {
      res.status(500).json({ error: `Failed to list documents: ${err.message}` });
    }
  },

  async detectDocument(req: Request, res: Response): Promise<void> {
    let tempPath: string | null = null;
    try {
      if (!req.file) {
        res.status(400).json({ error: 'No PDF file uploaded for detection' });
        return;
      }

      tempPath = path.resolve(req.file.path);
      const companies = await db.listCompanies();

      const aiResp = await axios.post(`${config.aiServiceUrl}/internal/documents/detect`, {
        file_path: tempPath,
        original_filename: req.file.originalname,
        known_companies: companies.map((c) => ({
          id: c.id,
          name: c.name,
          ticker: c.ticker,
        })),
      });

      res.json(aiResp.data);
    } catch (err: any) {
      res.status(500).json({ error: `Detection failed: ${err.message}` });
    } finally {
      if (tempPath && fs.existsSync(tempPath)) {
        try {
          fs.unlinkSync(tempPath);
        } catch {}
      }
    }
  },
};

