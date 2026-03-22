import React from 'react';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { Badge } from '../components/ui/badge';
import { Calendar } from '../components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { Button } from '../components/ui/button';
import { CalendarIcon, HelpCircle, Upload } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '../lib/utils';

/**
 * Renders a single dynamic field based on its configuration
 */
const DynamicField = ({ field, value, onChange, disabled = false }) => {
  const handleChange = (newValue) => {
    onChange(field.field_name, newValue);
  };

  const renderField = () => {
    switch (field.field_type) {
      case 'text':
        return (
          <Input
            id={field.field_name}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder || `Enter ${field.field_label.toLowerCase()}`}
            disabled={disabled}
            required={field.is_required}
          />
        );

      case 'number':
        return (
          <Input
            id={field.field_name}
            type="number"
            value={value || ''}
            onChange={(e) => handleChange(e.target.value ? Number(e.target.value) : '')}
            placeholder={field.placeholder || `Enter ${field.field_label.toLowerCase()}`}
            disabled={disabled}
            required={field.is_required}
            min={field.validation_rules?.min}
            max={field.validation_rules?.max}
          />
        );

      case 'textarea':
        return (
          <Textarea
            id={field.field_name}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder || `Enter ${field.field_label.toLowerCase()}`}
            disabled={disabled}
            required={field.is_required}
            rows={3}
          />
        );

      case 'select':
        return (
          <Select
            value={value || ''}
            onValueChange={handleChange}
            disabled={disabled}
          >
            <SelectTrigger id={field.field_name}>
              <SelectValue placeholder={field.placeholder || `Select ${field.field_label.toLowerCase()}`} />
            </SelectTrigger>
            <SelectContent>
              {field.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'multiselect':
        const selectedValues = Array.isArray(value) ? value : [];
        return (
          <div className="space-y-2">
            <div className="flex flex-wrap gap-1 min-h-[36px] p-2 border rounded-md bg-white">
              {selectedValues.length === 0 ? (
                <span className="text-slate-400 text-sm">{field.placeholder || 'Select options...'}</span>
              ) : (
                selectedValues.map((v) => (
                  <Badge key={v} variant="secondary" className="cursor-pointer" onClick={() => {
                    if (!disabled) handleChange(selectedValues.filter(sv => sv !== v));
                  }}>
                    {v} ×
                  </Badge>
                ))
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {field.options?.filter(o => !selectedValues.includes(o)).map((option) => (
                <Badge 
                  key={option} 
                  variant="outline" 
                  className={cn("cursor-pointer hover:bg-slate-100", disabled && "opacity-50 cursor-not-allowed")}
                  onClick={() => {
                    if (!disabled) handleChange([...selectedValues, option]);
                  }}
                >
                  + {option}
                </Badge>
              ))}
            </div>
          </div>
        );

      case 'checkbox':
        return (
          <div className="flex items-center space-x-2">
            <Checkbox
              id={field.field_name}
              checked={value || false}
              onCheckedChange={handleChange}
              disabled={disabled}
            />
            <label
              htmlFor={field.field_name}
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              {field.help_text || field.field_label}
            </label>
          </div>
        );

      case 'date':
        return (
          <Popover>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                className={cn(
                  "w-full justify-start text-left font-normal",
                  !value && "text-muted-foreground"
                )}
                disabled={disabled}
              >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {value ? format(new Date(value), 'PPP') : field.placeholder || 'Pick a date'}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={value ? new Date(value) : undefined}
                onSelect={(date) => handleChange(date ? date.toISOString() : '')}
                initialFocus
              />
            </PopoverContent>
          </Popover>
        );

      case 'file':
        return (
          <div className="flex items-center gap-2">
            <Input
              id={field.field_name}
              type="file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  handleChange(file.name); // In real implementation, upload and store URL
                }
              }}
              disabled={disabled}
              className="flex-1"
            />
            {value && (
              <Badge variant="secondary">{value}</Badge>
            )}
          </div>
        );

      default:
        return (
          <Input
            id={field.field_name}
            value={value || ''}
            onChange={(e) => handleChange(e.target.value)}
            placeholder={field.placeholder}
            disabled={disabled}
          />
        );
    }
  };

  // For checkbox, we render label differently
  if (field.field_type === 'checkbox') {
    return (
      <div className="space-y-1">
        {renderField()}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Label htmlFor={field.field_name} className="text-sm font-medium">
          {field.field_label}
          {field.is_required && <span className="text-red-500 ml-1">*</span>}
        </Label>
        {field.help_text && field.field_type !== 'checkbox' && (
          <Popover>
            <PopoverTrigger asChild>
              <HelpCircle className="h-3.5 w-3.5 text-slate-400 cursor-help" />
            </PopoverTrigger>
            <PopoverContent className="w-80 text-sm">
              {field.help_text}
            </PopoverContent>
          </Popover>
        )}
      </div>
      {renderField()}
    </div>
  );
};

/**
 * Renders a group of dynamic fields organized by sections
 * @param {Object} props
 * @param {Array} props.fields - Array of field configurations from useCustomFields
 * @param {Object} props.values - Current form values
 * @param {Function} props.onChange - Callback when a field value changes (fieldName, value)
 * @param {boolean} props.disabled - Whether all fields are disabled
 * @param {number} props.columns - Number of columns (1, 2, or 3)
 * @param {boolean} props.showSections - Whether to show section headers
 */
const DynamicFormFields = ({ 
  fields = [], 
  values = {}, 
  onChange, 
  disabled = false,
  columns = 2,
  showSections = true 
}) => {
  if (!fields || fields.length === 0) {
    return null;
  }

  // Group fields by section
  const sections = fields.reduce((acc, field) => {
    const section = field.section || 'Additional Information';
    if (!acc[section]) acc[section] = [];
    acc[section].push(field);
    return acc;
  }, {});

  const gridClass = columns === 1 
    ? 'grid-cols-1' 
    : columns === 3 
      ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
      : 'grid-cols-1 md:grid-cols-2';

  return (
    <div className="space-y-6">
      {Object.entries(sections).map(([sectionName, sectionFields]) => (
        <div key={sectionName} className="space-y-4">
          {showSections && (
            <div className="border-b pb-2">
              <h4 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                {sectionName}
              </h4>
            </div>
          )}
          <div className={cn("grid gap-4", gridClass)}>
            {sectionFields
              .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
              .map((field) => (
                <DynamicField
                  key={field.id || field.field_name}
                  field={field}
                  value={values[field.field_name]}
                  onChange={onChange}
                  disabled={disabled}
                />
              ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export { DynamicField, DynamicFormFields };
export default DynamicFormFields;
