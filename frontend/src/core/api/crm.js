/**
 * CRM API Service
 * V1 Layered Architecture endpoints for CRM module
 */
import { v1Api } from './client';

export const crmApi = {
  // Leads
  leads: {
    getAll: (params) => v1Api.get('/crm/leads', { params }),
    getKanban: () => v1Api.get('/crm/leads/kanban/view'),
    getById: (id) => v1Api.get(`/crm/leads/${id}`),
    create: (data) => v1Api.post('/crm/leads', data),
    update: (id, data) => v1Api.put(`/crm/leads/${id}`, data),
    delete: (id) => v1Api.delete(`/crm/leads/${id}`),
    updateStatus: (id, status) => v1Api.put(`/crm/leads/${id}/status`, { status }),
    convertToAccount: (id) => v1Api.post(`/crm/leads/${id}/convert`)
  },

  // Accounts
  accounts: {
    getAll: (params) => v1Api.get('/crm/accounts', { params }),
    getById: (id) => v1Api.get(`/crm/accounts/${id}`),
    create: (data) => v1Api.post('/crm/accounts', data),
    update: (id, data) => v1Api.put(`/crm/accounts/${id}`, data),
    delete: (id) => v1Api.delete(`/crm/accounts/${id}`)
  },

  // Quotations
  quotations: {
    getAll: (params) => v1Api.get('/crm/quotations', { params }),
    getById: (id) => v1Api.get(`/crm/quotations/${id}`),
    create: (data) => v1Api.post('/crm/quotations', data),
    update: (id, data) => v1Api.put(`/crm/quotations/${id}`, data),
    delete: (id) => v1Api.delete(`/crm/quotations/${id}`),
    convertToOrder: (id) => v1Api.post(`/crm/quotations/${id}/convert`)
  },

  // Samples
  samples: {
    getAll: (params) => v1Api.get('/crm/samples', { params }),
    getPendingFeedback: () => v1Api.get('/crm/samples/pending-feedback'),
    getById: (id) => v1Api.get(`/crm/samples/${id}`),
    create: (data) => v1Api.post('/crm/samples', data),
    update: (id, data) => v1Api.put(`/crm/samples/${id}`, data),
    delete: (id) => v1Api.delete(`/crm/samples/${id}`),
    updateStatus: (id, status) => v1Api.put(`/crm/samples/${id}/status`, null, { params: { status } }),
    recordFeedback: (id, feedback, status) => v1Api.post(`/crm/samples/${id}/feedback`, null, { params: { feedback, status } })
  }
};

export default crmApi;
