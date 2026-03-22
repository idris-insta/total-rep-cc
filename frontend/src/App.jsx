import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Toaster } from 'sonner';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import MainLayout from './components/layout/MainLayout';
import CRM from './pages/CRM';
import Inventory from './pages/Inventory';
import Production from './pages/Production';
import ProductionStages from './pages/ProductionStages';
import Procurement from './pages/Procurement';
import Accounts from './pages/Accounts';
import HRMS from './pages/HRMS';
import Quality from './pages/Quality';
import Settings from './pages/Settings';
import Customization from './pages/Customization';
import Approvals from './pages/Approvals';
import Reports from './pages/Reports';
import DirectorDashboard from './pages/DirectorDashboard';
import Gatepass from './pages/Gatepass';
import PayrollPage from './pages/PayrollPage';
import ImportBridge from './pages/ImportBridge';
import EmployeeVault from './pages/EmployeeVault';
import SalesIncentives from './pages/SalesIncentives';
import GSTCompliance from './pages/GSTCompliance';
import ReportsDashboard from './pages/ReportsDashboard';
import HRMSDashboard from './pages/HRMSDashboard';
import AdvancedInventory from './pages/AdvancedInventory';
import PowerSettings from './pages/PowerSettings';
import DocumentEditor from './pages/DocumentEditor';
import AIBIDashboard from './pages/AIBIDashboard';
import Chat from './pages/Chat';
import Drive from './pages/Drive';
import BulkImport from './pages/BulkImport';
import EInvoice from './pages/EInvoice';
import AutonomousCollector from './pages/AutonomousCollector';
import BuyingDNA from './pages/BuyingDNA';
import CustomerHealth from './pages/CustomerHealth';
import FieldRegistry from './pages/FieldRegistry';
import WarehouseDashboard from './pages/WarehouseDashboard';
import WarehouseForm from './pages/WarehouseForm';
import StockRegister from './pages/StockRegister';
import { StockTransferList, StockTransferForm } from './pages/StockTransfer';
import { StockAdjustmentList, StockAdjustmentForm } from './pages/StockAdjustment';


const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" />;
};

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <MainLayout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/crm/*" element={<CRM />} />
                <Route path="/inventory/*" element={<Inventory />} />
                <Route path="/advanced-inventory" element={<AdvancedInventory />} />
                <Route path="/production/*" element={<Production />} />
                <Route path="/production-stages/*" element={<ProductionStages />} />
                <Route path="/procurement/*" element={<Procurement />} />
                <Route path="/accounts/*" element={<Accounts />} />
                <Route path="/hrms/*" element={<HRMS />} />
                <Route path="/quality/*" element={<Quality />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/approvals" element={<Approvals />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/customization" element={<Customization />} />
                <Route path="/director" element={<DirectorDashboard />} />
                <Route path="/gatepass" element={<Gatepass />} />
                <Route path="/payroll" element={<PayrollPage />} />
                <Route path="/import-bridge" element={<ImportBridge />} />
                <Route path="/employee-vault" element={<EmployeeVault />} />
                <Route path="/sales-incentives" element={<SalesIncentives />} />
                <Route path="/gst-compliance" element={<GSTCompliance />} />
                <Route path="/analytics" element={<ReportsDashboard />} />
                <Route path="/hrms-dashboard" element={<HRMSDashboard />} />
                <Route path="/power-settings" element={<PowerSettings />} />
                <Route path="/document-editor" element={<DocumentEditor />} />
                <Route path="/ai-dashboard" element={<AIBIDashboard />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/drive" element={<Drive />} />
                <Route path="/bulk-import" element={<BulkImport />} />
                <Route path="/einvoice" element={<EInvoice />} />
                <Route path="/collector" element={<AutonomousCollector />} />
                <Route path="/buying-dna" element={<BuyingDNA />} />
                <Route path="/customer-health" element={<CustomerHealth />} />
                <Route path="/field-registry" element={<FieldRegistry />} />
                
                {/* Warehouse & Inventory Management Routes */}
                <Route path="/inventory/warehouses" element={<WarehouseDashboard />} />
                <Route path="/inventory/warehouses/new" element={<WarehouseForm />} />
                <Route path="/inventory/warehouses/:warehouseId" element={<WarehouseForm />} />
                <Route path="/inventory/stock-register" element={<StockRegister />} />
                <Route path="/inventory/stock-transfers" element={<StockTransferList />} />
                <Route path="/inventory/stock-transfers/new" element={<StockTransferForm />} />
                <Route path="/inventory/stock-adjustments" element={<StockAdjustmentList />} />
                <Route path="/inventory/stock-adjustments/new" element={<StockAdjustmentForm />} />
              </Routes>
            </MainLayout>
          </PrivateRoute>
        }
      />
    </Routes>
  );
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;