import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Plus, Wand2, FileText, Bell, Mail, Code, Download, Upload, Play, Trash2, Edit, Eye, Copy, Check } from 'lucide-react';
import { Textarea } from '../components/ui/textarea';
import api from '../lib/api';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';

const CustomFieldsManager = () => {
  const [customFields, setCustomFields] = useState([]);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    field_name: '',
    field_label: '',
    field_type: 'text',
    module: 'crm',
    entity: 'leads',
    options: [],
    required: false
  });
  const { user } = useAuth();

  useEffect(() => {
    fetchCustomFields();
  }, []);

  const fetchCustomFields = async () => {
    try {
      const response = await api.get('/customization/custom-fields');
      setCustomFields(response.data || []);
    } catch (error) {
      console.error('Failed to load custom fields:', error);
      setCustomFields([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/customization/custom-fields', formData);
      toast.success('Custom field created successfully');
      setOpen(false);
      fetchCustomFields();
      setFormData({ field_name: '', field_label: '', field_type: 'text', module: 'crm', entity: 'leads', options: [], required: false });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create custom field');
    }
  };

  const handleDelete = async (fieldId) => {
    if (!confirm('Are you sure you want to delete this custom field?')) return;
    try {
      await api.delete(`/customization/custom-fields/${fieldId}`);
      toast.success('Custom field deleted');
      fetchCustomFields();
    } catch (error) {
      toast.error('Failed to delete custom field');
    }
  };

  if (user?.role !== 'admin') {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-6">
          <p className="text-slate-600 font-inter">Only administrators can manage custom fields.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-slate-900 font-manrope">Custom Fields</h3>
          <p className="text-slate-600 text-sm mt-1 font-inter">Add custom fields to any module</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90 font-inter" data-testid="add-custom-field-button">
              <Plus className="h-4 w-4 mr-2" />
              Add Custom Field
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="font-manrope">Create Custom Field</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="module" className="font-inter">Module</Label>
                  <Select value={formData.module} onValueChange={(value) => setFormData({...formData, module: value})} required>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="crm">CRM</SelectItem>
                      <SelectItem value="inventory">Inventory</SelectItem>
                      <SelectItem value="production">Production</SelectItem>
                      <SelectItem value="procurement">Procurement</SelectItem>
                      <SelectItem value="accounts">Accounts</SelectItem>
                      <SelectItem value="hrms">HRMS</SelectItem>
                      <SelectItem value="quality">Quality</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="entity" className="font-inter">Entity</Label>
                  <Input id="entity" value={formData.entity} onChange={(e) => setFormData({...formData, entity: e.target.value})} placeholder="e.g., leads, items" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="field_name" className="font-inter">Field Name (Internal)</Label>
                  <Input id="field_name" value={formData.field_name} onChange={(e) => setFormData({...formData, field_name: e.target.value})} placeholder="e.g., customer_rating" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="field_label" className="font-inter">Field Label (Display)</Label>
                  <Input id="field_label" value={formData.field_label} onChange={(e) => setFormData({...formData, field_label: e.target.value})} placeholder="e.g., Customer Rating" required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="field_type" className="font-inter">Field Type</Label>
                  <Select value={formData.field_type} onValueChange={(value) => setFormData({...formData, field_type: value})} required>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="text">Text</SelectItem>
                      <SelectItem value="number">Number</SelectItem>
                      <SelectItem value="date">Date</SelectItem>
                      <SelectItem value="select">Dropdown</SelectItem>
                      <SelectItem value="checkbox">Checkbox</SelectItem>
                      <SelectItem value="textarea">Text Area</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Required</Label>
                  <div className="flex items-center gap-2 h-10">
                    <input
                      type="checkbox"
                      checked={formData.required}
                      onChange={(e) => setFormData({...formData, required: e.target.checked})}
                      className="h-4 w-4"
                    />
                    <span className="text-sm text-slate-600 font-inter">Make this field mandatory</span>
                  </div>
                </div>
              </div>
              {formData.field_type === 'select' && (
                <div className="space-y-2">
                  <Label htmlFor="options" className="font-inter">Dropdown Options (comma-separated)</Label>
                  <Input
                    id="options"
                    placeholder="e.g., Excellent, Good, Average, Poor"
                    onChange={(e) => setFormData({...formData, options: e.target.value.split(',').map(o => o.trim())})}
                  />
                </div>
              )}
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Create Field</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Module</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Entity</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Field Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Label</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Required</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {customFields.map((field) => (
                  <tr key={field.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3"><Badge className="bg-blue-100 text-blue-800 font-inter">{field.module}</Badge></td>
                    <td className="px-4 py-3 text-sm text-slate-600 font-inter">{field.entity}</td>
                    <td className="px-4 py-3 text-sm font-mono text-slate-900">{field.field_name}</td>
                    <td className="px-4 py-3 text-sm text-slate-600 font-inter">{field.field_label}</td>
                    <td className="px-4 py-3"><Badge variant="outline" className="font-inter">{field.field_type}</Badge></td>
                    <td className="px-4 py-3">{field.required ? <Badge className="bg-orange-100 text-orange-800">Yes</Badge> : <Badge className="bg-gray-100 text-gray-800">No</Badge>}</td>
                    <td className="px-4 py-3">
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(field.id)} className="text-destructive hover:text-destructive">Delete</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const ReportBuilder = () => {
  const [reports, setReports] = useState([]);
  const [open, setOpen] = useState(false);
  const [executeOpen, setExecuteOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    module: 'crm',
    query_filters: {},
    columns: [],
    group_by: [],
    chart_type: ''
  });
  const { user } = useAuth();

  const modules = [
    { value: 'crm', label: 'CRM (Leads)' },
    { value: 'inventory', label: 'Inventory (Stock)' },
    { value: 'production', label: 'Production (Work Orders)' },
    { value: 'accounts', label: 'Accounts (Invoices)' },
    { value: 'hrms', label: 'HRMS (Employees)' },
    { value: 'quality', label: 'Quality (Inspections)' }
  ];

  const columnOptions = {
    crm: ['company_name', 'contact_person', 'email', 'phone', 'status', 'source', 'estimated_value', 'created_at'],
    inventory: ['item_code', 'item_name', 'category', 'stock_quantity', 'uom', 'standard_cost', 'selling_price'],
    production: ['wo_number', 'product_name', 'quantity', 'status', 'planned_start_date', 'planned_end_date'],
    accounts: ['invoice_number', 'customer_name', 'invoice_date', 'total_amount', 'status', 'due_date'],
    hrms: ['employee_code', 'name', 'department', 'designation', 'date_of_joining', 'basic_salary'],
    quality: ['inspection_number', 'product_name', 'inspection_date', 'result', 'inspector_name']
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await api.get('/customization/report-templates');
      setReports(response.data || []);
    } catch (error) {
      console.error('Failed to load reports:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name || formData.columns.length === 0) {
      toast.error('Please provide a name and select at least one column');
      return;
    }
    try {
      const columnsData = formData.columns.map(col => ({ field: col, label: col.replace(/_/g, ' ').toUpperCase() }));
      await api.post('/customization/report-templates', {
        ...formData,
        columns: columnsData
      });
      toast.success('Report template created successfully');
      setOpen(false);
      fetchReports();
      setFormData({ name: '', description: '', module: 'crm', query_filters: {}, columns: [], group_by: [], chart_type: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create report');
    }
  };

  const handleExecute = async (report) => {
    setSelectedReport(report);
    setLoading(true);
    setExecuteOpen(true);
    try {
      const response = await api.post(`/customization/report-templates/${report.id}/execute`);
      setReportData(response.data);
    } catch (error) {
      toast.error('Failed to execute report');
    } finally {
      setLoading(false);
    }
  };

  const toggleColumn = (col) => {
    setFormData(prev => ({
      ...prev,
      columns: prev.columns.includes(col) 
        ? prev.columns.filter(c => c !== col)
        : [...prev.columns, col]
    }));
  };

  if (user?.role !== 'admin') {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-6">
          <p className="text-slate-600 font-inter">Only administrators can manage report templates.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-slate-900 font-manrope">Report Builder</h3>
          <p className="text-slate-600 text-sm mt-1 font-inter">Create and execute custom reports</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90 font-inter" data-testid="create-report-button">
              <Plus className="h-4 w-4 mr-2" />
              Create Report
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-manrope">Create Report Template</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="font-inter">Report Name *</Label>
                  <Input 
                    value={formData.name} 
                    onChange={(e) => setFormData({...formData, name: e.target.value})} 
                    placeholder="e.g., Monthly Sales Report"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Module *</Label>
                  <Select value={formData.module} onValueChange={(v) => setFormData({...formData, module: v, columns: []})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {modules.map(m => (
                        <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label className="font-inter">Description</Label>
                <Textarea 
                  value={formData.description} 
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  placeholder="What does this report show?"
                />
              </div>
              <div className="space-y-2">
                <Label className="font-inter">Select Columns *</Label>
                <div className="flex flex-wrap gap-2 p-3 bg-slate-50 rounded-lg border">
                  {columnOptions[formData.module]?.map(col => (
                    <Badge 
                      key={col} 
                      variant={formData.columns.includes(col) ? 'default' : 'outline'}
                      className="cursor-pointer hover:bg-accent/20"
                      onClick={() => toggleColumn(col)}
                    >
                      {formData.columns.includes(col) && <Check className="h-3 w-3 mr-1" />}
                      {col.replace(/_/g, ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <Label className="font-inter">Chart Type (optional)</Label>
                <Select value={formData.chart_type} onValueChange={(v) => setFormData({...formData, chart_type: v})}>
                  <SelectTrigger><SelectValue placeholder="No chart" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No chart</SelectItem>
                    <SelectItem value="bar">Bar Chart</SelectItem>
                    <SelectItem value="line">Line Chart</SelectItem>
                    <SelectItem value="pie">Pie Chart</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Create Report</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Execute Report Dialog */}
      <Dialog open={executeOpen} onOpenChange={setExecuteOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-manrope">{selectedReport?.name}</DialogTitle>
          </DialogHeader>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin h-8 w-8 border-4 border-accent border-t-transparent rounded-full"></div>
            </div>
          ) : reportData ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Badge variant="outline">{reportData.count} records found</Badge>
                <span className="text-xs text-slate-500">Executed: {new Date(reportData.executed_at).toLocaleString()}</span>
              </div>
              <div className="overflow-x-auto border rounded-lg">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 border-b">
                    <tr>
                      {reportData.template.columns.map((col, i) => (
                        <th key={i} className="px-3 py-2 text-left font-semibold text-slate-700">{col.label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {reportData.data.slice(0, 50).map((row, i) => (
                      <tr key={i} className="hover:bg-slate-50">
                        {reportData.template.columns.map((col, j) => (
                          <td key={j} className="px-3 py-2 text-slate-600">{row[col.field] ?? '-'}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {reportData.count > 50 && <p className="text-xs text-slate-500 text-center">Showing 50 of {reportData.count} records</p>}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Reports List */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          {reports.length === 0 ? (
            <div className="p-8 text-center">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-600 font-inter">No report templates yet. Create your first report!</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Name</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Module</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Columns</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Created</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {reports.map((report) => (
                    <tr key={report.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium text-slate-900">{report.name}</p>
                          {report.description && <p className="text-xs text-slate-500">{report.description}</p>}
                        </div>
                      </td>
                      <td className="px-4 py-3"><Badge className="bg-blue-100 text-blue-800">{report.module}</Badge></td>
                      <td className="px-4 py-3 text-sm text-slate-600">{report.columns?.length || 0} fields</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{new Date(report.created_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3">
                        <Button variant="ghost" size="sm" onClick={() => handleExecute(report)} className="text-accent">
                          <Play className="h-4 w-4 mr-1" /> Run
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Email Templates Manager
const EmailTemplatesManager = () => {
  const [templates, setTemplates] = useState([
    { id: '1', name: 'Welcome Email', type: 'customer_welcome', subject: 'Welcome to InstaBiz!', content: 'Dear {{customer_name}},\n\nThank you for choosing InstaBiz...', is_active: true },
    { id: '2', name: 'Invoice Email', type: 'invoice', subject: 'Invoice #{{invoice_number}}', content: 'Dear {{customer_name}},\n\nPlease find attached invoice...', is_active: true },
    { id: '3', name: 'Payment Reminder', type: 'payment_reminder', subject: 'Payment Reminder - Invoice #{{invoice_number}}', content: 'Dear {{customer_name}},\n\nThis is a gentle reminder...', is_active: true },
    { id: '4', name: 'Order Confirmation', type: 'order_confirm', subject: 'Order Confirmed - #{{order_number}}', content: 'Dear {{customer_name}},\n\nYour order has been confirmed...', is_active: false }
  ]);
  const [open, setOpen] = useState(false);
  const [editTemplate, setEditTemplate] = useState(null);
  const [formData, setFormData] = useState({ name: '', type: '', subject: '', content: '' });
  const { user } = useAuth();

  const templateTypes = [
    { value: 'customer_welcome', label: 'Customer Welcome' },
    { value: 'invoice', label: 'Invoice Email' },
    { value: 'payment_reminder', label: 'Payment Reminder' },
    { value: 'order_confirm', label: 'Order Confirmation' },
    { value: 'quotation', label: 'Quotation Email' },
    { value: 'sample_dispatch', label: 'Sample Dispatch' }
  ];

  const variables = ['{{customer_name}}', '{{company_name}}', '{{invoice_number}}', '{{order_number}}', '{{amount}}', '{{due_date}}', '{{sales_rep}}'];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (editTemplate) {
      setTemplates(templates.map(t => t.id === editTemplate.id ? { ...t, ...formData } : t));
      toast.success('Template updated');
    } else {
      setTemplates([...templates, { id: Date.now().toString(), ...formData, is_active: true }]);
      toast.success('Template created');
    }
    setOpen(false);
    setEditTemplate(null);
    setFormData({ name: '', type: '', subject: '', content: '' });
  };

  const handleEdit = (template) => {
    setEditTemplate(template);
    setFormData({ name: template.name, type: template.type, subject: template.subject, content: template.content });
    setOpen(true);
  };

  const toggleActive = (id) => {
    setTemplates(templates.map(t => t.id === id ? { ...t, is_active: !t.is_active } : t));
  };

  if (user?.role !== 'admin') {
    return <Card className="p-6"><p className="text-slate-600">Only administrators can manage email templates.</p></Card>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-slate-900 font-manrope">Email Templates</h3>
          <p className="text-slate-600 text-sm mt-1 font-inter">Customize email templates for different events</p>
        </div>
        <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) { setEditTemplate(null); setFormData({ name: '', type: '', subject: '', content: '' }); } }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="add-email-template-button">
              <Plus className="h-4 w-4 mr-2" /> Add Template
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>{editTemplate ? 'Edit' : 'Create'} Email Template</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Template Name *</Label>
                  <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label>Template Type *</Label>
                  <Select value={formData.type} onValueChange={(v) => setFormData({...formData, type: v})} required>
                    <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                    <SelectContent>
                      {templateTypes.map(t => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Subject Line *</Label>
                <Input value={formData.subject} onChange={(e) => setFormData({...formData, subject: e.target.value})} required />
              </div>
              <div className="space-y-2">
                <Label>Email Content *</Label>
                <Textarea value={formData.content} onChange={(e) => setFormData({...formData, content: e.target.value})} rows={8} required />
                <div className="flex flex-wrap gap-1">
                  <span className="text-xs text-slate-500 mr-2">Variables:</span>
                  {variables.map(v => (
                    <Badge key={v} variant="outline" className="text-xs cursor-pointer hover:bg-slate-100" onClick={() => setFormData({...formData, content: formData.content + ' ' + v})}>
                      {v}
                    </Badge>
                  ))}
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent">{editTemplate ? 'Update' : 'Create'}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="border-slate-200">
        <CardContent className="p-0">
          <table className="w-full">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Template</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Subject</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {templates.map(t => (
                <tr key={t.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">{t.name}</td>
                  <td className="px-4 py-3"><Badge variant="outline">{t.type.replace(/_/g, ' ')}</Badge></td>
                  <td className="px-4 py-3 text-sm text-slate-600 truncate max-w-xs">{t.subject}</td>
                  <td className="px-4 py-3">
                    <Badge className={t.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'}>
                      {t.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 flex gap-2">
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(t)}><Edit className="h-4 w-4" /></Button>
                    <Button variant="ghost" size="sm" onClick={() => toggleActive(t.id)}>{t.is_active ? 'Disable' : 'Enable'}</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
};

// Notification Rules Manager
const NotificationRulesManager = () => {
  const [rules, setRules] = useState([
    { id: '1', name: 'Low Stock Alert', event: 'stock_below_reorder', channels: ['in_app', 'email'], is_active: true },
    { id: '2', name: 'Payment Overdue', event: 'payment_overdue', channels: ['in_app', 'email'], is_active: true },
    { id: '3', name: 'New Lead Assigned', event: 'lead_assigned', channels: ['in_app'], is_active: true },
    { id: '4', name: 'Work Order Completed', event: 'wo_completed', channels: ['in_app'], is_active: false }
  ]);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', event: '', channels: [] });
  const { user } = useAuth();

  const events = [
    { value: 'stock_below_reorder', label: 'Stock Below Reorder Level' },
    { value: 'payment_overdue', label: 'Payment Overdue' },
    { value: 'lead_assigned', label: 'New Lead Assigned' },
    { value: 'wo_completed', label: 'Work Order Completed' },
    { value: 'quotation_expiring', label: 'Quotation Expiring' },
    { value: 'approval_pending', label: 'Approval Pending' }
  ];

  const channels = [
    { value: 'in_app', label: 'In-App Notification' },
    { value: 'email', label: 'Email' },
    { value: 'sms', label: 'SMS' },
    { value: 'whatsapp', label: 'WhatsApp' }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    setRules([...rules, { id: Date.now().toString(), ...formData, is_active: true }]);
    toast.success('Notification rule created');
    setOpen(false);
    setFormData({ name: '', event: '', channels: [] });
  };

  const toggleChannel = (ch) => {
    setFormData(prev => ({
      ...prev,
      channels: prev.channels.includes(ch) ? prev.channels.filter(c => c !== ch) : [...prev.channels, ch]
    }));
  };

  const toggleActive = (id) => {
    setRules(rules.map(r => r.id === id ? { ...r, is_active: !r.is_active } : r));
  };

  if (user?.role !== 'admin') {
    return <Card className="p-6"><p className="text-slate-600">Only administrators can manage notification rules.</p></Card>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-slate-900 font-manrope">Notification Rules</h3>
          <p className="text-slate-600 text-sm mt-1 font-inter">Configure when and how notifications are sent</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="add-notification-rule-button">
              <Plus className="h-4 w-4 mr-2" /> Add Rule
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Notification Rule</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Rule Name *</Label>
                <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} required />
              </div>
              <div className="space-y-2">
                <Label>Trigger Event *</Label>
                <Select value={formData.event} onValueChange={(v) => setFormData({...formData, event: v})} required>
                  <SelectTrigger><SelectValue placeholder="Select event" /></SelectTrigger>
                  <SelectContent>
                    {events.map(e => <SelectItem key={e.value} value={e.value}>{e.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Notification Channels *</Label>
                <div className="flex flex-wrap gap-2">
                  {channels.map(ch => (
                    <Badge
                      key={ch.value}
                      variant={formData.channels.includes(ch.value) ? 'default' : 'outline'}
                      className="cursor-pointer"
                      onClick={() => toggleChannel(ch.value)}
                    >
                      {formData.channels.includes(ch.value) && <Check className="h-3 w-3 mr-1" />}
                      {ch.label}
                    </Badge>
                  ))}
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent" disabled={formData.channels.length === 0}>Create</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="border-slate-200">
        <CardContent className="p-0">
          <table className="w-full">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Rule Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Event</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Channels</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {rules.map(r => (
                <tr key={r.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">{r.name}</td>
                  <td className="px-4 py-3 text-sm text-slate-600">{r.event.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {r.channels.map(ch => <Badge key={ch} variant="outline" className="text-xs">{ch}</Badge>)}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <Badge className={r.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'}>
                      {r.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Button variant="ghost" size="sm" onClick={() => toggleActive(r.id)}>
                      {r.is_active ? 'Disable' : 'Enable'}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
};

const Customization = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('fields');
  const backendUrl = import.meta.env.VITE_BACKEND_URL;

  const quickCards = [
    { id: 'fields', icon: Plus, color: 'blue', title: 'Custom Fields', desc: 'Add fields to any module' },
    { id: 'reports', icon: FileText, color: 'purple', title: 'Report Builder', desc: 'Create custom reports' },
    { id: 'templates', icon: Mail, color: 'orange', title: 'Email Templates', desc: 'Customize email content' },
    { id: 'notifications', icon: Bell, color: 'green', title: 'Notifications', desc: 'Setup alert rules' },
    { id: 'api', icon: Code, color: 'pink', title: 'API Access', desc: 'Integrate external systems' },
    { id: 'import', icon: Download, color: 'cyan', title: 'Data Import/Export', desc: 'Bulk operations' }
  ];

  const colorMap = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600',
    green: 'from-green-500 to-green-600',
    pink: 'from-pink-500 to-pink-600',
    cyan: 'from-cyan-500 to-cyan-600'
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 font-manrope" data-testid="customization-title">
          <Wand2 className="inline h-8 w-8 mr-2 text-accent" />
          Customization & Extensions
        </h1>
        <p className="text-slate-600 mt-1 font-inter">Extend and customize your ERP system</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {quickCards.map(card => (
          <Card 
            key={card.id}
            className={`border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer ${activeTab === card.id ? 'ring-2 ring-accent' : ''}`}
            onClick={() => setActiveTab(card.id)}
            data-testid={`quick-card-${card.id}`}
          >
            <CardContent className="p-6 text-center">
              <div className={`h-12 w-12 rounded-lg bg-gradient-to-br ${colorMap[card.color]} flex items-center justify-center mx-auto mb-3`}>
                <card.icon className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-semibold text-slate-900 font-manrope">{card.title}</h3>
              <p className="text-sm text-slate-600 mt-1 font-inter">{card.desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-white border border-slate-200">
          <TabsTrigger value="fields" className="font-inter">Custom Fields</TabsTrigger>
          <TabsTrigger value="reports" className="font-inter">Report Builder</TabsTrigger>
          <TabsTrigger value="templates" className="font-inter">Email Templates</TabsTrigger>
          <TabsTrigger value="notifications" className="font-inter">Notifications</TabsTrigger>
          <TabsTrigger value="api" className="font-inter">API Docs</TabsTrigger>
          <TabsTrigger value="import" className="font-inter">Import/Export</TabsTrigger>
        </TabsList>

        <TabsContent value="fields">
          <CustomFieldsManager />
        </TabsContent>

        <TabsContent value="reports">
          <ReportBuilder />
        </TabsContent>

        <TabsContent value="templates">
          <EmailTemplatesManager />
        </TabsContent>

        <TabsContent value="notifications">
          <NotificationRulesManager />
        </TabsContent>

        <TabsContent value="api">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="font-manrope">API Documentation</CardTitle>
              <CardDescription className="font-inter">RESTful API endpoints for external integrations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-slate-900 rounded-lg p-4 font-mono text-sm text-green-400">
                <p>Base URL: {backendUrl}/api</p>
                <p className="mt-2">Authentication: Bearer Token (JWT)</p>
                <p className="mt-4">Available Endpoints:</p>
                <ul className="mt-2 space-y-1 ml-4">
                  <li>GET /crm/leads - List all leads</li>
                  <li>POST /crm/leads - Create new lead</li>
                  <li>GET /inventory/stock - Get stock levels</li>
                  <li>POST /production/work-orders - Create work order</li>
                  <li>GET /dashboard/overview - Get dashboard data</li>
                  <li>GET /analytics/* - Reports & analytics</li>
                  <li>POST /bulk-import/* - Bulk data import</li>
                </ul>
              </div>
              <div className="mt-4 flex gap-2">
                <Button className="bg-accent hover:bg-accent/90" onClick={() => window.open(`${backendUrl}/docs`, '_blank')}>
                  <Code className="h-4 w-4 mr-2" /> Open Swagger UI
                </Button>
                <Button variant="outline" onClick={() => { navigator.clipboard.writeText(`${backendUrl}/api`); toast.success('Base URL copied!'); }}>
                  <Copy className="h-4 w-4 mr-2" /> Copy Base URL
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="import">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="font-manrope">Data Import / Export</CardTitle>
              <CardDescription className="font-inter">Bulk operations for data migration and backup</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="border-slate-200 p-4">
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <Upload className="h-5 w-5 text-blue-600" /> Import Data
                  </h4>
                  <p className="text-sm text-slate-600 mb-3">Upload Excel files to bulk import data</p>
                  <Button variant="outline" onClick={() => window.location.href = '/bulk-import'}>
                    Go to Bulk Import
                  </Button>
                </Card>
                <Card className="border-slate-200 p-4">
                  <h4 className="font-semibold mb-2 flex items-center gap-2">
                    <Download className="h-5 w-5 text-green-600" /> Export Data
                  </h4>
                  <p className="text-sm text-slate-600 mb-3">Export data to Excel or PDF format</p>
                  <Button variant="outline" onClick={() => window.location.href = '/analytics'}>
                    Go to Reports
                  </Button>
                </Card>
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <h4 className="font-semibold text-amber-800 mb-2">Supported Import Formats</h4>
                <ul className="text-sm text-amber-700 space-y-1">
                  <li>• Customers / Vendors (.xlsx)</li>
                  <li>• Items / Products (.xlsx)</li>
                  <li>• Opening Balance (.xlsx)</li>
                  <li>• Opening Stock (.xlsx)</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Customization;