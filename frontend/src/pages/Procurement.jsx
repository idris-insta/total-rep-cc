import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { 
  Plus, Search, Edit, Trash2, Eye, ShoppingCart, Building, 
  FileText, Package, CheckCircle, Clock, AlertTriangle, RefreshCw,
  Download, Filter, Truck, BarChart3, TrendingUp, Send
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
import api from '../lib/api';
import { toast } from 'sonner';
import ItemSearchSelect from '../components/ItemSearchSelect';

// ==================== PROCUREMENT DASHBOARD ====================
const ProcurementDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_suppliers: 0, total_pos: 0, pending_pos: 0, 
    total_po_value: 0, pending_grns: 0, monthly_purchases: 0,
    monthly_po_count: 0, top_suppliers: []
  });
  const [loading, setLoading] = useState(true);
  const [recentPOs, setRecentPOs] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, posRes] = await Promise.all([
        api.get('/procurement/stats/overview'),
        api.get('/procurement/purchase-orders')
      ]);
      setStats(statsRes.data);
      setRecentPOs(posRes.data.slice(0, 5));
    } catch (error) {
      console.error('Failed to load procurement stats', error);
    } finally {
      setLoading(false);
    }
  };

  const statusColors = {
    draft: 'bg-slate-100 text-slate-800',
    sent: 'bg-blue-100 text-blue-800',
    partial: 'bg-yellow-100 text-yellow-800',
    received: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="procurement-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Procurement Dashboard</h2>
          <p className="text-slate-600 mt-1 font-inter">Supplier management & purchase orders</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/procurement/suppliers')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Building className="h-6 w-6 text-blue-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">{stats.total_suppliers}</div>
                <p className="text-sm text-slate-500">Suppliers</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/procurement/purchase-orders')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-purple-100 flex items-center justify-center">
                <FileText className="h-6 w-6 text-purple-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-purple-600">{stats.total_pos}</div>
                <p className="text-sm text-slate-500">Total POs</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/procurement/purchase-orders')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center">
                <Clock className="h-6 w-6 text-orange-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-orange-600">{stats.pending_pos}</div>
                <p className="text-sm text-slate-500">Pending POs</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/procurement/grn')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                <Package className="h-6 w-6 text-green-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-green-600">{stats.pending_grns}</div>
                <p className="text-sm text-slate-500">Pending GRN</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-emerald-100 flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-emerald-600" />
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-emerald-600 font-mono">₹{(stats.total_po_value || 0).toLocaleString('en-IN')}</div>
                <p className="text-sm text-slate-500">Total PO Value</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Stats & Top Suppliers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="font-manrope">This Month</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-slate-600">Purchase Orders</p>
                <p className="text-2xl font-bold text-blue-600">{stats.monthly_po_count}</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-slate-600">Purchase Value</p>
                <p className="text-2xl font-bold text-green-600 font-mono">₹{(stats.monthly_purchases || 0).toLocaleString('en-IN')}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="font-manrope">Top Suppliers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {(stats.top_suppliers || []).length === 0 ? (
                <p className="text-center text-slate-500 py-4">No supplier data yet</p>
              ) : (
                stats.top_suppliers.map((supplier, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 flex items-center justify-center bg-blue-100 text-blue-600 rounded-full text-sm font-semibold">{idx + 1}</span>
                      <span className="font-medium text-slate-900">{supplier.supplier_name}</span>
                    </div>
                    <span className="font-mono text-slate-600">₹{(supplier.total_value || 0).toLocaleString('en-IN')}</span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent POs */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="font-manrope">Recent Purchase Orders</CardTitle>
          <Button variant="outline" size="sm" onClick={() => navigate('/procurement/purchase-orders')}>
            View All
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {recentPOs.length === 0 ? (
              <p className="text-center text-slate-500 py-4">No purchase orders yet</p>
            ) : (
              recentPOs.map((po) => (
                <div key={po.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50">
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="font-semibold text-slate-900 font-mono">{po.po_number}</p>
                      <p className="text-sm text-slate-500">{po.supplier_name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="font-mono text-slate-900">₹{(po.grand_total || 0).toLocaleString('en-IN')}</span>
                    <Badge className={statusColors[po.status]}>{po.status}</Badge>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="font-manrope">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/procurement/suppliers')}>
              <Building className="h-6 w-6" />
              <span>Suppliers</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/procurement/purchase-orders')}>
              <FileText className="h-6 w-6" />
              <span>Purchase Orders</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/procurement/grn')}>
              <Package className="h-6 w-6" />
              <span>Goods Received</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/procurement/purchase-orders')}>
              <TrendingUp className="h-6 w-6" />
              <span>PO Reports</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== SUPPLIERS LIST ====================
const SuppliersList = () => {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({ supplier_type: 'all', state: 'all' });
  const [gstinValidation, setGstinValidation] = useState({ valid: null, message: '' });
  const [formData, setFormData] = useState({
    supplier_code: '', supplier_name: '', supplier_type: 'Raw Material',
    contact_person: '', email: '', phone: '', mobile: '',
    address: '', city: '', state: '', pincode: '', country: 'India',
    gstin: '', pan: '', payment_terms: '30 days', credit_limit: '',
    bank_name: '', bank_account: '', ifsc_code: '', notes: ''
  });

  useEffect(() => { fetchSuppliers(); }, [filters]);

  const fetchSuppliers = async () => {
    try {
      let url = '/procurement/suppliers?';
      if (filters.supplier_type !== 'all') url += `supplier_type=${filters.supplier_type}&`;
      if (filters.state !== 'all') url += `state=${filters.state}&`;
      const response = await api.get(url);
      setSuppliers(response.data);
    } catch (error) {
      toast.error('Failed to load suppliers');
    } finally {
      setLoading(false);
    }
  };

  // Pincode auto-fetch
  const handlePincodeChange = async (pincode) => {
    setFormData({...formData, pincode: pincode});
    if (pincode.length === 6 && /^\d{6}$/.test(pincode)) {
      try {
        const res = await api.get(`/procurement/geo/pincode/${pincode}`);
        if (res.data) {
          setFormData(prev => ({
            ...prev,
            pincode: pincode,
            city: res.data.city || prev.city,
            state: res.data.state || prev.state,
            country: res.data.country || 'India'
          }));
          toast.success('Address auto-filled from pincode');
        }
      } catch (error) {
        // Silently ignore - pincode not found
      }
    }
  };

  // GSTIN validation and auto-fill
  const handleGstinChange = async (gstin) => {
    const upperGstin = gstin.toUpperCase();
    setFormData({...formData, gstin: upperGstin});
    setGstinValidation({ valid: null, message: '' });
    
    if (upperGstin.length === 15) {
      try {
        const res = await api.get(`/procurement/gstin/validate/${upperGstin}`);
        if (res.data.valid) {
          setGstinValidation({ valid: true, message: `Valid - State: ${res.data.state}` });
          setFormData(prev => ({
            ...prev,
            gstin: upperGstin,
            state: res.data.state || prev.state,
            pan: res.data.pan || prev.pan
          }));
          toast.success(`GSTIN valid - State: ${res.data.state}`);
        }
      } catch (error) {
        setGstinValidation({ valid: false, message: error.response?.data?.detail || 'Invalid GSTIN' });
        toast.error(error.response?.data?.detail || 'Invalid GSTIN format');
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        credit_limit: formData.credit_limit ? parseFloat(formData.credit_limit) : 0
      };

      if (editingSupplier) {
        await api.put(`/procurement/suppliers/${editingSupplier.id}`, payload);
        toast.success('Supplier updated');
      } else {
        await api.post('/procurement/suppliers', payload);
        toast.success('Supplier created');
      }
      setOpen(false);
      setEditingSupplier(null);
      fetchSuppliers();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save supplier');
    }
  };

  const handleEdit = (supplier) => {
    setEditingSupplier(supplier);
    setFormData({
      supplier_code: supplier.supplier_code || '',
      supplier_name: supplier.supplier_name || '',
      supplier_type: supplier.supplier_type || 'Raw Material',
      contact_person: supplier.contact_person || '',
      email: supplier.email || '',
      phone: supplier.phone || '',
      mobile: supplier.mobile || '',
      address: supplier.address || '',
      city: supplier.city || '',
      state: supplier.state || '',
      pincode: supplier.pincode || '',
      country: supplier.country || 'India',
      gstin: supplier.gstin || '',
      pan: supplier.pan || '',
      payment_terms: supplier.payment_terms || '30 days',
      credit_limit: supplier.credit_limit?.toString() || '',
      bank_name: supplier.bank_name || '',
      bank_account: supplier.bank_account || '',
      ifsc_code: supplier.ifsc_code || '',
      notes: supplier.notes || ''
    });
    setOpen(true);
  };

  const handleDelete = async (supplierId) => {
    if (!window.confirm('Deactivate this supplier?')) return;
    try {
      await api.delete(`/procurement/suppliers/${supplierId}`);
      toast.success('Supplier deactivated');
      fetchSuppliers();
    } catch (error) {
      toast.error('Failed to deactivate supplier');
    }
  };

  const resetForm = () => {
    setFormData({
      supplier_code: '', supplier_name: '', supplier_type: 'Raw Material',
      contact_person: '', email: '', phone: '', mobile: '',
      address: '', city: '', state: '', pincode: '', country: 'India',
      gstin: '', pan: '', payment_terms: '30 days', credit_limit: '',
      bank_name: '', bank_account: '', ifsc_code: '', notes: ''
    });
    setGstinValidation({ valid: null, message: '' });
  };

  const filteredSuppliers = suppliers.filter(s =>
    s.supplier_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.supplier_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.gstin?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const typeColors = {
    'Raw Material': 'bg-blue-100 text-blue-800',
    'Packaging': 'bg-purple-100 text-purple-800',
    'Services': 'bg-green-100 text-green-800',
    'Import': 'bg-orange-100 text-orange-800',
    'Other': 'bg-slate-100 text-slate-800'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="suppliers-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Suppliers</h2>
          <p className="text-slate-600 mt-1 font-inter">{suppliers.length} suppliers</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) { setEditingSupplier(null); resetForm(); } }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="add-supplier-button">
              <Plus className="h-4 w-4 mr-2" />Add Supplier
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-manrope">{editingSupplier ? 'Edit' : 'Create'} Supplier</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Tabs defaultValue="basic" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="basic">Basic Info</TabsTrigger>
                  <TabsTrigger value="address">Address</TabsTrigger>
                  <TabsTrigger value="banking">Banking & Terms</TabsTrigger>
                </TabsList>

                <TabsContent value="basic" className="space-y-4 mt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Supplier Code</Label>
                      <Input value={formData.supplier_code} onChange={(e) => setFormData({...formData, supplier_code: e.target.value})} placeholder="Auto-generated" data-testid="supplier-code-input" />
                    </div>
                    <div className="space-y-2 col-span-2">
                      <Label>Supplier Name *</Label>
                      <Input value={formData.supplier_name} onChange={(e) => setFormData({...formData, supplier_name: e.target.value})} required data-testid="supplier-name-input" />
                    </div>
                    <div className="space-y-2">
                      <Label>Supplier Type</Label>
                      <Select value={formData.supplier_type} onValueChange={(v) => setFormData({...formData, supplier_type: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Raw Material">Raw Material</SelectItem>
                          <SelectItem value="Packaging">Packaging</SelectItem>
                          <SelectItem value="Services">Services</SelectItem>
                          <SelectItem value="Import">Import</SelectItem>
                          <SelectItem value="Other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Contact Person *</Label>
                      <Input value={formData.contact_person} onChange={(e) => setFormData({...formData, contact_person: e.target.value})} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Email *</Label>
                      <Input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone *</Label>
                      <Input value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Mobile</Label>
                      <Input value={formData.mobile} onChange={(e) => setFormData({...formData, mobile: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>GSTIN</Label>
                      <div className="relative">
                        <Input 
                          value={formData.gstin} 
                          onChange={(e) => handleGstinChange(e.target.value)} 
                          placeholder="27XXXXX0000X1ZX"
                          className={gstinValidation.valid === true ? 'border-green-500' : gstinValidation.valid === false ? 'border-red-500' : ''}
                        />
                        {gstinValidation.valid !== null && (
                          <span className={`text-xs mt-1 ${gstinValidation.valid ? 'text-green-600' : 'text-red-600'}`}>
                            {gstinValidation.message}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>PAN</Label>
                      <Input value={formData.pan} onChange={(e) => setFormData({...formData, pan: e.target.value.toUpperCase()})} placeholder="AAAAA0000A" />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="address" className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="col-span-2 space-y-2">
                      <Label>Address *</Label>
                      <Textarea value={formData.address} onChange={(e) => setFormData({...formData, address: e.target.value})} rows={2} required />
                    </div>
                    <div className="space-y-2">
                      <Label>City</Label>
                      <Input value={formData.city} onChange={(e) => setFormData({...formData, city: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>State</Label>
                      <Select value={formData.state} onValueChange={(v) => setFormData({...formData, state: v})}>
                        <SelectTrigger><SelectValue placeholder="Select state" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Maharashtra">Maharashtra</SelectItem>
                          <SelectItem value="Gujarat">Gujarat</SelectItem>
                          <SelectItem value="Delhi">Delhi</SelectItem>
                          <SelectItem value="Karnataka">Karnataka</SelectItem>
                          <SelectItem value="Tamil Nadu">Tamil Nadu</SelectItem>
                          <SelectItem value="Rajasthan">Rajasthan</SelectItem>
                          <SelectItem value="Uttar Pradesh">Uttar Pradesh</SelectItem>
                          <SelectItem value="West Bengal">West Bengal</SelectItem>
                          <SelectItem value="Other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Pincode</Label>
                      <Input 
                        value={formData.pincode} 
                        onChange={(e) => handlePincodeChange(e.target.value)}
                        placeholder="Enter 6-digit pincode"
                        maxLength={6}
                      />
                      <span className="text-xs text-slate-500">Auto-fills city & state</span>
                    </div>
                    <div className="space-y-2">
                      <Label>Country</Label>
                      <Input value={formData.country} onChange={(e) => setFormData({...formData, country: e.target.value})} />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="banking" className="space-y-4 mt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Payment Terms</Label>
                      <Select value={formData.payment_terms} onValueChange={(v) => setFormData({...formData, payment_terms: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Advance">Advance</SelectItem>
                          <SelectItem value="Cash">Cash</SelectItem>
                          <SelectItem value="7 days">7 Days</SelectItem>
                          <SelectItem value="15 days">15 Days</SelectItem>
                          <SelectItem value="30 days">30 Days</SelectItem>
                          <SelectItem value="45 days">45 Days</SelectItem>
                          <SelectItem value="60 days">60 Days</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Credit Limit (₹)</Label>
                      <Input type="number" value={formData.credit_limit} onChange={(e) => setFormData({...formData, credit_limit: e.target.value})} placeholder="100000" />
                    </div>
                    <div className="space-y-2">
                      <Label>Bank Name</Label>
                      <Input value={formData.bank_name} onChange={(e) => setFormData({...formData, bank_name: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>Bank Account No.</Label>
                      <Input value={formData.bank_account} onChange={(e) => setFormData({...formData, bank_account: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>IFSC Code</Label>
                      <Input value={formData.ifsc_code} onChange={(e) => setFormData({...formData, ifsc_code: e.target.value.toUpperCase()})} />
                    </div>
                    <div className="col-span-3 space-y-2">
                      <Label>Notes</Label>
                      <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setOpen(false); setEditingSupplier(null); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90" data-testid="supplier-submit-button">{editingSupplier ? 'Update' : 'Create'}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder="Search suppliers..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" data-testid="supplier-search" />
        </div>
        <Select value={filters.supplier_type} onValueChange={(v) => setFilters({...filters, supplier_type: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="Raw Material">Raw Material</SelectItem>
            <SelectItem value="Packaging">Packaging</SelectItem>
            <SelectItem value="Services">Services</SelectItem>
            <SelectItem value="Import">Import</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters.state} onValueChange={(v) => setFilters({...filters, state: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="State" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All States</SelectItem>
            <SelectItem value="Maharashtra">Maharashtra</SelectItem>
            <SelectItem value="Gujarat">Gujarat</SelectItem>
            <SelectItem value="Delhi">Delhi</SelectItem>
            <SelectItem value="Karnataka">Karnataka</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Suppliers Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Code</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Contact</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Location</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">GSTIN</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Terms</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredSuppliers.length === 0 ? (
                  <tr><td colSpan="8" className="px-4 py-12 text-center text-slate-500">No suppliers found</td></tr>
                ) : (
                  filteredSuppliers.map((supplier) => (
                    <tr key={supplier.id} className="hover:bg-slate-50 transition-colors" data-testid={`supplier-row-${supplier.id}`}>
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{supplier.supplier_code}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900">{supplier.supplier_name}</div>
                        <div className="text-sm text-slate-500">{supplier.contact_person}</div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={typeColors[supplier.supplier_type] || 'bg-slate-100 text-slate-800'}>{supplier.supplier_type}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-slate-900">{supplier.email}</div>
                        <div className="text-sm text-slate-500 font-mono">{supplier.phone}</div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">{supplier.city}, {supplier.state}</td>
                      <td className="px-4 py-3 text-sm font-mono text-slate-600">{supplier.gstin || '-'}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{supplier.payment_terms}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleEdit(supplier)} data-testid={`edit-supplier-${supplier.id}`}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(supplier.id)} className="text-destructive">
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

// ==================== PURCHASE ORDERS ====================
const PurchaseOrdersList = () => {
  const navigate = useNavigate();
  const [pos, setPOs] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editingPO, setEditingPO] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({ status: 'all', supplier_id: 'all' });
  const [tdsInfo, setTdsInfo] = useState(null);  // TDS/TCS compliance info
  const [formData, setFormData] = useState({
    supplier_id: '', po_type: 'Standard', warehouse_id: '',
    items: [{ item_id: '', quantity: '', unit_price: '', tax_percent: '18', discount_percent: '0' }],
    payment_terms: '', delivery_terms: '', shipping_address: '', expected_date: '', notes: '',
    apply_tds: false, tds_rate: 0, tds_amount: 0
  });

  useEffect(() => { fetchData(); }, [filters]);

  const fetchData = async () => {
    try {
      let url = '/procurement/purchase-orders?';
      if (filters.status !== 'all') url += `status=${filters.status}&`;
      if (filters.supplier_id !== 'all') url += `supplier_id=${filters.supplier_id}&`;
      
      const [posRes, suppliersRes, warehousesRes, itemsRes] = await Promise.all([
        api.get(url),
        api.get('/procurement/suppliers'),
        api.get('/inventory/warehouses'),
        api.get('/inventory/items')
      ]);
      setPOs(posRes.data);
      setSuppliers(suppliersRes.data);
      setWarehouses(warehousesRes.data);
      setItems(itemsRes.data);
    } catch (error) {
      toast.error('Failed to load purchase orders');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        items: formData.items.filter(i => i.item_id && i.quantity && i.unit_price).map(i => ({
          item_id: i.item_id,
          quantity: parseFloat(i.quantity),
          unit_price: parseFloat(i.unit_price),
          tax_percent: parseFloat(i.tax_percent) || 18,
          discount_percent: parseFloat(i.discount_percent) || 0
        }))
      };
      
      if (editingPO) {
        await api.put(`/procurement/purchase-orders/${editingPO.id}`, payload);
        toast.success('Purchase order updated');
      } else {
        await api.post('/procurement/purchase-orders', payload);
        toast.success('Purchase order created');
      }
      setOpen(false);
      setEditingPO(null);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save PO');
    }
  };

  const handleEditPO = (po) => {
    if (po.status !== 'draft' && po.status !== 'sent') {
      toast.error('Can only edit POs in draft or sent status');
      return;
    }
    setEditingPO(po);
    setFormData({
      supplier_id: po.supplier_id || '',
      po_type: po.po_type || 'Standard',
      warehouse_id: po.warehouse_id || '',
      items: po.items?.length > 0 ? po.items.map(i => ({
        item_id: i.item_id || '',
        quantity: i.quantity?.toString() || '',
        unit_price: i.unit_price?.toString() || '',
        tax_percent: i.tax_percent?.toString() || '18',
        discount_percent: i.discount_percent?.toString() || '0'
      })) : [{ item_id: '', quantity: '', unit_price: '', tax_percent: '18', discount_percent: '0' }],
      payment_terms: po.payment_terms || '',
      delivery_terms: po.delivery_terms || '',
      shipping_address: po.shipping_address || '',
      expected_date: po.expected_date || '',
      notes: po.notes || ''
    });
    setOpen(true);
  };

  const handleStatusChange = async (poId, status) => {
    try {
      await api.put(`/procurement/purchase-orders/${poId}/status?status=${status}`);
      toast.success(`Status updated to ${status}`);
      fetchData();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const resetForm = () => {
    setFormData({
      supplier_id: '', po_type: 'Standard', warehouse_id: '',
      items: [{ item_id: '', quantity: '', unit_price: '', tax_percent: '18', discount_percent: '0' }],
      payment_terms: '', delivery_terms: '', shipping_address: '', expected_date: '', notes: '',
      apply_tds: false, tds_rate: 0, tds_amount: 0
    });
    setEditingPO(null);
    setTdsInfo(null);
  };

  const addPOItem = () => {
    setFormData({ ...formData, items: [...formData.items, { item_id: '', item_name: '', hsn_code: '', quantity: '', unit_price: '', tax_percent: '18', discount_percent: '0', uom: 'Pcs' }] });
  };

  const removePOItem = (idx) => {
    if (formData.items.length > 1) {
      setFormData({ ...formData, items: formData.items.filter((_, i) => i !== idx) });
    }
  };

  // Auto-populate item fields when item is selected
  const handlePOItemSelect = (idx, itemData) => {
    const newItems = [...formData.items];
    newItems[idx] = {
      ...newItems[idx],
      item_id: itemData.item_id,
      item_name: itemData.item_name,
      hsn_code: itemData.hsn_code || '',
      uom: itemData.uom || 'Pcs',
      unit_price: itemData.standard_cost || itemData.unit_price || '',
      tax_percent: '18'
    };
    setFormData({ ...formData, items: newItems });
    toast.success(`Item "${itemData.item_name}" auto-populated`);
  };

  // Fetch TDS/TCS info when supplier is selected
  const handleSupplierSelect = async (supplierId) => {
    setFormData({ ...formData, supplier_id: supplierId, apply_tds: false, tds_rate: 0, tds_amount: 0 });
    setTdsInfo(null);
    
    if (supplierId) {
      try {
        const res = await api.get(`/procurement/suppliers/${supplierId}/tds-info`);
        setTdsInfo(res.data);
        if (res.data.threshold_exceeded) {
          toast.warning(`⚠️ TDS applicable - Purchases exceed ₹50 Lakh threshold`, { duration: 5000 });
        }
      } catch (error) {
        // Silently ignore - TDS info not critical
      }
    }
  };

  const filteredPOs = pos.filter(po =>
    po.po_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    po.supplier_name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const statusColors = {
    draft: 'bg-slate-100 text-slate-800',
    sent: 'bg-blue-100 text-blue-800',
    partial: 'bg-yellow-100 text-yellow-800',
    received: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="purchase-orders-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Purchase Orders</h2>
          <p className="text-slate-600 mt-1 font-inter">{pos.length} orders</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="create-po-button">
              <Plus className="h-4 w-4 mr-2" />Create PO
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-manrope">{editingPO ? `Edit Purchase Order - ${editingPO.po_number}` : 'Create Purchase Order'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* TDS/TCS Warning Banner */}
              {tdsInfo && tdsInfo.threshold_exceeded && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5" />
                    <div className="flex-1">
                      <h4 className="font-semibold text-amber-800">TDS/TCS Applicable (Section 194Q)</h4>
                      <p className="text-sm text-amber-700 mt-1">
                        Cumulative purchases from this supplier: <span className="font-bold">₹{tdsInfo.cumulative_purchase_value?.toLocaleString('en-IN')}</span> (exceeds ₹50 Lakh threshold)
                      </p>
                      <div className="mt-3 flex items-center gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input 
                            type="checkbox" 
                            checked={formData.apply_tds} 
                            onChange={(e) => setFormData({...formData, apply_tds: e.target.checked, tds_rate: e.target.checked ? tdsInfo.tds_rate : 0})}
                            className="rounded border-amber-300"
                          />
                          <span className="text-sm font-medium text-amber-800">Apply TDS Deduction</span>
                        </label>
                        {formData.apply_tds && (
                          <span className="text-sm text-amber-700">
                            @ <span className="font-bold">{tdsInfo.tds_rate}%</span> {tdsInfo.pan ? '(with PAN)' : '(without PAN - higher rate)'}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-4 gap-4">
                <div className="space-y-2 col-span-2">
                  <Label>Supplier *</Label>
                  <Select value={formData.supplier_id} onValueChange={handleSupplierSelect}>
                    <SelectTrigger><SelectValue placeholder="Select supplier" /></SelectTrigger>
                    <SelectContent>
                      {suppliers.map(s => (
                        <SelectItem key={s.id} value={s.id}>{s.supplier_code} - {s.supplier_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>PO Type</Label>
                  <Select value={formData.po_type} onValueChange={(v) => setFormData({...formData, po_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Standard">Standard</SelectItem>
                      <SelectItem value="Blanket">Blanket</SelectItem>
                      <SelectItem value="Import">Import</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Warehouse *</Label>
                  <Select value={formData.warehouse_id} onValueChange={(v) => setFormData({...formData, warehouse_id: v})}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      {warehouses.map(w => (
                        <SelectItem key={w.id} value={w.id}>{w.warehouse_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Line Items *</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addPOItem}>
                    <Plus className="h-4 w-4 mr-1" />Add Item
                  </Button>
                </div>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Item</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-20">Qty</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-24">Rate (₹)</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-20">Tax %</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-20">Disc %</th>
                        <th className="px-3 py-2 w-10"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {formData.items.map((item, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-2 py-2">
                            <ItemSearchSelect
                              value={item.item_id}
                              onChange={(v) => {
                                const newItems = [...formData.items];
                                newItems[idx].item_id = v;
                                setFormData({...formData, items: newItems});
                              }}
                              onItemSelect={(itemData) => handlePOItemSelect(idx, itemData)}
                              placeholder="Search item..."
                              className="h-9"
                            />
                          </td>
                          <td className="px-2 py-2">
                            <Input type="number" className="h-9" value={item.quantity} onChange={(e) => {
                              const newItems = [...formData.items];
                              newItems[idx].quantity = e.target.value;
                              setFormData({...formData, items: newItems});
                            }} />
                          </td>
                          <td className="px-2 py-2">
                            <Input type="number" step="0.01" className="h-9" value={item.unit_price} onChange={(e) => {
                              const newItems = [...formData.items];
                              newItems[idx].unit_price = e.target.value;
                              setFormData({...formData, items: newItems});
                            }} />
                          </td>
                          <td className="px-2 py-2">
                            <Input type="number" className="h-9" value={item.tax_percent} onChange={(e) => {
                              const newItems = [...formData.items];
                              newItems[idx].tax_percent = e.target.value;
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
                            {formData.items.length > 1 && (
                              <Button type="button" variant="ghost" size="sm" onClick={() => removePOItem(idx)} className="text-destructive">
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Payment Terms</Label>
                  <Select value={formData.payment_terms} onValueChange={(v) => setFormData({...formData, payment_terms: v})}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Advance">Advance</SelectItem>
                      <SelectItem value="Cash">Cash</SelectItem>
                      <SelectItem value="30 days">30 Days</SelectItem>
                      <SelectItem value="45 days">45 Days</SelectItem>
                      <SelectItem value="60 days">60 Days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Delivery Terms</Label>
                  <Select value={formData.delivery_terms} onValueChange={(v) => setFormData({...formData, delivery_terms: v})}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Ex-Works">Ex-Works</SelectItem>
                      <SelectItem value="FOR">FOR</SelectItem>
                      <SelectItem value="CIF">CIF</SelectItem>
                      <SelectItem value="FOB">FOB</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Expected Date</Label>
                  <Input type="date" value={formData.expected_date} onChange={(e) => setFormData({...formData, expected_date: e.target.value})} />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Shipping Address</Label>
                <Textarea value={formData.shipping_address} onChange={(e) => setFormData({...formData, shipping_address: e.target.value})} rows={2} />
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">{editingPO ? 'Update PO' : 'Create PO'}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder="Search POs..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" />
        </div>
        <Select value={filters.status} onValueChange={(v) => setFilters({...filters, status: v})}>
          <SelectTrigger className="w-[140px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="sent">Sent</SelectItem>
            <SelectItem value="partial">Partial</SelectItem>
            <SelectItem value="received">Received</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters.supplier_id} onValueChange={(v) => setFilters({...filters, supplier_id: v})}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="Supplier" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Suppliers</SelectItem>
            {suppliers.map(s => (
              <SelectItem key={s.id} value={s.id}>{s.supplier_name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* POs Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">PO Number</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Supplier</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Warehouse</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Items</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Total</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredPOs.length === 0 ? (
                  <tr><td colSpan="8" className="px-4 py-12 text-center text-slate-500">No purchase orders found</td></tr>
                ) : (
                  filteredPOs.map((po) => (
                    <tr key={po.id} className="hover:bg-slate-50 transition-colors" data-testid={`po-row-${po.id}`}>
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{po.po_number}</td>
                      <td className="px-4 py-3 text-sm text-slate-900">{po.supplier_name}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{po.warehouse_name}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{po.items?.length || 0} items</td>
                      <td className="px-4 py-3 font-mono font-semibold text-slate-900">₹{(po.grand_total || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3">
                        <Select value={po.status} onValueChange={(v) => handleStatusChange(po.id, v)}>
                          <SelectTrigger className="w-[110px] h-8">
                            <Badge className={statusColors[po.status]}>{po.status}</Badge>
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="draft">Draft</SelectItem>
                            <SelectItem value="sent">Sent</SelectItem>
                            <SelectItem value="partial">Partial</SelectItem>
                            <SelectItem value="received">Received</SelectItem>
                            <SelectItem value="cancelled">Cancelled</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">
                        {po.created_at ? new Date(po.created_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          {(po.status === 'draft' || po.status === 'sent') && (
                            <Button variant="ghost" size="sm" onClick={() => handleEditPO(po)} data-testid={`edit-po-${po.id}`}>
                              <Edit className="h-4 w-4" />
                            </Button>
                          )}
                          {po.status === 'draft' && (
                            <Button variant="outline" size="sm" onClick={() => handleStatusChange(po.id, 'sent')}>
                              <Send className="h-4 w-4 mr-1" />Send
                            </Button>
                          )}
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

// ==================== GRN LIST ====================
const GRNList = () => {
  const [grns, setGRNs] = useState([]);
  const [pos, setPOs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [selectedPO, setSelectedPO] = useState(null);
  const [filters, setFilters] = useState({ status: 'all' });
  const [formData, setFormData] = useState({
    po_id: '', items: [], invoice_no: '', invoice_date: '', invoice_amount: '',
    lr_no: '', vehicle_no: '', notes: ''
  });

  useEffect(() => { fetchData(); }, [filters]);

  const fetchData = async () => {
    try {
      let url = '/procurement/grn?';
      if (filters.status !== 'all') url += `status=${filters.status}&`;
      
      const [grnRes, posRes] = await Promise.all([
        api.get(url),
        api.get('/procurement/purchase-orders?status=sent')
      ]);
      setGRNs(grnRes.data);
      setPOs(posRes.data);
    } catch (error) {
      toast.error('Failed to load GRNs');
    } finally {
      setLoading(false);
    }
  };

  const handlePOSelect = async (poId) => {
    try {
      const res = await api.get(`/procurement/purchase-orders/${poId}`);
      setSelectedPO(res.data);
      setFormData({
        ...formData,
        po_id: poId,
        items: res.data.items.map((item, idx) => ({
          po_item_index: idx,
          item_id: item.item_id,
          item_name: item.item_name,
          ordered_qty: item.quantity,
          received_qty: item.received_qty || 0,
          pending_qty: (item.quantity || 0) - (item.received_qty || 0),
          receive_qty: '',
          accepted_qty: '',
          rejected_qty: '0',
          rejection_reason: '',
          batch_no: '',
          unit_price: item.unit_price
        }))
      });
    } catch (error) {
      toast.error('Failed to load PO details');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        po_id: formData.po_id,
        items: formData.items.filter(i => i.receive_qty > 0).map(i => ({
          po_item_index: i.po_item_index,
          item_id: i.item_id,
          received_qty: parseFloat(i.receive_qty) || 0,
          accepted_qty: parseFloat(i.accepted_qty) || parseFloat(i.receive_qty) || 0,
          rejected_qty: parseFloat(i.rejected_qty) || 0,
          rejection_reason: i.rejection_reason,
          batch_no: i.batch_no,
          unit_price: i.unit_price
        })),
        invoice_no: formData.invoice_no,
        invoice_date: formData.invoice_date,
        invoice_amount: formData.invoice_amount ? parseFloat(formData.invoice_amount) : null,
        lr_no: formData.lr_no,
        vehicle_no: formData.vehicle_no,
        notes: formData.notes
      };
      await api.post('/procurement/grn', payload);
      toast.success('GRN created successfully');
      setOpen(false);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create GRN');
    }
  };

  const handleApprove = async (grnId) => {
    if (!window.confirm('Approve this GRN? Stock will be added to inventory.')) return;
    try {
      await api.put(`/procurement/grn/${grnId}/approve`);
      toast.success('GRN approved and stock updated');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve GRN');
    }
  };

  const resetForm = () => {
    setFormData({
      po_id: '', items: [], invoice_no: '', invoice_date: '', invoice_amount: '',
      lr_no: '', vehicle_no: '', notes: ''
    });
    setSelectedPO(null);
  };

  const statusColors = {
    pending_qc: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    partial: 'bg-orange-100 text-orange-800'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="grn-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Goods Received Notes</h2>
          <p className="text-slate-600 mt-1 font-inter">{grns.length} GRNs</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="create-grn-button">
              <Plus className="h-4 w-4 mr-2" />Create GRN
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-manrope">Create Goods Received Note</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Purchase Order *</Label>
                  <Select value={formData.po_id} onValueChange={handlePOSelect}>
                    <SelectTrigger><SelectValue placeholder="Select PO" /></SelectTrigger>
                    <SelectContent>
                      {pos.map(po => (
                        <SelectItem key={po.id} value={po.id}>{po.po_number} - {po.supplier_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Invoice No.</Label>
                  <Input value={formData.invoice_no} onChange={(e) => setFormData({...formData, invoice_no: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Invoice Date</Label>
                  <Input type="date" value={formData.invoice_date} onChange={(e) => setFormData({...formData, invoice_date: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Invoice Amount (₹)</Label>
                  <Input type="number" value={formData.invoice_amount} onChange={(e) => setFormData({...formData, invoice_amount: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>LR No.</Label>
                  <Input value={formData.lr_no} onChange={(e) => setFormData({...formData, lr_no: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Vehicle No.</Label>
                  <Input value={formData.vehicle_no} onChange={(e) => setFormData({...formData, vehicle_no: e.target.value})} />
                </div>
              </div>

              {selectedPO && formData.items.length > 0 && (
                <div className="space-y-2">
                  <Label>Items</Label>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-50">
                        <tr>
                          <th className="px-3 py-2 text-left">Item</th>
                          <th className="px-3 py-2 text-left w-20">Ordered</th>
                          <th className="px-3 py-2 text-left w-20">Pending</th>
                          <th className="px-3 py-2 text-left w-20">Receive</th>
                          <th className="px-3 py-2 text-left w-20">Accept</th>
                          <th className="px-3 py-2 text-left w-20">Reject</th>
                          <th className="px-3 py-2 text-left w-24">Batch</th>
                        </tr>
                      </thead>
                      <tbody>
                        {formData.items.map((item, idx) => (
                          <tr key={idx} className="border-t">
                            <td className="px-3 py-2">{item.item_name}</td>
                            <td className="px-3 py-2 font-mono">{item.ordered_qty}</td>
                            <td className="px-3 py-2 font-mono text-orange-600">{item.pending_qty}</td>
                            <td className="px-3 py-2">
                              <Input type="number" className="h-8 w-20" value={item.receive_qty} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].receive_qty = e.target.value;
                                newItems[idx].accepted_qty = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} />
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" className="h-8 w-20" value={item.accepted_qty} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].accepted_qty = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} />
                            </td>
                            <td className="px-3 py-2">
                              <Input type="number" className="h-8 w-20" value={item.rejected_qty} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].rejected_qty = e.target.value;
                                setFormData({...formData, items: newItems});
                              }} />
                            </td>
                            <td className="px-3 py-2">
                              <Input className="h-8 w-24" value={item.batch_no} onChange={(e) => {
                                const newItems = [...formData.items];
                                newItems[idx].batch_no = e.target.value;
                                setFormData({...formData, items: newItems});
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
                <Button type="submit" className="bg-accent hover:bg-accent/90" disabled={!formData.po_id}>Create GRN</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={filters.status} onValueChange={(v) => setFilters({...filters, status: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending_qc">Pending QC</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* GRN Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">GRN Number</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">PO Number</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Supplier</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Qty</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Value</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Invoice</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {grns.length === 0 ? (
                  <tr><td colSpan="9" className="px-4 py-12 text-center text-slate-500">No GRNs found</td></tr>
                ) : (
                  grns.map((grn) => (
                    <tr key={grn.id} className="hover:bg-slate-50 transition-colors" data-testid={`grn-row-${grn.id}`}>
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{grn.grn_number}</td>
                      <td className="px-4 py-3 font-mono text-sm text-slate-600">{grn.po_number}</td>
                      <td className="px-4 py-3 text-sm text-slate-900">{grn.supplier_name}</td>
                      <td className="px-4 py-3 font-mono text-sm text-slate-600">
                        {grn.accepted_qty}/{grn.total_qty}
                        {grn.rejected_qty > 0 && <span className="text-red-500 ml-1">(-{grn.rejected_qty})</span>}
                      </td>
                      <td className="px-4 py-3 font-mono font-semibold text-slate-900">₹{(grn.total_value || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{grn.invoice_no || '-'}</td>
                      <td className="px-4 py-3">
                        <Badge className={statusColors[grn.status]}>{grn.status?.replace('_', ' ')}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">
                        {grn.created_at ? new Date(grn.created_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                          {grn.status === 'pending_qc' && (
                            <Button variant="outline" size="sm" onClick={() => handleApprove(grn.id)} className="text-green-600">
                              <CheckCircle className="h-4 w-4 mr-1" />Approve
                            </Button>
                          )}
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

// ==================== MAIN PROCUREMENT COMPONENT ====================
const Procurement = () => {
  return (
    <Routes>
      <Route index element={<ProcurementDashboard />} />
      <Route path="suppliers" element={<SuppliersList />} />
      <Route path="purchase-orders" element={<PurchaseOrdersList />} />
      <Route path="grn" element={<GRNList />} />
    </Routes>
  );
};

export default Procurement;
