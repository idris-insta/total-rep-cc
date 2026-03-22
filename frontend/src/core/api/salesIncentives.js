/**
 * Sales Incentives API Service
 * V1 Layered Architecture endpoints for Sales Incentives module
 */
import { v1Api } from './client';

export const salesIncentivesApi = {
  // Targets
  targets: {
    getAll: (params) => v1Api.get('/sales-incentives/targets', { params }),
    getActive: () => v1Api.get('/sales-incentives/targets/active'),
    getById: (id) => v1Api.get(`/sales-incentives/targets/${id}`),
    create: (data) => v1Api.post('/sales-incentives/targets', data),
    updateAchievement: (id, achievedAmount, achievedQuantity) => v1Api.put(
      `/sales-incentives/targets/${id}/achievement`,
      null,
      { params: { achieved_amount: achievedAmount, achieved_quantity: achievedQuantity } }
    )
  },

  // Slabs
  slabs: {
    getAll: (activeOnly = true) => v1Api.get('/sales-incentives/slabs', { params: { active_only: activeOnly } }),
    create: (data) => v1Api.post('/sales-incentives/slabs', data),
    update: (id, data) => v1Api.put(`/sales-incentives/slabs/${id}`, data)
  },

  // Payouts
  payouts: {
    getAll: (params) => v1Api.get('/sales-incentives/payouts', { params }),
    getPendingApproval: () => v1Api.get('/sales-incentives/payouts/pending-approval'),
    calculate: (targetId) => v1Api.post(`/sales-incentives/payouts/calculate/${targetId}`),
    approve: (id) => v1Api.put(`/sales-incentives/payouts/${id}/approve`),
    markPaid: (id, payrollId) => v1Api.put(`/sales-incentives/payouts/${id}/mark-paid`, null, { 
      params: { payroll_id: payrollId } 
    }),
    getLeaderboard: (period, limit = 10) => v1Api.get(`/sales-incentives/payouts/leaderboard/${period}`, { 
      params: { limit } 
    })
  }
};

export default salesIncentivesApi;
