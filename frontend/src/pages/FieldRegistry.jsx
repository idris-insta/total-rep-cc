import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { 
  Settings, GripVertical, Plus, Trash2, Edit, Save, X, ChevronDown, ChevronRight,
  Database, Users, Package, FileText, Truck, Building2, Layers, LayoutGrid, RefreshCw,
  Check, AlertCircle
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { notifyFieldRegistryChange } from '../hooks/useFieldRegistry';

// ==================== DRAG DROP HELPERS ====================
const DraggableList = ({ items, onReorder, renderItem, keyField = 'field_name' }) => {
  const [draggedIndex, setDraggedIndex] = useState(null);

  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === index) return;
    
    const newItems = [...items];
    const draggedItem = newItems[draggedIndex];
    newItems.splice(draggedIndex, 1);
    newItems.splice(index, 0, draggedItem);
    
    // Update orders
    newItems.forEach((item, idx) => {
      item.order = idx;
    });
    
    setDraggedIndex(index);
    onReorder(newItems);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
  };

  return (
    <div className="space-y-1">
      {items.map((item, index) => (
        <div
          key={item[keyField] || index}
          draggable
          onDragStart={(e) => handleDragStart(e, index)}
          onDragOver={(e) => handleDragOver(e, index)}
          onDragEnd={handleDragEnd}
          className={`transition-all ${draggedIndex === index ? 'opacity-50 scale-95' : ''}`}
        >
          {renderItem(item, index)}
        </div>
      ))}
    </div>
  );
};

// ==================== FIELD EDITOR DIALOG ====================
const FieldEditorDialog = ({ field, onSave, onClose, open }) => {
  const [formData, setFormData] = useState(field || {
    field_name: '',
    field_label: '',
    field_type: 'text',
    section: 'default',
    is_required: false,
    is_readonly: false,
    show_in_list: true,
    show_in_form: true,
    placeholder: '',
    help_text: '',
    default_value: '',
    options: []
  });
  const [optionText, setOptionText] = useState('');
  
  // Track previous field value to update formData when field changes
  const prevFieldRef = React.useRef(null);
  
  React.useEffect(() => {
    if (field && field !== prevFieldRef.current) {
      prevFieldRef.current = field;
      setFormData(field);
    }
  }, [field]);

  const fieldTypes = [
    { value: 'text', label: 'Text' },
    { value: 'number', label: 'Number' },
    { value: 'currency', label: 'Currency' },
    { value: 'email', label: 'Email' },
    { value: 'phone', label: 'Phone' },
    { value: 'date', label: 'Date' },
    { value: 'select', label: 'Dropdown' },
    { value: 'multiselect', label: 'Multi-Select' },
    { value: 'checkbox', label: 'Checkbox' },
    { value: 'textarea', label: 'Text Area' },
    { value: 'auto', label: 'Auto-Generated' }
  ];

  const sections = [
    { value: 'basic', label: 'Basic Info' },
    { value: 'address', label: 'Address' },
    { value: 'contacts', label: 'Contacts' },
    { value: 'classification', label: 'Classification' },
    { value: 'followup', label: 'Follow-up' },
    { value: 'credit', label: 'Credit Terms' },
    { value: 'display', label: 'Display Fields' },
    { value: 'form', label: 'Form Fields' },
    { value: 'default', label: 'Default' }
  ];

  const addOption = () => {
    if (!optionText.trim()) return;
    const value = optionText.toLowerCase().replace(/\s+/g, '_');
    setFormData({
      ...formData,
      options: [...(formData.options || []), { value, label: optionText, order: (formData.options?.length || 0) }]
    });
    setOptionText('');
  };

  const removeOption = (index) => {
    const newOptions = formData.options.filter((_, i) => i !== index);
    setFormData({ ...formData, options: newOptions });
  };

  const handleSubmit = () => {
    if (!formData.field_name || !formData.field_label) {
      toast.error('Field name and label are required');
      return;
    }
    onSave(formData);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-manrope">{field ? 'Edit Field' : 'Add New Field'}</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Field Name (Internal) *</Label>
              <Input 
                value={formData.field_name}
                onChange={(e) => setFormData({...formData, field_name: e.target.value.toLowerCase().replace(/\s+/g, '_')})}
                placeholder="e.g., customer_type"
                disabled={!!field}
              />
            </div>
            <div className="space-y-2">
              <Label>Field Label (Display) *</Label>
              <Input 
                value={formData.field_label}
                onChange={(e) => setFormData({...formData, field_label: e.target.value})}
                placeholder="e.g., Customer Type"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Field Type</Label>
              <Select value={formData.field_type} onValueChange={(v) => setFormData({...formData, field_type: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {fieldTypes.map(t => (
                    <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Section</Label>
              <Select value={formData.section || 'default'} onValueChange={(v) => setFormData({...formData, section: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {sections.map(s => (
                    <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Placeholder</Label>
              <Input 
                value={formData.placeholder || ''}
                onChange={(e) => setFormData({...formData, placeholder: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <Label>Default Value</Label>
              <Input 
                value={formData.default_value || ''}
                onChange={(e) => setFormData({...formData, default_value: e.target.value})}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Help Text</Label>
            <Input 
              value={formData.help_text || ''}
              onChange={(e) => setFormData({...formData, help_text: e.target.value})}
              placeholder="Optional help text for users"
            />
          </div>

          {/* Options for dropdowns */}
          {(formData.field_type === 'select' || formData.field_type === 'multiselect') && (
            <div className="space-y-2 p-3 bg-slate-50 rounded-lg">
              <Label>Dropdown Options</Label>
              <div className="flex gap-2">
                <Input 
                  value={optionText}
                  onChange={(e) => setOptionText(e.target.value)}
                  placeholder="Add option..."
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addOption())}
                />
                <Button type="button" variant="outline" size="sm" onClick={addOption}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {(formData.options || []).map((opt, idx) => (
                  <Badge key={idx} variant="outline" className="flex items-center gap-1">
                    {opt.label}
                    <X className="h-3 w-3 cursor-pointer hover:text-destructive" onClick={() => removeOption(idx)} />
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Toggles */}
          <div className="grid grid-cols-2 gap-4 p-3 bg-slate-50 rounded-lg">
            <div className="flex items-center justify-between">
              <Label>Required Field</Label>
              <Switch 
                checked={formData.is_required || false}
                onCheckedChange={(v) => setFormData({...formData, is_required: v})}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label>Read Only</Label>
              <Switch 
                checked={formData.is_readonly || false}
                onCheckedChange={(v) => setFormData({...formData, is_readonly: v})}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label>Show in List View</Label>
              <Switch 
                checked={formData.show_in_list !== false}
                onCheckedChange={(v) => setFormData({...formData, show_in_list: v})}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label>Show in Form</Label>
              <Switch 
                checked={formData.show_in_form !== false}
                onCheckedChange={(v) => setFormData({...formData, show_in_form: v})}
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} className="bg-accent hover:bg-accent/90">
            <Save className="h-4 w-4 mr-2" />Save Field
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// ==================== STAGE EDITOR ====================
const StageEditor = ({ stages, onSave, onReorder }) => {
  const [editingStage, setEditingStage] = useState(null);
  const [newStage, setNewStage] = useState({ value: '', label: '', color: 'blue' });

  const colors = ['red', 'orange', 'yellow', 'green', 'emerald', 'teal', 'blue', 'purple', 'pink', 'slate'];
  
  const colorBadges = {
    red: 'bg-red-100 text-red-800',
    orange: 'bg-orange-100 text-orange-800',
    yellow: 'bg-yellow-100 text-yellow-800',
    green: 'bg-green-100 text-green-800',
    emerald: 'bg-emerald-100 text-emerald-800',
    teal: 'bg-teal-100 text-teal-800',
    blue: 'bg-blue-100 text-blue-800',
    purple: 'bg-purple-100 text-purple-800',
    pink: 'bg-pink-100 text-pink-800',
    slate: 'bg-slate-100 text-slate-800'
  };

  const addStage = () => {
    if (!newStage.label) return;
    const value = newStage.value || newStage.label.toLowerCase().replace(/\s+/g, '_');
    const updated = [...stages, { ...newStage, value, order: stages.length, is_active: true }];
    onSave(updated);
    setNewStage({ value: '', label: '', color: 'blue' });
  };

  const removeStage = (index) => {
    const updated = stages.filter((_, i) => i !== index);
    updated.forEach((s, i) => s.order = i);
    onSave(updated);
  };

  const updateStage = (index, updates) => {
    const updated = stages.map((s, i) => i === index ? { ...s, ...updates } : s);
    onSave(updated);
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2 p-3 bg-slate-50 rounded-lg">
        <Input 
          value={newStage.label}
          onChange={(e) => setNewStage({...newStage, label: e.target.value})}
          placeholder="Stage name..."
          className="flex-1"
        />
        <Select value={newStage.color} onValueChange={(v) => setNewStage({...newStage, color: v})}>
          <SelectTrigger className="w-32">
            <Badge className={colorBadges[newStage.color]}>{newStage.color}</Badge>
          </SelectTrigger>
          <SelectContent>
            {colors.map(c => (
              <SelectItem key={c} value={c}>
                <Badge className={colorBadges[c]}>{c}</Badge>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button onClick={addStage} className="bg-accent hover:bg-accent/90">
          <Plus className="h-4 w-4" />
        </Button>
      </div>

      <DraggableList
        items={stages}
        onReorder={onReorder}
        keyField="value"
        renderItem={(stage, index) => (
          <div className="flex items-center gap-2 p-2 bg-white border rounded-lg hover:bg-slate-50">
            <GripVertical className="h-4 w-4 text-slate-400 cursor-grab" />
            <Badge className={colorBadges[stage.color] || colorBadges.blue}>{stage.label}</Badge>
            <span className="text-xs text-slate-500 flex-1">({stage.value})</span>
            <Select value={stage.color} onValueChange={(v) => updateStage(index, { color: v })}>
              <SelectTrigger className="w-20 h-7">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {colors.map(c => (
                  <SelectItem key={c} value={c}>
                    <Badge className={`${colorBadges[c]} text-xs`}>{c}</Badge>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="ghost" size="sm" onClick={() => removeStage(index)} className="text-destructive h-7 w-7 p-0">
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        )}
      />
    </div>
  );
};

// ==================== FIELD LIST COMPONENT ====================
const FieldListEditor = ({ fields, onUpdate, onAddField, onEditField, onDeleteField }) => {
  const [expandedSections, setExpandedSections] = useState(['basic', 'address', 'classification', 'followup', 'display', 'form']);

  const groupedFields = fields.reduce((acc, field) => {
    const section = field.section || 'default';
    if (!acc[section]) acc[section] = [];
    acc[section].push(field);
    return acc;
  }, {});

  const sectionLabels = {
    basic: 'Basic Info',
    address: 'Address',
    contacts: 'Contacts',
    classification: 'Classification',
    followup: 'Follow-up',
    credit: 'Credit Terms',
    display: 'Display Fields',
    form: 'Form Fields',
    default: 'Other Fields'
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => 
      prev.includes(section) ? prev.filter(s => s !== section) : [...prev, section]
    );
  };

  const fieldTypeIcons = {
    text: '📝',
    number: '🔢',
    currency: '💰',
    email: '📧',
    phone: '📞',
    date: '📅',
    select: '▼',
    multiselect: '☑️',
    checkbox: '✓',
    textarea: '📄',
    auto: '⚡'
  };

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">{fields.length} fields configured</span>
        <Button onClick={onAddField} size="sm" className="bg-accent hover:bg-accent/90">
          <Plus className="h-4 w-4 mr-1" />Add Field
        </Button>
      </div>

      {Object.entries(groupedFields).map(([section, sectionFields]) => (
        <div key={section} className="border rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection(section)}
            className="w-full flex items-center justify-between p-3 bg-slate-50 hover:bg-slate-100 transition-colors"
          >
            <div className="flex items-center gap-2">
              {expandedSections.includes(section) ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              <span className="font-medium">{sectionLabels[section] || section}</span>
              <Badge variant="outline" className="text-xs">{sectionFields.length}</Badge>
            </div>
          </button>
          
          {expandedSections.includes(section) && (
            <div className="p-2 space-y-1">
              <DraggableList
                items={sectionFields.sort((a, b) => (a.order || 0) - (b.order || 0))}
                onReorder={(reordered) => {
                  const otherFields = fields.filter(f => (f.section || 'default') !== section);
                  onUpdate([...otherFields, ...reordered]);
                }}
                renderItem={(field, index) => (
                  <div className="flex items-center gap-2 p-2 bg-white border rounded hover:bg-slate-50 group">
                    <GripVertical className="h-4 w-4 text-slate-400 cursor-grab" />
                    <span className="text-sm">{fieldTypeIcons[field.field_type] || '📝'}</span>
                    <span className="flex-1 text-sm font-medium">{field.field_label}</span>
                    <span className="text-xs text-slate-500">{field.field_name}</span>
                    {field.is_required && <Badge className="bg-red-100 text-red-800 text-xs">Required</Badge>}
                    {field.field_type === 'select' && <Badge variant="outline" className="text-xs">{field.options?.length || 0} options</Badge>}
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                      <Button variant="ghost" size="sm" onClick={() => onEditField(field)} className="h-6 w-6 p-0">
                        <Edit className="h-3 w-3" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => onDeleteField(field.field_name)} className="h-6 w-6 p-0 text-destructive">
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                )}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

// ==================== MAIN COMPONENT ====================
const FieldRegistry = () => {
  const { user } = useAuth();
  const [searchParams] = React.useState(() => new URLSearchParams(window.location.search));
  const [activeModule, setActiveModule] = useState(searchParams.get('module') || 'crm');
  const [activeEntity, setActiveEntity] = useState(searchParams.get('entity') || 'leads');
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [modules, setModules] = useState({});
  const [fieldEditorOpen, setFieldEditorOpen] = useState(false);
  const [editingField, setEditingField] = useState(null);
  const [activeTab, setActiveTab] = useState('stages');

  // Fetch modules list
  useEffect(() => {
    fetchModules();
  }, []);

  const fetchConfig = useCallback(async () => {
    if (!activeModule || !activeEntity) return;
    setLoading(true);
    try {
      const response = await api.get(`/field-registry/config/${activeModule}/${activeEntity}`);
      setConfig(response.data);
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to load config:', error);
      // Use default config
      setConfig({
        module: activeModule,
        entity: activeEntity,
        entity_label: activeEntity.replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
        fields: [],
        kanban_stages: [],
        list_display_fields: []
      });
    } finally {
      setLoading(false);
    }
  }, [activeModule, activeEntity]);

  // Fetch config when module/entity changes
  useEffect(() => {
    if (activeModule && activeEntity) {
      fetchConfig();
    }
  }, [activeModule, activeEntity, fetchConfig]);

  const fetchModules = async () => {
    try {
      const response = await api.get('/field-registry/modules');
      setModules(response.data);
    } catch (error) {
      console.error('Failed to load modules:', error);
      toast.error('Failed to load modules');
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      await api.post('/field-registry/config', config);
      toast.success('Configuration saved successfully');
      setHasChanges(false);
      // Notify all listeners that this config has changed
      notifyFieldRegistryChange(config.module, config.entity);
    } catch (error) {
      console.error('Failed to save config:', error);
      toast.error('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const updateFields = (newFields) => {
    setConfig({ ...config, fields: newFields });
    setHasChanges(true);
  };

  const updateStages = (newStages) => {
    setConfig({ ...config, kanban_stages: newStages });
    setHasChanges(true);
  };

  const handleAddField = () => {
    setEditingField(null);
    setFieldEditorOpen(true);
  };

  const handleEditField = (field) => {
    setEditingField(field);
    setFieldEditorOpen(true);
  };

  const handleSaveField = (fieldData) => {
    const existingIndex = config.fields.findIndex(f => f.field_name === fieldData.field_name);
    
    if (existingIndex >= 0) {
      // Update existing
      const newFields = [...config.fields];
      newFields[existingIndex] = { ...newFields[existingIndex], ...fieldData };
      updateFields(newFields);
    } else {
      // Add new
      fieldData.order = config.fields.length;
      updateFields([...config.fields, fieldData]);
    }
  };

  const handleDeleteField = (fieldName) => {
    if (!confirm(`Are you sure you want to delete the field "${fieldName}"?`)) return;
    updateFields(config.fields.filter(f => f.field_name !== fieldName));
  };

  const moduleIcons = {
    crm: <Users className="h-5 w-5" />,
    inventory: <Package className="h-5 w-5" />,
    accounts: <FileText className="h-5 w-5" />,
    production: <Layers className="h-5 w-5" />,
    procurement: <Truck className="h-5 w-5" />,
    hrms: <Building2 className="h-5 w-5" />
  };

  if (user?.role !== 'admin' && user?.role !== 'director') {
    return (
      <div className="p-8 text-center">
        <AlertCircle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-slate-900 mb-2">Access Restricted</h2>
        <p className="text-slate-600">Only Administrators and Directors can configure field settings.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="field-registry">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope flex items-center gap-3">
            <Settings className="h-8 w-8 text-accent" />
            Field Registry
          </h1>
          <p className="text-slate-600 mt-1 font-inter">Configure fields, stages, and dropdown options for all modules</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchConfig} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Reload
          </Button>
          <Button 
            onClick={saveConfig} 
            disabled={!hasChanges || saving}
            className="bg-accent hover:bg-accent/90"
          >
            {saving ? (
              <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Saving...</>
            ) : (
              <><Save className="h-4 w-4 mr-2" />Save Changes</>
            )}
          </Button>
        </div>
      </div>

      {/* Module/Entity Selector */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Module Selector */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-manrope">Module</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            {Object.entries(modules).map(([key, mod]) => (
              <button
                key={key}
                onClick={() => {
                  setActiveModule(key);
                  const entities = Object.keys(mod.entities || {});
                  if (entities.length > 0) setActiveEntity(entities[0]);
                }}
                className={`w-full flex items-center gap-2 p-2 rounded-lg text-left transition-colors ${
                  activeModule === key ? 'bg-accent text-white' : 'hover:bg-slate-100'
                }`}
              >
                {moduleIcons[key] || <Database className="h-5 w-5" />}
                <span className="font-medium">{mod.label}</span>
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Entity Selector */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-manrope">Entity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            {modules[activeModule]?.entities && Object.entries(modules[activeModule].entities).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setActiveEntity(key)}
                className={`w-full flex items-center gap-2 p-2 rounded-lg text-left transition-colors ${
                  activeEntity === key ? 'bg-purple-600 text-white' : 'hover:bg-slate-100'
                }`}
              >
                <LayoutGrid className="h-4 w-4" />
                <span>{label}</span>
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Configuration Panel */}
        <Card className="lg:col-span-2 border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-manrope">
                Configure: {config?.entity_label || activeEntity}
              </CardTitle>
              {hasChanges && (
                <Badge className="bg-amber-100 text-amber-800">Unsaved Changes</Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <RefreshCw className="h-8 w-8 text-accent animate-spin" />
              </div>
            ) : config ? (
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="stages">Kanban Stages</TabsTrigger>
                  <TabsTrigger value="fields">Form Fields</TabsTrigger>
                  <TabsTrigger value="display">List Display</TabsTrigger>
                </TabsList>

                <TabsContent value="stages" className="mt-4">
                  {config.kanban_stages && config.kanban_stages.length > 0 ? (
                    <StageEditor
                      stages={config.kanban_stages}
                      onSave={updateStages}
                      onReorder={updateStages}
                    />
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <p>This entity does not have Kanban stages.</p>
                      <Button 
                        variant="outline" 
                        className="mt-2"
                        onClick={() => updateStages([
                          { value: 'new', label: 'New', color: 'blue', order: 0, is_active: true }
                        ])}
                      >
                        <Plus className="h-4 w-4 mr-2" />Add Kanban Stages
                      </Button>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="fields" className="mt-4">
                  <FieldListEditor
                    fields={config.fields || []}
                    onUpdate={updateFields}
                    onAddField={handleAddField}
                    onEditField={handleEditField}
                    onDeleteField={handleDeleteField}
                  />
                </TabsContent>

                <TabsContent value="display" className="mt-4">
                  <div className="space-y-3">
                    <p className="text-sm text-slate-600">Select fields to show in list view:</p>
                    <div className="grid grid-cols-2 gap-2">
                      {(config.fields || []).map(field => (
                        <label 
                          key={field.field_name}
                          className="flex items-center gap-2 p-2 border rounded-lg hover:bg-slate-50 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={field.show_in_list || false}
                            onChange={(e) => {
                              const updated = config.fields.map(f => 
                                f.field_name === field.field_name 
                                  ? { ...f, show_in_list: e.target.checked }
                                  : f
                              );
                              updateFields(updated);
                            }}
                            className="rounded border-slate-300"
                          />
                          <span className="text-sm">{field.field_label}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            ) : (
              <p className="text-slate-500 text-center py-8">Select a module and entity to configure.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Field Editor Dialog */}
      <FieldEditorDialog
        field={editingField}
        open={fieldEditorOpen}
        onClose={() => setFieldEditorOpen(false)}
        onSave={handleSaveField}
      />
    </div>
  );
};

export default FieldRegistry;
