/**
 * Shared Utility Functions
 * Common helper functions used across modules
 */

// ==================== DATE UTILITIES ====================
export const formatDate = (dateString, format = 'DD/MM/YYYY') => {
  if (!dateString) return '';
  const date = new Date(dateString);
  
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  
  switch (format) {
    case 'DD/MM/YYYY':
      return `${day}/${month}/${year}`;
    case 'YYYY-MM-DD':
      return `${year}-${month}-${day}`;
    case 'DD MMM YYYY':
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      return `${day} ${months[date.getMonth()]} ${year}`;
    default:
      return date.toLocaleDateString();
  }
};

export const formatDateTime = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString();
};

export const getRelativeTime = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return formatDate(dateString, 'DD MMM YYYY');
};

// ==================== CURRENCY UTILITIES ====================
export const formatCurrency = (amount, currency = 'INR') => {
  if (amount === null || amount === undefined) return '';
  
  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  
  return formatter.format(amount);
};

export const formatNumber = (num, decimals = 0) => {
  if (num === null || num === undefined) return '';
  return new Intl.NumberFormat('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
};

// ==================== STRING UTILITIES ====================
export const truncate = (str, length = 50) => {
  if (!str) return '';
  return str.length > length ? `${str.substring(0, length)}...` : str;
};

export const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
};

export const toTitleCase = (str) => {
  if (!str) return '';
  return str.split(' ').map(capitalize).join(' ');
};

export const slugify = (str) => {
  if (!str) return '';
  return str
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

// ==================== VALIDATION UTILITIES ====================
export const isValidEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

export const isValidPhone = (phone) => {
  const re = /^[6-9]\d{9}$/;
  return re.test(phone?.replace(/\D/g, ''));
};

export const isValidGSTIN = (gstin) => {
  const re = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
  return re.test(gstin);
};

export const isValidPAN = (pan) => {
  const re = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;
  return re.test(pan);
};

// ==================== OBJECT UTILITIES ====================
export const pick = (obj, keys) => {
  return keys.reduce((acc, key) => {
    if (obj && Object.prototype.hasOwnProperty.call(obj, key)) {
      acc[key] = obj[key];
    }
    return acc;
  }, {});
};

export const omit = (obj, keys) => {
  return Object.keys(obj)
    .filter(key => !keys.includes(key))
    .reduce((acc, key) => {
      acc[key] = obj[key];
      return acc;
    }, {});
};

export const isEmpty = (value) => {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
};

// ==================== ARRAY UTILITIES ====================
export const groupBy = (array, key) => {
  return array.reduce((acc, item) => {
    const groupKey = typeof key === 'function' ? key(item) : item[key];
    (acc[groupKey] = acc[groupKey] || []).push(item);
    return acc;
  }, {});
};

export const sortBy = (array, key, order = 'asc') => {
  return [...array].sort((a, b) => {
    const aVal = typeof key === 'function' ? key(a) : a[key];
    const bVal = typeof key === 'function' ? key(b) : b[key];
    
    if (aVal < bVal) return order === 'asc' ? -1 : 1;
    if (aVal > bVal) return order === 'asc' ? 1 : -1;
    return 0;
  });
};

export const uniqueBy = (array, key) => {
  const seen = new Set();
  return array.filter(item => {
    const k = typeof key === 'function' ? key(item) : item[key];
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
};

// ==================== COLOR UTILITIES ====================
export const getStatusColor = (status) => {
  const colors = {
    // Success states
    active: 'bg-green-100 text-green-800',
    completed: 'bg-green-100 text-green-800',
    approved: 'bg-green-100 text-green-800',
    paid: 'bg-green-100 text-green-800',
    delivered: 'bg-green-100 text-green-800',
    
    // Warning states
    pending: 'bg-yellow-100 text-yellow-800',
    in_progress: 'bg-blue-100 text-blue-800',
    draft: 'bg-slate-100 text-slate-800',
    
    // Error states
    cancelled: 'bg-red-100 text-red-800',
    rejected: 'bg-red-100 text-red-800',
    failed: 'bg-red-100 text-red-800',
    overdue: 'bg-red-100 text-red-800',
    
    // Default
    default: 'bg-gray-100 text-gray-800',
  };
  
  return colors[status?.toLowerCase()] || colors.default;
};

export const getPriorityColor = (priority) => {
  const colors = {
    urgent: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    normal: 'bg-blue-100 text-blue-800 border-blue-200',
    low: 'bg-slate-100 text-slate-800 border-slate-200',
  };
  
  return colors[priority?.toLowerCase()] || colors.normal;
};

// ==================== EXPORT ALL ====================
export default {
  formatDate,
  formatDateTime,
  getRelativeTime,
  formatCurrency,
  formatNumber,
  truncate,
  capitalize,
  toTitleCase,
  slugify,
  isValidEmail,
  isValidPhone,
  isValidGSTIN,
  isValidPAN,
  pick,
  omit,
  isEmpty,
  groupBy,
  sortBy,
  uniqueBy,
  getStatusColor,
  getPriorityColor,
};
