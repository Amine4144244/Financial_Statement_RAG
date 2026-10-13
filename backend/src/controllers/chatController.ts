import { Request, Response } from 'express';
import axios from 'axios';
import { db } from '../db';
import { config } from '../config';
import { AuthRequest } from '../middleware/auth';

export const chatController = {
  async createSession(req: AuthRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id || 'anonymous_user';
      const { title } = req.body;
      const session = await db.createSession(userId, title);
      res.status(201).json(session);
    } catch (err: any) {
      res.status(500).json({ error: `Failed to create session: ${err.message}` });
    }
  },

  async listSessions(req: AuthRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id || 'anonymous_user';
      const sessions = await db.listSessions(userId);
      res.json(sessions);
    } catch (err: any) {
      res.status(500).json({ error: `Failed to list sessions: ${err.message}` });
    }
  },

  async getMessages(req: Request, res: Response): Promise<void> {
    try {
      const { sessionId } = req.params;
      const messages = await db.getMessages(sessionId);
      res.json(messages);
    } catch (err: any) {
      res.status(500).json({ error: `Failed to fetch messages: ${err.message}` });
    }
  },

  async submitQuery(req: AuthRequest, res: Response): Promise<void> {
    try {
      const { session_id, question, company_ids, fiscal_years } = req.body;
      if (!question) {
        res.status(400).json({ error: 'Question is required' });
        return;
      }

      const activeSessionId = session_id || (await db.createSession(req.user?.id || 'guest', 'New Analysis')).id;

      // 1. Record user message
      await db.addMessage({
        session_id: activeSessionId,
        role: 'user',
        content: question,
      });

      // 2. Call FastAPI RAG query endpoint
      let ragResponse;
      try {
        const aiResp = await axios.post(`${config.aiServiceUrl}/internal/rag/query`, {
          question,
          company_ids,
          fiscal_years,
        });
        ragResponse = aiResp.data;
      } catch (aiErr: any) {
        ragResponse = {
          answer: 'Unable to communicate with AI service at this time.',
          status: 'failed',
          metrics_retrieved: [],
          calculations: [],
          citations: [],
          validation_status: 'error',
          validation_warnings: [aiErr.message],
        };
      }

      // 3. Record assistant message
      const assistantMessage = await db.addMessage({
        session_id: activeSessionId,
        role: 'assistant',
        content: ragResponse.answer,
        structured_payload: {
          intent: ragResponse.intent,
          metrics_retrieved: ragResponse.metrics_retrieved,
          calculations: ragResponse.calculations,
          citations: ragResponse.citations,
          validation_status: ragResponse.validation_status,
          validation_warnings: ragResponse.validation_warnings,
        },
      });

      res.json({
        session_id: activeSessionId,
        message: assistantMessage,
        data: ragResponse,
      });
    } catch (err: any) {
      res.status(500).json({ error: `Query failed: ${err.message}` });
    }
  },
};
