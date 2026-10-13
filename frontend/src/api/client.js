import axios from 'axios';

const API_BASE = '/api';

export const apiClient = {
  async getCompanies() {
    const res = await axios.get(`${API_BASE}/companies`);
    return res.data;
  },

  async detectDocumentMetadata(formData) {
    const res = await axios.post(`${API_BASE}/documents/detect`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  async uploadDocument(formData) {
    const res = await axios.post(`${API_BASE}/documents/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  async getDocumentStatus(docId) {
    const res = await axios.get(`${API_BASE}/documents/${docId}/status`);
    return res.data;
  },

  async getDocuments(companyId) {
    const params = companyId ? { company_id: companyId } : {};
    const res = await axios.get(`${API_BASE}/documents`, { params });
    return res.data;
  },

  async queryChat({ session_id, question, company_ids, fiscal_years }) {
    const res = await axios.post(`${API_BASE}/chat/query`, {
      session_id,
      question,
      company_ids,
      fiscal_years,
    });
    return res.data;
  },

  async getCompanyFinancials(companyId, years) {
    const params = years ? { years: years.join(',') } : {};
    const res = await axios.get(`${API_BASE}/companies/${companyId}/financials`, { params });
    return res.data;
  },
};
