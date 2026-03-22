/**
 * CRM Module - Main Container Page
 * Routes all CRM sub-modules: Overview, Leads, Accounts, Quotations, Samples
 */
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import CRMOverview from './CRMOverview';
import LeadsPage from '../../../pages/LeadsPage';
import { AccountsList, QuotationsList, SamplesList } from '../components';

const CRMPage = () => {
  return (
    <Routes>
      <Route index element={<CRMOverview />} />
      <Route path="leads" element={<LeadsPage />} />
      <Route path="accounts" element={<AccountsList />} />
      <Route path="quotations" element={<QuotationsList />} />
      <Route path="samples" element={<SamplesList />} />
    </Routes>
  );
};

export default CRMPage;
