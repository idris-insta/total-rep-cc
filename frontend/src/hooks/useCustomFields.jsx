import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';

/**
 * Hook to fetch and manage custom fields for a module
 * @param {string} moduleId - The module identifier (e.g., 'crm_leads', 'inventory_items')
 * @returns {Object} - { fields, loading, error, refetch }
 */
export const useCustomFields = (moduleId) => {
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchFields = useCallback(async () => {
    if (!moduleId) {
      setFields([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/custom-fields/fields/${moduleId}`);
      setFields(res.data || []);
    } catch (err) {
      console.error(`Failed to fetch custom fields for ${moduleId}:`, err);
      setError(err.response?.data?.detail || 'Failed to load custom fields');
      setFields([]);
    } finally {
      setLoading(false);
    }
  }, [moduleId]);

  useEffect(() => {
    fetchFields();
  }, [fetchFields]);

  return {
    fields,
    loading,
    error,
    refetch: fetchFields,
    // Group fields by section
    fieldsBySection: fields.reduce((acc, field) => {
      const section = field.section || 'Additional Information';
      if (!acc[section]) acc[section] = [];
      acc[section].push(field);
      return acc;
    }, {}),
    // Get field names for form initialization
    fieldNames: fields.map(f => f.field_name),
    // Generate initial values object
    getInitialValues: () => {
      const values = {};
      fields.forEach(f => {
        if (f.default_value) {
          values[f.field_name] = f.default_value;
        } else if (f.field_type === 'checkbox') {
          values[f.field_name] = false;
        } else if (f.field_type === 'multiselect') {
          values[f.field_name] = [];
        } else {
          values[f.field_name] = '';
        }
      });
      return values;
    }
  };
};

export default useCustomFields;
