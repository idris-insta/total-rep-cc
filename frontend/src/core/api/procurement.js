/**
 * Procurement API Service
 * V1 Layered Architecture endpoints for Procurement module
 */
import { v1Api } from './client';

export const procurementApi = {
  // Suppliers
  suppliers: {
    getAll: (params) => v1Api.get('/procurement/suppliers', { params }),
    getById: (id) => v1Api.get(`/procurement/suppliers/${id}`),
    create: (data) => v1Api.post('/procurement/suppliers', data),
    update: (id, data) => v1Api.put(`/procurement/suppliers/${id}`, data)
  },

  // Purchase Orders
  purchaseOrders: {
    getAll: (params) => v1Api.get('/procurement/purchase-orders', { params }),
    getPending: () => v1Api.get('/procurement/purchase-orders/pending'),
    getById: (id) => v1Api.get(`/procurement/purchase-orders/${id}`),
    create: (data) => v1Api.post('/procurement/purchase-orders', data),
    send: (id) => v1Api.put(`/procurement/purchase-orders/${id}/send`),
    cancel: (id, reason) => v1Api.put(`/procurement/purchase-orders/${id}/cancel`, null, { params: { reason } })
  },

  // GRN (Goods Receipt Notes)
  grn: {
    getAll: (params) => v1Api.get('/procurement/grn', { params }),
    create: (data) => v1Api.post('/procurement/grn', data)
  }
};

export default procurementApi;
