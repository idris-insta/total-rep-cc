/**
 * Inventory API Service
 * V1 Layered Architecture endpoints for Inventory module
 */
import { v1Api } from './client';

export const inventoryApi = {
  // Items
  items: {
    getAll: (params) => v1Api.get('/inventory/items', { params }),
    getLowStock: () => v1Api.get('/inventory/items/low-stock'),
    getById: (id) => v1Api.get(`/inventory/items/${id}`),
    getStock: (id) => v1Api.get(`/inventory/items/${id}/stock`),
    create: (data) => v1Api.post('/inventory/items', data),
    update: (id, data) => v1Api.put(`/inventory/items/${id}`, data),
    delete: (id) => v1Api.delete(`/inventory/items/${id}`)
  },

  // Warehouses
  warehouses: {
    getAll: (params) => v1Api.get('/inventory/warehouses', { params }),
    getById: (id) => v1Api.get(`/inventory/warehouses/${id}`),
    getStock: (id) => v1Api.get(`/inventory/warehouses/${id}/stock`),
    create: (data) => v1Api.post('/inventory/warehouses', data),
    update: (id, data) => v1Api.put(`/inventory/warehouses/${id}`, data)
  },

  // Stock Transfers
  transfers: {
    getAll: (params) => v1Api.get('/inventory/transfers', { params }),
    create: (data) => v1Api.post('/inventory/transfers', data),
    dispatch: (id) => v1Api.put(`/inventory/transfers/${id}/dispatch`),
    receive: (id) => v1Api.put(`/inventory/transfers/${id}/receive`)
  },

  // Stock Adjustments
  adjustments: {
    getAll: (params) => v1Api.get('/inventory/adjustments', { params }),
    getPending: () => v1Api.get('/inventory/adjustments/pending'),
    create: (data) => v1Api.post('/inventory/adjustments', data),
    approve: (id) => v1Api.put(`/inventory/adjustments/${id}/approve`)
  }
};

export default inventoryApi;
