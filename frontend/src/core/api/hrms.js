/**
 * HRMS API Service
 * V1 Layered Architecture endpoints for HRMS module
 */
import { v1Api } from './client';

export const hrmsApi = {
  // Employees
  employees: {
    getAll: (params) => v1Api.get('/hrms/employees', { params }),
    getById: (id) => v1Api.get(`/hrms/employees/${id}`),
    create: (data) => v1Api.post('/hrms/employees', data),
    update: (id, data) => v1Api.put(`/hrms/employees/${id}`, data),
    terminate: (id, terminationDate, reason) => v1Api.put(`/hrms/employees/${id}/terminate`, null, { 
      params: { termination_date: terminationDate, reason } 
    })
  },

  // Attendance
  attendance: {
    getAll: (params) => v1Api.get('/hrms/attendance', { params }),
    mark: (data) => v1Api.post('/hrms/attendance', data),
    checkIn: (employeeId) => v1Api.post(`/hrms/attendance/${employeeId}/check-in`),
    checkOut: (employeeId) => v1Api.post(`/hrms/attendance/${employeeId}/check-out`),
    getMonthlySummary: (employeeId, year, month) => v1Api.get(`/hrms/attendance/${employeeId}/monthly-summary`, {
      params: { year, month }
    })
  },

  // Leave Requests
  leaveRequests: {
    getAll: (params) => v1Api.get('/hrms/leave-requests', { params }),
    getPending: () => v1Api.get('/hrms/leave-requests/pending'),
    create: (data) => v1Api.post('/hrms/leave-requests', data),
    approve: (id) => v1Api.put(`/hrms/leave-requests/${id}/approve`),
    reject: (id, reason) => v1Api.put(`/hrms/leave-requests/${id}/reject`, null, { params: { reason } })
  },

  // Payroll
  payroll: {
    getAll: (params) => v1Api.get('/hrms/payroll', { params }),
    generate: (employeeId, year, month) => v1Api.post('/hrms/payroll/generate', null, {
      params: { employee_id: employeeId, year, month }
    })
  }
};

export default hrmsApi;
