import React, { useState, useEffect } from 'react';
import { 
  Plus, Search, Edit, Trash2, Eye, Settings
} from 'lucide-react';
import { Card, CardContent } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../../../components/ui/dialog';
import { Textarea } from '../../../components/ui/textarea';
import api from '../../../lib/api';
import { toast } from 'sonner';
import useFieldRegistry from '../../../hooks/useFieldRegistry';
import DynamicFormFields from '../../../components/DynamicRegistryForm';

const SamplesList = () => {
  const [samples, setSamples] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [formData, setFormData] = useState({
    account_id: '', contact_person: '', quotation_id: '',
    items: [{ product_name: '', product_specs: '', quantity: 1, unit: 'Pcs' }],
    from_location: '', courier: '', tracking_number: '',
    expected_delivery: '', feedback_due_date: '', purpose: '', notes: ''
  });
  const [editingSample, setEditingSample] = useState(null);

  const { 
    formFields: registryFields, 
    loading: registryLoading, 
    sectionLabels 
  } = useFieldRegistry('crm', 'samples');
  
  const headerFields = registryFields?.filter(f => f.section === 'header' || f.section === 'basic' || !f.section) || [];
  const useDynamicForm = headerFields.length > 0;

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [samplesRes, accountsRes] = await Promise.all([
        api.get('/crm/samples'),
        api.get('/crm/accounts')
      ]);
      setSamples(samplesRes.data);
      setAccounts(accountsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        items: (formData.items || []).map((it) => ({
          product_name: it.product_name,
          product_specs: it.product_specs,
          quantity: parseFloat(it.quantity) || 1,
          unit: it.unit || 'Pcs'
        }))
      };

      if (editingSample) {
        await api.put(`/crm/samples/${editingSample.id}`, payload);
        toast.success('Sample updated successfully');
      } else {
        await api.post('/crm/samples', payload);
        toast.success('Sample created successfully');
      }
      setOpen(false);
      setEditingSample(null);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save sample');
    }
  };

  const handleFeedback = async (sampleId, status) => {
    try {
      await api.put(`/crm/samples/${sampleId}/feedback?feedback_status=${status}`);
      toast.success('Feedback updated');
      fetchData();
    } catch (error) {
      toast.error('Failed to update feedback');
    }
  };

  const handleDelete = async (sampleId) => {
    if (!window.confirm('Are you sure you want to delete this sample?')) return;
    try {
      await api.delete(`/crm/samples/${sampleId}`);
      toast.success('Sample deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete sample');
    }
  };

  const handleEditSample = (sample) => {
    setEditingSample(sample);
    setFormData({
      account_id: sample.account_id || '',
      contact_person: sample.contact_person || '',
      quotation_id: sample.quotation_id || '',
      items: (sample.items && sample.items.length > 0) ? sample.items.map((it) => ({
        product_name: it.product_name || '',
        product_specs: it.product_specs || '',
        quantity: it.quantity || 1,
        unit: it.unit || 'Pcs'
      })) : [{ product_name: sample.product_name || '', product_specs: sample.product_specs || '', quantity: sample.quantity || 1, unit: sample.unit || 'Pcs' }],
      from_location: sample.from_location || '',
      courier: sample.courier || '',
      tracking_number: sample.tracking_number || '',
      expected_delivery: sample.expected_delivery || '',
      feedback_due_date: sample.feedback_due_date || '',
      purpose: sample.purpose || '',
      notes: sample.notes || ''
    });
    setOpen(true);
  };

  const resetForm = () => {
    setFormData({
      account_id: '', contact_person: '', quotation_id: '',
      items: [{ product_name: '', product_specs: '', quantity: 1, unit: 'Pcs' }],
      from_location: '', courier: '', tracking_number: '',
      expected_delivery: '', feedback_due_date: '', purpose: '', notes: ''
    });
  };

  const filteredSamples = samples.filter(sample => {
    const matchesSearch = sample.sample_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sample.account_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sample.product_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (sample.items || []).some((it) => (it.product_name || '').toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === 'all' || sample.feedback_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  if (loading || registryLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="samples-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Samples Management</h2>
          <p className="text-slate-600 mt-1 font-inter">{samples.length} total samples</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) { setEditingSample(null); resetForm(); } }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90 font-inter" onClick={() => { setEditingSample(null); resetForm(); }} data-testid="add-sample-button">
              <Plus className="h-4 w-4 mr-2" />New Sample
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <div className="flex items-center justify-between">
                <DialogTitle className="font-manrope">Send Sample</DialogTitle>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open('/field-registry?module=crm&entity=samples', '_blank')}
                  className="text-slate-500 hover:text-accent"
                  title="Customize form fields"
                >
                  <Settings className="h-4 w-4 mr-1" />
                  Customize Fields
                </Button>
              </div>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="font-inter">Customer *</Label>
                  <Select value={formData.account_id} onValueChange={(value) => setFormData({...formData, account_id: value})} required>
                    <SelectTrigger data-testid="sample-account"><SelectValue placeholder="Select customer" /></SelectTrigger>
                    <SelectContent>
                      {accounts.map(acc => (
                        <SelectItem key={acc.id} value={acc.id}>{acc.customer_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Contact Person</Label>
                  <Input value={formData.contact_person} onChange={(e) => setFormData({...formData, contact_person: e.target.value})} />
                </div>
              </div>
              
              {useDynamicForm && headerFields.length > 0 && (
                <DynamicFormFields
                  fields={headerFields}
                  formData={formData}
                  onChange={setFormData}
                  sectionLabels={sectionLabels}
                  groupBySection={false}
                  columns={2}
                />
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="font-inter">Sample Items *</Label>
                    <Button type="button" variant="outline" size="sm" onClick={() => setFormData((prev) => ({
                      ...prev,
                      items: [...(prev.items || []), { product_name: '', product_specs: '', quantity: 1, unit: 'Pcs' }]
                    }))}>
                      <Plus className="h-4 w-4 mr-2" /> Add Item
                    </Button>
                  </div>

                  <div className="space-y-3">
                    {(formData.items || []).map((it, idx) => (
                      <div key={idx} className="grid grid-cols-6 gap-2 border border-slate-200 rounded-lg p-3">
                        <div className="col-span-2 space-y-1">
                          <Label className="text-xs text-slate-600">Product Name</Label>
                          <Input value={it.product_name} onChange={(e) => setFormData((prev) => ({
                            ...prev,
                            items: prev.items.map((x, i) => i === idx ? { ...x, product_name: e.target.value } : x)
                          }))} required />
                        </div>
                        <div className="col-span-2 space-y-1">
                          <Label className="text-xs text-slate-600">Specs</Label>
                          <Input value={it.product_specs} onChange={(e) => setFormData((prev) => ({
                            ...prev,
                            items: prev.items.map((x, i) => i === idx ? { ...x, product_specs: e.target.value } : x)
                          }))} required />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs text-slate-600">Qty</Label>
                          <Input type="number" min="1" value={it.quantity} onChange={(e) => setFormData((prev) => ({
                            ...prev,
                            items: prev.items.map((x, i) => i === idx ? { ...x, quantity: e.target.value } : x)
                          }))} required />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs text-slate-600">Unit</Label>
                          <Select value={it.unit} onValueChange={(value) => setFormData((prev) => ({
                            ...prev,
                            items: prev.items.map((x, i) => i === idx ? { ...x, unit: value } : x)
                          }))}>
                            <SelectTrigger className="h-10"><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="Pcs">Pcs</SelectItem>
                              <SelectItem value="Rolls">Rolls</SelectItem>
                              <SelectItem value="Box">Box</SelectItem>
                              <SelectItem value="Kg">Kg</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="col-span-6 flex justify-end">
                          <Button type="button" variant="ghost" size="sm" className="text-destructive" onClick={() => setFormData((prev) => ({
                            ...prev,
                            items: prev.items.filter((_, i) => i !== idx)
                          }))} disabled={(formData.items || []).length <= 1}>
                            <Trash2 className="h-4 w-4 mr-2" /> Remove
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">From Location *</Label>
                  <Input value={formData.from_location} onChange={(e) => setFormData({...formData, from_location: e.target.value})} placeholder="Mumbai Factory" required data-testid="sample-location" />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Courier</Label>
                  <Select value={formData.courier} onValueChange={(value) => setFormData({...formData, courier: value})}>
                    <SelectTrigger><SelectValue placeholder="Select courier" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="DTDC">DTDC</SelectItem>
                      <SelectItem value="BlueDart">BlueDart</SelectItem>
                      <SelectItem value="Delhivery">Delhivery</SelectItem>
                      <SelectItem value="FedEx">FedEx</SelectItem>
                      <SelectItem value="Self">Self Delivery</SelectItem>
                      <SelectItem value="Transport">Transport</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Tracking Number</Label>
                  <Input value={formData.tracking_number} onChange={(e) => setFormData({...formData, tracking_number: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Expected Delivery</Label>
                  <Input type="date" value={formData.expected_delivery} onChange={(e) => setFormData({...formData, expected_delivery: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Feedback Due Date *</Label>
                  <Input type="date" value={formData.feedback_due_date} onChange={(e) => setFormData({...formData, feedback_due_date: e.target.value})} required data-testid="sample-feedback-date" />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Purpose</Label>
                  <Select value={formData.purpose} onValueChange={(value) => setFormData({...formData, purpose: value})}>
                    <SelectTrigger><SelectValue placeholder="Select purpose" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Trial">Trial</SelectItem>
                      <SelectItem value="Evaluation">Evaluation</SelectItem>
                      <SelectItem value="Quality Check">Quality Check</SelectItem>
                      <SelectItem value="New Development">New Development</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label className="font-inter">Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setOpen(false); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90" data-testid="sample-submit-button">{editingSample ? 'Update Sample' : 'Create Sample'}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder="Search samples..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" data-testid="sample-search" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="Feedback Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="positive">Positive</SelectItem>
            <SelectItem value="negative">Negative</SelectItem>
            <SelectItem value="needs_revision">Needs Revision</SelectItem>
            <SelectItem value="no_response">No Response</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Sample #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Product</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Feedback</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Due Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredSamples.length === 0 ? (
                  <tr><td colSpan="8" className="px-4 py-12 text-center text-slate-500 font-inter">
                    {searchTerm || statusFilter !== 'all' ? 'No samples found' : 'No samples yet. Click "New Sample" to create one.'}
                  </td></tr>
                ) : (
                  filteredSamples.map((sample) => (
                    <tr key={sample.id} className="hover:bg-slate-50 transition-colors" data-testid={`sample-row-${sample.id}`}>
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-orange-600">{sample.sample_number}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900 font-inter">{sample.account_name}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-slate-900 font-inter">{sample.product_name}</div>
                        <div className="text-sm text-slate-500">{sample.product_specs}</div>
                      </td>
                      <td className="px-4 py-3 font-mono text-sm">{sample.quantity} {sample.unit}</td>
                      <td className="px-4 py-3">
                        <Badge className={`font-inter ${
                          sample.status === 'created' ? 'bg-slate-100 text-slate-800' :
                          sample.status === 'dispatched' ? 'bg-blue-100 text-blue-800' :
                          sample.status === 'delivered' ? 'bg-green-100 text-green-800' : 'bg-purple-100 text-purple-800'
                        }`}>{sample.status}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Select value={sample.feedback_status} onValueChange={(val) => handleFeedback(sample.id, val)}>
                          <SelectTrigger className="w-[130px] h-8">
                            <Badge className={`font-inter ${
                              sample.feedback_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              sample.feedback_status === 'positive' ? 'bg-green-100 text-green-800' :
                              sample.feedback_status === 'negative' ? 'bg-red-100 text-red-800' : 'bg-orange-100 text-orange-800'
                            }`}>{sample.feedback_status}</Badge>
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pending">Pending</SelectItem>
                            <SelectItem value="positive">Positive</SelectItem>
                            <SelectItem value="negative">Negative</SelectItem>
                            <SelectItem value="needs_revision">Needs Revision</SelectItem>
                            <SelectItem value="no_response">No Response</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600 font-mono">{new Date(sample.feedback_due_date).toLocaleDateString()}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleEditSample(sample)} data-testid={`edit-sample-${sample.id}`}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(sample.id)} className="text-destructive" data-testid={`delete-sample-${sample.id}`}>
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
    </div>
  );
};

export default SamplesList;
