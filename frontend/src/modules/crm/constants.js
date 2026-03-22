/**
 * CRM Module - Shared Constants and Utilities
 */

// Status colors for badges and charts
export const STATUS_COLORS = {
  // Lead statuses
  new: 'bg-blue-500',
  contacted: 'bg-yellow-500',
  qualified: 'bg-green-500',
  proposal: 'bg-purple-500',
  negotiation: 'bg-orange-500',
  converted: 'bg-emerald-500',
  lost: 'bg-red-500',
  // Quote statuses
  draft: 'bg-slate-400',
  sent: 'bg-blue-500',
  accepted: 'bg-green-500',
  rejected: 'bg-red-500',
  expired: 'bg-yellow-500',
  // Sample statuses
  pending: 'bg-yellow-500',
  dispatched: 'bg-blue-500',
  delivered: 'bg-purple-500',
  feedback_received: 'bg-green-500'
};

// Badge colors for UI
export const BADGE_COLORS = {
  new: 'bg-blue-100 text-blue-800',
  contacted: 'bg-yellow-100 text-yellow-800',
  qualified: 'bg-green-100 text-green-800',
  proposal: 'bg-purple-100 text-purple-800',
  negotiation: 'bg-orange-100 text-orange-800',
  converted: 'bg-emerald-100 text-emerald-800',
  lost: 'bg-red-100 text-red-800',
  draft: 'bg-slate-100 text-slate-800',
  sent: 'bg-blue-100 text-blue-800',
  accepted: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  expired: 'bg-yellow-100 text-yellow-800',
  pending: 'bg-yellow-100 text-yellow-800',
  dispatched: 'bg-blue-100 text-blue-800',
  delivered: 'bg-purple-100 text-purple-800',
  feedback_received: 'bg-green-100 text-green-800'
};

// Lead sources
export const LEAD_SOURCES = [
  'IndiaMART',
  'TradeIndia',
  'Alibaba',
  'Website',
  'Referral',
  'Cold Call',
  'Exhibition',
  'Other'
];

// Lead statuses
export const LEAD_STATUSES = [
  'new',
  'contacted',
  'qualified',
  'proposal',
  'negotiation',
  'converted',
  'lost'
];

// Quote statuses
export const QUOTE_STATUSES = [
  'draft',
  'sent',
  'accepted',
  'rejected',
  'expired'
];

// Sample statuses
export const SAMPLE_STATUSES = [
  'pending',
  'dispatched',
  'delivered',
  'feedback_received'
];

// Payment terms options
export const PAYMENT_TERMS = [
  '100% Advance',
  '50% Advance, 50% on Delivery',
  '30 Days Credit',
  '45 Days Credit',
  '60 Days Credit',
  'Against Delivery'
];

// Format currency in INR
export const formatCurrency = (amount) => {
  if (!amount && amount !== 0) return '-';
  return `₹${Number(amount).toLocaleString('en-IN')}`;
};

// Format date
export const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric'
  });
};

// Get badge color class
export const getBadgeColor = (status) => {
  return BADGE_COLORS[status] || 'bg-slate-100 text-slate-800';
};
