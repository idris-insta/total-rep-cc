/**
 * CRM Module - Entry Point
 * 
 * This is a simplified wrapper that delegates to the modular CRM implementation.
 * The actual components are now organized in /modules/crm/ for better maintainability.
 * 
 * Component Structure:
 * - /modules/crm/pages/CRMOverview.jsx - Dashboard overview
 * - /modules/crm/components/AccountsList.jsx - Customer accounts management
 * - /modules/crm/components/QuotationsList.jsx - Quotations management
 * - /modules/crm/components/SamplesList.jsx - Samples management
 * - /pages/LeadsPage.jsx - Leads with Kanban board (standalone)
 */
import CRMPage from '../modules/crm/pages/CRMPage';

export default CRMPage;
