/**
 * Core API Module Exports
 * Provides access to both legacy API and new V1 layered architecture APIs
 */
export { default as apiClient, v1Api, setAuthToken, clearAuthToken, getAuthToken } from './client';

// V1 API Module Services
export { crmApi } from './crm';
export { inventoryApi } from './inventory';
export { productionApi } from './production';
export { accountsApi } from './accounts';
export { hrmsApi } from './hrms';
export { procurementApi } from './procurement';
export { qualityApi } from './quality';
export { salesIncentivesApi } from './salesIncentives';
export { settingsApi } from './settings';

