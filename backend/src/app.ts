import express from 'express';
import cors from 'cors';
import path from 'path';
import { config } from './config';
import apiRoutes from './routes';

export const createApp = (): express.Application => {
  const app = express();

  // Middleware
  app.use(cors({ origin: '*' }));
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Static files for uploaded reports
  app.use('/uploads', express.static(config.uploadDir));

  // Mount API router
  app.use('/api', apiRoutes);

  // Global error handler
  app.use((err: any, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
    console.error('Unhandled server error:', err);
    res.status(err.status || 500).json({
      error: err.message || 'Internal Server Error',
    });
  });

  return app;
};
