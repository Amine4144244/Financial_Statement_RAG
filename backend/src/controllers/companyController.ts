import { Request, Response } from 'express';
import { db } from '../db';
import axios from 'axios';
import { config } from '../config';

export const companyController = {
  async listCompanies(req: Request, res: Response): Promise<void> {
    try {
      const companies = await db.listCompanies();
      res.json(companies);
    } catch (err: any) {
      res.status(500).json({ error: `Failed to fetch companies: ${err.message}` });
    }
  },

  async createCompany(req: Request, res: Response): Promise<void> {
    try {
      const { id, name, ticker, country, reporting_currency, sector } = req.body;
      if (!name) {
        res.status(400).json({ error: 'Company name is required' });
        return;
      }

      const compId = id || name.toLowerCase().replace(/[^a-z0-9]/g, '_');
      const company = await db.createCompany({
        id: compId,
        name,
        ticker,
        country: country || 'US',
        reporting_currency: reporting_currency || 'USD',
        sector,
      });

      res.status(201).json(company);
    } catch (err: any) {
      res.status(500).json({ error: `Failed to create company: ${err.message}` });
    }
  },

  async getFinancials(req: Request, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { years } = req.query;

      const parsedYears = years
        ? (years as string).split(',').map(y => parseInt(y.trim(), 10))
        : undefined;

      // Delegate query to FastAPI AI service
      const aiResponse = await axios.post(`${config.aiServiceUrl}/internal/rag/query`, {
        question: `Retrieve all verified financial statements and margins for ${id}`,
        company_ids: [id],
        fiscal_years: parsedYears,
      });

      res.json({
        company_id: id,
        facts: aiResponse.data.metrics_retrieved,
        calculations: aiResponse.data.calculations,
      });
    } catch (err: any) {
      res.status(500).json({ error: `Failed to fetch company financials: ${err.message}` });
    }
  },
};
