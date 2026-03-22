import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { 
  Settings, Plus, Edit, Trash2, GripVertical, Save, RefreshCw,
  FileText, Package, Factory, Users, Receipt, ShoppingCart, Truck,
  Building, UserPlus, Cog, CreditCard, Warehouse, ChevronRight, Database
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

const FIELD_TYPES = [
  { value: 'text', label: 'Text', icon: '📝' },
  { value: 'number', label: 'Number', icon: '🔢' },
  { value: 'date', label: 'Date', icon: '📅' },
  { value: 'select', label: 'Dropdown', icon: '📋' },
  { value: 'multiselect', label: 'Multi-Select', icon: '☑️' },
  { value: 'checkbox', label: 'Checkbox', icon: '✓' },
  { value: 'textarea', label: 'Text Area', icon: '📄' },
  { value: 'file', label: 'File Upload', icon: '📎' },
];

const MODULE_ICONS = {
  crm_leads: UserPlus,
  crm_accounts: Building,
  crm_quotations: FileText,
  inventory_items: Package,
  inventory_warehouses: Warehouse,
  production_work_orders: Factory,
  production_machines: Cog,
  accounts_invoices: Receipt,
  accounts_payments: CreditCard,
  hrms_employees: Users,
  procurement_suppliers: Truck,
  procurement_purchase_orders: ShoppingCart,
};

const PowerSettings = () => {
  const [modules, setModules] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [fields, setFields] = useState([]);
  const [loading, setLoading] = useState(true);
  const [fieldDialogOpen, setFieldDialogOpen] = useState(false);
  const [editingField, setEditingField] = useState(null);
  
  const [fieldForm, setFieldForm] = useState({
    field_name: '', field_label: '', field_type: 'text', is_required: false,
    default_value: '', options: '', section: '', placeholder: '', help_text: '',
    is_searchable: false, is_filterable: false, show_in_list: false, display_order: 0
  });

  useEffect(() => {
    fetchModules();
  }, []);

  useEffect(() => {
    if (selectedModule) {
      fetchFields(selectedModule.id);
    }
  }, [selectedModule]);

  const fetchModules = async () => {
    try {
      const res = await api.get('/custom-fields/modules');
      setModules(res.data);
      if (res.data.length > 0) {
        setSelectedModule(res.data[0]);
      }
    } catch (error) {
      toast.error('Failed to load modules');
    } finally {
      setLoading(false);
    }
  };

  const fetchFields = async (moduleId) => {
    try {
      const res = await api.get(`/custom-fields/fields/${moduleId}`);
      setFields(res.data || []);
    } catch (error) {
      console.error('Failed to load fields');
    }
  };

  const handleSaveField = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...fieldForm,
        module: selectedModule.id,
        options: fieldForm.options ? fieldForm.options.split(',').map(o => o.trim()) : null,
        display_order: fields.length + 1
      };

      if (editingField) {
        await api.put(`/custom-fields/fields/${editingField.id}`, payload);
        toast.success('Field updated');
      } else {
        await api.post('/custom-fields/fields', payload);
        toast.success('Field created');
      }

      setFieldDialogOpen(false);
      resetFieldForm();
      fetchFields(selectedModule.id);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save field');
    }
  };

  const handleDeleteField = async (fieldId) => {
    if (!confirm('Are you sure you want to delete this field?')) return;
    try {
      await api.delete(`/custom-fields/fields/${fieldId}`);
      toast.success('Field deleted');
      fetchFields(selectedModule.id);
    } catch (error) {
      toast.error('Failed to delete field');
    }
  };

  const handleSeedDefaults = async () => {
    try {
      const res = await api.post('/custom-fields/seed-defaults');
      toast.success(res.data.message);
      if (selectedModule) {
        fetchFields(selectedModule.id);
      }
    } catch (error) {
      toast.error('Failed to seed defaults');
    }
  };

  const resetFieldForm = () => {
    setFieldForm({
      field_name: '', field_label: '', field_type: 'text', is_required: false,
      default_value: '', options: '', section: '', placeholder: '', help_text: '',
      is_searchable: false, is_filterable: false, show_in_list: false, display_order: 0
    });
    setEditingField(null);
  };

  const openEditDialog = (field) => {
    setEditingField(field);
    setFieldForm({
      field_name: field.field_name,
      field_label: field.field_label,
      field_type: field.field_type,
      is_required: field.is_required || false,
      default_value: field.default_value || '',
      options: field.options ? field.options.join(', ') : '',
      section: field.section || '',
      placeholder: field.placeholder || '',
      help_text: field.help_text || '',
      is_searchable: field.is_searchable || false,
      is_filterable: field.is_filterable || false,
      show_in_list: field.show_in_list || false,
      display_order: field.display_order || 0
    });
    setFieldDialogOpen(true);
  };

  const getIconComponent = (moduleId) => {
    const Icon = MODULE_ICONS[moduleId] || Settings;
    return Icon;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6" data-testid="power-settings">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope flex items-center gap-3">
            <Settings className="h-8 w-8 text-accent" />
            Power Settings
          </h1>
          <p className="text-slate-600 mt-1">Customize fields, forms, and module behavior</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={handleSeedDefaults}>
            <Database className="h-4 w-4 mr-2" />Seed Defaults
          </Button>
          <Button variant="outline" onClick={() => selectedModule && fetchFields(selectedModule.id)}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Module List */}
        <div className="col-span-3">
          <Card className="sticky top-6">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-slate-600">Modules</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y">
                {modules.map((module) => {
                  const Icon = getIconComponent(module.id);
                  return (
                    <button
                      key={module.id}
                      onClick={() => setSelectedModule(module)}
                      className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors",
                        selectedModule?.id === module.id && "bg-accent/10 border-l-2 border-accent"
                      )}
                    >
                      <Icon className="h-4 w-4 text-slate-500" />
                      <span className="text-sm font-medium flex-1">{module.name}</span>
                      <ChevronRight className="h-4 w-4 text-slate-300" />
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Fields Configuration */}
        <div className="col-span-9">
          {selectedModule && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {(() => {
                      const Icon = getIconComponent(selectedModule.id);
                      return <Icon className="h-6 w-6 text-accent" />;
                    })()}
                    <div>
                      <CardTitle>{selectedModule.name}</CardTitle>
                      <p className="text-sm text-slate-500 mt-1">
                        {fields.length} custom fields configured
                      </p>
                    </div>
                  </div>
                  <Dialog open={fieldDialogOpen} onOpenChange={(open) => {
                    setFieldDialogOpen(open);
                    if (!open) resetFieldForm();
                  }}>
                    <DialogTrigger asChild>
                      <Button className="bg-accent hover:bg-accent/90">
                        <Plus className="h-4 w-4 mr-2" />Add Field
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>{editingField ? 'Edit Field' : 'Add Custom Field'}</DialogTitle>
                      </DialogHeader>
                      <form onSubmit={handleSaveField} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Field Name (API) *</Label>
                            <Input
                              value={fieldForm.field_name}
                              onChange={(e) => setFieldForm({...fieldForm, field_name: e.target.value.toLowerCase().replace(/\s+/g, '_')})}
                              placeholder="custom_field_name"
                              required
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Field Label (Display) *</Label>
                            <Input
                              value={fieldForm.field_label}
                              onChange={(e) => setFieldForm({...fieldForm, field_label: e.target.value})}
                              placeholder="Custom Field Label"
                              required
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Field Type *</Label>
                            <Select value={fieldForm.field_type} onValueChange={(v) => setFieldForm({...fieldForm, field_type: v})}>
                              <SelectTrigger><SelectValue /></SelectTrigger>
                              <SelectContent>
                                {FIELD_TYPES.map(type => (
                                  <SelectItem key={type.value} value={type.value}>
                                    {type.icon} {type.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Section</Label>
                            <Input
                              value={fieldForm.section}
                              onChange={(e) => setFieldForm({...fieldForm, section: e.target.value})}
                              placeholder="e.g., Personal Info, Tax Details"
                            />
                          </div>
                        </div>

                        {(fieldForm.field_type === 'select' || fieldForm.field_type === 'multiselect') && (
                          <div className="space-y-2">
                            <Label>Options (comma separated)</Label>
                            <Textarea
                              value={fieldForm.options}
                              onChange={(e) => setFieldForm({...fieldForm, options: e.target.value})}
                              placeholder="Option 1, Option 2, Option 3"
                            />
                          </div>
                        )}

                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Placeholder</Label>
                            <Input
                              value={fieldForm.placeholder}
                              onChange={(e) => setFieldForm({...fieldForm, placeholder: e.target.value})}
                              placeholder="Enter placeholder text..."
                            />
                          </div>
                          <div className="space-y-2">
                            <Label>Default Value</Label>
                            <Input
                              value={fieldForm.default_value}
                              onChange={(e) => setFieldForm({...fieldForm, default_value: e.target.value})}
                              placeholder="Default value"
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <Label>Help Text</Label>
                          <Textarea
                            value={fieldForm.help_text}
                            onChange={(e) => setFieldForm({...fieldForm, help_text: e.target.value})}
                            placeholder="Instructions or help text for this field"
                            rows={2}
                          />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                          <div className="flex items-center gap-3">
                            <Switch
                              checked={fieldForm.is_required}
                              onCheckedChange={(v) => setFieldForm({...fieldForm, is_required: v})}
                            />
                            <Label>Required Field</Label>
                          </div>
                          <div className="flex items-center gap-3">
                            <Switch
                              checked={fieldForm.is_searchable}
                              onCheckedChange={(v) => setFieldForm({...fieldForm, is_searchable: v})}
                            />
                            <Label>Searchable</Label>
                          </div>
                          <div className="flex items-center gap-3">
                            <Switch
                              checked={fieldForm.is_filterable}
                              onCheckedChange={(v) => setFieldForm({...fieldForm, is_filterable: v})}
                            />
                            <Label>Filterable</Label>
                          </div>
                          <div className="flex items-center gap-3">
                            <Switch
                              checked={fieldForm.show_in_list}
                              onCheckedChange={(v) => setFieldForm({...fieldForm, show_in_list: v})}
                            />
                            <Label>Show in List View</Label>
                          </div>
                        </div>

                        <DialogFooter>
                          <Button type="button" variant="outline" onClick={() => setFieldDialogOpen(false)}>Cancel</Button>
                          <Button type="submit" className="bg-accent">
                            <Save className="h-4 w-4 mr-2" />{editingField ? 'Update' : 'Create'} Field
                          </Button>
                        </DialogFooter>
                      </form>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent>
                {fields.length > 0 ? (
                  <div className="space-y-2">
                    {/* Group by section */}
                    {(() => {
                      const sections = {};
                      fields.forEach(f => {
                        const sec = f.section || 'General';
                        if (!sections[sec]) sections[sec] = [];
                        sections[sec].push(f);
                      });
                      return Object.entries(sections).map(([section, sectionFields]) => (
                        <div key={section} className="mb-4">
                          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">{section}</h3>
                          <div className="space-y-2">
                            {sectionFields.map((field) => (
                              <div key={field.id} className="flex items-center gap-4 p-3 border rounded-lg hover:bg-slate-50 group">
                                <GripVertical className="h-4 w-4 text-slate-300 cursor-move" />
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium">{field.field_label}</span>
                                    {field.is_required && <Badge variant="destructive" className="text-[10px]">Required</Badge>}
                                    {field.is_searchable && <Badge variant="outline" className="text-[10px]">Searchable</Badge>}
                                  </div>
                                  <p className="text-xs text-slate-500">{field.field_name} • {field.field_type}</p>
                                </div>
                                <Badge>{FIELD_TYPES.find(t => t.value === field.field_type)?.label || field.field_type}</Badge>
                                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <Button size="sm" variant="ghost" onClick={() => openEditDialog(field)}>
                                    <Edit className="h-3.5 w-3.5" />
                                  </Button>
                                  <Button size="sm" variant="ghost" className="text-red-500" onClick={() => handleDeleteField(field.id)}>
                                    <Trash2 className="h-3.5 w-3.5" />
                                  </Button>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ));
                    })()}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Settings className="h-12 w-12 text-slate-200 mx-auto mb-3" />
                    <p className="text-slate-500">No custom fields configured for this module</p>
                    <p className="text-sm text-slate-400 mt-1">Click "Add Field" to create your first custom field</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default PowerSettings;
