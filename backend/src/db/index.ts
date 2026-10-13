import { Pool } from 'pg';
import { config } from '../config';
import { v4 as uuidv4 } from 'uuid';

export interface User {
  id: string;
  email: string;
  password_hash: string;
  full_name: string;
  role: string;
  created_at?: Date;
}

export interface Company {
  id: string;
  name: string;
  ticker?: string;
  country?: string;
  reporting_currency?: string;
  sector?: string;
  industry?: string;
}

export interface DocumentRecord {
  id: string;
  company_id: string;
  fiscal_year: number;
  period_type: string;
  document_type: string;
  original_filename: string;
  storage_path: string;
  status: string;
  total_pages?: number;
  created_at: Date;
}

export interface DocumentJob {
  id: string;
  document_id: string;
  stage: string;
  progress_percent: number;
  error_message?: string;
  created_at: Date;
  updated_at: Date;
}

export interface ChatSession {
  id: string;
  user_id: string;
  title: string;
  created_at: Date;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  structured_payload?: any;
  created_at: Date;
}

// In-Memory Fallback Store (Ensures seamless testing even without running Postgres)
class InMemoryStore {
  users: Map<string, User> = new Map();
  companies: Map<string, Company> = new Map([
    ['company_a', { id: 'company_a', name: 'Example Corp A', ticker: 'EXA', country: 'US', reporting_currency: 'USD', sector: 'Technology' }],
    ['msft', { id: 'msft', name: 'Microsoft Corporation', ticker: 'MSFT', country: 'US', reporting_currency: 'USD', sector: 'Technology' }],
    ['aapl', { id: 'aapl', name: 'Apple Inc.', ticker: 'AAPL', country: 'US', reporting_currency: 'USD', sector: 'Technology' }],
  ]);
  documents: Map<string, DocumentRecord> = new Map();
  jobs: Map<string, DocumentJob> = new Map();
  chatSessions: Map<string, ChatSession> = new Map();
  chatMessages: Map<string, ChatMessage[]> = new Map();
}

export const inMemoryDb = new InMemoryStore();

let pool: Pool | null = null;
try {
  pool = new Pool({
    connectionString: config.databaseUrl,
    connectionTimeoutMillis: 2000,
  });
} catch {
  pool = null;
}

export const db = {
  // User operations
  async findUserByEmail(email: string): Promise<User | null> {
    if (pool) {
      try {
        const res = await pool.query('SELECT * FROM users WHERE email = $1', [email]);
        if (res.rows.length > 0) return res.rows[0];
      } catch {}
    }
    for (const u of inMemoryDb.users.values()) {
      if (u.email.toLowerCase() === email.toLowerCase()) return u;
    }
    return null;
  },

  async createUser(user: Omit<User, 'id'>): Promise<User> {
    const newUser: User = { ...user, id: uuidv4(), created_at: new Date() };
    if (pool) {
      try {
        const res = await pool.query(
          'INSERT INTO users (id, email, password_hash, full_name, role) VALUES ($1, $2, $3, $4, $5) RETURNING *',
          [newUser.id, newUser.email, newUser.password_hash, newUser.full_name, newUser.role]
        );
        return res.rows[0];
      } catch {}
    }
    inMemoryDb.users.set(newUser.id, newUser);
    return newUser;
  },

  // Company operations
  async listCompanies(): Promise<Company[]> {
    if (pool) {
      try {
        const res = await pool.query('SELECT * FROM companies ORDER BY name ASC');
        if (res.rows.length > 0) return res.rows;
      } catch {}
    }
    return Array.from(inMemoryDb.companies.values());
  },

  async createCompany(comp: Company): Promise<Company> {
    if (pool) {
      try {
        const res = await pool.query(
          'INSERT INTO companies (id, name, ticker, country, reporting_currency, sector) VALUES ($1, $2, $3, $4, $5, $6) RETURNING *',
          [comp.id, comp.name, comp.ticker, comp.country || 'US', comp.reporting_currency || 'USD', comp.sector]
        );
        return res.rows[0];
      } catch {}
    }
    inMemoryDb.companies.set(comp.id, comp);
    return comp;
  },

  // Document operations
  async createDocument(doc: Omit<DocumentRecord, 'id' | 'created_at'>): Promise<DocumentRecord> {
    const newDoc: DocumentRecord = { ...doc, id: uuidv4(), created_at: new Date() };
    if (pool) {
      try {
        const res = await pool.query(
          `INSERT INTO documents (id, company_id, fiscal_year, period_type, document_type, original_filename, storage_path, status)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *`,
          [newDoc.id, newDoc.company_id, newDoc.fiscal_year, newDoc.period_type, newDoc.document_type, newDoc.original_filename, newDoc.storage_path, newDoc.status]
        );
        return res.rows[0];
      } catch {}
    }
    inMemoryDb.documents.set(newDoc.id, newDoc);
    return newDoc;
  },

  async getDocument(id: string): Promise<DocumentRecord | null> {
    if (pool) {
      try {
        const res = await pool.query('SELECT * FROM documents WHERE id = $1', [id]);
        if (res.rows.length > 0) return res.rows[0];
      } catch {}
    }
    return inMemoryDb.documents.get(id) || null;
  },

  async listDocuments(companyId?: string): Promise<DocumentRecord[]> {
    if (pool) {
      try {
        const query = companyId
          ? 'SELECT * FROM documents WHERE company_id = $1 ORDER BY created_at DESC'
          : 'SELECT * FROM documents ORDER BY created_at DESC';
        const params = companyId ? [companyId] : [];
        const res = await pool.query(query, params);
        return res.rows;
      } catch {}
    }
    let docs = Array.from(inMemoryDb.documents.values());
    if (companyId) docs = docs.filter(d => d.company_id === companyId);
    return docs;
  },

  // Document Jobs
  async createJob(documentId: string): Promise<DocumentJob> {
    const job: DocumentJob = {
      id: uuidv4(),
      document_id: documentId,
      stage: 'QUEUED',
      progress_percent: 0,
      created_at: new Date(),
      updated_at: new Date(),
    };
    if (pool) {
      try {
        const res = await pool.query(
          'INSERT INTO document_jobs (id, document_id, stage, progress_percent) VALUES ($1, $2, $3, $4) RETURNING *',
          [job.id, job.document_id, job.stage, job.progress_percent]
        );
        return res.rows[0];
      } catch {}
    }
    inMemoryDb.jobs.set(job.id, job);
    return job;
  },

  async updateJob(jobId: string, updates: Partial<DocumentJob>): Promise<DocumentJob | null> {
    if (pool) {
      try {
        const fields = [];
        const values = [jobId];
        let idx = 2;
        if (updates.stage) { fields.push(`stage = $${idx++}`); values.push(updates.stage); }
        if (updates.progress_percent !== undefined) { fields.push(`progress_percent = $${idx++}`); values.push(updates.progress_percent.toString()); }
        if (updates.error_message) { fields.push(`error_message = $${idx++}`); values.push(updates.error_message); }
        fields.push(`updated_at = CURRENT_TIMESTAMP`);

        const res = await pool.query(
          `UPDATE document_jobs SET ${fields.join(', ')} WHERE id = $1 RETURNING *`,
          values
        );
        if (res.rows.length > 0) return res.rows[0];
      } catch {}
    }
    const current = inMemoryDb.jobs.get(jobId);
    if (!current) return null;
    const updated = { ...current, ...updates, updated_at: new Date() };
    inMemoryDb.jobs.set(jobId, updated);
    return updated;
  },

  async getJobByDocumentId(documentId: string): Promise<DocumentJob | null> {
    if (pool) {
      try {
        const res = await pool.query(
          'SELECT * FROM document_jobs WHERE document_id = $1 ORDER BY created_at DESC LIMIT 1',
          [documentId]
        );
        if (res.rows.length > 0) return res.rows[0];
      } catch {}
    }
    for (const j of inMemoryDb.jobs.values()) {
      if (j.document_id === documentId) return j;
    }
    return null;
  },

  // Chat sessions
  async createSession(userId: string, title?: string): Promise<ChatSession> {
    const session: ChatSession = {
      id: uuidv4(),
      user_id: userId,
      title: title || 'New Financial Analysis',
      created_at: new Date(),
    };
    if (pool) {
      try {
        const res = await pool.query(
          'INSERT INTO chat_sessions (id, user_id, title) VALUES ($1, $2, $3) RETURNING *',
          [session.id, session.user_id, session.title]
        );
        return res.rows[0];
      } catch {}
    }
    inMemoryDb.chatSessions.set(session.id, session);
    inMemoryDb.chatMessages.set(session.id, []);
    return session;
  },

  async listSessions(userId: string): Promise<ChatSession[]> {
    if (pool) {
      try {
        const res = await pool.query('SELECT * FROM chat_sessions WHERE user_id = $1 ORDER BY created_at DESC', [userId]);
        return res.rows;
      } catch {}
    }
    return Array.from(inMemoryDb.chatSessions.values()).filter(s => s.user_id === userId);
  },

  async addMessage(msg: Omit<ChatMessage, 'id' | 'created_at'>): Promise<ChatMessage> {
    const newMsg: ChatMessage = { ...msg, id: uuidv4(), created_at: new Date() };
    if (pool) {
      try {
        const res = await pool.query(
          'INSERT INTO chat_messages (id, session_id, role, content, structured_payload) VALUES ($1, $2, $3, $4, $5) RETURNING *',
          [newMsg.id, newMsg.session_id, newMsg.role, newMsg.content, JSON.stringify(newMsg.structured_payload || {})]
        );
        return res.rows[0];
      } catch {}
    }
    const list = inMemoryDb.chatMessages.get(newMsg.session_id) || [];
    list.push(newMsg);
    inMemoryDb.chatMessages.set(newMsg.session_id, list);
    return newMsg;
  },

  async getMessages(sessionId: string): Promise<ChatMessage[]> {
    if (pool) {
      try {
        const res = await pool.query('SELECT * FROM chat_messages WHERE session_id = $1 ORDER BY created_at ASC', [sessionId]);
        return res.rows;
      } catch {}
    }
    return inMemoryDb.chatMessages.get(sessionId) || [];
  },
};
