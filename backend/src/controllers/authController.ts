import { Request, Response } from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import { db } from '../db';
import { config } from '../config';
import { AuthRequest } from '../middleware/auth';

export const authController = {
  async register(req: Request, res: Response): Promise<void> {
    try {
      const { email, password, full_name } = req.body;
      if (!email || !password) {
        res.status(400).json({ error: 'Email and password are required' });
        return;
      }

      const existing = await db.findUserByEmail(email);
      if (existing) {
        res.status(409).json({ error: 'User already exists with this email' });
        return;
      }

      const password_hash = await bcrypt.hash(password, 10);
      const user = await db.createUser({
        email,
        password_hash,
        full_name: full_name || '',
        role: 'analyst',
      });

      const token = jwt.sign(
        { id: user.id, email: user.email, role: user.role },
        config.jwtSecret,
        { expiresIn: '7d' }
      );

      res.status(201).json({
        user: { id: user.id, email: user.email, full_name: user.full_name, role: user.role },
        token,
      });
    } catch (err: any) {
      res.status(500).json({ error: `Registration failed: ${err.message}` });
    }
  },

  async login(req: Request, res: Response): Promise<void> {
    try {
      const { email, password } = req.body;
      if (!email || !password) {
        res.status(400).json({ error: 'Email and password are required' });
        return;
      }

      const user = await db.findUserByEmail(email);
      if (!user) {
        res.status(401).json({ error: 'Invalid email or password' });
        return;
      }

      const isMatch = await bcrypt.compare(password, user.password_hash);
      if (!isMatch) {
        res.status(401).json({ error: 'Invalid email or password' });
        return;
      }

      const token = jwt.sign(
        { id: user.id, email: user.email, role: user.role },
        config.jwtSecret,
        { expiresIn: '7d' }
      );

      res.json({
        user: { id: user.id, email: user.email, full_name: user.full_name, role: user.role },
        token,
      });
    } catch (err: any) {
      res.status(500).json({ error: `Login failed: ${err.message}` });
    }
  },

  async getMe(req: AuthRequest, res: Response): Promise<void> {
    if (!req.user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }
    const user = await db.findUserByEmail(req.user.email);
    if (!user) {
      res.status(404).json({ error: 'User not found' });
      return;
    }
    res.json({
      user: { id: user.id, email: user.email, full_name: user.full_name, role: user.role },
    });
  },
};
