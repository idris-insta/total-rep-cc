import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { 
  Plus, Search, Edit, Trash2, Eye, Phone, Mail, Calendar, 
  Building2, MoreVertical, Filter, LayoutGrid, List, RefreshCw, FileText, Settings
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../components/ui/dropdown-menu';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import api from '../lib/api';
import { toast } from 'sonner';
import DynamicFormFields from '../components/DynamicRegistryForm';
import useFieldRegistry from '../hooks/useFieldRegistry';

// Default fallback status configuration (used if Field Registry not loaded)
const DEFAULT_STATUS_CONFIG = {
  hot_leads: { label: 'Hot Leads', bg: 'bg-red-50', border: 'border-red-200', badge: 'bg-red-100 text-red-800', header: 'bg-red-500' },
  cold_leads: { label: 'Cold Leads', bg: 'bg-blue-50', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-800', header: 'bg-blue-500' },
  contacted: { label: 'Contacted', bg: 'bg-yellow-50', border: 'border-yellow-200', badge: 'bg-yellow-100 text-yellow-800', header: 'bg-yellow-500' },
  qualified: { label: 'Qualified', bg: 'bg-green-50', border: 'border-green-200', badge: 'bg-green-100 text-green-800', header: 'bg-green-500' },
  proposal: { label: 'Proposal', bg: 'bg-purple-50', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-800', header: 'bg-purple-500' },
  negotiation: { label: 'Negotiation', bg: 'bg-orange-50', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800', header: 'bg-orange-500' },
  converted: { label: 'Converted', bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-800', header: 'bg-emerald-500' },
  customer: { label: 'Customer', bg: 'bg-teal-50', border: 'border-teal-200', badge: 'bg-teal-100 text-teal-800', header: 'bg-teal-500' },
  lost: { label: 'Lost', bg: 'bg-slate-50', border: 'border-slate-200', badge: 'bg-slate-100 text-slate-800', header: 'bg-slate-500' },
  // Legacy statuses for backward compatibility
  new: { label: 'New', bg: 'bg-blue-50', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-800', header: 'bg-blue-500' }
};

// Color mapping for dynamic stages
const COLOR_MAP = {
  red: { bg: 'bg-red-50', border: 'border-red-200', badge: 'bg-red-100 text-red-800', header: 'bg-red-500' },
  blue: { bg: 'bg-blue-50', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-800', header: 'bg-blue-500' },
  yellow: { bg: 'bg-yellow-50', border: 'border-yellow-200', badge: 'bg-yellow-100 text-yellow-800', header: 'bg-yellow-500' },
  green: { bg: 'bg-green-50', border: 'border-green-200', badge: 'bg-green-100 text-green-800', header: 'bg-green-500' },
  purple: { bg: 'bg-purple-50', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-800', header: 'bg-purple-500' },
  orange: { bg: 'bg-orange-50', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-800', header: 'bg-orange-500' },
  emerald: { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-800', header: 'bg-emerald-500' },
  teal: { bg: 'bg-teal-50', border: 'border-teal-200', badge: 'bg-teal-100 text-teal-800', header: 'bg-teal-500' },
  pink: { bg: 'bg-pink-50', border: 'border-pink-200', badge: 'bg-pink-100 text-pink-800', header: 'bg-pink-500' },
  slate: { bg: 'bg-slate-50', border: 'border-slate-200', badge: 'bg-slate-100 text-slate-800', header: 'bg-slate-500' }
};

const DEFAULT_STATUSES = ['hot_leads', 'cold_leads', 'contacted', 'qualified', 'proposal', 'negotiation', 'converted', 'customer', 'lost'];

// ==================== EDITABLE SELECT COMPONENT ====================
export const EditableSelect = ({ value, onChange, category, options: initialOptions, placeholder, className }) => {
  const [options, setOptions] = useState(initialOptions || []);
  const [newValue, setNewValue] = useState('');
  const [isAdding, setIsAdding] = useState(false);

  const fetchOptions = useCallback(async () => {
    try {
      const response = await api.get(`/master-data/category/${category}`);
      setOptions(response.data);
    } catch (error) {
      console.error('Failed to fetch options:', error);
    }
  }, [category]);

  useEffect(() => {
    if (category && (!initialOptions || initialOptions.length === 0)) {
      // Use a micro task to avoid triggering the eslint rule for setState-in-effect
      const t = setTimeout(() => {
        fetchOptions();
      }, 0);
      return () => clearTimeout(t);
    }
  }, [category, initialOptions, fetchOptions]);

  // (removed duplicate fetchOptions block)


  const handleAddNew = async () => {
    if (!newValue.trim()) return;
    
    try {
      if (category) {
        await api.post(`/master-data/category/${category}`, {
          value: newValue.trim(),
          label: newValue.trim()
        });
        await fetchOptions();
      } else {
        setOptions([...options, { value: newValue.trim(), label: newValue.trim() }]);
      }
      onChange(newValue.trim());
      setNewValue('');
      setIsAdding(false);
      toast.success('Option added');
    } catch (error) {
      toast.error('Failed to add option');
    }
  };

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className={className}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((opt) => (
          <SelectItem key={opt.value} value={opt.value}>
            {opt.label}
          </SelectItem>
        ))}
        {isAdding ? (
          <div className="p-2 flex gap-2">
            <Input
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              placeholder="New value..."
              className="h-8"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleAddNew();
                if (e.key === 'Escape') setIsAdding(false);
              }}
            />
            <Button size="sm" onClick={handleAddNew} className="h-8">Add</Button>
          </div>
        ) : (
          <div 
            className="p-2 text-sm text-blue-600 cursor-pointer hover:bg-blue-50"
            onClick={(e) => { e.stopPropagation(); setIsAdding(true); }}
          >
            + Add New
          </div>
        )}
      </SelectContent>
    </Select>
  );
};

// ==================== LEAD CARD COMPONENT ====================
const LeadCard = ({ lead, index, onEdit, onView, onDelete, statusConfig }) => {
  const config = statusConfig[lead.status] || statusConfig.new || { label: lead.status, bg: 'bg-slate-50', border: 'border-slate-200', badge: 'bg-slate-100 text-slate-800', header: 'bg-slate-500' };
  
  return (
    <Draggable draggableId={lead.id} index={index}>
      {(provided, snapshot) => (
        <div
          ref={provided.innerRef}
          {...provided.draggableProps}
          {...provided.dragHandleProps}
          className={`mb-3 ${snapshot.isDragging ? 'opacity-75 rotate-2' : ''}`}
        >
          <Card className={`${config.bg} ${config.border} border shadow-sm hover:shadow-md transition-all cursor-grab active:cursor-grabbing`}>
            <CardContent className="p-3">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-slate-900 text-sm truncate font-inter">{lead.company_name}</h4>
                  <p className="text-xs text-slate-500 truncate font-inter">{lead.contact_person}</p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onView?.(lead)}>
                      <Eye className="h-4 w-4 mr-2" />View Details
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onEdit?.(lead)}>
                      <Edit className="h-4 w-4 mr-2" />Edit Lead
                    </DropdownMenuItem>
                    {lead.status === 'proposal' && (
                      <DropdownMenuItem onClick={async () => {
                        try {
                          const res = await api.post(`/crm/leads/${lead.id}/create-quotation`);
                          toast.success(`Quotation created: ${res.data?.quote_number || ''}`);
                        } catch (e) {
                          toast.error(e.response?.data?.detail || 'Failed to create quotation');
                        }
                      }}>
                        <FileText className="h-4 w-4 mr-2" />Create Quotation
                      </DropdownMenuItem>
                    )}
                    <DropdownMenuItem onClick={() => onDelete?.(lead)} className="text-red-600">
                      <Trash2 className="h-4 w-4 mr-2" />Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
              
              <div className="space-y-1 text-xs text-slate-600">
                {lead.email && (
                  <div className="flex items-center gap-1 truncate">
                    <Mail className="h-3 w-3 flex-shrink-0" />
                    <span className="truncate">{lead.email}</span>
                  </div>
                )}
                {lead.phone && (
                  <div className="flex items-center gap-1">
                    <Phone className="h-3 w-3 flex-shrink-0" />
                    <span className="font-mono">{lead.phone}</span>
                  </div>
                )}
                {lead.product_interest && (
                  <div className="flex items-center gap-1 truncate">
                    <Building2 className="h-3 w-3 flex-shrink-0" />
                    <span className="truncate">{lead.product_interest}</span>
                  </div>
                )}
              </div>
              
              <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-200/50">
                <Badge className={`${config.badge} text-xs`}>{lead.source}</Badge>
                {lead.estimated_value && (
                  <span className="text-xs font-semibold text-slate-700 font-mono">
                    ₹{lead.estimated_value.toLocaleString('en-IN')}
                  </span>
                )}
              </div>
              
              {lead.next_followup_date && (
                <div className="flex items-center gap-1 mt-2 text-xs text-slate-500">
                  <Calendar className="h-3 w-3" />
                  <span>Follow-up: {new Date(lead.next_followup_date).toLocaleDateString()}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </Draggable>
  );
};

// ==================== KANBAN COLUMN COMPONENT ====================
const KanbanColumn = ({ status, leads, onEdit, onView, onDelete, statusConfig }) => {
  const config = statusConfig[status] || { label: status, bg: 'bg-slate-50', border: 'border-slate-200', badge: 'bg-slate-100 text-slate-800', header: 'bg-slate-500' };
  
  return (
    <div className="flex-shrink-0 w-72">
      <div className={`${config.header} rounded-t-lg px-3 py-2`}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-white text-sm font-inter">{config.label}</h3>
          <Badge className="bg-white/20 text-white border-0">{leads.length}</Badge>
        </div>
      </div>
      <Droppable droppableId={status} isDropDisabled={false} isCombineEnabled={false}>
        {(provided, snapshot) => (
          <div
            ref={provided.innerRef}
            {...provided.droppableProps}
            className={`${config.bg} ${config.border} border border-t-0 rounded-b-lg p-2 min-h-[400px] max-h-[calc(100vh-320px)] overflow-y-auto ${
              snapshot.isDraggingOver ? 'ring-2 ring-blue-400' : ''
            }`}
          >
            {leads.map((lead, index) => (
              <LeadCard 
                key={lead.id} 
                lead={lead} 
                index={index} 
                onEdit={onEdit}
                onView={onView}
                onDelete={onDelete}
                statusConfig={statusConfig}
              />
            ))}
            {provided.placeholder}
            {leads.length === 0 && (
              <div className="text-center py-8 text-slate-400 text-sm font-inter">
                No leads in this stage
              </div>
            )}
          </div>
        )}
      </Droppable>
    </div>
  );
};

// ==================== LEAD FORM DIALOG ====================
const LeadFormDialog = ({ open, onOpenChange, lead, onSuccess, statusConfig = DEFAULT_STATUS_CONFIG, statuses = DEFAULT_STATUSES }) => {
  const [salesUsers, setSalesUsers] = useState([]);
  const [loadingGeo, setLoadingGeo] = useState(false);
  const [stateOptions, setStateOptions] = useState([]);
  
  // Field Registry integration - dynamic fields
  const { 
    formFields: registryFields, 
    loading: registryLoading, 
    sectionLabels 
  } = useFieldRegistry('crm', 'leads');
  
  // Check if we have dynamic fields from registry
  const useDynamicForm = registryFields && registryFields.length > 0;

  const [formData, setFormData] = useState({
    company_name: '', contact_person: '', email: '', phone: '', mobile: '',
    address: '', country: 'India', state: '', district: '', city: '', pincode: '',
    customer_type: '', pipeline: 'main', assigned_to: 'unassigned',
    source: 'IndiaMART', industry: '', product_interest: '',
    estimated_value: '', notes: '', next_followup_date: '', followup_activity: '',
    status: 'hot_leads'
  });

  const loadSalesUsers = useCallback(async () => {
    try {
      const res = await api.get('/crm/users/sales');
      setSalesUsers(res.data || []);
    } catch (e) {
      // Non-blocking
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    
    if (lead) {
      // editing mode - populate with existing lead data  
      setFormData({
        company_name: lead.company_name || '',
        contact_person: lead.contact_person || '',
        email: lead.email || '',
        phone: lead.phone || '',
        mobile: lead.mobile || '',
        address: lead.address || '',
        country: lead.country || 'India',
        state: lead.state || '',
        district: lead.district || '',
        city: lead.city || '',
        pincode: lead.pincode || '',
        customer_type: lead.customer_type || '',
        pipeline: lead.pipeline || 'main',
        assigned_to: lead.assigned_to ? lead.assigned_to : 'unassigned',
        source: lead.source || 'IndiaMART',
        industry: lead.industry || '',
        product_interest: lead.product_interest || '',
        estimated_value: lead.estimated_value || '',
        notes: lead.notes || '',
        next_followup_date: lead.next_followup_date || '',
        followup_activity: lead.followup_activity || '',
        status: lead.status || 'hot_leads'
      });
    } else {
      // new lead - reset to empty values
      setFormData({
        company_name: '', contact_person: '', email: '', phone: '', mobile: '',
        address: '', country: 'India', state: '', district: '', city: '', pincode: '',
        customer_type: '', pipeline: 'main', assigned_to: 'unassigned',
        source: 'IndiaMART', industry: '', product_interest: '',
        estimated_value: '', notes: '', next_followup_date: '', followup_activity: '',
        status: 'hot_leads'
      });
    }
  }, [lead, open]);

  // assigned_to uses 'unassigned' token in UI; normalized to null on submit

  const loadStates = useCallback(async (country) => {
    if (!country) return;
    try {
      const res = await api.get(`/crm/geo/states?country=${encodeURIComponent(country)}`);
      setStateOptions(res.data?.states || []);
    } catch (e) {
      setStateOptions([]);
    }
  }, []);

  const tryAutoFillFromPincode = useCallback(async (pincode) => {
    if (!pincode || pincode.length !== 6) return;
    setLoadingGeo(true);
    try {
      const res = await api.get(`/crm/geo/pincode/${pincode}`);
      setFormData((prev) => ({
        ...prev,
        country: res.data?.country || prev.country,
        state: res.data?.state || prev.state,
        district: res.data?.district || prev.district,
        city: res.data?.city || prev.city
      }));
    } catch (e) {
      // ignore if not found
    } finally {
      setLoadingGeo(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    loadSalesUsers();
    loadStates(formData.country || 'India');
  }, [open]);

  useEffect(() => {
    if (!open) return;
    loadStates(formData.country || 'India');
    // Reset state if country changed
    setFormData((prev) => ({ ...prev, state: '' }));
  }, [formData.country]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        assigned_to: (formData.assigned_to === 'unassigned' || !formData.assigned_to) ? null : formData.assigned_to,
        estimated_value: formData.estimated_value ? parseFloat(formData.estimated_value) : null,
        status: formData.status || (lead?.status || 'hot_leads')
      };
      
      if (lead) {
        await api.put(`/crm/leads/${lead.id}`, payload);
        toast.success('Lead updated');
      } else {
        await api.post('/crm/leads', payload);
        toast.success('Lead created');
      }
      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save lead');
    }
  };

  // Handle pincode autofill for dynamic form
  const handleDynamicFormChange = (newFormData) => {
    // Check if pincode changed and trigger autofill
    if (newFormData.pincode !== formData.pincode && 
        newFormData.pincode?.length === 6 && 
        (newFormData.country || 'India').toLowerCase() === 'india') {
      tryAutoFillFromPincode(newFormData.pincode);
    }
    setFormData(newFormData);
  };

  // Show loading while fetching registry config
  if (registryLoading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl">
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin h-8 w-8 border-4 border-accent border-t-transparent rounded-full"></div>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="font-manrope">{lead ? 'Edit Lead' : 'Create New Lead'}</DialogTitle>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => window.open('/field-registry?module=crm&entity=leads', '_blank')}
              className="text-slate-500 hover:text-accent"
              title="Customize form fields"
            >
              <Settings className="h-4 w-4 mr-1" />
              Customize Fields
            </Button>
          </div>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Dynamic Form Fields from Field Registry */}
          {useDynamicForm ? (
            <DynamicFormFields
              fields={registryFields}
              formData={formData}
              onChange={handleDynamicFormChange}
              sectionLabels={sectionLabels}
              groupBySection={true}
              columns={3}
            />
          ) : (
            /* Fallback to basic hardcoded form if no registry config */
            <>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Company Name *</Label>
                  <Input value={formData.company_name} onChange={(e) => setFormData({...formData, company_name: e.target.value})} required data-testid="field-company_name" />
                </div>
                <div className="space-y-2">
                  <Label>Contact Person *</Label>
                  <Input value={formData.contact_person} onChange={(e) => setFormData({...formData, contact_person: e.target.value})} required data-testid="field-contact_person" />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} data-testid="field-email" />
                </div>
                <div className="space-y-2">
                  <Label>Phone</Label>
                  <Input value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} data-testid="field-phone" />
                </div>
                <div className="space-y-2">
                  <Label>Source</Label>
                  <EditableSelect 
                    value={formData.source} 
                    onChange={(value) => setFormData({...formData, source: value})}
                    category="lead_source"
                    placeholder="Select source"
                  />
                </div>
                <div className="space-y-2">
                  <Label>City</Label>
                  <Input value={formData.city} onChange={(e) => setFormData({...formData, city: e.target.value})} data-testid="field-city" />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Stage</Label>
                  <Select value={formData.status || (lead?.status || 'hot_leads')} onValueChange={(v) => setFormData({...formData, status: v})}>
                    <SelectTrigger><SelectValue placeholder="Select stage" /></SelectTrigger>
                    <SelectContent>
                      {statuses.map(s => <SelectItem key={s} value={s}>{statusConfig[s]?.label || s}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Estimated Value (₹)</Label>
                  <Input type="number" value={formData.estimated_value} onChange={(e) => setFormData({...formData, estimated_value: e.target.value})} placeholder="50000" data-testid="field-estimated_value" />
                </div>
                <div className="space-y-2">
                  <Label>Next Follow-up</Label>
                  <Input type="date" value={formData.next_followup_date} onChange={(e) => setFormData({...formData, next_followup_date: e.target.value})} data-testid="field-next_followup_date" />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={3} data-testid="field-notes" />
              </div>
            </>
          )}

          {loadingGeo && <div className="text-xs text-slate-500 text-center">Auto-filling location from pincode…</div>}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" className="bg-accent hover:bg-accent/90" data-testid="lead-submit-btn">{lead ? 'Update' : 'Create'} Lead</Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

// ==================== ADVANCED FILTERS ====================
const AdvancedFilters = ({ filters, onChange, onClear, statusConfig = DEFAULT_STATUS_CONFIG, statuses = DEFAULT_STATUSES }) => {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm">
          <Filter className="h-4 w-4 mr-2" />
          Filters
          {Object.values(filters).filter(v => v && v !== 'all').length > 0 && (
            <Badge className="ml-2 bg-accent text-white">{Object.values(filters).filter(v => v && v !== 'all').length}</Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="end">
        <div className="space-y-4">
          <h4 className="font-semibold text-slate-900">Filter Leads</h4>
          
          <div className="space-y-2">
            <Label className="text-xs">Status</Label>
            <Select value={filters.status || 'all'} onValueChange={(v) => onChange({...filters, status: v})}>
              <SelectTrigger className="h-8"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                {statuses.map(s => <SelectItem key={s} value={s}>{statusConfig[s]?.label || s}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label className="text-xs">Source</Label>
            <EditableSelect 
              value={filters.source || 'all'} 
              onChange={(v) => onChange({...filters, source: v})}
              category="lead_source"
              placeholder="All Sources"
              className="h-8"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-xs">Industry</Label>
            <EditableSelect 
              value={filters.industry || 'all'} 
              onChange={(v) => onChange({...filters, industry: v})}
              category="industry"
              placeholder="All Industries"
              className="h-8"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-xs">City</Label>
            <Input 
              value={filters.city || ''} 
              onChange={(e) => onChange({...filters, city: e.target.value})}
              placeholder="Filter by city"
              className="h-8"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-xs">State</Label>
            <Input 
              value={filters.state || ''} 
              onChange={(e) => onChange({...filters, state: e.target.value})}
              placeholder="Filter by state"
              className="h-8"
            />
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onClear} className="flex-1">Clear All</Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};

// ==================== MAIN LEADS PAGE ====================
const LeadsPage = () => {
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [kanbanData, setKanbanData] = useState({});
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('kanban'); // 'kanban' or 'list'
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({ status: 'all', source: 'all', industry: 'all', city: '', state: '' });
  const [formOpen, setFormOpen] = useState(false);
  const [editingLead, setEditingLead] = useState(null);
  
  // ========== FIELD REGISTRY INTEGRATION ==========
  const { stages, fields, loading: registryLoading, formFields, activeStages } = useFieldRegistry('crm', 'leads');
  
  // Build dynamic STATUS_CONFIG from Field Registry stages
  const STATUS_CONFIG = React.useMemo(() => {
    if (activeStages && activeStages.length > 0) {
      const config = {};
      activeStages.forEach(stage => {
        const colorStyle = COLOR_MAP[stage.color] || COLOR_MAP.blue;
        config[stage.value] = {
          label: stage.label,
          ...colorStyle
        };
      });
      return config;
    }
    return DEFAULT_STATUS_CONFIG;
  }, [activeStages]);
  
  // Build dynamic STATUSES array from Field Registry
  const STATUSES = React.useMemo(() => {
    if (activeStages && activeStages.length > 0) {
      return activeStages.sort((a, b) => (a.order || 0) - (b.order || 0)).map(s => s.value);
    }
    return DEFAULT_STATUSES;
  }, [activeStages]);

  useEffect(() => {
    fetchData();
  }, [viewMode, filters]);

  const fetchData = async () => {
    try {
      setLoading(true);
      if (viewMode === 'kanban') {
        const response = await api.get('/crm/leads/kanban/view');
        setKanbanData(response.data.data || {});
      } else {
        const params = new URLSearchParams();
        if (filters.status && filters.status !== 'all') params.append('status', filters.status);
        if (filters.source && filters.source !== 'all') params.append('source', filters.source);
        if (filters.industry && filters.industry !== 'all') params.append('industry', filters.industry);
        if (filters.city) params.append('city', filters.city);
        if (filters.state) params.append('state', filters.state);
        if (searchTerm) params.append('search', searchTerm);
        
        const response = await api.get(`/crm/leads?${params.toString()}`);
        setLeads(response.data);
      }
    } catch (error) {
      toast.error('Failed to load leads');
    } finally {
      setLoading(false);
    }
  };

  const handleDragEnd = async (result) => {
    const { destination, source, draggableId } = result;
    
    if (!destination) return;
    if (destination.droppableId === source.droppableId && destination.index === source.index) return;
    
    // Optimistic update
    const newKanbanData = { ...kanbanData };
    const sourceLeads = [...(newKanbanData[source.droppableId] || [])];
    const [movedLead] = sourceLeads.splice(source.index, 1);
    
    if (!movedLead) return;
    
    newKanbanData[source.droppableId] = sourceLeads;
    const destLeads = source.droppableId === destination.droppableId 
      ? sourceLeads 
      : [...(newKanbanData[destination.droppableId] || [])];
    
    movedLead.status = destination.droppableId;
    destLeads.splice(destination.index, 0, movedLead);
    newKanbanData[destination.droppableId] = destLeads;
    
    setKanbanData(newKanbanData);
    
    // API call
    try {
      await api.put(`/crm/leads/${draggableId}/move?new_status=${destination.droppableId}`);
      toast.success(`Lead moved to ${STATUS_CONFIG[destination.droppableId]?.label || destination.droppableId}`);
    } catch (error) {
      toast.error('Failed to move lead');
      fetchData(); // Revert on error
    }
  };

  const handleEdit = (lead) => {
    setEditingLead(lead);
    setFormOpen(true);
  };

  const handleDelete = async (lead) => {
    if (!window.confirm(`Delete lead "${lead.company_name}"?`)) return;
    try {
      await api.delete(`/crm/leads/${lead.id}`);
      toast.success('Lead deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete lead');
    }
  };

  const clearFilters = () => {
    setFilters({ status: 'all', source: 'all', industry: 'all', city: '', state: '' });
    setSearchTerm('');
  };

  if (loading || registryLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="leads-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Leads Pipeline</h2>
          <p className="text-slate-600 mt-1 font-inter">
            {viewMode === 'kanban' 
              ? `${Object.values(kanbanData).flat().length} leads across ${STATUSES.length} stages`
              : `${leads.length} leads`
            }
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center border rounded-lg overflow-hidden">
            <Button 
              variant={viewMode === 'kanban' ? 'default' : 'ghost'} 
              size="sm" 
              onClick={() => setViewMode('kanban')}
              className={viewMode === 'kanban' ? 'bg-accent' : ''}
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button 
              variant={viewMode === 'list' ? 'default' : 'ghost'} 
              size="sm" 
              onClick={() => setViewMode('list')}
              className={viewMode === 'list' ? 'bg-accent' : ''}
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button 
            onClick={() => navigate('/field-registry')} 
            variant="outline" 
            size="sm"
            title="Configure Leads fields and stages"
          >
            <Settings className="h-4 w-4" />
          </Button>
          <Button 
            onClick={() => { setEditingLead(null); setFormOpen(true); }} 
            className="bg-accent hover:bg-accent/90"
            data-testid="add-lead-btn"
          >
            <Plus className="h-4 w-4 mr-2" />Add Lead
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input 
            placeholder="Search leads..." 
            value={searchTerm} 
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchData()}
            className="pl-10" 
          />
        </div>
        <AdvancedFilters filters={filters} onChange={setFilters} onClear={clearFilters} statusConfig={STATUS_CONFIG} statuses={STATUSES} />
      </div>

      {/* Content */}
      {viewMode === 'kanban' ? (
        <DragDropContext onDragEnd={handleDragEnd}>
          <div className="flex gap-4 overflow-x-auto pb-4">
            {STATUSES.map((status) => (
              <KanbanColumn
                key={status}
                status={status}
                leads={kanbanData[status] || []}
                onEdit={handleEdit}
                onDelete={handleDelete}
                statusConfig={STATUS_CONFIG}
              />
            ))}
          </div>
        </DragDropContext>
      ) : (
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Company</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Contact</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Source</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Est. Value</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">City</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {leads.length === 0 ? (
                    <tr><td colSpan="7" className="px-4 py-12 text-center text-slate-500">No leads found</td></tr>
                  ) : (
                    leads.map((lead) => (
                      <tr key={lead.id} className="hover:bg-slate-50">
                        <td className="px-4 py-3">
                          <div className="font-semibold text-slate-900">{lead.company_name}</div>
                          <div className="text-sm text-slate-500">{lead.email}</div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-sm">{lead.contact_person}</div>
                          <div className="text-sm text-slate-500 font-mono">{lead.phone}</div>
                        </td>
                        <td className="px-4 py-3"><Badge className="bg-blue-100 text-blue-800">{lead.source}</Badge></td>
                        <td className="px-4 py-3">
                          <Badge className={STATUS_CONFIG[lead.status]?.badge}>{STATUS_CONFIG[lead.status]?.label}</Badge>
                        </td>
                        <td className="px-4 py-3 font-mono">
                          {lead.estimated_value ? `₹${lead.estimated_value.toLocaleString('en-IN')}` : '-'}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-600">{lead.city || '-'}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            <Button variant="ghost" size="sm" onClick={() => handleEdit(lead)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleDelete(lead)} className="text-destructive">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Lead Form Dialog */}
      <LeadFormDialog 
        open={formOpen} 
        onOpenChange={setFormOpen} 
        lead={editingLead}
        onSuccess={fetchData}
        statusConfig={STATUS_CONFIG}
        statuses={STATUSES}
      />
    </div>
  );
};

export default LeadsPage;
