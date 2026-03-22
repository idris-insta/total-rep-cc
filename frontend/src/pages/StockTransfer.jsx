import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  ArrowRightLeft, Plus, Search, Truck, Package, Warehouse, CheckCircle,
  XCircle, Clock, RefreshCw, ArrowLeft, Save, Trash2, Eye, Settings
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import api from '../lib/api';
import { toast } from 'sonner';

// ==================== TRANSFER LIST ====================
const StockTransferList = () => {
  const navigate = useNavigate();
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    fetchTransfers();
  }, [statusFilter]);

  const fetchTransfers = async () => {
    setLoading(true);
    try {
      const params = statusFilter !== 'all' ? `?status=${statusFilter}` : '';
      const res = await api.get(`/warehouse/stock-transfers${params}`);
      setTransfers(res.data);
    } catch (error) {
      toast.error('Failed to load transfers');
    } finally {
      setLoading(false);
    }
  };

  const handleDispatch = async (transferId) => {
    if (!window.confirm('Dispatch this transfer? Stock will be deducted from source warehouse.')) return;
    try {
      await api.put(`/warehouse/stock-transfers/${transferId}/dispatch`);
      toast.success('Transfer dispatched');
      fetchTransfers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to dispatch');
    }
  };

  const handleReceive = async (transferId) => {
    if (!window.confirm('Receive this transfer? Stock will be added to destination warehouse.')) return;
    try {
      await api.put(`/warehouse/stock-transfers/${transferId}/receive`);
      toast.success('Transfer received');
      fetchTransfers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to receive');
    }
  };

  const statusBadge = (status) => {
    const configs = {
      draft: { bg: 'bg-slate-100 text-slate-800', icon: Clock },
      in_transit: { bg: 'bg-blue-100 text-blue-800', icon: Truck },
      received: { bg: 'bg-green-100 text-green-800', icon: CheckCircle },
      cancelled: { bg: 'bg-red-100 text-red-800', icon: XCircle }
    };
    const config = configs[status] || configs.draft;
    const Icon = config.icon;
    return (
      <Badge className={config.bg}>
        <Icon className="h-3 w-3 mr-1" />
        {status?.replace('_', ' ').toUpperCase()}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="stock-transfers">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope flex items-center gap-3">
            <ArrowRightLeft className="h-8 w-8 text-accent" />
            Stock Transfers
          </h1>
          <p className="text-slate-600 mt-1 font-inter">Transfer stock between warehouses</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchTransfers}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button onClick={() => navigate('/inventory/stock-transfers/new')} className="bg-accent hover:bg-accent/90">
            <Plus className="h-4 w-4 mr-2" />New Transfer
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'draft', 'in_transit', 'received'].map(status => (
          <Button 
            key={status}
            variant={statusFilter === status ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter(status)}
            className={statusFilter === status ? 'bg-accent' : ''}
          >
            {status === 'all' ? 'All' : status.replace('_', ' ').toUpperCase()}
          </Button>
        ))}
      </div>

      {/* Transfer List */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b">
                <tr>
                  <th className="text-left p-3 font-medium text-slate-700">Transfer No</th>
                  <th className="text-left p-3 font-medium text-slate-700">Date</th>
                  <th className="text-left p-3 font-medium text-slate-700">From</th>
                  <th className="text-left p-3 font-medium text-slate-700">To</th>
                  <th className="text-center p-3 font-medium text-slate-700">Items</th>
                  <th className="text-center p-3 font-medium text-slate-700">Status</th>
                  <th className="text-center p-3 font-medium text-slate-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {transfers.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-12 text-slate-400">
                      <ArrowRightLeft className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>No transfers found</p>
                    </td>
                  </tr>
                ) : (
                  transfers.map((transfer) => (
                    <tr key={transfer.id} className="border-b hover:bg-slate-50">
                      <td className="p-3">
                        <code className="text-sm bg-slate-100 px-2 py-1 rounded">{transfer.transfer_no}</code>
                      </td>
                      <td className="p-3 text-sm">{transfer.transfer_date?.split('T')[0]}</td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Warehouse className="h-4 w-4 text-slate-400" />
                          <span>{transfer.from_warehouse_name}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Warehouse className="h-4 w-4 text-slate-400" />
                          <span>{transfer.to_warehouse_name}</span>
                        </div>
                      </td>
                      <td className="p-3 text-center">
                        <Badge variant="outline">{transfer.total_items}</Badge>
                      </td>
                      <td className="p-3 text-center">{statusBadge(transfer.status)}</td>
                      <td className="p-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          {transfer.status === 'draft' && (
                            <Button variant="outline" size="sm" onClick={() => handleDispatch(transfer.id)}>
                              <Truck className="h-4 w-4 mr-1" />Dispatch
                            </Button>
                          )}
                          {transfer.status === 'in_transit' && (
                            <Button variant="outline" size="sm" onClick={() => handleReceive(transfer.id)} className="text-green-600">
                              <CheckCircle className="h-4 w-4 mr-1" />Receive
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

// ==================== NEW TRANSFER FORM ====================
const StockTransferForm = () => {
  const navigate = useNavigate();
  const [warehouses, setWarehouses] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [availableStock, setAvailableStock] = useState([]);
  
  const [formData, setFormData] = useState({
    from_warehouse_id: '',
    to_warehouse_id: '',
    vehicle_no: '',
    driver_name: '',
    driver_phone: '',
    notes: '',
    items: []
  });

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (formData.from_warehouse_id) {
      fetchWarehouseStock();
    }
  }, [formData.from_warehouse_id]);

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
      const res = await api.get(`/warehouse/stock-register?warehouse_id=${formData.from_warehouse_id}`);
      setAvailableStock(res.data);
    } catch (error) {
      console.error('Failed to load stock:', error);
    }
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { item_id: '', batch_no: '', quantity: 0, uom: 'PCS' }]
    });
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    
    // Auto-fill details when item is selected
    if (field === 'item_id') {
      const stockItem = availableStock.find(s => s._id?.item_id === value || s.item_id === value);
      if (stockItem) {
        newItems[index].item_name = stockItem.item_name;
        newItems[index].available = stockItem.total_quantity;
      }
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
    
    if (!formData.from_warehouse_id || !formData.to_warehouse_id) {
      toast.error('Please select both warehouses');
      return;
    }
    
    if (formData.items.length === 0) {
      toast.error('Please add at least one item');
      return;
    }
    
    setSaving(true);
    try {
      await api.post('/warehouse/stock-transfers', formData);
      toast.success('Stock transfer created');
      navigate('/inventory/stock-transfers');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create transfer');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="stock-transfer-form">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/inventory/stock-transfers')}>
          <ArrowLeft className="h-4 w-4 mr-2" />Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 font-manrope">New Stock Transfer</h1>
          <p className="text-slate-600 font-inter">Transfer stock between warehouses</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Warehouse Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-manrope">Transfer Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>From Warehouse *</Label>
                    <Select 
                      value={formData.from_warehouse_id} 
                      onValueChange={(v) => setFormData({...formData, from_warehouse_id: v, items: []})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select source warehouse" />
                      </SelectTrigger>
                      <SelectContent>
                        {warehouses.map(wh => (
                          <SelectItem key={wh.id} value={wh.id} disabled={wh.id === formData.to_warehouse_id}>
                            {wh.warehouse_name} ({wh.warehouse_code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>To Warehouse *</Label>
                    <Select 
                      value={formData.to_warehouse_id} 
                      onValueChange={(v) => setFormData({...formData, to_warehouse_id: v})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select destination warehouse" />
                      </SelectTrigger>
                      <SelectContent>
                        {warehouses.map(wh => (
                          <SelectItem key={wh.id} value={wh.id} disabled={wh.id === formData.from_warehouse_id}>
                            {wh.warehouse_name} ({wh.warehouse_code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Items */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg font-manrope">Transfer Items</CardTitle>
                  <Button type="button" variant="outline" size="sm" onClick={addItem} disabled={!formData.from_warehouse_id}>
                    <Plus className="h-4 w-4 mr-1" />Add Item
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {!formData.from_warehouse_id ? (
                  <div className="text-center py-8 text-slate-400">
                    <Warehouse className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>Select source warehouse first</p>
                  </div>
                ) : formData.items.length === 0 ? (
                  <div className="text-center py-8 text-slate-400">
                    <Package className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p>No items added. Click "Add Item" to start.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {formData.items.map((item, index) => (
                      <div key={index} className="grid grid-cols-12 gap-2 items-end p-3 bg-slate-50 rounded-lg">
                        <div className="col-span-4 space-y-1">
                          <Label className="text-xs">Item</Label>
                          <Select 
                            value={item.item_id} 
                            onValueChange={(v) => updateItem(index, 'item_id', v)}
                          >
                            <SelectTrigger className="h-9">
                              <SelectValue placeholder="Select item" />
                            </SelectTrigger>
                            <SelectContent>
                              {availableStock.map(stock => (
                                <SelectItem key={stock._id?.item_id || stock.item_id} value={stock._id?.item_id || stock.item_id}>
                                  {stock.item_name || stock.item_code} (Avl: {stock.total_quantity})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="col-span-2 space-y-1">
                          <Label className="text-xs">Batch No</Label>
                          <Input 
                            value={item.batch_no}
                            onChange={(e) => updateItem(index, 'batch_no', e.target.value)}
                            placeholder="Optional"
                            className="h-9"
                          />
                        </div>
                        <div className="col-span-2 space-y-1">
                          <Label className="text-xs">Quantity *</Label>
                          <Input 
                            type="number"
                            value={item.quantity}
                            onChange={(e) => updateItem(index, 'quantity', parseFloat(e.target.value) || 0)}
                            className="h-9"
                            min={1}
                            max={item.available || 9999}
                          />
                        </div>
                        <div className="col-span-2 space-y-1">
                          <Label className="text-xs">UOM</Label>
                          <Select value={item.uom} onValueChange={(v) => updateItem(index, 'uom', v)}>
                            <SelectTrigger className="h-9">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="PCS">PCS</SelectItem>
                              <SelectItem value="KG">KG</SelectItem>
                              <SelectItem value="ROLL">ROLL</SelectItem>
                              <SelectItem value="MTR">MTR</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="col-span-2 flex justify-end">
                          <Button type="button" variant="ghost" size="sm" onClick={() => removeItem(index)} className="text-red-500">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-manrope flex items-center gap-2">
                  <Truck className="h-5 w-5 text-accent" />
                  Transport Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Vehicle Number</Label>
                  <Input 
                    value={formData.vehicle_no}
                    onChange={(e) => setFormData({...formData, vehicle_no: e.target.value.toUpperCase()})}
                    placeholder="GJ01XX0000"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Driver Name</Label>
                  <Input 
                    value={formData.driver_name}
                    onChange={(e) => setFormData({...formData, driver_name: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Driver Phone</Label>
                  <Input 
                    value={formData.driver_phone}
                    onChange={(e) => setFormData({...formData, driver_phone: e.target.value})}
                    placeholder="+91 00000 00000"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea 
                    value={formData.notes}
                    onChange={(e) => setFormData({...formData, notes: e.target.value})}
                    rows={3}
                  />
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
                    <><Save className="h-4 w-4 mr-2" />Create Transfer</>
                  )}
                </Button>
                <p className="text-xs text-slate-500 text-center">
                  Transfer will be created in Draft status
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
export { StockTransferList, StockTransferForm };
export default StockTransferList;
