import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { 
  Plus, Search, Edit, Trash2, Package, AlertTriangle, TrendingDown, 
  Warehouse, ArrowRightLeft, Box, Filter, RefreshCw, Download,
  ChevronDown, Eye, Truck, CheckCircle, Clock, BarChart3, Settings
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
import useCustomFields from '../hooks/useCustomFields';
import useFieldRegistry from '../hooks/useFieldRegistry';
import DynamicFormFields from '../components/DynamicFormFields';
import DynamicRegistryForm from '../components/DynamicRegistryForm';

// ==================== INVENTORY DASHBOARD ====================
const InventoryDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_items: 0, total_warehouses: 0, low_stock_items: 0, 
    pending_transfers: 0, total_stock_value: 0, by_category: {}
  });
  const [loading, setLoading] = useState(true);
  const [lowStockItems, setLowStockItems] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, stockRes] = await Promise.all([
        api.get('/inventory/stats/overview'),
        api.get('/inventory/stock/balance?low_stock=true')
      ]);
      setStats(statsRes.data);
      setLowStockItems(stockRes.data.slice(0, 5));
    } catch (error) {
      console.error('Failed to load inventory stats', error);
    } finally {
      setLoading(false);
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
    <div className="space-y-6" data-testid="inventory-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Inventory Dashboard</h2>
          <p className="text-slate-600 mt-1 font-inter">Multi-location stock management & tracking</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/inventory/items')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Box className="h-6 w-6 text-blue-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">{stats.total_items}</div>
                <p className="text-sm text-slate-500">Items</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/inventory/warehouses')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                <Warehouse className="h-6 w-6 text-green-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-green-600">{stats.total_warehouses}</div>
                <p className="text-sm text-slate-500">Warehouses</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/inventory/stock')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-orange-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-orange-600">{stats.low_stock_items}</div>
                <p className="text-sm text-slate-500">Low Stock</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/inventory/transfers')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-purple-100 flex items-center justify-center">
                <ArrowRightLeft className="h-6 w-6 text-purple-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-purple-600">{stats.pending_transfers}</div>
                <p className="text-sm text-slate-500">Transfers</p>
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
                <div className="text-2xl font-bold text-emerald-600 font-mono">₹{(stats.total_stock_value || 0).toLocaleString('en-IN')}</div>
                <p className="text-sm text-slate-500">Stock Value</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Category Distribution & Low Stock */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="font-manrope">Stock by Category</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.by_category || {}).map(([category, data]) => (
                <div key={category} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div>
                    <p className="font-semibold text-slate-900 font-inter">{category}</p>
                    <p className="text-sm text-slate-500 font-inter">{data.count} items</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-slate-900 font-mono">{data.stock}</p>
                    <p className="text-xs text-slate-500">units</p>
                  </div>
                </div>
              ))}
              {Object.keys(stats.by_category || {}).length === 0 && (
                <p className="text-center text-slate-500 py-4">No items yet</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-manrope">Low Stock Alert</CardTitle>
            <Button variant="outline" size="sm" onClick={() => navigate('/inventory/stock')}>
              View All
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {lowStockItems.length === 0 ? (
                <p className="text-center text-slate-500 py-4">No low stock items</p>
              ) : (
                lowStockItems.map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-200">
                    <div>
                      <p className="font-semibold text-slate-900 font-inter">{item.item_name}</p>
                      <p className="text-sm text-slate-500 font-mono">{item.item_code}</p>
                    </div>
                    <div className="text-right">
                      <Badge className="bg-orange-100 text-orange-800">{item.quantity} {item.uom}</Badge>
                      <p className="text-xs text-slate-500 mt-1">{item.warehouse_name}</p>
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/inventory/items')}>
              <Box className="h-6 w-6" />
              <span>Item Master</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/inventory/stock')}>
              <Package className="h-6 w-6" />
              <span>Stock Balance</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/inventory/transfers')}>
              <ArrowRightLeft className="h-6 w-6" />
              <span>Stock Transfers</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/inventory/warehouses')}>
              <Warehouse className="h-6 w-6" />
              <span>Warehouses</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== ITEMS MASTER ====================
const ItemsMaster = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({ category: 'all', item_type: 'all', low_stock: false });
  const [formData, setFormData] = useState({
    item_code: '', item_name: '', category: 'Finished Goods', item_type: 'BOPP Tape',
    hsn_code: '', uom: 'Rolls', secondary_uom: '', conversion_factor: '1',
    thickness: '', width: '', length: '', color: '', adhesive_type: '', base_material: '', grade: '',
    standard_cost: '', selling_price: '', min_order_qty: '1',
    reorder_level: '10', safety_stock: '5', lead_time_days: '7',
    shelf_life_days: '', storage_conditions: ''
  });
  
  // Dynamic fields from both systems - Field Registry (new) and Custom Fields (legacy)
  const { fields: customFields } = useCustomFields('inventory_items');
  const { formFields: registryFields, sectionLabels, loading: registryLoading } = useFieldRegistry('inventory', 'stock_items');
  const [customFieldValues, setCustomFieldValues] = useState({});
  
  // Handler for registry form changes
  const handleRegistryFormChange = (newData) => {
    setFormData(prev => ({ ...prev, ...newData }));
  };

  useEffect(() => { fetchItems(); }, [filters]);

  const fetchItems = async () => {
    try {
      let url = '/inventory/items?';
      if (filters.category !== 'all') url += `category=${filters.category}&`;
      if (filters.item_type !== 'all') url += `item_type=${filters.item_type}&`;
      if (filters.low_stock) url += 'low_stock=true&';
      const response = await api.get(url);
      setItems(response.data);
    } catch (error) {
      toast.error('Failed to load items');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        thickness: formData.thickness ? parseFloat(formData.thickness) : null,
        width: formData.width ? parseFloat(formData.width) : null,
        length: formData.length ? parseFloat(formData.length) : null,
        conversion_factor: parseFloat(formData.conversion_factor) || 1,
        standard_cost: parseFloat(formData.standard_cost) || 0,
        selling_price: parseFloat(formData.selling_price) || 0,
        min_order_qty: parseFloat(formData.min_order_qty) || 1,
        reorder_level: parseFloat(formData.reorder_level) || 0,
        safety_stock: parseFloat(formData.safety_stock) || 0,
        lead_time_days: parseInt(formData.lead_time_days) || 7,
        shelf_life_days: formData.shelf_life_days ? parseInt(formData.shelf_life_days) : null,
        custom_fields: customFieldValues
      };

      if (editingItem) {
        await api.put(`/inventory/items/${editingItem.id}`, payload);
        toast.success('Item updated');
      } else {
        await api.post('/inventory/items', payload);
        toast.success('Item created');
      }
      setOpen(false);
      setEditingItem(null);
      setCustomFieldValues({});
      fetchItems();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save item');
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setFormData({
      item_code: item.item_code || '',
      item_name: item.item_name || '',
      category: item.category || 'Finished Goods',
      item_type: item.item_type || 'BOPP Tape',
      hsn_code: item.hsn_code || '',
      uom: item.uom || 'Rolls',
      secondary_uom: item.secondary_uom || '',
      conversion_factor: item.conversion_factor?.toString() || '1',
      thickness: item.thickness?.toString() || '',
      width: item.width?.toString() || '',
      length: item.length?.toString() || '',
      color: item.color || '',
      adhesive_type: item.adhesive_type || '',
      base_material: item.base_material || '',
      grade: item.grade || '',
      standard_cost: item.standard_cost?.toString() || '',
      selling_price: item.selling_price?.toString() || '',
      min_order_qty: item.min_order_qty?.toString() || '1',
      reorder_level: item.reorder_level?.toString() || '10',
      safety_stock: item.safety_stock?.toString() || '5',
      lead_time_days: item.lead_time_days?.toString() || '7',
      shelf_life_days: item.shelf_life_days?.toString() || '',
      storage_conditions: item.storage_conditions || ''
    });
    setCustomFieldValues(item.custom_fields || {});
    setOpen(true);
  };

  const handleDelete = async (itemId) => {
    if (!window.confirm('Deactivate this item?')) return;
    try {
      await api.delete(`/inventory/items/${itemId}`);
      toast.success('Item deactivated');
      fetchItems();
    } catch (error) {
      toast.error('Failed to deactivate item');
    }
  };

  const resetForm = () => {
    setFormData({
      item_code: '', item_name: '', category: 'Finished Goods', item_type: 'BOPP Tape',
      hsn_code: '', uom: 'Rolls', secondary_uom: '', conversion_factor: '1',
      thickness: '', width: '', length: '', color: '', adhesive_type: '', base_material: '', grade: '',
      standard_cost: '', selling_price: '', min_order_qty: '1',
      reorder_level: '10', safety_stock: '5', lead_time_days: '7',
      shelf_life_days: '', storage_conditions: ''
    });
    setCustomFieldValues({});
  };
  
  const handleCustomFieldChange = (fieldName, value) => {
    setCustomFieldValues(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const filteredItems = items.filter(item =>
    item.item_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.item_code?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const categoryColors = {
    'Raw Material': 'bg-blue-100 text-blue-800',
    'Semi-Finished': 'bg-yellow-100 text-yellow-800',
    'Finished Goods': 'bg-green-100 text-green-800',
    'Packaging': 'bg-purple-100 text-purple-800'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="items-master">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Item Master</h2>
          <p className="text-slate-600 mt-1 font-inter">{items.length} items</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) { setEditingItem(null); resetForm(); } }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90 font-inter" data-testid="add-item-button">
              <Plus className="h-4 w-4 mr-2" />Add Item
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <div className="flex items-center justify-between">
                <DialogTitle className="font-manrope">{editingItem ? 'Edit' : 'Create'} Item</DialogTitle>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="text-xs text-slate-500 hover:text-accent"
                  onClick={() => window.open('/field-registry?module=inventory&entity=stock_items', '_blank')}
                >
                  <Settings className="h-3 w-3 mr-1" />Customize Fields
                </Button>
              </div>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Tabs defaultValue="basic" className="w-full">
                <TabsList className={`grid w-full ${(customFields.length > 0 || registryFields.length > 0) ? 'grid-cols-5' : 'grid-cols-4'}`}>
                  <TabsTrigger value="basic">Basic Info</TabsTrigger>
                  <TabsTrigger value="specs">Specifications</TabsTrigger>
                  <TabsTrigger value="pricing">Pricing & MOQ</TabsTrigger>
                  <TabsTrigger value="inventory">Inventory</TabsTrigger>
                  {(customFields.length > 0 || registryFields.length > 0) && <TabsTrigger value="custom">Custom Fields</TabsTrigger>}
                </TabsList>

                <TabsContent value="basic" className="space-y-4 mt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label className="font-inter">Item Code *</Label>
                      <Input value={formData.item_code} onChange={(e) => setFormData({...formData, item_code: e.target.value})} placeholder="IT-001" required data-testid="item-code-input" />
                    </div>
                    <div className="space-y-2 col-span-2">
                      <Label className="font-inter">Item Name *</Label>
                      <Input value={formData.item_name} onChange={(e) => setFormData({...formData, item_name: e.target.value})} placeholder="BOPP Tape 48mm Brown" required data-testid="item-name-input" />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Category *</Label>
                      <Select value={formData.category} onValueChange={(value) => setFormData({...formData, category: value})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Raw Material">Raw Material</SelectItem>
                          <SelectItem value="Semi-Finished">Semi-Finished</SelectItem>
                          <SelectItem value="Finished Goods">Finished Goods</SelectItem>
                          <SelectItem value="Packaging">Packaging</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Item Type *</Label>
                      <Select value={formData.item_type} onValueChange={(value) => setFormData({...formData, item_type: value})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="BOPP Tape">BOPP Tape</SelectItem>
                          <SelectItem value="Masking Tape">Masking Tape</SelectItem>
                          <SelectItem value="Double Sided">Double Sided Tape</SelectItem>
                          <SelectItem value="Cloth Tape">Cloth Tape</SelectItem>
                          <SelectItem value="PVC Tape">PVC Tape</SelectItem>
                          <SelectItem value="Foam Tape">Foam Tape</SelectItem>
                          <SelectItem value="Specialty">Specialty Tape</SelectItem>
                          <SelectItem value="Jumbo Roll">Jumbo Roll</SelectItem>
                          <SelectItem value="Core">Core</SelectItem>
                          <SelectItem value="Carton">Carton</SelectItem>
                          <SelectItem value="Other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">HSN Code</Label>
                      <Input value={formData.hsn_code} onChange={(e) => setFormData({...formData, hsn_code: e.target.value})} placeholder="39191010" />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Primary UOM *</Label>
                      <Select value={formData.uom} onValueChange={(value) => setFormData({...formData, uom: value})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Rolls">Rolls</SelectItem>
                          <SelectItem value="SQM">SQM</SelectItem>
                          <SelectItem value="KG">KG</SelectItem>
                          <SelectItem value="PCS">PCS</SelectItem>
                          <SelectItem value="MTR">MTR</SelectItem>
                          <SelectItem value="BOX">BOX</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Secondary UOM</Label>
                      <Select value={formData.secondary_uom || 'none'} onValueChange={(value) => setFormData({...formData, secondary_uom: value === 'none' ? '' : value})}>
                        <SelectTrigger><SelectValue placeholder="Optional" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">None</SelectItem>
                          <SelectItem value="SQM">SQM</SelectItem>
                          <SelectItem value="MTR">MTR</SelectItem>
                          <SelectItem value="KG">KG</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Conversion Factor</Label>
                      <Input type="number" step="0.001" value={formData.conversion_factor} onChange={(e) => setFormData({...formData, conversion_factor: e.target.value})} placeholder="1" />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="specs" className="space-y-4 mt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label className="font-inter">Thickness (micron)</Label>
                      <Input type="number" step="0.1" value={formData.thickness} onChange={(e) => setFormData({...formData, thickness: e.target.value})} placeholder="40" />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Width (mm)</Label>
                      <Input type="number" value={formData.width} onChange={(e) => setFormData({...formData, width: e.target.value})} placeholder="48" />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Length (m)</Label>
                      <Input type="number" value={formData.length} onChange={(e) => setFormData({...formData, length: e.target.value})} placeholder="100" />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Color</Label>
                      <Select value={formData.color} onValueChange={(value) => setFormData({...formData, color: value})}>
                        <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Transparent">Transparent</SelectItem>
                          <SelectItem value="Brown">Brown</SelectItem>
                          <SelectItem value="White">White</SelectItem>
                          <SelectItem value="Black">Black</SelectItem>
                          <SelectItem value="Red">Red</SelectItem>
                          <SelectItem value="Yellow">Yellow</SelectItem>
                          <SelectItem value="Green">Green</SelectItem>
                          <SelectItem value="Blue">Blue</SelectItem>
                          <SelectItem value="Custom">Custom</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Adhesive Type</Label>
                      <Select value={formData.adhesive_type} onValueChange={(value) => setFormData({...formData, adhesive_type: value})}>
                        <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Acrylic">Acrylic</SelectItem>
                          <SelectItem value="Hotmelt">Hotmelt</SelectItem>
                          <SelectItem value="Rubber">Rubber</SelectItem>
                          <SelectItem value="Solvent">Solvent</SelectItem>
                          <SelectItem value="Water-based">Water-based</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Base Material</Label>
                      <Select value={formData.base_material} onValueChange={(value) => setFormData({...formData, base_material: value})}>
                        <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="BOPP">BOPP</SelectItem>
                          <SelectItem value="PVC">PVC</SelectItem>
                          <SelectItem value="Cloth">Cloth</SelectItem>
                          <SelectItem value="Paper">Paper</SelectItem>
                          <SelectItem value="Foam">Foam</SelectItem>
                          <SelectItem value="PE">PE</SelectItem>
                          <SelectItem value="PET">PET</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Grade</Label>
                      <Select value={formData.grade} onValueChange={(value) => setFormData({...formData, grade: value})}>
                        <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Premium">Premium</SelectItem>
                          <SelectItem value="Standard">Standard</SelectItem>
                          <SelectItem value="Economy">Economy</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="col-span-2 space-y-2">
                      <Label className="font-inter">Storage Conditions</Label>
                      <Input value={formData.storage_conditions} onChange={(e) => setFormData({...formData, storage_conditions: e.target.value})} placeholder="Cool, dry place. Avoid direct sunlight." />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="pricing" className="space-y-4 mt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label className="font-inter">Standard Cost (₹)</Label>
                      <Input type="number" step="0.01" value={formData.standard_cost} onChange={(e) => setFormData({...formData, standard_cost: e.target.value})} placeholder="50.00" />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Selling Price (₹)</Label>
                      <Input type="number" step="0.01" value={formData.selling_price} onChange={(e) => setFormData({...formData, selling_price: e.target.value})} placeholder="75.00" />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Min Order Qty</Label>
                      <Input type="number" value={formData.min_order_qty} onChange={(e) => setFormData({...formData, min_order_qty: e.target.value})} placeholder="1" />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="inventory" className="space-y-4 mt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label className="font-inter">Reorder Level *</Label>
                      <Input type="number" value={formData.reorder_level} onChange={(e) => setFormData({...formData, reorder_level: e.target.value})} placeholder="10" required />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Safety Stock *</Label>
                      <Input type="number" value={formData.safety_stock} onChange={(e) => setFormData({...formData, safety_stock: e.target.value})} placeholder="5" required />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Lead Time (Days)</Label>
                      <Input type="number" value={formData.lead_time_days} onChange={(e) => setFormData({...formData, lead_time_days: e.target.value})} placeholder="7" />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Shelf Life (Days)</Label>
                      <Input type="number" value={formData.shelf_life_days} onChange={(e) => setFormData({...formData, shelf_life_days: e.target.value})} placeholder="365" />
                    </div>
                  </div>
                </TabsContent>
                
                {/* Dynamic Custom Fields Tab - Combines Field Registry and Legacy Custom Fields */}
                {(customFields.length > 0 || registryFields.length > 0) && (
                  <TabsContent value="custom" className="space-y-4 mt-4">
                    {/* Field Registry Fields */}
                    {registryFields.length > 0 && (
                      <div className="space-y-4">
                        <div className="text-sm font-medium text-slate-500 border-b pb-2">Configured Fields (from Settings)</div>
                        <DynamicRegistryForm
                          fields={registryFields}
                          formData={formData}
                          onChange={handleRegistryFormChange}
                          sectionLabels={sectionLabels}
                          groupBySection={true}
                          columns={2}
                        />
                      </div>
                    )}
                    
                    {/* Legacy Custom Fields */}
                    {customFields.length > 0 && (
                      <div className="space-y-4 mt-6">
                        <div className="text-sm font-medium text-slate-500 border-b pb-2">Legacy Custom Fields</div>
                        <DynamicFormFields
                          fields={customFields}
                          values={customFieldValues}
                          onChange={handleCustomFieldChange}
                          columns={2}
                          showSections={true}
                        />
                      </div>
                    )}
                  </TabsContent>
                )}
              </Tabs>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setOpen(false); setEditingItem(null); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90" data-testid="item-submit-button">{editingItem ? 'Update' : 'Create'}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder="Search items..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" data-testid="item-search" />
        </div>
        <Select value={filters.category} onValueChange={(v) => setFilters({...filters, category: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Category" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            <SelectItem value="Raw Material">Raw Material</SelectItem>
            <SelectItem value="Semi-Finished">Semi-Finished</SelectItem>
            <SelectItem value="Finished Goods">Finished Goods</SelectItem>
            <SelectItem value="Packaging">Packaging</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters.item_type} onValueChange={(v) => setFilters({...filters, item_type: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="BOPP Tape">BOPP Tape</SelectItem>
            <SelectItem value="Masking Tape">Masking Tape</SelectItem>
            <SelectItem value="Double Sided">Double Sided</SelectItem>
            <SelectItem value="PVC Tape">PVC Tape</SelectItem>
          </SelectContent>
        </Select>
        <Button variant={filters.low_stock ? "default" : "outline"} size="sm" onClick={() => setFilters({...filters, low_stock: !filters.low_stock})}>
          <AlertTriangle className="h-4 w-4 mr-2" />Low Stock
        </Button>
      </div>

      {/* Items Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Code</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Category</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Specs</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">UOM</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Stock</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Reorder</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredItems.length === 0 ? (
                  <tr><td colSpan="9" className="px-4 py-12 text-center text-slate-500">No items found</td></tr>
                ) : (
                  filteredItems.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-50 transition-colors" data-testid={`item-row-${item.id}`}>
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{item.item_code}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900">{item.item_name}</div>
                        <div className="text-sm text-slate-500">{item.color || '-'}</div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={categoryColors[item.category] || 'bg-slate-100 text-slate-800'}>{item.category}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">{item.item_type}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 font-mono">
                        {item.thickness && `${item.thickness}µ`}
                        {item.width && ` × ${item.width}mm`}
                        {item.length && ` × ${item.length}m`}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{item.uom}</Badge>
                        {item.secondary_uom && <Badge variant="outline" className="ml-1 text-xs">{item.secondary_uom}</Badge>}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`font-mono font-semibold ${item.current_stock <= item.reorder_level ? 'text-red-600' : 'text-slate-900'}`}>
                          {item.current_stock || 0}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm font-mono text-slate-600">{item.reorder_level}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleEdit(item)} data-testid={`edit-item-${item.id}`}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(item.id)} className="text-destructive">
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

// ==================== WAREHOUSES ====================
const WarehousesList = () => {
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    warehouse_code: '', warehouse_name: '', warehouse_type: 'Main',
    address: '', city: '', state: '', pincode: ''
  });

  useEffect(() => { fetchWarehouses(); }, []);

  const fetchWarehouses = async () => {
    try {
      const response = await api.get('/inventory/warehouses');
      setWarehouses(response.data);
    } catch (error) {
      toast.error('Failed to load warehouses');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/inventory/warehouses', formData);
      toast.success('Warehouse created');
      setOpen(false);
      fetchWarehouses();
      setFormData({ warehouse_code: '', warehouse_name: '', warehouse_type: 'Main', address: '', city: '', state: '', pincode: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create warehouse');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="warehouses-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Warehouses</h2>
          <p className="text-slate-600 mt-1 font-inter">{warehouses.length} locations</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="add-warehouse-button">
              <Plus className="h-4 w-4 mr-2" />Add Warehouse
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Warehouse</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Warehouse Code *</Label>
                  <Input value={formData.warehouse_code} onChange={(e) => setFormData({...formData, warehouse_code: e.target.value})} placeholder="WH-001" required />
                </div>
                <div className="space-y-2">
                  <Label>Warehouse Name *</Label>
                  <Input value={formData.warehouse_name} onChange={(e) => setFormData({...formData, warehouse_name: e.target.value})} placeholder="Main Warehouse" required />
                </div>
                <div className="space-y-2">
                  <Label>Type</Label>
                  <Select value={formData.warehouse_type} onValueChange={(v) => setFormData({...formData, warehouse_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Main">Main</SelectItem>
                      <SelectItem value="Branch">Branch</SelectItem>
                      <SelectItem value="Transit">Transit</SelectItem>
                      <SelectItem value="Factory">Factory</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>City</Label>
                  <Input value={formData.city} onChange={(e) => setFormData({...formData, city: e.target.value})} placeholder="Mumbai" />
                </div>
                <div className="space-y-2">
                  <Label>State</Label>
                  <Input value={formData.state} onChange={(e) => setFormData({...formData, state: e.target.value})} placeholder="Maharashtra" />
                </div>
                <div className="space-y-2">
                  <Label>Pincode</Label>
                  <Input value={formData.pincode} onChange={(e) => setFormData({...formData, pincode: e.target.value})} placeholder="400001" />
                </div>
                <div className="col-span-2 space-y-2">
                  <Label>Address</Label>
                  <Textarea value={formData.address} onChange={(e) => setFormData({...formData, address: e.target.value})} rows={2} />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Create</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {warehouses.map((wh) => (
          <Card key={wh.id} className="border-slate-200 shadow-sm hover:shadow-md transition-all">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
                    <Warehouse className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-900">{wh.warehouse_name}</p>
                    <p className="text-sm text-slate-500 font-mono">{wh.warehouse_code}</p>
                  </div>
                </div>
                <Badge className={wh.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-800'}>
                  {wh.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
              <div className="mt-4 space-y-1 text-sm text-slate-600">
                <p><span className="font-medium">Type:</span> {wh.warehouse_type}</p>
                {wh.city && <p><span className="font-medium">Location:</span> {wh.city}, {wh.state}</p>}
              </div>
            </CardContent>
          </Card>
        ))}
        {warehouses.length === 0 && (
          <div className="col-span-full text-center py-12 text-slate-500">
            No warehouses yet. Click &quot;Add Warehouse&quot; to create one.
          </div>
        )}
      </div>
    </div>
  );
};

// ==================== STOCK BALANCE ====================
const StockBalance = () => {
  const [balances, setBalances] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ warehouse_id: 'all', low_stock: false });
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => { fetchData(); }, [filters]);

  const fetchData = async () => {
    try {
      let url = '/inventory/stock/balance?';
      if (filters.warehouse_id !== 'all') url += `warehouse_id=${filters.warehouse_id}&`;
      if (filters.low_stock) url += 'low_stock=true&';
      
      const [balanceRes, warehouseRes] = await Promise.all([
        api.get(url),
        api.get('/inventory/warehouses')
      ]);
      setBalances(balanceRes.data);
      setWarehouses(warehouseRes.data);
    } catch (error) {
      toast.error('Failed to load stock data');
    } finally {
      setLoading(false);
    }
  };

  const filteredBalances = balances.filter(b =>
    b.item_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    b.item_code?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="stock-balance">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Stock Balance</h2>
          <p className="text-slate-600 mt-1 font-inter">Current inventory levels</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder="Search items..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" />
        </div>
        <Select value={filters.warehouse_id} onValueChange={(v) => setFilters({...filters, warehouse_id: v})}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="Warehouse" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Warehouses</SelectItem>
            {warehouses.map(wh => (
              <SelectItem key={wh.id} value={wh.id}>{wh.warehouse_name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button variant={filters.low_stock ? "default" : "outline"} size="sm" onClick={() => setFilters({...filters, low_stock: !filters.low_stock})}>
          <AlertTriangle className="h-4 w-4 mr-2" />Low Stock Only
        </Button>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Item Code</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Item Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Warehouse</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Quantity</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Reserved</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Available</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">UOM</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Value</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredBalances.length === 0 ? (
                  <tr><td colSpan="8" className="px-4 py-12 text-center text-slate-500">No stock records found</td></tr>
                ) : (
                  filteredBalances.map((bal, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{bal.item_code}</td>
                      <td className="px-4 py-3 text-sm text-slate-900">{bal.item_name}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{bal.warehouse_name}</td>
                      <td className="px-4 py-3 font-mono font-semibold text-slate-900">{bal.quantity}</td>
                      <td className="px-4 py-3 font-mono text-slate-600">{bal.reserved_qty || 0}</td>
                      <td className="px-4 py-3 font-mono font-semibold text-green-600">{bal.available_qty || bal.quantity}</td>
                      <td className="px-4 py-3"><Badge variant="outline">{bal.uom}</Badge></td>
                      <td className="px-4 py-3 font-mono text-slate-900">₹{(bal.total_value || 0).toLocaleString('en-IN')}</td>
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

// ==================== STOCK TRANSFERS ====================
const StockTransfers = () => {
  const [transfers, setTransfers] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({ status: 'all' });
  const [formData, setFormData] = useState({
    from_warehouse: '', to_warehouse: '', items: [{ item_id: '', quantity: '', batch_no: '' }],
    scheduled_date: '', truck_no: '', driver_name: '', driver_phone: '', notes: ''
  });

  useEffect(() => { fetchData(); }, [filters]);

  const fetchData = async () => {
    try {
      let url = '/inventory/transfers?';
      if (filters.status !== 'all') url += `status=${filters.status}&`;
      
      const [transferRes, warehouseRes, itemsRes] = await Promise.all([
        api.get(url),
        api.get('/inventory/warehouses'),
        api.get('/inventory/items')
      ]);
      setTransfers(transferRes.data);
      setWarehouses(warehouseRes.data);
      setItems(itemsRes.data);
    } catch (error) {
      toast.error('Failed to load transfers');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        items: formData.items.filter(i => i.item_id && i.quantity).map(i => ({
          item_id: i.item_id,
          quantity: parseFloat(i.quantity),
          batch_no: i.batch_no || null
        }))
      };
      await api.post('/inventory/transfers', payload);
      toast.success('Transfer created');
      setOpen(false);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create transfer');
    }
  };

  const handleIssue = async (transferId) => {
    if (!window.confirm('Issue this transfer? Stock will be deducted from source warehouse.')) return;
    try {
      await api.put(`/inventory/transfers/${transferId}/issue`);
      toast.success('Transfer issued');
      fetchData();
    } catch (error) {
      const msg = error.response?.data?.detail;
      if (msg && msg.includes('Approval required')) {
        toast.error('Approval required. Please approve in Approvals Inbox, then issue again.');
        return;
      }
      toast.error(msg || 'Failed to issue transfer');
    }
  };

  const resetForm = () => {
    setFormData({
      from_warehouse: '', to_warehouse: '', items: [{ item_id: '', quantity: '', batch_no: '' }],
      scheduled_date: '', truck_no: '', driver_name: '', driver_phone: '', notes: ''
    });
  };

  const addTransferItem = () => {
    setFormData({ ...formData, items: [...formData.items, { item_id: '', quantity: '', batch_no: '' }] });
  };

  const statusColors = {
    draft: 'bg-slate-100 text-slate-800',
    issued: 'bg-blue-100 text-blue-800',
    in_transit: 'bg-yellow-100 text-yellow-800',
    received: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="stock-transfers">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Stock Transfers</h2>
          <p className="text-slate-600 mt-1 font-inter">Inter-warehouse movements</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="create-transfer-button">
              <Plus className="h-4 w-4 mr-2" />New Transfer
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create Stock Transfer</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>From Warehouse *</Label>
                  <Select value={formData.from_warehouse} onValueChange={(v) => setFormData({...formData, from_warehouse: v})}>
                    <SelectTrigger><SelectValue placeholder="Select source" /></SelectTrigger>
                    <SelectContent>
                      {warehouses.map(wh => (
                        <SelectItem key={wh.id} value={wh.id}>{wh.warehouse_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>To Warehouse *</Label>
                  <Select value={formData.to_warehouse} onValueChange={(v) => setFormData({...formData, to_warehouse: v})}>
                    <SelectTrigger><SelectValue placeholder="Select destination" /></SelectTrigger>
                    <SelectContent>
                      {warehouses.filter(wh => wh.id !== formData.from_warehouse).map(wh => (
                        <SelectItem key={wh.id} value={wh.id}>{wh.warehouse_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Items *</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addTransferItem}>
                    <Plus className="h-4 w-4 mr-1" />Add Item
                  </Button>
                </div>
                {formData.items.map((item, idx) => (
                  <div key={idx} className="grid grid-cols-4 gap-2">
                    <Select value={item.item_id} onValueChange={(v) => {
                      const newItems = [...formData.items];
                      newItems[idx].item_id = v;
                      setFormData({...formData, items: newItems});
                    }} className="col-span-2">
                      <SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger>
                      <SelectContent>
                        {items.map(i => (
                          <SelectItem key={i.id} value={i.id}>{i.item_code} - {i.item_name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Input type="number" placeholder="Qty" value={item.quantity} onChange={(e) => {
                      const newItems = [...formData.items];
                      newItems[idx].quantity = e.target.value;
                      setFormData({...formData, items: newItems});
                    }} />
                    <Input placeholder="Batch (opt)" value={item.batch_no} onChange={(e) => {
                      const newItems = [...formData.items];
                      newItems[idx].batch_no = e.target.value;
                      setFormData({...formData, items: newItems});
                    }} />
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Scheduled Date</Label>
                  <Input type="date" value={formData.scheduled_date} onChange={(e) => setFormData({...formData, scheduled_date: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Truck No.</Label>
                  <Input value={formData.truck_no} onChange={(e) => setFormData({...formData, truck_no: e.target.value})} placeholder="MH01XX1234" />
                </div>
                <div className="space-y-2">
                  <Label>Driver Name</Label>
                  <Input value={formData.driver_name} onChange={(e) => setFormData({...formData, driver_name: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Driver Phone</Label>
                  <Input value={formData.driver_phone} onChange={(e) => setFormData({...formData, driver_phone: e.target.value})} />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Create Transfer</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center gap-4">
        <Select value={filters.status} onValueChange={(v) => setFilters({...filters, status: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="in_transit">In Transit</SelectItem>
            <SelectItem value="received">Received</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Transfer #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">From</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">To</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Items</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {transfers.length === 0 ? (
                  <tr><td colSpan="7" className="px-4 py-12 text-center text-slate-500">No transfers found</td></tr>
                ) : (
                  transfers.map((transfer) => (
                    <tr key={transfer.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{transfer.transfer_number}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{transfer.from_warehouse_name}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{transfer.to_warehouse_name}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{transfer.items?.length || 0} items</td>
                      <td className="px-4 py-3">
                        <Badge className={statusColors[transfer.status]}>{transfer.status}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">
                        {transfer.created_at ? new Date(transfer.created_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {transfer.status === 'draft' && (
                            <Button variant="outline" size="sm" onClick={() => handleIssue(transfer.id)}>
                              <Truck className="h-4 w-4 mr-1" />Issue
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

// ==================== MAIN INVENTORY COMPONENT ====================
const Inventory = () => {
  return (
    <Routes>
      <Route index element={<InventoryDashboard />} />
      <Route path="items" element={<ItemsMaster />} />
      <Route path="warehouses" element={<WarehousesList />} />
      <Route path="stock" element={<StockBalance />} />
      <Route path="transfers" element={<StockTransfers />} />
    </Routes>
  );
};

export default Inventory;
