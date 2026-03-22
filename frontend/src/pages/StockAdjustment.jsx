import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ClipboardList, Plus, Search, Warehouse, CheckCircle, Clock,
  RefreshCw, ArrowLeft, Save, Trash2, Eye, Package, AlertTriangle, Settings
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import api from '../lib/api';
import { toast } from 'sonner';

// ==================== ADJUSTMENT TYPES ====================
const ADJUSTMENT_TYPES = [
  { value: 'opening', label: 'Opening Stock', color: 'blue', description: 'Set initial stock levels' },
  { value: 'closing', label: 'Closing Stock', color: 'purple', description: 'Record closing balances' },
  { value: 'increase', label: 'Stock Increase', color: 'green', description: 'Add stock without purchase' },
  { value: 'decrease', label: 'Stock Decrease', color: 'orange', description: 'Remove stock manually' },
  { value: 'damage', label: 'Damage/Loss', color: 'red', description: 'Record damaged/lost items' },
  { value: 'expired', label: 'Expired Stock', color: 'red', description: 'Write off expired items' },
  { value: 'recount', label: 'Physical Recount', color: 'slate', description: 'Adjust after physical count' }
];

// ==================== ADJUSTMENT LIST ====================
const StockAdjustmentList = () => {
  const navigate = useNavigate();
  const [adjustments, setAdjustments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  useEffect(() => {
    fetchAdjustments();
  }, [statusFilter, typeFilter]);

  const fetchAdjustments = async () => {
    setLoading(true);
    try {
      let params = [];
      if (statusFilter !== 'all') params.push(`status=${statusFilter}`);
      if (typeFilter !== 'all') params.push(`adjustment_type=${typeFilter}`);
      const queryString = params.length > 0 ? `?${params.join('&')}` : '';
      const res = await api.get(`/warehouse/stock-adjustments${queryString}`);
      setAdjustments(res.data);
    } catch (error) {
      toast.error('Failed to load adjustments');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (adjustmentId) => {
    if (!window.confirm('Approve this adjustment? Stock levels will be updated.')) return;
    try {
      await api.put(`/warehouse/stock-adjustments/${adjustmentId}/approve`);
      toast.success('Adjustment approved and applied');
      fetchAdjustments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve');
    }
  };

  const getTypeBadge = (type) => {
    const typeConfig = ADJUSTMENT_TYPES.find(t => t.value === type);
    const colorClass = {
      blue: 'bg-blue-100 text-blue-800',
      green: 'bg-green-100 text-green-800',
      red: 'bg-red-100 text-red-800',
      orange: 'bg-orange-100 text-orange-800',
      purple: 'bg-purple-100 text-purple-800',
      slate: 'bg-slate-100 text-slate-800'
    }[typeConfig?.color] || 'bg-slate-100 text-slate-800';
    
    return <Badge className={colorClass}>{typeConfig?.label || type}</Badge>;
  };

  const statusBadge = (status) => {
    if (status === 'approved') {
      return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Approved</Badge>;
    }
    return <Badge className="bg-yellow-100 text-yellow-800"><Clock className="h-3 w-3 mr-1" />Draft</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="stock-adjustments">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope flex items-center gap-3">
            <ClipboardList className="h-8 w-8 text-accent" />
            Stock Adjustments
          </h1>
          <p className="text-slate-600 mt-1 font-inter">Manage opening stock, adjustments, and recounts</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchAdjustments}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button onClick={() => navigate('/inventory/stock-adjustments/new')} className="bg-accent hover:bg-accent/90">
            <Plus className="h-4 w-4 mr-2" />New Adjustment
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-4">
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {ADJUSTMENT_TYPES.map(type => (
                  <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Adjustment List */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b">
                <tr>
                  <th className="text-left p-3 font-medium text-slate-700">Adjustment No</th>
                  <th className="text-left p-3 font-medium text-slate-700">Date</th>
                  <th className="text-left p-3 font-medium text-slate-700">Warehouse</th>
                  <th className="text-left p-3 font-medium text-slate-700">Type</th>
                  <th className="text-center p-3 font-medium text-slate-700">Items</th>
                  <th className="text-center p-3 font-medium text-slate-700">Status</th>
                  <th className="text-center p-3 font-medium text-slate-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {adjustments.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-slate-400">
                      <ClipboardList className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>No adjustments found</p>
                    </td>
                  </tr>
                ) : (
                  adjustments.map((adj) => (
                    <tr key={adj.id} className="border-b hover:bg-slate-50">
                      <td className="p-3">
                        <code className="text-sm bg-slate-100 px-2 py-1 rounded">{adj.adjustment_no}</code>
                      </td>
                      <td className="p-3 text-sm">{adj.adjustment_date?.split('T')[0]}</td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Warehouse className="h-4 w-4 text-slate-400" />
                          <span>{adj.warehouse_name}</span>
                        </div>
                      </td>
                      <td className="p-3">{getTypeBadge(adj.adjustment_type)}</td>
                      <td className="p-3 text-center">
                        <Badge variant="outline">{adj.items?.length || 0}</Badge>
                      </td>
                      <td className="p-3 text-center">{statusBadge(adj.status)}</td>
                      <td className="p-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          {adj.status === 'draft' && (
                            <Button variant="outline" size="sm" onClick={() => handleApprove(adj.id)} className="text-green-600">
                              <CheckCircle className="h-4 w-4 mr-1" />Approve
                            </Button>
                          )}
                          <Button variant="ghost" size="sm">
                            <Eye className="h-4 w-4" />
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

// ==================== NEW ADJUSTMENT FORM ====================
const StockAdjustmentForm = () => {
  const navigate = useNavigate();
  const [warehouses, setWarehouses] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [currentStock, setCurrentStock] = useState({});
  
  const [formData, setFormData] = useState({
    warehouse_id: '',
    adjustment_type: '',
    reason: '',
    reference: '',
    items: []
  });

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (formData.warehouse_id) {
      fetchWarehouseStock();
    }
  }, [formData.warehouse_id]);

  const fetchInitialData = async () => {
    try {
      const [whRes, itemsRes] = await Promise.all([
        api.get('/warehouse/warehouses'),
        api.get('/inventory/items')
      ]);
      setWarehouses(whRes.data);
      setItems(itemsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const fetchWarehouseStock = async () => {
    try {
      const res = await api.get(`/warehouse/stock-register?warehouse_id=${formData.warehouse_id}`);
      const stockMap = {};
      (res.data || []).forEach(item => {
        stockMap[item._id?.item_id || item.item_id] = item.total_quantity || 0;
      });
      setCurrentStock(stockMap);
    } catch (error) {
      console.error('Failed to load stock:', error);
    }
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { item_id: '', batch_no: '', current_qty: 0, adjusted_qty: 0, uom: 'PCS' }]
    });
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    
    // Auto-fill current quantity when item is selected
    if (field === 'item_id') {
      const item = items.find(i => i.id === value);
      if (item) {
        newItems[index].item_name = item.item_name;
        newItems[index].item_code = item.item_code;
        newItems[index].uom = item.primary_uom || 'PCS';
      }
      newItems[index].current_qty = currentStock[value] || 0;
    }
    
    setFormData({ ...formData, items: newItems });
  };

  const removeItem = (index) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.warehouse_id || !formData.adjustment_type) {
      toast.error('Please select warehouse and adjustment type');
      return;
    }
    
    if (formData.items.length === 0) {
      toast.error('Please add at least one item');
      return;
    }
    
    setSaving(true);
    try {
      await api.post('/warehouse/stock-adjustments', formData);
      toast.success('Stock adjustment created');
      navigate('/inventory/stock-adjustments');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create adjustment');
    } finally {
      setSaving(false);
    }
  };

  const selectedType = ADJUSTMENT_TYPES.find(t => t.value === formData.adjustment_type);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="stock-adjustment-form">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/inventory/stock-adjustments')}>
            <ArrowLeft className="h-4 w-4 mr-2" />Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 font-manrope">New Stock Adjustment</h1>
            <p className="text-slate-600 font-inter">Enter opening stock, record adjustments, or perform recount</p>
          </div>
        </div>
        <Button 
          variant="ghost" 
          onClick={() => window.open('/field-registry?module=inventory&entity=stock_adjustments', '_blank')}
        >
          <Settings className="h-4 w-4 mr-2" />Customize Fields
        </Button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Basic Details */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-manrope">Adjustment Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Warehouse *</Label>
                    <Select 
                      value={formData.warehouse_id} 
                      onValueChange={(v) => setFormData({...formData, warehouse_id: v, items: []})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select warehouse" />
                      </SelectTrigger>
                      <SelectContent>
                        {warehouses.map(wh => (
                          <SelectItem key={wh.id} value={wh.id}>
                            {wh.warehouse_name} ({wh.warehouse_code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Adjustment Type *</Label>
                    <Select 
                      value={formData.adjustment_type} 
                      onValueChange={(v) => setFormData({...formData, adjustment_type: v})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        {ADJUSTMENT_TYPES.map(type => (
                          <SelectItem key={type.value} value={type.value}>
                            <div className="flex flex-col">
                              <span>{type.label}</span>
                              <span className="text-xs text-slate-500">{type.description}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {selectedType && (
                  <div className={`p-3 rounded-lg border ${
                    selectedType.color === 'green' ? 'bg-green-50 border-green-200' :
                    selectedType.color === 'red' ? 'bg-red-50 border-red-200' :
                    selectedType.color === 'blue' ? 'bg-blue-50 border-blue-200' :
                    'bg-slate-50 border-slate-200'
                  }`}>
                    <p className="text-sm font-medium">{selectedType.label}</p>
                    <p className="text-xs text-slate-600">{selectedType.description}</p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Reference Document</Label>
                    <Input 
                      value={formData.reference}
                      onChange={(e) => setFormData({...formData, reference: e.target.value})}
                      placeholder="e.g., Physical count sheet no."
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Reason / Notes</Label>
                  <Textarea 
                    value={formData.reason}
                    onChange={(e) => setFormData({...formData, reason: e.target.value})}
                    placeholder="Enter reason for adjustment..."
                    rows={2}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Items */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg font-manrope">Adjustment Items</CardTitle>
                  <Button type="button" variant="outline" size="sm" onClick={addItem} disabled={!formData.warehouse_id}>
                    <Plus className="h-4 w-4 mr-1" />Add Item
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {!formData.warehouse_id ? (
                  <div className="text-center py-8 text-slate-400">
                    <Warehouse className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>Select warehouse first</p>
                  </div>
                ) : formData.items.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">
                    <Package className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No items added. Click "Add Item" to start.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="grid grid-cols-12 gap-2 text-xs font-medium text-slate-600 pb-2 border-b">
                      <div className="col-span-4">Item</div>
                      <div className="col-span-2">Batch No</div>
                      <div className="col-span-2 text-right">Current Qty</div>
                      <div className="col-span-2 text-right">Adjusted Qty</div>
                      <div className="col-span-1 text-right">Diff</div>
                      <div className="col-span-1"></div>
                    </div>
                    {formData.items.map((item, index) => {
                      const diff = (item.adjusted_qty || 0) - (item.current_qty || 0);
                      return (
                        <div key={index} className="grid grid-cols-12 gap-2 items-center p-2 bg-slate-50 rounded-lg">
                          <div className="col-span-4">
                            <Select 
                              value={item.item_id} 
                              onValueChange={(v) => updateItem(index, 'item_id', v)}
                            >
                              <SelectTrigger className="h-9">
                                <SelectValue placeholder="Select item" />
                              </SelectTrigger>
                              <SelectContent>
                                {items.map(i => (
                                  <SelectItem key={i.id} value={i.id}>
                                    {i.item_name} ({i.item_code})
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="col-span-2">
                            <Input 
                              value={item.batch_no}
                              onChange={(e) => updateItem(index, 'batch_no', e.target.value)}
                              placeholder="Optional"
                              className="h-9"
                            />
                          </div>
                          <div className="col-span-2 text-right">
                            <span className="text-sm font-mono bg-slate-100 px-2 py-1 rounded">
                              {item.current_qty || 0}
                            </span>
                          </div>
                          <div className="col-span-2">
                            <Input 
                              type="number"
                              value={item.adjusted_qty}
                              onChange={(e) => updateItem(index, 'adjusted_qty', parseFloat(e.target.value) || 0)}
                              className="h-9 text-right"
                              min={0}
                            />
                          </div>
                          <div className="col-span-1 text-right">
                            <span className={`text-sm font-mono font-medium ${
                              diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : 'text-slate-400'
                            }`}>
                              {diff > 0 ? '+' : ''}{diff}
                            </span>
                          </div>
                          <div className="col-span-1 text-right">
                            <Button type="button" variant="ghost" size="sm" onClick={() => removeItem(index)} className="text-red-500 h-8 w-8 p-0">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-manrope">Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-600">Total Items</span>
                  <span className="font-bold">{formData.items.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Net Increase</span>
                  <span className="font-bold text-green-600">
                    +{formData.items.reduce((sum, item) => {
                      const diff = (item.adjusted_qty || 0) - (item.current_qty || 0);
                      return sum + (diff > 0 ? diff : 0);
                    }, 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Net Decrease</span>
                  <span className="font-bold text-red-600">
                    {formData.items.reduce((sum, item) => {
                      const diff = (item.adjusted_qty || 0) - (item.current_qty || 0);
                      return sum + (diff < 0 ? diff : 0);
                    }, 0)}
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4 space-y-2">
                <Button 
                  type="submit" 
                  className="w-full bg-accent hover:bg-accent/90"
                  disabled={saving}
                >
                  {saving ? (
                    <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Creating...</>
                  ) : (
                    <><Save className="h-4 w-4 mr-2" />Create Adjustment</>
                  )}
                </Button>
                <p className="text-xs text-slate-500 text-center">
                  Adjustment will be created in Draft status. Approve to apply changes.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

// ==================== EXPORT ====================
export { StockAdjustmentList, StockAdjustmentForm };
export default StockAdjustmentList;
