import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { Plus, Search, Edit, Trash2, Eye, FileText, Package as PackageIcon, Beaker, Users as UsersIcon, Building2, CheckCircle, Send, Calendar } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import api from '../lib/api';
import { toast } from 'sonner';

// Previous CRMOverview, LeadsList, AccountsList code remains...
// Adding Quotations and Samples components

const QuotationsList = () => {
  const [quotations, setQuotations] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [quoteItems, setQuoteItems] = useState([{ item_id: '', quantity: '', price: '' }]);
  const [formData, setFormData] = useState({
    account_id: '', transport: 'To Pay', credit_period: '30 days',
    validity_days: 15, supply_location: 'BWD', notes: ''
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [quotesRes, accountsRes, itemsRes] = await Promise.all([
        api.get('/crm/quotations'),
        api.get('/crm/accounts'),
        api.get('/inventory/items')
      ]);
      setQuotations(quotesRes.data);
      setAccounts(accountsRes.data);
      setItems(itemsRes.data.filter(i => i.category === 'FG'));
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/crm/quotations', { ...formData, items: quoteItems });
      toast.success('Quotation created');
      setOpen(false);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error('Failed to create quotation');
    }
  };

  const addItem = () => {
    setQuoteItems([...quoteItems, { item_id: '', quantity: '', price: '' }]);
  };

  const removeItem = (index) => {
    setQuoteItems(quoteItems.filter((_, i) => i !== index));
  };

  const updateItem = (index, field, value) => {
    const updated = [...quoteItems];
    updated[index][field] = value;
    setQuoteItems(updated);
  };

  const resetForm = () => {
    setFormData({ account_id: '', transport: 'To Pay', credit_period: '30 days', validity_days: 15, supply_location: 'BWD', notes: '' });
    setQuoteItems([{ item_id: '', quantity: '', price: '' }]);
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Quotations</h2>
          <p className="text-slate-600 mt-1 font-inter">{quotations.length} total quotations</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90 font-inter"><Plus className="h-4 w-4 mr-2" />Create Quotation</Button>
          </DialogTrigger>
          <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-manrope">Create Quotation</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2 col-span-2">
                  <Label className="font-inter">Customer Account *</Label>
                  <Select value={formData.account_id} onValueChange={(value) => setFormData({...formData, account_id: value})} required>
                    <SelectTrigger><SelectValue placeholder="Select account" /></SelectTrigger>
                    <SelectContent>
                      {accounts.map(acc => (
                        <SelectItem key={acc.id} value={acc.id}>{acc.customer_name} - {acc.gstin}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Validity (days) *</Label>
                  <Input type="number" value={formData.validity_days} onChange={(e) => setFormData({...formData, validity_days: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Transport *</Label>
                  <Select value={formData.transport} onValueChange={(value) => setFormData({...formData, transport: value})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="To Pay">To Pay</SelectItem>
                      <SelectItem value="Paid">Paid</SelectItem>
                      <SelectItem value="Extra">Extra</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Credit Period *</Label>
                  <Select value={formData.credit_period} onValueChange={(value) => setFormData({...formData, credit_period: value})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Cash">Cash</SelectItem>
                      <SelectItem value="15 days">15 Days</SelectItem>
                      <SelectItem value="30 days">30 Days</SelectItem>
                      <SelectItem value="45 days">45 Days</SelectItem>
                      <SelectItem value="60 days">60 Days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Supply Location *</Label>
                  <Select value={formData.supply_location} onValueChange={(value) => setFormData({...formData, supply_location: value})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BWD">BWD Warehouse</SelectItem>
                      <SelectItem value="SGM">SGM Factory</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="border border-slate-200 rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="font-inter text-base font-semibold">Quotation Items *</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addItem}><Plus className="h-4 w-4 mr-1" />Add Item</Button>
                </div>
                {quoteItems.map((item, index) => (
                  <div key={index} className="grid grid-cols-12 gap-2 items-end">
                    <div className="col-span-5 space-y-1">
                      <Label className="text-xs font-inter">Item</Label>
                      <Select value={item.item_id} onValueChange={(value) => updateItem(index, 'item_id', value)} required>
                        <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                        <SelectContent>
                          {items.map(i => (
                            <SelectItem key={i.id} value={i.id}>{i.item_code} - {i.item_name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="col-span-3 space-y-1">
                      <Label className="text-xs font-inter">Quantity</Label>
                      <Input type="number" value={item.quantity} onChange={(e) => updateItem(index, 'quantity', e.target.value)} required />
                    </div>
                    <div className="col-span-3 space-y-1">
                      <Label className="text-xs font-inter">Price (₹)</Label>
                      <Input type="number" step="0.01" value={item.price} onChange={(e) => updateItem(index, 'price', e.target.value)} required />
                    </div>
                    <div className="col-span-1">
                      {index > 0 && (
                        <Button type="button" variant="ghost" size="sm" onClick={() => removeItem(index)} className="text-destructive"><Trash2 className="h-4 w-4" /></Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              <div className="space-y-2">
                <Label className="font-inter">Notes / Terms</Label>
                <textarea className="w-full min-h-[80px] px-3 py-2 border border-slate-200 rounded-md font-inter" value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} placeholder="Payment terms, delivery conditions, etc." />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => { setOpen(false); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Create Quotation</Button>
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
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Quote #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Items</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Valid Until</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {quotations.length === 0 ? (
                  <tr><td colSpan="7" className="px-4 py-12 text-center text-slate-500 font-inter">
                    No quotations yet. Click "Create Quotation" to send a quote.
                  </td></tr>
                ) : (
                  quotations.map((quote) => {
                    const account = accounts.find(a => a.id === quote.account_id);
                    return (
                      <tr key={quote.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{quote.quote_number}</td>
                        <td className="px-4 py-3">
                          <div className="font-semibold text-slate-900 font-inter">{account?.customer_name || 'N/A'}</div>
                          <div className="text-sm text-slate-500 font-mono">{account?.gstin || ''}</div>
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-600 font-inter">{quote.items.length} items</td>
                        <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">₹{quote.total_amount.toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3"><Badge className={`font-inter ${
                          quote.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          quote.status === 'accepted' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>{quote.status}</Badge></td>
                        <td className="px-4 py-3 text-sm text-slate-500 font-mono">{new Date(quote.expiry_date).toLocaleDateString()}</td>
                        <td className="px-4 py-3 text-sm text-slate-500 font-mono">{new Date(quote.created_at).toLocaleDateString()}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const SamplesList = () => {
  const [samples, setSamples] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    account_id: '', quotation_id: '', product_specs: '',
    quantity: '', from_location: 'BWD', courier: '', feedback_date: ''
  });

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
      await api.post('/crm/samples', formData);
      toast.success('Sample record created');
      setOpen(false);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error('Failed to create sample');
    }
  };

  const resetForm = () => {
    setFormData({ account_id: '', quotation_id: '', product_specs: '', quantity: '', from_location: 'BWD', courier: '', feedback_date: '' });
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Sample Management</h2>
          <p className="text-slate-600 mt-1 font-inter">{samples.length} samples dispatched</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90 font-inter"><Plus className="h-4 w-4 mr-2" />Send Sample</Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle className="font-manrope">Send Sample</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2 col-span-2">
                  <Label className="font-inter">Customer Account *</Label>
                  <Select value={formData.account_id} onValueChange={(value) => setFormData({...formData, account_id: value})} required>
                    <SelectTrigger><SelectValue placeholder="Select account" /></SelectTrigger>
                    <SelectContent>
                      {accounts.map(acc => (
                        <SelectItem key={acc.id} value={acc.id}>{acc.customer_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 col-span-2">
                  <Label className="font-inter">Product Specifications *</Label>
                  <textarea className="w-full min-h-[80px] px-3 py-2 border border-slate-200 rounded-md font-inter" value={formData.product_specs} onChange={(e) => setFormData({...formData, product_specs: e.target.value})} placeholder="BOPP Tape 48mm x 100m, Brown, Acrylic adhesive" required />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Quantity *</Label>
                  <Input type="number" value={formData.quantity} onChange={(e) => setFormData({...formData, quantity: e.target.value})} placeholder="5" required />
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">From Location *</Label>
                  <Select value={formData.from_location} onValueChange={(value) => setFormData({...formData, from_location: value})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BWD">BWD Warehouse</SelectItem>
                      <SelectItem value="SGM">SGM Factory</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Courier *</Label>
                  <Select value={formData.courier} onValueChange={(value) => setFormData({...formData, courier: value})} required>
                    <SelectTrigger><SelectValue placeholder="Select courier" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Blue Dart">Blue Dart</SelectItem>
                      <SelectItem value="DTDC">DTDC</SelectItem>
                      <SelectItem value="Delhivery">Delhivery</SelectItem>
                      <SelectItem value="FedEx">FedEx</SelectItem>
                      <SelectItem value="DHL">DHL</SelectItem>
                      <SelectItem value="By Hand">By Hand</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="font-inter">Expected Feedback Date *</Label>
                  <Input type="date" value={formData.feedback_date} onChange={(e) => setFormData({...formData, feedback_date: e.target.value})} required />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button type="button" variant="outline" onClick={() => { setOpen(false); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Send Sample</Button>
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
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Sample #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Product Specs</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Qty</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Courier</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Feedback Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Feedback Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {samples.length === 0 ? (
                  <tr><td colSpan="7" className="px-4 py-12 text-center text-slate-500 font-inter">
                    No samples sent yet. Click "Send Sample" to dispatch samples.
                  </td></tr>
                ) : (
                  samples.map((sample) => {
                    const account = accounts.find(a => a.id === sample.account_id);
                    return (
                      <tr key={sample.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{sample.sample_number}</td>
                        <td className="px-4 py-3 text-sm font-inter text-slate-900">{account?.customer_name || 'N/A'}</td>
                        <td className="px-4 py-3 text-sm text-slate-600 font-inter">{sample.product_specs}</td>
                        <td className="px-4 py-3 font-mono text-sm text-slate-600">{sample.quantity}</td>
                        <td className="px-4 py-3"><Badge variant="outline" className="font-inter">{sample.courier}</Badge></td>
                        <td className="px-4 py-3"><Badge className={`font-inter ${
                          sample.feedback_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          sample.feedback_status === 'approved' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>{sample.feedback_status}</Badge></td>
                        <td className="px-4 py-3 text-sm text-slate-500 font-mono">{new Date(sample.feedback_date).toLocaleDateString()}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Export note: This file needs to be merged with existing CRM.js to include all components
// The complete CRM.js should have: CRMOverview, LeadsList, AccountsList, QuotationsList, SamplesList
// and Routes component that includes all of them