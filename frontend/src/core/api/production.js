/**
 * Production API Service
 * V1 Layered Architecture endpoints for Production module
 */
import { v1Api } from './client';

export const productionApi = {
  // Machines
  machines: {
    getAll: (params) => v1Api.get('/production/machines', { params }),
    getAvailable: () => v1Api.get('/production/machines/available'),
    getById: (id) => v1Api.get(`/production/machines/${id}`),
    getUtilization: (id, startDate, endDate) => v1Api.get(`/production/machines/${id}/utilization`, { 
      params: { start_date: startDate, end_date: endDate } 
    }),
    create: (data) => v1Api.post('/production/machines', data),
    update: (id, data) => v1Api.put(`/production/machines/${id}`, data)
  },

  // Order Sheets
  orderSheets: {
    getAll: (params) => v1Api.get('/production/order-sheets', { params }),
    getPending: () => v1Api.get('/production/order-sheets/pending'),
    getById: (id) => v1Api.get(`/production/order-sheets/${id}`),
    create: (data) => v1Api.post('/production/order-sheets', data),
    update: (id, data) => v1Api.put(`/production/order-sheets/${id}`, data),
    start: (id) => v1Api.put(`/production/order-sheets/${id}/start`),
    complete: (id) => v1Api.put(`/production/order-sheets/${id}/complete`)
  },

  // Work Orders
  workOrders: {
    getAll: (params) => v1Api.get('/production/work-orders', { params }),
    getInProgress: () => v1Api.get('/production/work-orders/in-progress'),
    getById: (id) => v1Api.get(`/production/work-orders/${id}`),
    create: (data) => v1Api.post('/production/work-orders', data),
    update: (id, data) => v1Api.put(`/production/work-orders/${id}`, data),
    assignMachine: (id, machineId) => v1Api.put(`/production/work-orders/${id}/assign-machine/${machineId}`),
    start: (id) => v1Api.put(`/production/work-orders/${id}/start`),
    complete: (id) => v1Api.put(`/production/work-orders/${id}/complete`),
    // Production Entries
    getEntries: (id) => v1Api.get(`/production/work-orders/${id}/entries`),
    createEntry: (id, data) => v1Api.post(`/production/work-orders/${id}/entries`, data)
  }
};

export default productionApi;
