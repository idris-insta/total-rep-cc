import React, { useState, useEffect } from 'react';
import { 
  Plus, Search, Edit, Trash2, X, Settings
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
import ItemSearchSelect from '../../../components/ItemSearchSelect';
import CustomerSearchSelect from '../../../components/CustomerSearchSelect';
import DocumentActions from '../../../components/DocumentActions';

const QuotationsList = () => {
  const [quotations, setQuotations] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingQuotation, setEditingQuotation] = useState(null);

  const [statusFilter, setStatusFilter] = useState('all');
  const [formData, setFormData] = useState({
    account_id: '', contact_person: '', reference: '',
    valid_until: '', transport: '', delivery_terms: '', payment_terms: '',
    terms_conditions: '', notes: '', header_discount_percent: 0,
    billing_address: '', billing_city: '', billing_state: '', billing_pincode: '',
    shipping_address: '', shipping_city: '', shipping_state: '', shipping_pincode: '',
    gstin: '',
    items: [{ item_id: '', item_name: '', description: '', hsn_code: '', quantity: 1, unit: 'Pcs', unit_price: 0, discount_percent: 0, tax_percent: 18 }]
  });

  const { 
    formFields: registryFields, 
    loading: registryLoading, 
    sectionLabels 
  } = useFieldRegistry('crm', 'quotations');
  
  const headerFields = registryFields?.filter(f => f.section === 'header' || f.section === 'basic' || !f.section) || [];
  const useDynamicForm = headerFields.length > 0;

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [quotesRes, accountsRes] = await Promise.all([
        api.get('/crm/quotations'),
        api.get('/crm/accounts')
      ]);
      setQuotations(quotesRes.data);
      setAccounts(accountsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCustomerSelect = (customerData) => {
    setFormData(prev => ({
      ...prev,
      account_id: customerData.account_id,
      contact_person: customerData.contact_person || prev.contact_person,
      billing_address: customerData.billing_address || '',
      billing_city: customerData.billing_city || '',
      billing_state: customerData.billing_state || '',
      billing_pincode: customerData.billing_pincode || '',
      shipping_address: customerData.shipping_address || '',
      shipping_city: customerData.shipping_city || '',
      shipping_state: customerData.shipping_state || '',
      shipping_pincode: customerData.shipping_pincode || '',
      gstin: customerData.gstin || '',
      payment_terms: customerData.payment_terms || prev.payment_terms
    }));
    toast.success('Customer details auto-populated');
  };

  const handleItemSelect = (idx, itemData) => {
    const newItems = [...formData.items];
    newItems[idx] = {
      ...newItems[idx],
      item_id: itemData.item_id,
      item_name: itemData.item_name,
      hsn_code: itemData.hsn_code || '',
      unit: itemData.uom || 'Pcs',
      unit_price: itemData.unit_price || 0,
      tax_percent: itemData.tax_percent || 18
    };
    setFormData({ ...formData, items: newItems });
    toast.success(`Item "${itemData.item_name}" auto-populated`);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        header_discount_percent: parseFloat(formData.header_discount_percent) || 0,
        items: formData.items.map(item => ({
          ...item,
          quantity: parseFloat(item.quantity) || 0,
          unit_price: parseFloat(item.unit_price) || 0,
          discount_percent: parseFloat(item.discount_percent) || 0,
          tax_percent: parseFloat(item.tax_percent) || 18
        }))
      };
      
      if (editingQuotation) {
        await api.put(`/crm/quotations/${editingQuotation.id}`, payload);
        toast.success('Quotation updated successfully');
      } else {
        await api.post('/crm/quotations', payload);
        toast.success('Quotation created successfully');
      }
      setOpen(false);
      setEditingQuotation(null);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save quotation');
    }
  };

  const handleStatusChange = async (quoteId, newStatus) => {
    try {
      await api.put(`/crm/quotations/${quoteId}/status?status=${newStatus}`);
      toast.success('Status updated');
      fetchData();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const handleDelete = async (quoteId) => {
    if (!window.confirm('Are you sure you want to delete this quotation?')) return;
    try {
      await api.delete(`/crm/quotations/${quoteId}`);
      toast.success('Quotation deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete quotation');
    }
  };

  const resetForm = () => {
    setFormData({
      account_id: '', contact_person: '', reference: '',
      valid_until: '', transport: '', delivery_terms: '', payment_terms: '',
      terms_conditions: '', notes: '', header_discount_percent: 0,
      billing_address: '', billing_city: '', billing_state: '', billing_pincode: '',
      shipping_address: '', shipping_city: '', shipping_state: '', shipping_pincode: '',
      gstin: '',
      items: [{ item_id: '', item_name: '', description: '', hsn_code: '', quantity: 1, unit: 'Pcs', unit_price: 0, discount_percent: 0, tax_percent: 18 }]
    });
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { item_id: '', item_name: '', description: '', hsn_code: '', quantity: 1, unit: 'Pcs', unit_price: 0, discount_percent: 0, tax_percent: 18 }]
    });
  };

  const removeItem = (idx) => {
    if (formData.items.length > 1) {
      setFormData({
        ...formData,
        items: formData.items.filter((_, i) => i !== idx)
      });
    }
  };

  const handleEditQuotation = (quote) => {
    setEditingQuotation(quote);
    setFormData({
      account_id: quote.account_id || '',
      contact_person: quote.contact_person || '',
      reference: quote.reference || '',
      valid_until: quote.valid_until || '',
      transport: quote.transport || '',
      delivery_terms: quote.delivery_terms || '',
      payment_terms: quote.payment_terms || '',
      terms_conditions: quote.terms_conditions || '',
      notes: quote.notes || '',
      header_discount_percent: quote.header_discount_percent || 0,
      items: (quote.items && quote.items.length > 0) ? quote.items.map((it) => ({
        item_name: it.item_name || '',
        description: it.description || '',
        hsn_code: it.hsn_code || '',
        quantity: it.quantity || 1,
        unit: it.unit || 'Pcs',
        unit_price: it.unit_price || 0,
        discount_percent: it.discount_percent || 0,
        tax_percent: it.tax_percent || 18
      })) : [{ item_name: '', description: '', hsn_code: '', quantity: 1, unit: 'Pcs', unit_price: 0, discount_percent: 0, tax_percent: 18 }]
    });
    setOpen(true);
  };

  const calculateTotals = () => {
    let subtotal = 0;
    formData.items.forEach(item => {
      const lineSubtotal = (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0);
      subtotal += lineSubtotal;
    });
    const headerDiscount = subtotal * ((parseFloat(formData.header_discount_percent) || 0) / 100);
    const taxable = subtotal - headerDiscount;
    const tax = taxable * 0.18;
    return { subtotal, headerDiscount, taxable, tax, total: taxable + tax };
  };

  const totals = calculateTotals();

  const filteredQuotations = quotations.filter(quote => {
    const matchesSearch = quote.quote_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      quote.account_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || quote.status === statusFilter;
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
    <div className="space-y-6" data-testid="quotations-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Quotations</h2>
          <p className="text-slate-600 mt-1 font-inter">{quotations.length} total quotations</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) { setEditingQuotation(null); resetForm(); } }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90 font-inter" data-testid="add-quotation-button">
              <Plus className="h-4 w-4 mr-2" />New Quotation
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <div className="flex items-center justify-between">
                <DialogTitle className="font-manrope">Create Quotation</DialogTitle>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open('/field-registry?module=crm&entity=quotations', '_blank')}
                  className="text-slate-500 hover:text-accent"
                  title="Customize form fields"
                >
                  <Settings className="h-4 w-4 mr-1" />
                  Customize Fields
                </Button>
              </div>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label className="font-inter">Customer *</Label>
                  <CustomerSearchSelect
                    value={formData.account_id}
                    onChange={(v) => setFormData({...formData, account_id: v})}
                    onCustomerSelect={handleCustomerSelect}
                    placeholder="Search customer..."
                  />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Contact Person</Label>
                  <Input value={formData.contact_person} onChange={(e) => setFormData({...formData, contact_person: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Reference</Label>
                  <Input value={formData.reference} onChange={(e) => setFormData({...formData, reference: e.target.value})} placeholder="Enquiry ref, PO ref..." />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Valid Until *</Label>
                  <Input type="date" value={formData.valid_until} onChange={(e) => setFormData({...formData, valid_until: e.target.value})} required data-testid="quotation-valid-until" />
                </div>
              </div>
              
              {useDynamicForm && headerFields.length > 0 && (
                <DynamicFormFields
                  fields={headerFields}
                  formData={formData}
                  onChange={setFormData}
                  sectionLabels={sectionLabels}
                  groupBySection={false}
                  columns={4}
                />
              )}

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-slate-900">Line Items</h4>
                  <Button type="button" variant="outline" size="sm" onClick={addItem}>
                    <Plus className="h-4 w-4 mr-1" />Add Item
                  </Button>
                </div>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Item Name *</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">HSN</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-20">Qty *</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-20">Unit</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-28">Price *</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-20">Disc %</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-20">Tax %</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-28">Total</th>
                        <th className="px-3 py-2 w-10"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {formData.items.map((item, idx) => {
                        const lineTotal = (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0) * (1 - (parseFloat(item.discount_percent) || 0) / 100) * (1 + (parseFloat(item.tax_percent) || 0) / 100);
                        return (
                          <tr key={idx}>
                            <td className="px-3 py-2">
                              <ItemSearchSelect
                                value={item.item_id}
                                onChange={(v) => {
                                  const newItems = [...formData.items];
                                  newItems[idx].item_id = v;
                                  setFormData({...formData, items: newItems});
                                }}
                                onItemSelect={(itemData) => handleItemSelect(idx, itemData)}
                                placeholder="Search item..."
                                className="h-8"
                              />
                            </td>
                            <td className="px-3 py-2">
                              <Input value={item.hsn_code} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].hsn_code = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} className="h-8" />
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" value={item.quantity} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].quantity = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} required className="h-8" min="0" step="0.01" data-testid={`item-qty-${idx}`} />
                            </td>
                            <td className="px-3 py-2">
                              <Select value={item.unit} onValueChange={(value) => {
                                const newItems = [...formData.items];
                                newItems[idx].unit = value;
                                setFormData({...formData, items: newItems});
                              }}>
                                <SelectTrigger className="h-8"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="Pcs">Pcs</SelectItem>
                                  <SelectItem value="Box">Box</SelectItem>
                                  <SelectItem value="Rolls">Rolls</SelectItem>
                                  <SelectItem value="Kg">Kg</SelectItem>
                                  <SelectItem value="Mtr">Mtr</SelectItem>
                                </SelectContent>
                              </Select>
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" value={item.unit_price} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].unit_price = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} required className="h-8" min="0" step="0.01" data-testid={`item-price-${idx}`} />
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" value={item.discount_percent} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].discount_percent = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} className="h-8" min="0" max="100" />
                            </td>
                            <td className="px-3 py-2">
                              <Select value={item.tax_percent.toString()} onValueChange={(value) => {
                                const newItems = [...formData.items];
                                newItems[idx].tax_percent = parseFloat(value);
                                setFormData({...formData, items: newItems});
                              }}>
                                <SelectTrigger className="h-8"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="0">0%</SelectItem>
                                  <SelectItem value="5">5%</SelectItem>
                                  <SelectItem value="12">12%</SelectItem>
                                  <SelectItem value="18">18%</SelectItem>
                                  <SelectItem value="28">28%</SelectItem>
                                </SelectContent>
                              </Select>
                            </td>
                            <td className="px-3 py-2 font-mono text-sm font-semibold">₹{lineTotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</td>
                            <td className="px-3 py-2">
                              {formData.items.length > 1 && (
                                <Button type="button" variant="ghost" size="sm" onClick={() => removeItem(idx)}>
                                  <X className="h-4 w-4 text-red-500" />
                                </Button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="font-inter">Transport</Label>
                      <Select value={formData.transport} onValueChange={(value) => setFormData({...formData, transport: value})}>
                        <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Ex-Works">Ex-Works</SelectItem>
                          <SelectItem value="FOR Destination">FOR Destination</SelectItem>
                          <SelectItem value="CIF">CIF</SelectItem>
                          <SelectItem value="To Pay">To Pay</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Payment Terms</Label>
                      <Select value={formData.payment_terms} onValueChange={(value) => setFormData({...formData, payment_terms: value})}>
                        <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Advance">Advance</SelectItem>
                          <SelectItem value="30 days">30 Days</SelectItem>
                          <SelectItem value="45 days">45 Days</SelectItem>
                          <SelectItem value="60 days">60 Days</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="font-inter">Terms & Conditions</Label>
                    <Textarea value={formData.terms_conditions} onChange={(e) => setFormData({...formData, terms_conditions: e.target.value})} rows={3} />
                  </div>
                </div>
                <div className="bg-slate-50 p-4 rounded-lg space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Subtotal:</span>
                    <span className="font-mono font-semibold">₹{totals.subtotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-600">Discount:</span>
                      <Input type="number" value={formData.header_discount_percent} onChange={(e) => setFormData({...formData, header_discount_percent: e.target.value})} className="w-16 h-6 text-sm" min="0" max="100" />
                      <span className="text-slate-600">%</span>
                    </div>
                    <span className="font-mono">-₹{totals.headerDiscount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Taxable Amount:</span>
                    <span className="font-mono">₹{totals.taxable.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">GST:</span>
                    <span className="font-mono">₹{totals.tax.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t pt-3">
                    <span>Grand Total:</span>
                    <span className="font-mono text-green-600">₹{totals.total.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                  </div>
                </div>
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setOpen(false); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90" data-testid="quotation-submit-button">{editingQuotation ? 'Update Quotation' : 'Create Quotation'}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder="Search quotations..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" data-testid="quotation-search" />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="sent">Sent</SelectItem>
            <SelectItem value="accepted">Accepted</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Quote #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Valid Until</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredQuotations.length === 0 ? (
                  <tr><td colSpan="7" className="px-4 py-12 text-center text-slate-500 font-inter">
                    {searchTerm || statusFilter !== 'all' ? 'No quotations found' : 'No quotations yet. Click "New Quotation" to create one.'}
                  </td></tr>
                ) : (
                  filteredQuotations.map((quote) => (
                    <tr key={quote.id} className="hover:bg-slate-50 transition-colors" data-testid={`quotation-row-${quote.id}`}>
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-blue-600">{quote.quote_number}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900 font-inter">{quote.account_name}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600 font-mono">{new Date(quote.quote_date).toLocaleDateString()}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 font-mono">{new Date(quote.valid_until).toLocaleDateString()}</td>
                      <td className="px-4 py-3 font-mono font-semibold text-slate-900">₹{quote.grand_total?.toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3">
                        <Select value={quote.status} onValueChange={(val) => handleStatusChange(quote.id, val)}>
                          <SelectTrigger className="w-[120px] h-8">
                            <Badge className={`font-inter ${
                              quote.status === 'draft' ? 'bg-slate-100 text-slate-800' :
                              quote.status === 'sent' ? 'bg-blue-100 text-blue-800' :
                              quote.status === 'accepted' ? 'bg-green-100 text-green-800' :
                              quote.status === 'rejected' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>{quote.status}</Badge>
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="draft">Draft</SelectItem>
                            <SelectItem value="sent">Sent</SelectItem>
                            <SelectItem value="accepted">Accepted</SelectItem>
                            <SelectItem value="rejected">Rejected</SelectItem>
                            <SelectItem value="expired">Expired</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleEditQuotation(quote)} data-testid={`edit-quotation-${quote.id}`}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <DocumentActions
                            documentType="quotation"
                            documentId={quote.id}
                            documentNumber={quote.quote_number}
                            recipient={{
                              name: quote.contact_person || quote.account_name,
                              email: quote.contact_email,
                              phone: quote.contact_phone
                            }}
                            compact={true}
                          />
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(quote.id)} className="text-destructive" data-testid={`delete-quotation-${quote.id}`}>
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

export default QuotationsList;
