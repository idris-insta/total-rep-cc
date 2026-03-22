import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  Warehouse, Package, ArrowRightLeft, ClipboardList, AlertTriangle, TrendingUp,
  Plus, Search, Eye, Edit, Trash2, MoreVertical, RefreshCw, Building2, MapPin,
  Barcode, QrCode, FileText, Settings, ChevronRight, Box, IndianRupee
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../components/ui/dropdown-menu';
import api from '../lib/api';
import { toast } from 'sonner';

// ==================== WAREHOUSE DASHBOARD ====================
const WarehouseDashboard = () => {
  const navigate = useNavigate();
  const [warehouses, setWarehouses] = useState([]);
  const [consolidatedStock, setConsolidatedStock] = useState({ stock: [], totals: {} });
  const [pendingTransfers, setPendingTransfers] = useState([]);
  const [lowStockItems, setLowStockItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedWarehouse, setSelectedWarehouse] = useState('all');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [whRes, stockRes, transfersRes] = await Promise.all([
        api.get('/warehouse/warehouses'),
        api.get('/warehouse/consolidated-stock'),
        api.get('/warehouse/stock-transfers?status=in_transit')
      ]);
      
      setWarehouses(whRes.data);
      setConsolidatedStock(stockRes.data);
      setPendingTransfers(transfersRes.data);
      
      // Calculate low stock items
      const lowStock = (stockRes.data.stock || []).filter(item => {
        const reorderLevel = item.reorder_level || 10;
        return item.total_quantity < reorderLevel;
      });
      setLowStockItems(lowStock);
      
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      toast.error('Failed to load warehouse dashboard');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="warehouse-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope flex items-center gap-3">
            <Warehouse className="h-8 w-8 text-accent" />
            Warehouse Dashboard
          </h1>
          <p className="text-slate-600 mt-1 font-inter">Consolidated stock view across all GST locations</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchDashboardData}>
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button onClick={() => navigate('/inventory/warehouses/new')} className="bg-accent hover:bg-accent/90">
            <Plus className="h-4 w-4 mr-2" />Add Warehouse
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 font-inter">Total Warehouses</p>
                <p className="text-2xl font-bold text-slate-900">{warehouses.length}</p>
                <p className="text-xs text-slate-400 mt-1">GST Locations</p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Building2 className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 font-inter">Total Stock Value</p>
                <p className="text-2xl font-bold text-slate-900">{formatCurrency(consolidatedStock.totals?.total_value)}</p>
                <p className="text-xs text-slate-400 mt-1">{consolidatedStock.totals?.total_items || 0} SKUs</p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
                <IndianRupee className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 font-inter">Pending Transfers</p>
                <p className="text-2xl font-bold text-slate-900">{pendingTransfers.length}</p>
                <p className="text-xs text-slate-400 mt-1">In Transit</p>
              </div>
              <div className="h-12 w-12 bg-orange-100 rounded-lg flex items-center justify-center">
                <ArrowRightLeft className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-red-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 font-inter">Low Stock Alerts</p>
                <p className="text-2xl font-bold text-slate-900">{lowStockItems.length}</p>
                <p className="text-xs text-slate-400 mt-1">Below Reorder Level</p>
              </div>
              <div className="h-12 w-12 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Warehouse Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {warehouses.map((wh) => (
          <Card key={wh.id} className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate(`/inventory/warehouses/${wh.id}`)}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-10 w-10 bg-accent/10 rounded-lg flex items-center justify-center">
                    <Warehouse className="h-5 w-5 text-accent" />
                  </div>
                  <div>
                    <CardTitle className="text-base font-manrope">{wh.warehouse_name}</CardTitle>
                    <p className="text-xs text-slate-500">{wh.warehouse_code}</p>
                  </div>
                </div>
                <Badge className={wh.is_active !== false ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-800'}>
                  {wh.is_active !== false ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <MapPin className="h-4 w-4" />
                  <span>{wh.city}, {wh.state}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <FileText className="h-4 w-4" />
                  <span>GSTIN: {wh.gstin || 'Not Set'}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t">
                  <div className="text-center">
                    <p className="text-lg font-bold text-slate-900">{wh.stock_summary?.total_items || 0}</p>
                    <p className="text-xs text-slate-500">Items</p>
                  </div>
                  <div className="text-center">
                    <p className="text-lg font-bold text-slate-900">{formatCurrency(wh.stock_summary?.total_value)}</p>
                    <p className="text-xs text-slate-500">Value</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        
        {/* Add Warehouse Card */}
        <Card className="border-dashed border-2 hover:border-accent transition-colors cursor-pointer" onClick={() => navigate('/inventory/warehouses/new')}>
          <CardContent className="flex flex-col items-center justify-center h-full min-h-[200px] text-slate-400 hover:text-accent">
            <Plus className="h-12 w-12 mb-2" />
            <p className="font-medium">Add New Warehouse</p>
            <p className="text-sm">Setup a new GST location</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions & Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Low Stock Alerts */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-manrope flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                Low Stock Alerts
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => navigate('/inventory/stock-register')}>
                View All <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {lowStockItems.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <Package className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No low stock alerts</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {lowStockItems.slice(0, 10).map((item, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-red-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 bg-red-100 rounded flex items-center justify-center">
                        <Package className="h-4 w-4 text-red-600" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{item.item_name || item.item_code}</p>
                        <p className="text-xs text-slate-500">{item.item_code}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className="bg-red-100 text-red-800">{item.total_quantity} left</Badge>
                      <p className="text-xs text-slate-500 mt-1">Reorder: {item.reorder_level || 10}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pending Transfers */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-manrope flex items-center gap-2">
                <ArrowRightLeft className="h-5 w-5 text-orange-500" />
                Pending Transfers
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => navigate('/inventory/stock-transfers')}>
                View All <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {pendingTransfers.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <ArrowRightLeft className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No pending transfers</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[300px] overflow-y-auto">
                {pendingTransfers.slice(0, 10).map((transfer) => (
                  <div key={transfer.id} className="flex items-center justify-between p-2 bg-orange-50 rounded-lg">
                    <div>
                      <p className="font-medium text-sm">{transfer.transfer_no}</p>
                      <p className="text-xs text-slate-500">
                        {transfer.from_warehouse_name} → {transfer.to_warehouse_name}
                      </p>
                    </div>
                    <div className="text-right">
                      <Badge className="bg-orange-100 text-orange-800">In Transit</Badge>
                      <p className="text-xs text-slate-500 mt-1">{transfer.total_items} items</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Navigation */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-manrope">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => navigate('/inventory/stock-register')}>
              <ClipboardList className="h-6 w-6 text-blue-600" />
              <span className="text-sm">Stock Register</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => navigate('/inventory/stock-transfers/new')}>
              <ArrowRightLeft className="h-6 w-6 text-green-600" />
              <span className="text-sm">New Transfer</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => navigate('/inventory/stock-adjustments/new')}>
              <ClipboardList className="h-6 w-6 text-purple-600" />
              <span className="text-sm">Stock Adjustment</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => navigate('/inventory/serial-numbers')}>
              <FileText className="h-6 w-6 text-orange-600" />
              <span className="text-sm">Serial No Master</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => navigate('/inventory/batches')}>
              <Barcode className="h-6 w-6 text-teal-600" />
              <span className="text-sm">Batch Manager</span>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" onClick={() => navigate('/field-registry?module=inventory&entity=items')}>
              <Settings className="h-6 w-6 text-slate-600" />
              <span className="text-sm">Configure Fields</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default WarehouseDashboard;
