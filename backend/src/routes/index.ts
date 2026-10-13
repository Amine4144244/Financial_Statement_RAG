import { Router } from 'express';
import { authController } from '../controllers/authController';
import { companyController } from '../controllers/companyController';
import { documentController, uploadMiddleware } from '../controllers/documentController';
import { chatController } from '../controllers/chatController';
import { authenticateJwt } from '../middleware/auth';

const router = Router();

// Health
router.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'financial-rag-backend' });
});

// Auth Routes
router.post('/auth/register', authController.register);
router.post('/auth/login', authController.login);
router.get('/auth/me', authenticateJwt, authController.getMe);

// Company Routes
router.get('/companies', companyController.listCompanies);
router.post('/companies', authenticateJwt, companyController.createCompany);
router.get('/companies/:id/financials', companyController.getFinancials);

// Document Routes
router.post('/documents/detect', uploadMiddleware.single('file'), documentController.detectDocument);
router.post('/documents/upload', uploadMiddleware.single('file'), documentController.uploadDocument);
router.get('/documents/:id/status', documentController.getDocumentStatus);
router.get('/documents', documentController.listDocuments);

// Chat & Query Routes
router.post('/chat/query', chatController.submitQuery);
router.get('/chat/sessions', authenticateJwt, chatController.listSessions);
router.post('/chat/sessions', authenticateJwt, chatController.createSession);
router.get('/chat/sessions/:sessionId/messages', chatController.getMessages);

export default router;
