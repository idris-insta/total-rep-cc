/**
 * Settings API Service
 * V1 Layered Architecture endpoints for Settings module
 */
import { v1Api } from './client';

export const settingsApi = {
  // Field Registry
  fieldRegistry: {
    getAll: (module) => v1Api.get('/settings/field-registry', { params: { module } }),
    getModules: () => v1Api.get('/settings/field-registry/modules'),
    getConfig: (module, entity) => v1Api.get(`/settings/field-registry/${module}/${entity}`),
    saveConfig: (module, entity, data) => v1Api.post(`/settings/field-registry/${module}/${entity}`, data)
  },

  // System Settings
  system: {
    getAll: (category) => v1Api.get('/settings/system', { params: { category } }),
    get: (key) => v1Api.get(`/settings/system/${key}`),
    set: (key, value, category) => v1Api.post('/settings/system', { key, value, category })
  },

  // Branches
  branches: {
    getAll: (activeOnly = true) => v1Api.get('/settings/branches', { params: { active_only: activeOnly } }),
    getHeadOffice: () => v1Api.get('/settings/branches/head-office'),
    getById: (id) => v1Api.get(`/settings/branches/${id}`),
    create: (data) => v1Api.post('/settings/branches', data),
    update: (id, data) => v1Api.put(`/settings/branches/${id}`, data)
  },

  // Users
  users: {
    getAll: (params) => v1Api.get('/settings/users', { params }),
    getById: (id) => v1Api.get(`/settings/users/${id}`),
    create: (data) => v1Api.post('/settings/users', data),
    update: (id, data) => v1Api.put(`/settings/users/${id}`, data),
    deactivate: (id) => v1Api.put(`/settings/users/${id}/deactivate`)
  }
};

export default settingsApi;
