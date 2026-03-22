import { useState, useEffect, useCallback } from 'react';
import api from '../lib/api';

// Global event emitter for field registry changes
const fieldRegistryListeners = new Set();

export const notifyFieldRegistryChange = (module, entity) => {
  fieldRegistryListeners.forEach(listener => listener(module, entity));
};

/**
 * Hook to fetch field configuration from the Field Registry
 * This provides the complete configuration for a module entity including fields, stages, and list display settings
 * 
 * @param {string} module - The module identifier (e.g., 'crm', 'inventory')
 * @param {string} entity - The entity identifier (e.g., 'leads', 'accounts')
 * @returns {Object} - { config, fields, stages, loading, error, refetch }
 */
export const useFieldRegistry = (module, entity) => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const fetchConfig = useCallback(async () => {
    if (!module || !entity) {
      setConfig(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/field-registry/config/${module}/${entity}?_t=${Date.now()}`);
      setConfig(res.data);
    } catch (err) {
      console.error(`Failed to fetch field registry for ${module}/${entity}:`, err);
      setError(err.response?.data?.detail || 'Failed to load field configuration');
      setConfig(null);
    } finally {
      setLoading(false);
    }
  }, [module, entity, refreshKey]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  // Listen for registry changes
  useEffect(() => {
    const listener = (changedModule, changedEntity) => {
      if (changedModule === module && changedEntity === entity) {
        setRefreshKey(k => k + 1);
      }
    };
    fieldRegistryListeners.add(listener);
    return () => fieldRegistryListeners.delete(listener);
  }, [module, entity]);

  // Extract data from config
  const fields = config?.fields || [];
  const stages = config?.kanban_stages || [];
  const listDisplayFields = config?.list_display_fields || [];

  // Group fields by section
  const fieldsBySection = fields.reduce((acc, field) => {
    const section = field.section || 'default';
    if (!acc[section]) acc[section] = [];
    acc[section].push(field);
    // Sort by order within section
    acc[section].sort((a, b) => (a.order || 0) - (b.order || 0));
    return acc;
  }, {});

  // Get form fields only (show_in_form !== false)
  const formFields = fields.filter(f => f.show_in_form !== false);

  // Get list fields only (show_in_list === true)
  const listFields = fields.filter(f => f.show_in_list === true);

  // Get required fields
  const requiredFields = fields.filter(f => f.is_required);

  // Generate initial values for form
  const getInitialValues = () => {
    const values = {};
    fields.forEach(f => {
      if (f.default_value !== undefined && f.default_value !== null) {
        values[f.field_name] = f.default_value;
      } else if (f.field_type === 'checkbox') {
        values[f.field_name] = false;
      } else if (f.field_type === 'multiselect') {
        values[f.field_name] = [];
      } else if (f.field_type === 'number' || f.field_type === 'currency') {
        values[f.field_name] = '';
      } else {
        values[f.field_name] = '';
      }
    });
    return values;
  };

  // Get options for a specific field
  const getFieldOptions = (fieldName) => {
    const field = fields.find(f => f.field_name === fieldName);
    return field?.options || [];
  };

  // Get field configuration
  const getFieldConfig = (fieldName) => {
    return fields.find(f => f.field_name === fieldName);
  };

  // Validate form data against required fields
  const validateRequired = (formData) => {
    const errors = {};
    requiredFields.forEach(f => {
      const value = formData[f.field_name];
      if (value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0)) {
        errors[f.field_name] = `${f.field_label} is required`;
      }
    });
    return errors;
  };

  // Get stage configuration (for Kanban)
  const getStageConfig = (stageValue) => {
    return stages.find(s => s.value === stageValue);
  };

  // Get active stages only
  const activeStages = stages.filter(s => s.is_active !== false);

  // Section labels for display
  const sectionLabels = {
    basic: 'Basic Info',
    address: 'Address',
    contacts: 'Contacts',
    classification: 'Classification',
    followup: 'Follow-up',
    credit: 'Credit Terms',
    display: 'Display Fields',
    form: 'Form Fields',
    default: 'Other'
  };

  return {
    config,
    fields,
    stages,
    activeStages,
    listDisplayFields,
    fieldsBySection,
    formFields,
    listFields,
    requiredFields,
    loading,
    error,
    refetch: fetchConfig,
    getInitialValues,
    getFieldOptions,
    getFieldConfig,
    validateRequired,
    getStageConfig,
    sectionLabels,
    entityLabel: config?.entity_label || entity
  };
};

export default useFieldRegistry;
