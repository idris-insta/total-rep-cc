import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { 
  Plus, Search, Edit, Trash2, Eye, FileText, CreditCard, Receipt,
  TrendingUp, TrendingDown, AlertTriangle, RefreshCw, Download,
  Building, Calendar, CheckCircle, Clock, DollarSign, BarChart3,
  PieChart, ArrowUpRight, ArrowDownRight, Filter, Send, Printer,
  FileDown, FileMinus, Mail, MessageSquare
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import DocumentActions from '../components/DocumentActions';
import api from '../lib/api';
import { toast } from 'sonner';
import ItemSearchSelect from '../components/ItemSearchSelect';
import CustomerSearchSelect from '../components/CustomerSearchSelect';

// ==================== ACCOUNTS DASHBOARD ====================
const AccountsDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_receivables: 0, total_payables: 0, net_position: 0,
    overdue_invoices: 0, monthly_collections: 0, monthly_payments: 0, net_cashflow: 0
  });
  const [loading, setLoading] = useState(true);
  const [recentInvoices, setRecentInvoices] = useState([]);
  const [recentPayments, setRecentPayments] = useState([]);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [statsRes, invoicesRes, paymentsRes] = await Promise.all([
        api.get('/accounts/stats/overview'),
        api.get('/accounts/invoices?limit=5'),
        api.get('/accounts/payments?limit=5')
      ]);
      setStats(statsRes.data);
      setRecentInvoices(invoicesRes.data.slice(0, 5));
      setRecentPayments(paymentsRes.data.slice(0, 5));
    } catch (error) {
      console.error('Failed to load accounts stats', error);
    } finally {
      setLoading(false);
    }
  };

  const statusColors = {
    draft: 'bg-slate-100 text-slate-800',
    sent: 'bg-blue-100 text-blue-800',
    partial: 'bg-yellow-100 text-yellow-800',
    paid: 'bg-green-100 text-green-800',
    overdue: 'bg-red-100 text-red-800',
    cancelled: 'bg-slate-100 text-slate-500'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="accounts-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Accounts & Finance</h2>
          <p className="text-slate-600 mt-1 font-inter">AR/AP management, invoicing & GST compliance</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/accounts/invoices?type=Sales')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                <ArrowUpRight className="h-6 w-6 text-green-600" />
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-green-600 font-mono">₹{stats.total_receivables.toLocaleString('en-IN')}</div>
                <p className="text-sm text-slate-500">Receivables</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/accounts/invoices?type=Purchase')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-red-100 flex items-center justify-center">
                <ArrowDownRight className="h-6 w-6 text-red-600" />
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-red-600 font-mono">₹{stats.total_payables.toLocaleString('en-IN')}</div>
                <p className="text-sm text-slate-500">Payables</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/accounts/invoices?overdue=true')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-orange-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-orange-600">{stats.overdue_invoices}</div>
                <p className="text-sm text-slate-500">Overdue</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-blue-600" />
              </div>
              <div className="text-right">
                <div className={`text-2xl font-bold font-mono ${stats.net_position >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ₹{Math.abs(stats.net_position).toLocaleString('en-IN')}
                </div>
                <p className="text-sm text-slate-500">Net Position</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Cashflow */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">This Month Collections</p>
                <p className="text-2xl font-bold text-green-600 font-mono">₹{stats.monthly_collections.toLocaleString('en-IN')}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">This Month Payments</p>
                <p className="text-2xl font-bold text-red-600 font-mono">₹{stats.monthly_payments.toLocaleString('en-IN')}</p>
              </div>
              <TrendingDown className="h-8 w-8 text-red-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Net Cashflow</p>
                <p className={`text-2xl font-bold font-mono ${stats.net_cashflow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ₹{Math.abs(stats.net_cashflow).toLocaleString('en-IN')}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-manrope">Recent Invoices</CardTitle>
            <Button variant="outline" size="sm" onClick={() => navigate('/accounts/invoices')}>View All</Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentInvoices.length === 0 ? (
                <p className="text-center text-slate-500 py-4">No invoices yet</p>
              ) : (
                recentInvoices.map((inv) => (
                  <div key={inv.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50">
                    <div>
                      <p className="font-semibold text-slate-900 font-mono">{inv.invoice_number}</p>
                      <p className="text-sm text-slate-500">{inv.account_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono font-semibold text-slate-900">₹{(inv.grand_total || 0).toLocaleString('en-IN')}</p>
                      <Badge className={statusColors[inv.status]}>{inv.status}</Badge>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-manrope">Recent Payments</CardTitle>
            <Button variant="outline" size="sm" onClick={() => navigate('/accounts/payments')}>View All</Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentPayments.length === 0 ? (
                <p className="text-center text-slate-500 py-4">No payments yet</p>
              ) : (
                recentPayments.map((pmt) => (
                  <div key={pmt.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50">
                    <div>
                      <p className="font-semibold text-slate-900 font-mono">{pmt.payment_number}</p>
                      <p className="text-sm text-slate-500">{pmt.account_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono font-semibold text-slate-900">₹{(pmt.amount || 0).toLocaleString('en-IN')}</p>
                      <Badge className={pmt.payment_type === 'receipt' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                        {pmt.payment_type}
                      </Badge>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="font-manrope">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/accounts/invoices')}>
              <FileText className="h-6 w-6" />
              <span>Invoices</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/accounts/payments')}>
              <CreditCard className="h-6 w-6" />
              <span>Payments</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/accounts/aging')}>
              <Clock className="h-6 w-6" />
              <span>Aging Report</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/accounts/gst')}>
              <Receipt className="h-6 w-6" />
              <span>GST Reports</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/accounts/ledger')}>
              <BarChart3 className="h-6 w-6" />
              <span>Ledger</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== INVOICES LIST ====================
const InvoicesList = () => {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [creditNoteOpen, setCreditNoteOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('sales'); // 'sales' or 'purchase'
  const [filters, setFilters] = useState({ invoice_type: 'all', status: 'all', overdue: false });
  const [formData, setFormData] = useState({
    invoice_type: 'Sales', account_id: '', order_id: '',
    items: [{ item_id: '', description: '', hsn_code: '', quantity: '1', unit: 'Pcs', unit_price: '', discount_percent: '0', tax_percent: '18' }],
    invoice_date: new Date().toISOString().split('T')[0],
    due_date: '', payment_terms: '30 days', shipping_address: '', notes: '',
    billing_address: '', billing_city: '', billing_state: '', billing_pincode: '', gstin: ''
  });
  const [creditNoteData, setCreditNoteData] = useState({
    note_type: 'Credit', reference_invoice_id: '', account_id: '', reason: '',
    items: [{ description: '', quantity: '1', unit_price: '', tax_percent: '18' }],
    note_date: new Date().toISOString().split('T')[0], notes: ''
  });

  useEffect(() => { fetchData(); }, [filters, activeTab]);

  const fetchData = async () => {
    try {
      let url = '/accounts/invoices?';
      // Filter by active tab (Sales or Purchase)
      url += `invoice_type=${activeTab === 'sales' ? 'Sales' : 'Purchase'}&`;
      if (filters.status !== 'all') url += `status=${filters.status}&`;
      if (filters.overdue) url += 'overdue=true&';

      const [invoicesRes, accountsRes, itemsRes] = await Promise.all([
        api.get(url),
        api.get('/crm/accounts'),
        api.get('/inventory/items')
      ]);
      setInvoices(invoicesRes.data);
      setAccounts(accountsRes.data);
      setItems(itemsRes.data);
    } catch (error) {
      toast.error('Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        invoice_type: activeTab === 'sales' ? 'Sales' : 'Purchase',
        items: formData.items.filter(i => (i.description || i.item_id) && i.unit_price).map(i => ({
          item_id: i.item_id || '',
          description: i.description,
          hsn_code: i.hsn_code,
          quantity: parseFloat(i.quantity) || 1,
          unit: i.unit,
          unit_price: parseFloat(i.unit_price) || 0,
          discount_percent: parseFloat(i.discount_percent) || 0,
          tax_percent: parseFloat(i.tax_percent) || 18
        }))
      };
      await api.post('/accounts/invoices', payload);
      toast.success('Invoice created');
      setOpen(false);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create invoice');
    }
  };

  // Handle Credit/Debit Note submission
  const handleCreditNoteSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...creditNoteData,
        items: creditNoteData.items.filter(i => i.description && i.unit_price).map(i => ({
          description: i.description,
          quantity: parseFloat(i.quantity) || 1,
          unit_price: parseFloat(i.unit_price) || 0,
          tax_percent: parseFloat(i.tax_percent) || 18
        }))
      };
      await api.post('/accounts/credit-notes', payload);
      toast.success(`${creditNoteData.note_type} Note created`);
      setCreditNoteOpen(false);
      fetchData();
      resetCreditNoteForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create note');
    }
  };

  const handleStatusChange = async (invId, status) => {
    try {
      await api.put(`/accounts/invoices/${invId}/status?status=${status}`);
      toast.success(`Status updated to ${status}`);
      fetchData();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  // Auto-populate customer fields when customer is selected
  const handleCustomerSelect = (customerData) => {
    setFormData(prev => ({
      ...prev,
      account_id: customerData.account_id,
      billing_address: customerData.billing_address || '',
      billing_city: customerData.billing_city || '',
      billing_state: customerData.billing_state || '',
      billing_pincode: customerData.billing_pincode || '',
      shipping_address: customerData.shipping_address || '',
      gstin: customerData.gstin || '',
      payment_terms: customerData.payment_terms || prev.payment_terms
    }));
    toast.success('Customer details auto-populated');
  };

  // Auto-populate item fields when item is selected
  const handleItemSelect = (idx, itemData) => {
    const newItems = [...formData.items];
    newItems[idx] = {
      ...newItems[idx],
      item_id: itemData.item_id,
      description: itemData.item_name,
      hsn_code: itemData.hsn_code || '',
      unit: itemData.uom || 'Pcs',
      unit_price: itemData.unit_price || 0,
      tax_percent: itemData.tax_percent || 18
    };
    setFormData({ ...formData, items: newItems });
    toast.success(`Item "${itemData.item_name}" auto-populated`);
  };

  const resetForm = () => {
    setFormData({
      invoice_type: activeTab === 'sales' ? 'Sales' : 'Purchase', account_id: '', order_id: '',
      items: [{ item_id: '', description: '', hsn_code: '', quantity: '1', unit: 'Pcs', unit_price: '', discount_percent: '0', tax_percent: '18' }],
      invoice_date: new Date().toISOString().split('T')[0],
      due_date: '', payment_terms: '30 days', shipping_address: '', notes: '',
      billing_address: '', billing_city: '', billing_state: '', billing_pincode: '', gstin: ''
    });
  };

  const resetCreditNoteForm = () => {
    setCreditNoteData({
      note_type: 'Credit', reference_invoice_id: '', account_id: '', reason: '',
      items: [{ description: '', quantity: '1', unit_price: '', tax_percent: '18' }],
      note_date: new Date().toISOString().split('T')[0], notes: ''
    });
  };

  const addInvoiceItem = () => {
    setFormData({ ...formData, items: [...formData.items, { item_id: '', description: '', hsn_code: '', quantity: '1', unit: 'Pcs', unit_price: '', discount_percent: '0', tax_percent: '18' }] });
  };

  const removeInvoiceItem = (idx) => {
    if (formData.items.length > 1) {
      setFormData({ ...formData, items: formData.items.filter((_, i) => i !== idx) });
    }
  };

  const calculateTotals = () => {
    let subtotal = 0, totalDiscount = 0, totalTax = 0;
    formData.items.forEach(item => {
      const lineSubtotal = (parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0);
      const lineDiscount = lineSubtotal * ((parseFloat(item.discount_percent) || 0) / 100);
      const lineTaxable = lineSubtotal - lineDiscount;
      const lineTax = lineTaxable * ((parseFloat(item.tax_percent) || 0) / 100);
      subtotal += lineSubtotal;
      totalDiscount += lineDiscount;
      totalTax += lineTax;
    });
    return { subtotal, totalDiscount, taxable: subtotal - totalDiscount, totalTax, grandTotal: subtotal - totalDiscount + totalTax };
  };

  const totals = calculateTotals();

  const filteredInvoices = invoices.filter(inv =>
    inv.invoice_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    inv.account_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const statusColors = {
    draft: 'bg-slate-100 text-slate-800',
    sent: 'bg-blue-100 text-blue-800',
    partial: 'bg-yellow-100 text-yellow-800',
    paid: 'bg-green-100 text-green-800',
    overdue: 'bg-red-100 text-red-800',
    cancelled: 'bg-slate-100 text-slate-500'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="invoices-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Invoices</h2>
          <p className="text-slate-600 mt-1 font-inter">{invoices.length} {activeTab === 'sales' ? 'Sales' : 'Purchase'} invoices</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Credit/Debit Note Button */}
          <Dialog open={creditNoteOpen} onOpenChange={(val) => { setCreditNoteOpen(val); if (!val) resetCreditNoteForm(); }}>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2">
                <FileMinus className="h-4 w-4" />CN/DN
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle className="font-manrope">Create Credit/Debit Note</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreditNoteSubmit} className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Note Type *</Label>
                    <Select value={creditNoteData.note_type} onValueChange={(v) => setCreditNoteData({...creditNoteData, note_type: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Credit">Credit Note</SelectItem>
                        <SelectItem value="Debit">Debit Note</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Reference Invoice</Label>
                    <Select value={creditNoteData.reference_invoice_id} onValueChange={(v) => setCreditNoteData({...creditNoteData, reference_invoice_id: v})}>
                      <SelectTrigger><SelectValue placeholder="Select invoice" /></SelectTrigger>
                      <SelectContent>
                        {invoices.map(inv => (
                          <SelectItem key={inv.id} value={inv.id}>{inv.invoice_number} - ₹{inv.total_amount?.toLocaleString('en-IN')}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Date *</Label>
                    <Input type="date" value={creditNoteData.note_date} onChange={(e) => setCreditNoteData({...creditNoteData, note_date: e.target.value})} required />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Reason *</Label>
                  <Select value={creditNoteData.reason} onValueChange={(v) => setCreditNoteData({...creditNoteData, reason: v})}>
                    <SelectTrigger><SelectValue placeholder="Select reason" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Sales Return">Sales Return</SelectItem>
                      <SelectItem value="Rate Difference">Rate Difference</SelectItem>
                      <SelectItem value="Quality Issue">Quality Issue</SelectItem>
                      <SelectItem value="Shortage">Shortage</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Items</Label>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-3 py-2 text-left">Description</th>
                          <th className="px-3 py-2 text-left w-20">Qty</th>
                          <th className="px-3 py-2 text-left w-24">Amount</th>
                          <th className="px-3 py-2 text-left w-20">GST %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {creditNoteData.items.map((item, idx) => (
                          <tr key={idx} className="border-t">
                            <td className="px-3 py-2">
                              <Input value={item.description} onChange={(e) => {
                                const newItems = [...creditNoteData.items];
                                newItems[idx].description = e.target.value;
                                setCreditNoteData({...creditNoteData, items: newItems});
                              }} className="h-8" placeholder="Description" />
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" value={item.quantity} onChange={(e) => {
                                const newItems = [...creditNoteData.items];
                                newItems[idx].quantity = e.target.value;
                                setCreditNoteData({...creditNoteData, items: newItems});
                              }} className="h-8" />
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" value={item.unit_price} onChange={(e) => {
                                const newItems = [...creditNoteData.items];
                                newItems[idx].unit_price = e.target.value;
                                setCreditNoteData({...creditNoteData, items: newItems});
                              }} className="h-8" placeholder="₹" />
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" value={item.tax_percent} onChange={(e) => {
                                const newItems = [...creditNoteData.items];
                                newItems[idx].tax_percent = e.target.value;
                                setCreditNoteData({...creditNoteData, items: newItems});
                              }} className="h-8" />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <Button type="button" variant="outline" size="sm" onClick={() => setCreditNoteData({...creditNoteData, items: [...creditNoteData.items, { description: '', quantity: '1', unit_price: '', tax_percent: '18' }]})}>
                    <Plus className="h-4 w-4 mr-1" />Add Item
                  </Button>
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea value={creditNoteData.notes} onChange={(e) => setCreditNoteData({...creditNoteData, notes: e.target.value})} rows={2} />
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setCreditNoteOpen(false)}>Cancel</Button>
                  <Button type="submit" className="bg-accent hover:bg-accent/90">Create {creditNoteData.note_type} Note</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>

          {/* Create Invoice Button */}
          <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) resetForm(); }}>
            <DialogTrigger asChild>
              <Button className="bg-accent hover:bg-accent/90" data-testid="create-invoice-button">
                <Plus className="h-4 w-4 mr-2" />Create {activeTab === 'sales' ? 'Sales' : 'Purchase'} Invoice
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle className="font-manrope">Create {activeTab === 'sales' ? 'Sales' : 'Purchase'} Invoice</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-4 gap-4">
                  <div className="space-y-2 col-span-2">
                    <Label>{activeTab === 'sales' ? 'Customer' : 'Supplier'} *</Label>
                    <CustomerSearchSelect
                      value={formData.account_id}
                      onChange={(v) => setFormData({...formData, account_id: v})}
                      onCustomerSelect={handleCustomerSelect}
                      placeholder={`Search ${activeTab === 'sales' ? 'customer' : 'supplier'}...`}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Order Reference</Label>
                    <Input value={formData.order_id} onChange={(e) => setFormData({...formData, order_id: e.target.value})} placeholder="SO-001" />
                  </div>
                  <div className="space-y-2">
                    <Label>GSTIN</Label>
                    <Input value={formData.gstin} disabled className="bg-slate-50" />
                  </div>
                </div>

                <div className="grid grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <Label>Invoice Date *</Label>
                    <Input type="date" value={formData.invoice_date} onChange={(e) => setFormData({...formData, invoice_date: e.target.value})} required />
                  </div>
                  <div className="space-y-2">
                    <Label>Due Date *</Label>
                    <Input type="date" value={formData.due_date} onChange={(e) => setFormData({...formData, due_date: e.target.value})} required />
                  </div>
                  <div className="space-y-2">
                    <Label>Payment Terms</Label>
                    <Select value={formData.payment_terms} onValueChange={(v) => setFormData({...formData, payment_terms: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Immediate">Immediate</SelectItem>
                      <SelectItem value="7 days">7 Days</SelectItem>
                      <SelectItem value="15 days">15 Days</SelectItem>
                      <SelectItem value="30 days">30 Days</SelectItem>
                      <SelectItem value="45 days">45 Days</SelectItem>
                      <SelectItem value="60 days">60 Days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Line Items *</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addInvoiceItem}>
                    <Plus className="h-4 w-4 mr-1" />Add Item
                  </Button>
                </div>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Description</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-20">HSN</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-16">Qty</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-16">Unit</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-24">Rate</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-16">Disc%</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-16">Tax%</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-24">Amount</th>
                        <th className="px-3 py-2 w-10"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {formData.items.map((item, idx) => {
                        const lineAmount = ((parseFloat(item.quantity) || 0) * (parseFloat(item.unit_price) || 0)) * (1 - (parseFloat(item.discount_percent) || 0) / 100) * (1 + (parseFloat(item.tax_percent) || 0) / 100);
                        return (
                          <tr key={idx} className="border-t">
                            <td className="px-2 py-2">
                              <Input className="h-9" value={item.description} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].description = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} placeholder="Item description" />
                            </td>
                            <td className="px-2 py-2">
                              <Input className="h-9" value={item.hsn_code} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].hsn_code = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} placeholder="HSN" />
                            </td>
                            <td className="px-2 py-2">
                              <Input type="number" className="h-9" value={item.quantity} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].quantity = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} />
                            </td>
                            <td className="px-2 py-2">
                              <Select value={item.unit} onValueChange={(v) => {
                                const newItems = [...formData.items];
                                newItems[idx].unit = v;
                                setFormData({...formData, items: newItems});
                              }}>
                                <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="Pcs">Pcs</SelectItem>
                                  <SelectItem value="Rolls">Rolls</SelectItem>
                                  <SelectItem value="Box">Box</SelectItem>
                                  <SelectItem value="KG">KG</SelectItem>
                                  <SelectItem value="SQM">SQM</SelectItem>
                                </SelectContent>
                              </Select>
                            </td>
                            <td className="px-2 py-2">
                              <Input type="number" step="0.01" className="h-9" value={item.unit_price} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].unit_price = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} />
                            </td>
                            <td className="px-2 py-2">
                              <Input type="number" className="h-9" value={item.discount_percent} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].discount_percent = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} />
                            </td>
                            <td className="px-2 py-2">
                              <Select value={item.tax_percent} onValueChange={(v) => {
                                const newItems = [...formData.items];
                                newItems[idx].tax_percent = v;
                                setFormData({...formData, items: newItems});
                              }}>
                                <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="0">0%</SelectItem>
                                  <SelectItem value="5">5%</SelectItem>
                                  <SelectItem value="12">12%</SelectItem>
                                  <SelectItem value="18">18%</SelectItem>
                                  <SelectItem value="28">28%</SelectItem>
                                </SelectContent>
                              </Select>
                            </td>
                            <td className="px-2 py-2 text-right font-mono text-sm">₹{lineAmount.toFixed(2)}</td>
                            <td className="px-2 py-2">
                              {formData.items.length > 1 && (
                                <Button type="button" variant="ghost" size="sm" onClick={() => removeInvoiceItem(idx)} className="text-destructive">
                                  <Trash2 className="h-4 w-4" />
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

              {/* Totals Summary */}
              <div className="flex justify-end">
                <div className="w-72 space-y-2 text-sm">
                  <div className="flex justify-between"><span>Subtotal:</span><span className="font-mono">₹{totals.subtotal.toFixed(2)}</span></div>
                  <div className="flex justify-between text-slate-500"><span>Discount:</span><span className="font-mono">-₹{totals.totalDiscount.toFixed(2)}</span></div>
                  <div className="flex justify-between"><span>Taxable Amount:</span><span className="font-mono">₹{totals.taxable.toFixed(2)}</span></div>
                  <div className="flex justify-between text-slate-500"><span>GST:</span><span className="font-mono">₹{totals.totalTax.toFixed(2)}</span></div>
                  <div className="flex justify-between text-lg font-bold border-t pt-2"><span>Grand Total:</span><span className="font-mono">₹{totals.grandTotal.toFixed(2)}</span></div>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} placeholder="Payment instructions, terms, etc." />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Create Invoice</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
        </div>
      </div>

      {/* Sale/Purchase Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="sales" className="gap-2">
            <ArrowUpRight className="h-4 w-4" />Sales Invoices
          </TabsTrigger>
          <TabsTrigger value="purchase" className="gap-2">
            <ArrowDownRight className="h-4 w-4" />Purchase Invoices
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder="Search invoices..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" />
        </div>
        <Select value={filters.status} onValueChange={(v) => setFilters({...filters, status: v})}>
          <SelectTrigger className="w-[130px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="sent">Sent</SelectItem>
            <SelectItem value="partial">Partial</SelectItem>
            <SelectItem value="paid">Paid</SelectItem>
            <SelectItem value="overdue">Overdue</SelectItem>
          </SelectContent>
        </Select>
        <Button variant={filters.overdue ? "default" : "outline"} size="sm" onClick={() => setFilters({...filters, overdue: !filters.overdue})}>
          <AlertTriangle className="h-4 w-4 mr-2" />Overdue Only
        </Button>
      </div>

      {/* Invoices Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Invoice #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Customer/Supplier</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Due Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Balance</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredInvoices.length === 0 ? (
                  <tr><td colSpan="9" className="px-4 py-12 text-center text-slate-500">No invoices found</td></tr>
                ) : (
                  filteredInvoices.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-50 transition-colors" data-testid={`invoice-row-${inv.id}`}>
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{inv.invoice_number}</td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{inv.invoice_type}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900">{inv.account_name}</div>
                        <div className="text-sm text-slate-500 font-mono">{inv.account_gstin || '-'}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">{inv.invoice_date}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{inv.due_date}</td>
                      <td className="px-4 py-3 font-mono font-semibold text-slate-900">₹{(inv.grand_total || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 font-mono font-semibold text-orange-600">₹{(inv.balance_amount || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3">
                        <Select value={inv.status} onValueChange={(v) => handleStatusChange(inv.id, v)}>
                          <SelectTrigger className="w-[100px] h-8">
                            <Badge className={statusColors[inv.status]}>{inv.status}</Badge>
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="draft">Draft</SelectItem>
                            <SelectItem value="sent">Sent</SelectItem>
                            <SelectItem value="partial">Partial</SelectItem>
                            <SelectItem value="paid">Paid</SelectItem>
                            <SelectItem value="overdue">Overdue</SelectItem>
                            <SelectItem value="cancelled">Cancelled</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="px-4 py-3">
                        <DocumentActions
                          documentType="invoice"
                          documentId={inv.id}
                          documentNumber={inv.invoice_number}
                          recipient={{
                            name: inv.account_name,
                            email: inv.account_email,
                            phone: inv.account_phone
                          }}
                          compact={true}
                        />
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

// ==================== PAYMENTS LIST ====================
const PaymentsList = () => {
  const [payments, setPayments] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({ payment_type: 'all', status: 'all' });
  const [formData, setFormData] = useState({
    payment_type: 'receipt', account_id: '', amount: '',
    payment_date: new Date().toISOString().split('T')[0],
    payment_mode: 'bank_transfer', bank_name: '', cheque_no: '', cheque_date: '',
    transaction_ref: '', invoices: [], tds_amount: '0', tds_section: '', notes: ''
  });
  const [selectedInvoices, setSelectedInvoices] = useState([]);

  useEffect(() => { fetchData(); }, [filters]);

  const fetchData = async () => {
    try {
      let url = '/accounts/payments?';
      if (filters.payment_type !== 'all') url += `payment_type=${filters.payment_type}&`;
      if (filters.status !== 'all') url += `status=${filters.status}&`;

      const [paymentsRes, accountsRes, invoicesRes] = await Promise.all([
        api.get(url),
        api.get('/crm/accounts'),
        api.get('/accounts/invoices?status=partial&status=sent')
      ]);
      setPayments(paymentsRes.data);
      setAccounts(accountsRes.data);
      setInvoices(invoicesRes.data);
    } catch (error) {
      toast.error('Failed to load payments');
    } finally {
      setLoading(false);
    }
  };

  const handleAccountChange = async (accountId) => {
    setFormData({ ...formData, account_id: accountId });
    try {
      const res = await api.get(`/accounts/invoices?account_id=${accountId}`);
      const unpaid = res.data.filter(inv => inv.status !== 'paid' && inv.status !== 'cancelled');
      setSelectedInvoices(unpaid.map(inv => ({ ...inv, allocate: '' })));
    } catch (error) {
      console.error('Failed to load account invoices');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount) || 0,
        tds_amount: parseFloat(formData.tds_amount) || 0,
        invoices: selectedInvoices.filter(inv => inv.allocate > 0).map(inv => ({
          invoice_id: inv.id,
          amount: parseFloat(inv.allocate)
        }))
      };
      await api.post('/accounts/payments', payload);
      toast.success('Payment recorded');
      setOpen(false);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record payment');
    }
  };

  const resetForm = () => {
    setFormData({
      payment_type: 'receipt', account_id: '', amount: '',
      payment_date: new Date().toISOString().split('T')[0],
      payment_mode: 'bank_transfer', bank_name: '', cheque_no: '', cheque_date: '',
      transaction_ref: '', invoices: [], tds_amount: '0', tds_section: '', notes: ''
    });
    setSelectedInvoices([]);
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="payments-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Payments</h2>
          <p className="text-slate-600 mt-1 font-inter">{payments.length} transactions</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="record-payment-button">
              <Plus className="h-4 w-4 mr-2" />Record Payment
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-manrope">Record Payment</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Payment Type *</Label>
                  <Select value={formData.payment_type} onValueChange={(v) => setFormData({...formData, payment_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="receipt">Receipt (Money In)</SelectItem>
                      <SelectItem value="payment">Payment (Money Out)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 col-span-2">
                  <Label>Customer/Supplier *</Label>
                  <Select value={formData.account_id} onValueChange={handleAccountChange}>
                    <SelectTrigger><SelectValue placeholder="Select account" /></SelectTrigger>
                    <SelectContent>
                      {accounts.map(acc => (
                        <SelectItem key={acc.id} value={acc.id}>{acc.customer_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Amount *</Label>
                  <Input type="number" step="0.01" value={formData.amount} onChange={(e) => setFormData({...formData, amount: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label>Payment Date *</Label>
                  <Input type="date" value={formData.payment_date} onChange={(e) => setFormData({...formData, payment_date: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label>Payment Mode *</Label>
                  <Select value={formData.payment_mode} onValueChange={(v) => setFormData({...formData, payment_mode: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="cash">Cash</SelectItem>
                      <SelectItem value="cheque">Cheque</SelectItem>
                      <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                      <SelectItem value="upi">UPI</SelectItem>
                      <SelectItem value="card">Card</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {formData.payment_mode === 'cheque' && (
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Cheque No.</Label>
                    <Input value={formData.cheque_no} onChange={(e) => setFormData({...formData, cheque_no: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Cheque Date</Label>
                    <Input type="date" value={formData.cheque_date} onChange={(e) => setFormData({...formData, cheque_date: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Bank Name</Label>
                    <Input value={formData.bank_name} onChange={(e) => setFormData({...formData, bank_name: e.target.value})} />
                  </div>
                </div>
              )}

              {(formData.payment_mode === 'bank_transfer' || formData.payment_mode === 'upi') && (
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Transaction Reference</Label>
                    <Input value={formData.transaction_ref} onChange={(e) => setFormData({...formData, transaction_ref: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Bank Name</Label>
                    <Input value={formData.bank_name} onChange={(e) => setFormData({...formData, bank_name: e.target.value})} />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>TDS Amount</Label>
                  <Input type="number" step="0.01" value={formData.tds_amount} onChange={(e) => setFormData({...formData, tds_amount: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>TDS Section</Label>
                  <Select value={formData.tds_section} onValueChange={(v) => setFormData({...formData, tds_section: v})}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="194C">194C - Contractors</SelectItem>
                      <SelectItem value="194H">194H - Commission</SelectItem>
                      <SelectItem value="194I">194I - Rent</SelectItem>
                      <SelectItem value="194J">194J - Professional</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Invoice Allocation */}
              {selectedInvoices.length > 0 && (
                <div className="space-y-2">
                  <Label>Allocate to Invoices</Label>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-3 py-2 text-left">Invoice</th>
                          <th className="px-3 py-2 text-left">Date</th>
                          <th className="px-3 py-2 text-right">Total</th>
                          <th className="px-3 py-2 text-right">Balance</th>
                          <th className="px-3 py-2 text-right w-32">Allocate</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedInvoices.map((inv, idx) => (
                          <tr key={inv.id} className="border-t">
                            <td className="px-3 py-2 font-mono">{inv.invoice_number}</td>
                            <td className="px-3 py-2">{inv.invoice_date}</td>
                            <td className="px-3 py-2 text-right font-mono">₹{(inv.grand_total || 0).toLocaleString('en-IN')}</td>
                            <td className="px-3 py-2 text-right font-mono text-orange-600">₹{(inv.balance_amount || 0).toLocaleString('en-IN')}</td>
                            <td className="px-3 py-2">
                              <Input type="number" step="0.01" className="h-8 text-right" value={inv.allocate} onChange={(e) => {
                                const newInvoices = [...selectedInvoices];
                                newInvoices[idx].allocate = e.target.value;
                                setSelectedInvoices(newInvoices);
                              }} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Record Payment</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={filters.payment_type} onValueChange={(v) => setFilters({...filters, payment_type: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="receipt">Receipts</SelectItem>
            <SelectItem value="payment">Payments</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters.status} onValueChange={(v) => setFilters({...filters, status: v})}>
          <SelectTrigger className="w-[130px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="cleared">Cleared</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="bounced">Bounced</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Payments Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Payment #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Account</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Mode</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {payments.length === 0 ? (
                  <tr><td colSpan="7" className="px-4 py-12 text-center text-slate-500">No payments found</td></tr>
                ) : (
                  payments.map((pmt) => (
                    <tr key={pmt.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{pmt.payment_number}</td>
                      <td className="px-4 py-3">
                        <Badge className={pmt.payment_type === 'receipt' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {pmt.payment_type === 'receipt' ? 'Receipt' : 'Payment'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-900">{pmt.account_name}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{pmt.payment_date}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 capitalize">{pmt.payment_mode?.replace('_', ' ')}</td>
                      <td className="px-4 py-3 font-mono font-semibold text-slate-900">₹{(pmt.amount || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3">
                        <Badge className={pmt.status === 'cleared' ? 'bg-green-100 text-green-800' : pmt.status === 'bounced' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}>
                          {pmt.status}
                        </Badge>
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

// ==================== AGING REPORT ====================
const AgingReport = () => {
  const [agingData, setAgingData] = useState([]);
  const [reportType, setReportType] = useState('receivable');
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); }, [reportType]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/accounts/reports/aging?report_type=${reportType}`);
      setAgingData(res.data);
    } catch (error) {
      toast.error('Failed to load aging report');
    } finally {
      setLoading(false);
    }
  };

  const totals = agingData.reduce((acc, row) => ({
    current: acc.current + (row.current || 0),
    '1-30': acc['1-30'] + (row['1-30'] || 0),
    '31-60': acc['31-60'] + (row['31-60'] || 0),
    '61-90': acc['61-90'] + (row['61-90'] || 0),
    '90+': acc['90+'] + (row['90+'] || 0),
    total: acc.total + (row.total || 0)
  }), { current: 0, '1-30': 0, '31-60': 0, '61-90': 0, '90+': 0, total: 0 });

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="aging-report">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Aging Report</h2>
          <p className="text-slate-600 mt-1 font-inter">{reportType === 'receivable' ? 'Accounts Receivable' : 'Accounts Payable'} aging analysis</p>
        </div>
        <div className="flex gap-2">
          <Select value={reportType} onValueChange={setReportType}>
            <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="receivable">AR (Receivables)</SelectItem>
              <SelectItem value="payable">AP (Payables)</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm"><Download className="h-4 w-4 mr-2" />Export</Button>
        </div>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Account</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Current</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">1-30 Days</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">31-60 Days</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">61-90 Days</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">90+ Days</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {agingData.length === 0 ? (
                  <tr><td colSpan="7" className="px-4 py-12 text-center text-slate-500">No outstanding balances</td></tr>
                ) : (
                  agingData.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-semibold text-slate-900">{row.account_name}</td>
                      <td className="px-4 py-3 text-right font-mono text-slate-600">₹{(row.current || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono text-yellow-600">₹{(row['1-30'] || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono text-orange-600">₹{(row['31-60'] || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono text-red-600">₹{(row['61-90'] || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono text-red-800 font-semibold">₹{(row['90+'] || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono font-semibold text-slate-900">₹{(row.total || 0).toLocaleString('en-IN')}</td>
                    </tr>
                  ))
                )}
              </tbody>
              {agingData.length > 0 && (
                <tfoot className="bg-slate-100 font-semibold">
                  <tr>
                    <td className="px-4 py-3 text-slate-900">TOTAL</td>
                    <td className="px-4 py-3 text-right font-mono">₹{totals.current.toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-right font-mono text-yellow-600">₹{totals['1-30'].toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-right font-mono text-orange-600">₹{totals['31-60'].toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-right font-mono text-red-600">₹{totals['61-90'].toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-right font-mono text-red-800">₹{totals['90+'].toLocaleString('en-IN')}</td>
                    <td className="px-4 py-3 text-right font-mono text-slate-900">₹{totals.total.toLocaleString('en-IN')}</td>
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== GST REPORTS ====================
const GSTReports = () => {
  const [gstData, setGstData] = useState(null);
  const [month, setMonth] = useState(String(new Date().getMonth() + 1).padStart(2, '0'));
  const [year, setYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); }, [month, year]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/accounts/reports/gst-summary?month=${month}&year=${year}`);
      setGstData(res.data);
    } catch (error) {
      toast.error('Failed to load GST summary');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="gst-reports">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">GST Summary</h2>
          <p className="text-slate-600 mt-1 font-inter">Monthly GST computation for GSTR filing</p>
        </div>
        <div className="flex gap-2">
          <Select value={month} onValueChange={setMonth}>
            <SelectTrigger className="w-[120px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              {[...Array(12)].map((_, i) => (
                <SelectItem key={i} value={String(i + 1).padStart(2, '0')}>
                  {new Date(2000, i).toLocaleString('default', { month: 'long' })}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={String(year)} onValueChange={(v) => setYear(parseInt(v))}>
            <SelectTrigger className="w-[100px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              {[2024, 2025, 2026].map(y => (
                <SelectItem key={y} value={String(y)}>{y}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" size="sm"><Download className="h-4 w-4 mr-2" />Export</Button>
        </div>
      </div>

      {gstData && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Outward Supplies */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="bg-green-50">
              <CardTitle className="font-manrope text-green-800">Outward Supplies (Sales)</CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              <div className="flex justify-between"><span className="text-slate-600">Invoices:</span><span className="font-semibold">{gstData.outward_supplies.count}</span></div>
              <div className="flex justify-between"><span className="text-slate-600">Taxable Value:</span><span className="font-mono">₹{gstData.outward_supplies.taxable_value.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between"><span className="text-slate-600">CGST:</span><span className="font-mono">₹{gstData.outward_supplies.cgst.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between"><span className="text-slate-600">SGST:</span><span className="font-mono">₹{gstData.outward_supplies.sgst.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between"><span className="text-slate-600">IGST:</span><span className="font-mono">₹{gstData.outward_supplies.igst.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between border-t pt-2 font-semibold"><span>Total Tax:</span><span className="font-mono text-green-600">₹{gstData.outward_supplies.total_tax.toLocaleString('en-IN')}</span></div>
            </CardContent>
          </Card>

          {/* Inward Supplies */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="bg-red-50">
              <CardTitle className="font-manrope text-red-800">Inward Supplies (Purchases)</CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              <div className="flex justify-between"><span className="text-slate-600">Invoices:</span><span className="font-semibold">{gstData.inward_supplies.count}</span></div>
              <div className="flex justify-between"><span className="text-slate-600">Taxable Value:</span><span className="font-mono">₹{gstData.inward_supplies.taxable_value.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between"><span className="text-slate-600">CGST (ITC):</span><span className="font-mono">₹{gstData.inward_supplies.cgst.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between"><span className="text-slate-600">SGST (ITC):</span><span className="font-mono">₹{gstData.inward_supplies.sgst.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between"><span className="text-slate-600">IGST (ITC):</span><span className="font-mono">₹{gstData.inward_supplies.igst.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between border-t pt-2 font-semibold"><span>Total ITC:</span><span className="font-mono text-red-600">₹{gstData.inward_supplies.total_tax.toLocaleString('en-IN')}</span></div>
            </CardContent>
          </Card>

          {/* Net Liability */}
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="bg-blue-50">
              <CardTitle className="font-manrope text-blue-800">Net GST Liability</CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              <div className="flex justify-between"><span className="text-slate-600">CGST Payable:</span><span className={`font-mono ${gstData.net_liability.cgst >= 0 ? 'text-red-600' : 'text-green-600'}`}>₹{gstData.net_liability.cgst.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between"><span className="text-slate-600">SGST Payable:</span><span className={`font-mono ${gstData.net_liability.sgst >= 0 ? 'text-red-600' : 'text-green-600'}`}>₹{gstData.net_liability.sgst.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between"><span className="text-slate-600">IGST Payable:</span><span className={`font-mono ${gstData.net_liability.igst >= 0 ? 'text-red-600' : 'text-green-600'}`}>₹{gstData.net_liability.igst.toLocaleString('en-IN')}</span></div>
              <div className="flex justify-between border-t pt-2 font-semibold text-lg">
                <span>Total Payable:</span>
                <span className={`font-mono ${gstData.net_liability.total >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                  ₹{Math.abs(gstData.net_liability.total).toLocaleString('en-IN')}
                  {gstData.net_liability.total < 0 && ' (Refund)'}
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

// ==================== CUSTOMER LEDGER ====================
const CustomerLedger = () => {
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchAccounts(); }, []);

  const fetchAccounts = async () => {
    try {
      const res = await api.get('/crm/accounts');
      setAccounts(res.data);
    } catch (error) {
      toast.error('Failed to load accounts');
    } finally {
      setLoading(false);
    }
  };

  const fetchLedger = async (accountId) => {
    setSelectedAccount(accountId);
    setLoading(true);
    try {
      const [invoicesRes, paymentsRes] = await Promise.all([
        api.get(`/accounts/invoices?account_id=${accountId}`),
        api.get(`/accounts/payments?account_id=${accountId}`)
      ]);
      
      // Combine and sort transactions
      const allTxns = [
        ...invoicesRes.data.map(inv => ({
          date: inv.invoice_date,
          type: 'Invoice',
          reference: inv.invoice_number,
          debit: inv.invoice_type === 'Sales' ? inv.grand_total : 0,
          credit: inv.invoice_type === 'Purchase' ? inv.grand_total : 0,
          description: `${inv.invoice_type} Invoice`
        })),
        ...paymentsRes.data.map(pmt => ({
          date: pmt.payment_date,
          type: 'Payment',
          reference: pmt.payment_number,
          debit: pmt.payment_type === 'payment' ? pmt.amount : 0,
          credit: pmt.payment_type === 'receipt' ? pmt.amount : 0,
          description: `${pmt.payment_type === 'receipt' ? 'Receipt' : 'Payment'} - ${pmt.payment_mode}`
        }))
      ].sort((a, b) => new Date(a.date) - new Date(b.date));
      
      // Calculate running balance
      let balance = 0;
      const withBalance = allTxns.map(txn => {
        balance += txn.debit - txn.credit;
        return { ...txn, balance };
      });
      
      setTransactions(withBalance);
    } catch (error) {
      toast.error('Failed to load ledger');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="customer-ledger">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Customer/Supplier Ledger</h2>
          <p className="text-slate-600 mt-1 font-inter">Transaction history and balance</p>
        </div>
      </div>

      <div className="flex gap-4">
        <Select value={selectedAccount} onValueChange={fetchLedger}>
          <SelectTrigger className="w-[300px]"><SelectValue placeholder="Select account" /></SelectTrigger>
          <SelectContent>
            {accounts.map(acc => (
              <SelectItem key={acc.id} value={acc.id}>{acc.customer_name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        {selectedAccount && (
          <Button variant="outline" size="sm"><Download className="h-4 w-4 mr-2" />Export</Button>
        )}
      </div>

      {selectedAccount && (
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Reference</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Description</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Debit</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Credit</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Balance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transactions.length === 0 ? (
                    <tr><td colSpan="7" className="px-4 py-12 text-center text-slate-500">No transactions found</td></tr>
                  ) : (
                    transactions.map((txn, idx) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-4 py-3 text-sm text-slate-600">{txn.date}</td>
                        <td className="px-4 py-3"><Badge variant="outline">{txn.type}</Badge></td>
                        <td className="px-4 py-3 font-mono text-sm text-slate-900">{txn.reference}</td>
                        <td className="px-4 py-3 text-sm text-slate-600">{txn.description}</td>
                        <td className="px-4 py-3 text-right font-mono text-red-600">{txn.debit > 0 ? `₹${txn.debit.toLocaleString('en-IN')}` : '-'}</td>
                        <td className="px-4 py-3 text-right font-mono text-green-600">{txn.credit > 0 ? `₹${txn.credit.toLocaleString('en-IN')}` : '-'}</td>
                        <td className="px-4 py-3 text-right font-mono font-semibold">{txn.balance >= 0 ? `₹${txn.balance.toLocaleString('en-IN')} Dr` : `₹${Math.abs(txn.balance).toLocaleString('en-IN')} Cr`}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// ==================== MAIN ACCOUNTS COMPONENT ====================
const Accounts = () => {
  return (
    <Routes>
      <Route index element={<AccountsDashboard />} />
      <Route path="invoices" element={<InvoicesList />} />
      <Route path="payments" element={<PaymentsList />} />
      <Route path="aging" element={<AgingReport />} />
      <Route path="gst" element={<GSTReports />} />
      <Route path="ledger" element={<CustomerLedger />} />
    </Routes>
  );
};

export default Accounts;
