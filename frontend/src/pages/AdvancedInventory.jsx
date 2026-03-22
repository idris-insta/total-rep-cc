import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { 
  Package, Barcode, MapPin, AlertTriangle, Clock, RefreshCw, Plus, 
  Search, Layers, QrCode, Calendar, TrendingDown, ShoppingCart,
  Archive, CheckCircle, XCircle, Box, Warehouse, Tag
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const AdvancedInventory = () => {
  const [loading, setLoading] = useState(true);
  const [batches, setBatches] = useState([]);
  const [serialNumbers, setSerialNumbers] = useState([]);
  const [binLocations, setBinLocations] = useState([]);
  const [reorderAlerts, setReorderAlerts] = useState([]);
  const [stockAging, setStockAging] = useState(null);
  const [stockValuation, setStockValuation] = useState(null);
  const [expiringBatches, setExpiringBatches] = useState([]);
  const [items, setItems] = useState([]);
  const [warehouses, setWarehouses] = useState([]);

  // Dialog states
  const [batchDialogOpen, setBatchDialogOpen] = useState(false);
  const [serialDialogOpen, setSerialDialogOpen] = useState(false);
  const [binDialogOpen, setBinDialogOpen] = useState(false);
  const [barcodeSearch, setBarcodeSearch] = useState('');
  const [barcodeResult, setBarcodeResult] = useState(null);

  // Forms
  const [batchForm, setBatchForm] = useState({
    item_id: '', warehouse_id: '', batch_number: '', manufacturing_date: '',
    expiry_date: '', quantity: '', unit_cost: '', supplier_batch: ''
  });
  const [serialForm, setSerialForm] = useState({
    item_id: '', quantity: 1, prefix: ''
  });
  const [binForm, setBinForm] = useState({
    warehouse_id: '', aisle: '', rack: '', shelf: '', bin_type: 'picking', max_capacity: 100
  });

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [
        batchesRes, binRes, alertsRes, agingRes, valuationRes, expiringRes, itemsRes, warehousesRes
      ] = await Promise.all([
        api.get('/inventory-advanced/batches').catch(() => ({ data: [] })),
        api.get('/inventory-advanced/bin-locations').catch(() => ({ data: [] })),
        api.get('/inventory-advanced/reorder-alerts').catch(() => ({ data: { alerts: [] } })),
        api.get('/inventory-advanced/stock-aging').catch(() => ({ data: null })),
        api.get('/inventory-advanced/stock-valuation').catch(() => ({ data: null })),
        api.get('/inventory-advanced/batches/expiring?days=30').catch(() => ({ data: [] })),
        api.get('/inventory/items').catch(() => ({ data: [] })),
        api.get('/inventory/warehouses').catch(() => ({ data: [] }))
      ]);

      setBatches(batchesRes.data || []);
      setBinLocations(binRes.data || []);
      setReorderAlerts(alertsRes.data?.alerts || []);
      setStockAging(agingRes.data);
      setStockValuation(valuationRes.data);
      setExpiringBatches(expiringRes.data || []);
      setItems(itemsRes.data || []);
      setWarehouses(warehousesRes.data || []);
    } catch (error) {
      toast.error('Failed to load inventory data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBatch = async (e) => {
    e.preventDefault();
    try {
      await api.post('/inventory-advanced/batches', {
        ...batchForm,
        quantity: parseFloat(batchForm.quantity),
        unit_cost: parseFloat(batchForm.unit_cost)
      });
      toast.success('Batch created successfully');
      setBatchDialogOpen(false);
      setBatchForm({ item_id: '', warehouse_id: '', batch_number: '', manufacturing_date: '', expiry_date: '', quantity: '', unit_cost: '', supplier_batch: '' });
      fetchAllData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create batch');
    }
  };

  const handleGenerateSerials = async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/inventory-advanced/serial-numbers', {
        item_id: serialForm.item_id,
        quantity: parseInt(serialForm.quantity),
        prefix: serialForm.prefix || undefined
      });
      toast.success(`Generated ${res.data.created} serial numbers`);
      setSerialDialogOpen(false);
      setSerialForm({ item_id: '', quantity: 1, prefix: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate serial numbers');
    }
  };

  const handleCreateBin = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/inventory-advanced/bin-locations?warehouse_id=${binForm.warehouse_id}&aisle=${binForm.aisle}&rack=${binForm.rack}&shelf=${binForm.shelf}&bin_type=${binForm.bin_type}&max_capacity=${binForm.max_capacity}`);
      toast.success('Bin location created');
      setBinDialogOpen(false);
      setBinForm({ warehouse_id: '', aisle: '', rack: '', shelf: '', bin_type: 'picking', max_capacity: 100 });
      fetchAllData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create bin location');
    }
  };

  const handleBarcodeLookup = async () => {
    if (!barcodeSearch) return;
    try {
      const res = await api.get(`/inventory-advanced/barcode/lookup/${barcodeSearch}`);
      setBarcodeResult(res.data);
      toast.success('Item found!');
    } catch (error) {
      toast.error('Item not found for this barcode');
      setBarcodeResult(null);
    }
  };

  const handleCreatePOFromAlert = async (alert) => {
    // This would typically show a dialog to select supplier
    toast.info('PO creation from reorder alert - Select supplier to proceed');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount || 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6" data-testid="advanced-inventory">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope">Advanced Inventory</h1>
          <p className="text-slate-600 mt-1">Batch tracking, Serial numbers, Bin locations & Reorder management</p>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={fetchAllData} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Layers className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Active Batches</p>
                <p className="text-2xl font-bold">{batches.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <MapPin className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Bin Locations</p>
                <p className="text-2xl font-bold">{binLocations.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Reorder Alerts</p>
                <p className="text-2xl font-bold">{reorderAlerts.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-red-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <Clock className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Expiring (30d)</p>
                <p className="text-2xl font-bold">{expiringBatches.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingDown className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Stock Value</p>
                <p className="text-xl font-bold">{formatCurrency(stockValuation?.total_value)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Barcode Scanner */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-slate-100 rounded-lg">
              <QrCode className="h-6 w-6 text-slate-600" />
            </div>
            <div className="flex-1">
              <Label className="text-sm font-medium">Barcode / Item Code Lookup</Label>
              <div className="flex gap-2 mt-1">
                <Input 
                  placeholder="Scan or enter barcode/item code..." 
                  value={barcodeSearch}
                  onChange={(e) => setBarcodeSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleBarcodeLookup()}
                  className="max-w-md"
                />
                <Button onClick={handleBarcodeLookup}>
                  <Search className="h-4 w-4 mr-2" />Search
                </Button>
              </div>
            </div>
            {barcodeResult && (
              <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                <p className="font-semibold text-green-800">{barcodeResult.item_name}</p>
                <p className="text-sm text-green-600">Code: {barcodeResult.item_code} | Stock: {barcodeResult.current_stock}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs defaultValue="batches" className="space-y-4">
        <TabsList className="grid grid-cols-5 w-full max-w-3xl">
          <TabsTrigger value="batches" className="gap-2">
            <Layers className="h-4 w-4" />Batches
          </TabsTrigger>
          <TabsTrigger value="bins" className="gap-2">
            <MapPin className="h-4 w-4" />Bin Locations
          </TabsTrigger>
          <TabsTrigger value="reorder" className="gap-2">
            <ShoppingCart className="h-4 w-4" />Reorder
          </TabsTrigger>
          <TabsTrigger value="aging" className="gap-2">
            <Clock className="h-4 w-4" />Stock Aging
          </TabsTrigger>
          <TabsTrigger value="valuation" className="gap-2">
            <TrendingDown className="h-4 w-4" />Valuation
          </TabsTrigger>
        </TabsList>

        {/* Batches Tab */}
        <TabsContent value="batches">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Batch Tracking</CardTitle>
                <div className="flex gap-2">
                  <Dialog open={serialDialogOpen} onOpenChange={setSerialDialogOpen}>
                    <DialogTrigger asChild>
                      <Button variant="outline">
                        <Barcode className="h-4 w-4 mr-2" />Generate Serial Numbers
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Generate Serial Numbers</DialogTitle>
                      </DialogHeader>
                      <form onSubmit={handleGenerateSerials} className="space-y-4">
                        <div className="space-y-2">
                          <Label>Item</Label>
                          <Select value={serialForm.item_id} onValueChange={(v) => setSerialForm({...serialForm, item_id: v})}>
                            <SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger>
                            <SelectContent>
                              {items.map(item => (
                                <SelectItem key={item.id} value={item.id}>{item.item_code} - {item.item_name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Quantity</Label>
                            <Input type="number" min="1" value={serialForm.quantity} onChange={(e) => setSerialForm({...serialForm, quantity: e.target.value})} />
                          </div>
                          <div className="space-y-2">
                            <Label>Prefix (optional)</Label>
                            <Input placeholder="SN-" value={serialForm.prefix} onChange={(e) => setSerialForm({...serialForm, prefix: e.target.value})} />
                          </div>
                        </div>
                        <DialogFooter>
                          <Button type="submit" className="bg-accent">Generate</Button>
                        </DialogFooter>
                      </form>
                    </DialogContent>
                  </Dialog>
                  
                  <Dialog open={batchDialogOpen} onOpenChange={setBatchDialogOpen}>
                    <DialogTrigger asChild>
                      <Button className="bg-accent hover:bg-accent/90">
                        <Plus className="h-4 w-4 mr-2" />Create Batch
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-lg">
                      <DialogHeader>
                        <DialogTitle>Create New Batch</DialogTitle>
                      </DialogHeader>
                      <form onSubmit={handleCreateBatch} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Item *</Label>
                            <Select value={batchForm.item_id} onValueChange={(v) => setBatchForm({...batchForm, item_id: v})}>
                              <SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger>
                              <SelectContent>
                                {items.map(item => (
                                  <SelectItem key={item.id} value={item.id}>{item.item_code} - {item.item_name}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div className="space-y-2">
                            <Label>Warehouse *</Label>
                            <Select value={batchForm.warehouse_id} onValueChange={(v) => setBatchForm({...batchForm, warehouse_id: v})}>
                              <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                              <SelectContent>
                                {warehouses.map(wh => (
                                  <SelectItem key={wh.id} value={wh.id}>{wh.warehouse_name}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Batch Number *</Label>
                            <Input value={batchForm.batch_number} onChange={(e) => setBatchForm({...batchForm, batch_number: e.target.value})} required />
                          </div>
                          <div className="space-y-2">
                            <Label>Supplier Batch</Label>
                            <Input value={batchForm.supplier_batch} onChange={(e) => setBatchForm({...batchForm, supplier_batch: e.target.value})} />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Manufacturing Date</Label>
                            <Input type="date" value={batchForm.manufacturing_date} onChange={(e) => setBatchForm({...batchForm, manufacturing_date: e.target.value})} />
                          </div>
                          <div className="space-y-2">
                            <Label>Expiry Date</Label>
                            <Input type="date" value={batchForm.expiry_date} onChange={(e) => setBatchForm({...batchForm, expiry_date: e.target.value})} />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label>Quantity *</Label>
                            <Input type="number" step="0.01" value={batchForm.quantity} onChange={(e) => setBatchForm({...batchForm, quantity: e.target.value})} required />
                          </div>
                          <div className="space-y-2">
                            <Label>Unit Cost *</Label>
                            <Input type="number" step="0.01" value={batchForm.unit_cost} onChange={(e) => setBatchForm({...batchForm, unit_cost: e.target.value})} required />
                          </div>
                        </div>
                        <DialogFooter>
                          <Button type="submit" className="bg-accent">Create Batch</Button>
                        </DialogFooter>
                      </form>
                    </DialogContent>
                  </Dialog>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {batches.length > 0 ? (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="px-4 py-3 text-left">Batch #</th>
                        <th className="px-4 py-3 text-left">Item</th>
                        <th className="px-4 py-3 text-left">Warehouse</th>
                        <th className="px-4 py-3 text-right">Quantity</th>
                        <th className="px-4 py-3 text-left">Mfg Date</th>
                        <th className="px-4 py-3 text-left">Expiry</th>
                        <th className="px-4 py-3 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {batches.map((batch, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-4 py-3 font-mono font-medium">{batch.batch_number}</td>
                          <td className="px-4 py-3">{batch.item_name || batch.item_code}</td>
                          <td className="px-4 py-3">{batch.warehouse_name || '-'}</td>
                          <td className="px-4 py-3 text-right">{batch.current_quantity?.toLocaleString()}</td>
                          <td className="px-4 py-3">{batch.manufacturing_date || '-'}</td>
                          <td className="px-4 py-3">
                            {batch.expiry_date ? (
                              <span className={new Date(batch.expiry_date) < new Date(Date.now() + 30*24*60*60*1000) ? 'text-red-600 font-medium' : ''}>
                                {batch.expiry_date}
                              </span>
                            ) : '-'}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <Badge variant={batch.status === 'active' ? 'default' : 'secondary'}>{batch.status}</Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <Layers className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No batches found. Create your first batch.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Bin Locations Tab */}
        <TabsContent value="bins">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Bin Location Management</CardTitle>
                <Dialog open={binDialogOpen} onOpenChange={setBinDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="bg-accent hover:bg-accent/90">
                      <Plus className="h-4 w-4 mr-2" />Add Bin Location
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Create Bin Location</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleCreateBin} className="space-y-4">
                      <div className="space-y-2">
                        <Label>Warehouse</Label>
                        <Select value={binForm.warehouse_id} onValueChange={(v) => setBinForm({...binForm, warehouse_id: v})}>
                          <SelectTrigger><SelectValue placeholder="Select warehouse" /></SelectTrigger>
                          <SelectContent>
                            {warehouses.map(wh => (
                              <SelectItem key={wh.id} value={wh.id}>{wh.warehouse_name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <Label>Aisle</Label>
                          <Input placeholder="A" value={binForm.aisle} onChange={(e) => setBinForm({...binForm, aisle: e.target.value.toUpperCase()})} required />
                        </div>
                        <div className="space-y-2">
                          <Label>Rack</Label>
                          <Input placeholder="01" value={binForm.rack} onChange={(e) => setBinForm({...binForm, rack: e.target.value})} required />
                        </div>
                        <div className="space-y-2">
                          <Label>Shelf</Label>
                          <Input placeholder="01" value={binForm.shelf} onChange={(e) => setBinForm({...binForm, shelf: e.target.value})} required />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Bin Type</Label>
                          <Select value={binForm.bin_type} onValueChange={(v) => setBinForm({...binForm, bin_type: v})}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="picking">Picking</SelectItem>
                              <SelectItem value="bulk">Bulk Storage</SelectItem>
                              <SelectItem value="reserve">Reserve</SelectItem>
                              <SelectItem value="staging">Staging</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Max Capacity</Label>
                          <Input type="number" value={binForm.max_capacity} onChange={(e) => setBinForm({...binForm, max_capacity: e.target.value})} />
                        </div>
                      </div>
                      <DialogFooter>
                        <Button type="submit" className="bg-accent">Create Bin</Button>
                      </DialogFooter>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {binLocations.length > 0 ? (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                  {binLocations.map((bin, idx) => (
                    <div key={idx} className="p-4 border rounded-lg hover:border-accent transition-colors cursor-pointer">
                      <div className="flex items-center gap-2 mb-2">
                        <Box className="h-5 w-5 text-slate-400" />
                        <span className="font-mono font-semibold">{bin.bin_code}</span>
                      </div>
                      <div className="space-y-1 text-xs text-slate-500">
                        <p>Type: <span className="capitalize">{bin.bin_type}</span></p>
                        <p>Capacity: {bin.current_capacity}/{bin.max_capacity}</p>
                      </div>
                      <div className="mt-2">
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-accent rounded-full transition-all"
                            style={{ width: `${(bin.current_capacity / bin.max_capacity) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <Warehouse className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No bin locations configured. Add your first bin.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reorder Alerts Tab */}
        <TabsContent value="reorder">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-orange-500" />
                Reorder Alerts ({reorderAlerts.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {reorderAlerts.length > 0 ? (
                <div className="space-y-3">
                  {reorderAlerts.map((alert, idx) => (
                    <div key={idx} className={`p-4 rounded-lg border ${alert.urgency === 'critical' ? 'bg-red-50 border-red-200' : 'bg-orange-50 border-orange-200'}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${alert.urgency === 'critical' ? 'bg-red-100' : 'bg-orange-100'}`}>
                            {alert.urgency === 'critical' ? (
                              <XCircle className="h-5 w-5 text-red-600" />
                            ) : (
                              <AlertTriangle className="h-5 w-5 text-orange-600" />
                            )}
                          </div>
                          <div>
                            <p className="font-semibold">{alert.item_name}</p>
                            <p className="text-sm text-slate-600">Code: {alert.item_code}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge variant={alert.urgency === 'critical' ? 'destructive' : 'warning'}>
                            {alert.urgency}
                          </Badge>
                        </div>
                      </div>
                      <div className="mt-3 grid grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-slate-500">Current Stock</p>
                          <p className="font-semibold text-lg">{alert.current_stock}</p>
                        </div>
                        <div>
                          <p className="text-slate-500">Reorder Level</p>
                          <p className="font-semibold text-lg">{alert.reorder_level}</p>
                        </div>
                        <div>
                          <p className="text-slate-500">Safety Stock</p>
                          <p className="font-semibold text-lg">{alert.safety_stock}</p>
                        </div>
                        <div>
                          <p className="text-slate-500">Suggested Order</p>
                          <p className="font-semibold text-lg text-accent">{alert.suggested_qty}</p>
                        </div>
                      </div>
                      <div className="mt-3 flex justify-end">
                        <Button size="sm" onClick={() => handleCreatePOFromAlert(alert)}>
                          <ShoppingCart className="h-4 w-4 mr-2" />Create PO
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-300" />
                  <p>All stock levels are healthy. No reorder needed.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Stock Aging Tab */}
        <TabsContent value="aging">
          <Card>
            <CardHeader>
              <CardTitle>Stock Aging Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              {stockAging ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-5 gap-4">
                    {Object.entries(stockAging.aging_buckets || {}).map(([key, bucket]) => {
                      const labels = {
                        '0_30_days': '0-30 Days',
                        '31_60_days': '31-60 Days',
                        '61_90_days': '61-90 Days',
                        '91_180_days': '91-180 Days',
                        'over_180_days': '180+ Days'
                      };
                      const colors = {
                        '0_30_days': 'bg-green-50 border-green-200 text-green-700',
                        '31_60_days': 'bg-blue-50 border-blue-200 text-blue-700',
                        '61_90_days': 'bg-yellow-50 border-yellow-200 text-yellow-700',
                        '91_180_days': 'bg-orange-50 border-orange-200 text-orange-700',
                        'over_180_days': 'bg-red-50 border-red-200 text-red-700'
                      };
                      return (
                        <div key={key} className={`p-4 rounded-lg border ${colors[key]}`}>
                          <p className="text-sm font-medium">{labels[key]}</p>
                          <p className="text-2xl font-bold mt-1">{bucket.count}</p>
                          <p className="text-sm mt-1">{formatCurrency(bucket.value)}</p>
                        </div>
                      );
                    })}
                  </div>
                  <div className="text-sm text-slate-600">
                    <p>Total Batches: {stockAging.total_batches} | Total Value: {formatCurrency(stockAging.total_value)}</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <Clock className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No stock aging data available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Stock Valuation Tab */}
        <TabsContent value="valuation">
          <Card>
            <CardHeader>
              <CardTitle>Stock Valuation ({stockValuation?.valuation_method || 'Weighted Average'})</CardTitle>
            </CardHeader>
            <CardContent>
              {stockValuation?.items?.length > 0 ? (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="px-4 py-3 text-left">Item Code</th>
                        <th className="px-4 py-3 text-left">Item Name</th>
                        <th className="px-4 py-3 text-right">Quantity</th>
                        <th className="px-4 py-3 text-right">Avg Cost</th>
                        <th className="px-4 py-3 text-right">Total Value</th>
                        <th className="px-4 py-3 text-center">Batches</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stockValuation.items.slice(0, 20).map((item, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-4 py-3 font-mono">{item.item_code}</td>
                          <td className="px-4 py-3">{item.item_name}</td>
                          <td className="px-4 py-3 text-right">{item.quantity?.toLocaleString()}</td>
                          <td className="px-4 py-3 text-right">{formatCurrency(item.avg_cost)}</td>
                          <td className="px-4 py-3 text-right font-semibold">{formatCurrency(item.total_value)}</td>
                          <td className="px-4 py-3 text-center">{item.batch_count}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="bg-slate-50 font-semibold">
                      <tr>
                        <td colSpan={4} className="px-4 py-3 text-right">Total Stock Value:</td>
                        <td className="px-4 py-3 text-right text-lg">{formatCurrency(stockValuation.total_value)}</td>
                        <td className="px-4 py-3 text-center">{stockValuation.total_items} items</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <Archive className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No stock valuation data available</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdvancedInventory;
