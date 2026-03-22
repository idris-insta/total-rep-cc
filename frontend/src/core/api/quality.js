/**
 * Quality API Service
 * V1 Layered Architecture endpoints for Quality module
 */
import { v1Api } from './client';

export const qualityApi = {
  // Inspections
  inspections: {
    getAll: (params) => v1Api.get('/quality/inspections', { params }),
    getFailed: () => v1Api.get('/quality/inspections/failed'),
    getStats: (startDate, endDate) => v1Api.get('/quality/inspections/stats', { 
      params: { start_date: startDate, end_date: endDate } 
    }),
    getById: (id) => v1Api.get(`/quality/inspections/${id}`),
    create: (data) => v1Api.post('/quality/inspections', data)
  },

  // Complaints
  complaints: {
    getAll: (params) => v1Api.get('/quality/complaints', { params }),
    getOpen: () => v1Api.get('/quality/complaints/open'),
    getStats: () => v1Api.get('/quality/complaints/stats'),
    getById: (id) => v1Api.get(`/quality/complaints/${id}`),
    create: (data) => v1Api.post('/quality/complaints', data),
    updateStatus: (id, status, resolution) => v1Api.put(`/quality/complaints/${id}/status`, null, { 
      params: { status, resolution } 
    })
  }
};

export default qualityApi;
