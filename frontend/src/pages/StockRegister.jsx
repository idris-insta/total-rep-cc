import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Package, Search, Filter, Download, RefreshCw, Warehouse, Eye,
  ChevronDown, ChevronRight, Barcode, Box, AlertTriangle, Settings
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import api from '../lib/api';
import { toast } from 'sonner';

const StockRegister = () => {
  const navigate = useNavigate();
  const [stockData, setStockData] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedWarehouse, setSelectedWarehouse] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('consolidated'); // 'consolidated' or 'warehouse'
  const [expandedItems, setExpandedItems] = useState({});
  const [selectedItem, setSelectedItem] = useState(null);
  const [ledgerData, setLedgerData] = useState(null);

  useEffect(() => {
    fetchData();
  }, [selectedWarehouse]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [stockRes, whRes] = await Promise.all([
        selectedWarehouse === 'all' 
          ? api.get('/warehouse/consolidated-stock')
          : api.get(`/warehouse/stock-register?warehouse_id=${selectedWarehouse}`),
        api.get('/warehouse/warehouses')
      ]);
      
      if (selectedWarehouse === 'all') {
        setStockData(stockRes.data.stock || []);
      } else {
        setStockData(stockRes.data || []);
      }
      setWarehouses(whRes.data);
    } catch (error) {
      console.error('Failed to load stock:', error);
      toast.error('Failed to load stock register');
    } finally {
      setLoading(false);
    }
  };

  const fetchItemLedger = async (itemId) => {
    try {
      const res = await api.get(`/warehouse/item-ledger/${itemId}${selectedWarehouse !== 'all' ? `?warehouse_id=${selectedWarehouse}` : ''}`);
      setLedgerData(res.data);
    } catch (error) {
      toast.error('Failed to load item ledger');
    }
  };

  const toggleExpand = (itemId) => {
    setExpandedItems(prev => ({
      ...prev,
      [itemId]: !prev[itemId]
    }));
  };

  const filteredStock = stockData.filter(item => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      item.item_code?.toLowerCase().includes(search) ||
      item.item_name?.toLowerCase().includes(search)
    );
  });

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0);
  };

  const getTotalValue = () => {
    return filteredStock.reduce((sum, item) => sum + (item.total_value || 0), 0);
  };

  const getTotalQuantity = () => {
    return filteredStock.reduce((sum, item) => sum + (item.total_quantity || 0), 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="stock-register">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope flex items-center gap-3">
            <Package className="h-8 w-8 text-accent" />
            Stock Register
          </h1>
          <p className="text-slate-600 mt-1 font-inter">View stock levels across all warehouses</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />Export
          </Button>
          <Button 
            variant="ghost" 
            onClick={() => window.open('/field-registry?module=inventory&entity=stock', '_blank')}
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search by item code or name..."
                className="pl-10"
              />
            </div>
            <Select value={selectedWarehouse} onValueChange={setSelectedWarehouse}>
              <SelectTrigger className="w-[200px]">
                <Warehouse className="h-4 w-4 mr-2" />
                <SelectValue placeholder="All Warehouses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Warehouses</SelectItem>
                {warehouses.map(wh => (
                  <SelectItem key={wh.id} value={wh.id}>{wh.warehouse_name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-slate-500">Total SKUs</p>
            <p className="text-2xl font-bold text-slate-900">{filteredStock.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-slate-500">Total Quantity</p>
            <p className="text-2xl font-bold text-slate-900">{getTotalQuantity().toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-slate-500">Total Value</p>
            <p className="text-2xl font-bold text-green-600">{formatCurrency(getTotalValue())}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-sm text-slate-500">Low Stock Items</p>
            <p className="text-2xl font-bold text-red-600">
              {filteredStock.filter(i => i.total_quantity < (i.reorder_level || 10)).length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Stock Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b">
                <tr>
                  <th className="text-left p-3 font-medium text-slate-700">Item Code</th>
                  <th className="text-left p-3 font-medium text-slate-700">Item Name</th>
                  <th className="text-right p-3 font-medium text-slate-700">Quantity</th>
                  <th className="text-right p-3 font-medium text-slate-700">Value</th>
                  <th className="text-center p-3 font-medium text-slate-700">Batches</th>
                  {selectedWarehouse === 'all' && (
                    <th className="text-center p-3 font-medium text-slate-700">Warehouses</th>
                  )}
                  <th className="text-center p-3 font-medium text-slate-700">Status</th>
                  <th className="text-center p-3 font-medium text-slate-700">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredStock.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-12 text-slate-400">
                      <Box className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>No stock data found</p>
                    </td>
                  </tr>
                ) : (
                  filteredStock.map((item) => (
                    <React.Fragment key={item._id?.item_id || item.item_id}>
                      <tr className="border-b hover:bg-slate-50">
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            {item.batches?.length > 0 && (
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                className="h-6 w-6 p-0"
                                onClick={() => toggleExpand(item._id?.item_id || item.item_id)}
                              >
                                {expandedItems[item._id?.item_id || item.item_id] ? 
                                  <ChevronDown className="h-4 w-4" /> : 
                                  <ChevronRight className="h-4 w-4" />
                                }
                              </Button>
                            )}
                            <code className="text-sm bg-slate-100 px-2 py-1 rounded">{item.item_code}</code>
                          </div>
                        </td>
                        <td className="p-3 font-medium">{item.item_name}</td>
                        <td className="p-3 text-right font-mono">{item.total_quantity?.toLocaleString()}</td>
                        <td className="p-3 text-right font-mono text-green-600">{formatCurrency(item.total_value)}</td>
                        <td className="p-3 text-center">
                          <Badge variant="outline">{item.batch_count || item.batches?.length || 0}</Badge>
                        </td>
                        {selectedWarehouse === 'all' && (
                          <td className="p-3 text-center">
                            <Badge variant="outline">{item.warehouse_stock?.length || 1}</Badge>
                          </td>
                        )}
                        <td className="p-3 text-center">
                          {item.total_quantity < (item.reorder_level || 10) ? (
                            <Badge className="bg-red-100 text-red-800">
                              <AlertTriangle className="h-3 w-3 mr-1" />Low Stock
                            </Badge>
                          ) : (
                            <Badge className="bg-green-100 text-green-800">In Stock</Badge>
                          )}
                        </td>
                        <td className="p-3 text-center">
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => {
                              setSelectedItem(item);
                              fetchItemLedger(item._id?.item_id || item.item_id);
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                      
                      {/* Expanded Batch Details */}
                      {expandedItems[item._id?.item_id || item.item_id] && item.batches && (
                        <tr>
                          <td colSpan={8} className="bg-slate-50 p-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                              {item.batches.map((batch, idx) => (
                                <div key={idx} className="flex items-center justify-between p-2 bg-white rounded border">
                                  <div className="flex items-center gap-2">
                                    <Barcode className="h-4 w-4 text-slate-400" />
                                    <span className="text-sm font-mono">{batch.batch_no || 'No Batch'}</span>
                                  </div>
                                  <div className="text-right">
                                    <span className="font-medium">{batch.quantity}</span>
                                    {batch.expiry_date && (
                                      <p className="text-xs text-slate-500">Exp: {batch.expiry_date}</p>
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                            
                            {/* Warehouse-wise breakdown */}
                            {item.warehouse_stock && item.warehouse_stock.length > 0 && (
                              <div className="mt-3 pt-3 border-t">
                                <p className="text-sm font-medium text-slate-700 mb-2">Warehouse Distribution:</p>
                                <div className="flex flex-wrap gap-2">
                                  {item.warehouse_stock.map((ws, idx) => (
                                    <Badge key={idx} variant="outline" className="text-sm">
                                      {ws.warehouse_name || ws.warehouse_code}: {ws.quantity}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Item Ledger Dialog */}
      <Dialog open={!!selectedItem} onOpenChange={() => { setSelectedItem(null); setLedgerData(null); }}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="font-manrope flex items-center gap-2">
              <Package className="h-5 w-5 text-accent" />
              Item Ledger: {selectedItem?.item_name}
            </DialogTitle>
          </DialogHeader>
          
          {ledgerData ? (
            <div className="space-y-4">
              {/* Item Summary */}
              <div className="grid grid-cols-3 gap-4">
                <Card>
                  <CardContent className="p-3 text-center">
                    <p className="text-sm text-slate-500">Item Code</p>
                    <p className="font-mono font-bold">{ledgerData.item?.item_code}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-3 text-center">
                    <p className="text-sm text-slate-500">Total In</p>
                    <p className="text-xl font-bold text-green-600">+{ledgerData.summary?.total_in || 0}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-3 text-center">
                    <p className="text-sm text-slate-500">Total Out</p>
                    <p className="text-xl font-bold text-red-600">-{ledgerData.summary?.total_out || 0}</p>
                  </CardContent>
                </Card>
              </div>

              {/* Movement History */}
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="text-left p-2 text-sm font-medium">Date</th>
                      <th className="text-left p-2 text-sm font-medium">Type</th>
                      <th className="text-left p-2 text-sm font-medium">Document</th>
                      <th className="text-left p-2 text-sm font-medium">Warehouse</th>
                      <th className="text-right p-2 text-sm font-medium">In</th>
                      <th className="text-right p-2 text-sm font-medium">Out</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(ledgerData.movements || []).length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-center py-8 text-slate-400">No movements found</td>
                      </tr>
                    ) : (
                      ledgerData.movements.map((mov, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="p-2 text-sm">{mov.date?.split('T')[0]}</td>
                          <td className="p-2">
                            <Badge variant="outline" className="text-xs">{mov.type}</Badge>
                          </td>
                          <td className="p-2 text-sm font-mono">{mov.doc_no}</td>
                          <td className="p-2 text-sm">{mov.warehouse}</td>
                          <td className="p-2 text-right text-green-600 font-medium">
                            {mov.in_qty > 0 ? `+${mov.in_qty}` : '-'}
                          </td>
                          <td className="p-2 text-right text-red-600 font-medium">
                            {mov.out_qty > 0 ? `-${mov.out_qty}` : '-'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-accent" />
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default StockRegister;
