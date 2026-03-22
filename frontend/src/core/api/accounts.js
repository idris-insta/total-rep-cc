/**
 * Accounts API Service
 * V1 Layered Architecture endpoints for Accounts module
 */
import { v1Api } from './client';

export const accountsApi = {
  // Invoices
  invoices: {
    getAll: (params) => v1Api.get('/accounts/invoices', { params }),
    getOverdue: () => v1Api.get('/accounts/invoices/overdue'),
    getAging: () => v1Api.get('/accounts/invoices/aging'),
    getById: (id) => v1Api.get(`/accounts/invoices/${id}`),
    create: (data) => v1Api.post('/accounts/invoices', data),
    updateStatus: (id, status) => v1Api.put(`/accounts/invoices/${id}/status`, null, { params: { status } }),
    recordPayment: (id, amount) => v1Api.post(`/accounts/invoices/${id}/payment`, null, { params: { amount } })
  },

  // Payments
  payments: {
    getAll: (params) => v1Api.get('/accounts/payments', { params }),
    create: (data) => v1Api.post('/accounts/payments', data)
  }
};

export default accountsApi;
