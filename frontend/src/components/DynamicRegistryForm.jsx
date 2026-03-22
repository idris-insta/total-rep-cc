import React from 'react';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { HelpCircle } from 'lucide-react';

/**
 * Dynamic Form Field Renderer
 * Renders form fields based on Field Registry configuration
 * 
 * @param {Object} props
 * @param {Array} props.fields - Array of field configurations
 * @param {Object} props.formData - Current form data
 * @param {Function} props.onChange - Function to update form data
 * @param {Object} props.sectionLabels - Labels for sections
 * @param {boolean} props.groupBySection - Whether to group fields by section
 * @param {number} props.columns - Number of columns (1, 2, 3, or 4)
 */
const DynamicFormFields = ({ 
  fields = [], 
  formData = {}, 
  onChange, 
  sectionLabels = {},
  groupBySection = true,
  columns = 3
}) => {
  
  const handleChange = (fieldName, value) => {
    onChange({ ...formData, [fieldName]: value });
  };

  // Render a single field based on its type
  const renderField = (field) => {
    const value = formData[field.field_name] || field.default_value || '';
    const commonProps = {
      id: field.field_name,
      disabled: field.is_readonly,
      placeholder: field.placeholder || '',
      'data-testid': `field-${field.field_name}`
    };

    switch (field.field_type) {
      case 'text':
      case 'email':
      case 'phone':
        return (
          <Input
            {...commonProps}
            type={field.field_type === 'email' ? 'email' : 'text'}
            value={value}
            onChange={(e) => handleChange(field.field_name, e.target.value)}
          />
        );

      case 'number':
      case 'currency':
        return (
          <div className="relative">
            {field.field_type === 'currency' && (
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">₹</span>
            )}
            <Input
              {...commonProps}
              type="number"
              value={value}
              onChange={(e) => handleChange(field.field_name, e.target.value)}
              className={field.field_type === 'currency' ? 'pl-7' : ''}
            />
          </div>
        );

      case 'date':
        return (
          <Input
            {...commonProps}
            type="date"
            value={value}
            onChange={(e) => handleChange(field.field_name, e.target.value)}
          />
        );

      case 'textarea':
        return (
          <Textarea
            {...commonProps}
            value={value}
            onChange={(e) => handleChange(field.field_name, e.target.value)}
            rows={3}
          />
        );

      case 'select':
        return (
          <Select 
            value={value || ''} 
            onValueChange={(v) => handleChange(field.field_name, v)}
            disabled={field.is_readonly}
          >
            <SelectTrigger data-testid={`select-${field.field_name}`}>
              <SelectValue placeholder={field.placeholder || `Select ${field.field_label}`} />
            </SelectTrigger>
            <SelectContent>
              {(field.options || []).map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.color ? (
                    <Badge className={`bg-${opt.color}-100 text-${opt.color}-800`}>{opt.label}</Badge>
                  ) : (
                    opt.label
                  )}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'multiselect':
        const selectedValues = Array.isArray(value) ? value : [];
        return (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1 p-2 min-h-[38px] border rounded-md bg-white">
              {selectedValues.length === 0 ? (
                <span className="text-slate-400 text-sm">{field.placeholder || 'Select options...'}</span>
              ) : (
                selectedValues.map(v => {
                  const opt = (field.options || []).find(o => o.value === v);
                  return (
                    <Badge 
                      key={v} 
                      variant="secondary" 
                      className="cursor-pointer"
                      onClick={() => handleChange(field.field_name, selectedValues.filter(x => x !== v))}
                    >
                      {opt?.label || v} ×
                    </Badge>
                  );
                })
              )}
            </div>
            <div className="flex flex-wrap gap-1">
              {(field.options || []).filter(opt => !selectedValues.includes(opt.value)).map(opt => (
                <Badge 
                  key={opt.value}
                  variant="outline"
                  className="cursor-pointer hover:bg-slate-100"
                  onClick={() => handleChange(field.field_name, [...selectedValues, opt.value])}
                >
                  + {opt.label}
                </Badge>
              ))}
            </div>
          </div>
        );

      case 'checkbox':
        return (
          <div className="flex items-center gap-2 h-10">
            <input
              type="checkbox"
              id={field.field_name}
              checked={value === true || value === 'true'}
              onChange={(e) => handleChange(field.field_name, e.target.checked)}
              disabled={field.is_readonly}
              className="h-4 w-4 rounded border-slate-300"
            />
            <span className="text-sm text-slate-600">{field.help_text || field.field_label}</span>
          </div>
        );

      case 'auto':
        return (
          <Input
            {...commonProps}
            type="text"
            value={value}
            disabled
            className="bg-slate-50"
          />
        );

      default:
        return (
          <Input
            {...commonProps}
            type="text"
            value={value}
            onChange={(e) => handleChange(field.field_name, e.target.value)}
          />
        );
    }
  };

  // Render field with label
  const renderFieldWithLabel = (field) => {
    // Skip checkbox from normal rendering (it has its own label)
    const showLabel = field.field_type !== 'checkbox';
    
    return (
      <div key={field.field_name} className="space-y-2">
        {showLabel && (
          <Label htmlFor={field.field_name} className="flex items-center gap-1 font-inter">
            {field.field_label}
            {field.is_required && <span className="text-destructive">*</span>}
            {field.help_text && field.field_type !== 'checkbox' && (
              <HelpCircle className="h-3 w-3 text-slate-400 cursor-help" title={field.help_text} />
            )}
          </Label>
        )}
        {renderField(field)}
      </div>
    );
  };

  // Group fields by section
  if (groupBySection) {
    const grouped = fields.reduce((acc, field) => {
      const section = field.section || 'default';
      if (!acc[section]) acc[section] = [];
      acc[section].push(field);
      return acc;
    }, {});

    // Sort sections
    const sectionOrder = ['basic', 'address', 'contacts', 'classification', 'followup', 'credit', 'display', 'form', 'default'];
    const sortedSections = Object.keys(grouped).sort((a, b) => {
      const aIdx = sectionOrder.indexOf(a);
      const bIdx = sectionOrder.indexOf(b);
      return (aIdx === -1 ? 999 : aIdx) - (bIdx === -1 ? 999 : bIdx);
    });

    return (
      <div className="space-y-6">
        {sortedSections.map(section => {
          const sectionFields = grouped[section].sort((a, b) => (a.order || 0) - (b.order || 0));
          const label = sectionLabels[section] || section.charAt(0).toUpperCase() + section.slice(1).replace(/_/g, ' ');
          
          return (
            <div key={section} className="space-y-4">
              <h4 className="font-semibold text-slate-900 border-b pb-2">{label}</h4>
              <div className={`grid gap-4 ${
                columns === 1 ? 'grid-cols-1' : 
                columns === 2 ? 'grid-cols-2' : 
                columns === 4 ? 'grid-cols-4' : 'grid-cols-3'
              }`}>
                {sectionFields.filter(f => f.show_in_form !== false).map(renderFieldWithLabel)}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Flat rendering without sections
  const sortedFields = [...fields].sort((a, b) => (a.order || 0) - (b.order || 0));
  
  return (
    <div className={`grid gap-4 ${
      columns === 1 ? 'grid-cols-1' : 
      columns === 2 ? 'grid-cols-2' : 
      columns === 4 ? 'grid-cols-4' : 'grid-cols-3'
    }`}>
      {sortedFields.filter(f => f.show_in_form !== false).map(renderFieldWithLabel)}
    </div>
  );
};

export default DynamicFormFields;
