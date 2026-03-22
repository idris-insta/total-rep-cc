import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { 
  Plus, Search, Edit, Eye, Factory, Settings, Play, Pause, CheckCircle,
  Clock, AlertTriangle, RefreshCw, Download, BarChart3, TrendingUp,
  Package, Cog, Calendar, Zap, Activity, Target
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Progress } from '../components/ui/progress';
import api from '../lib/api';
import { toast } from 'sonner';
import ItemSearchSelect from '../components/ItemSearchSelect';

// ==================== PRODUCTION DASHBOARD ====================
const ProductionDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_work_orders: 0, in_progress: 0, completed: 0, planned: 0,
    total_machines: 0, active_machines: 0, today_output: 0, wastage_percent: 0
  });
  const [loading, setLoading] = useState(true);
  const [recentWOs, setRecentWOs] = useState([]);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [workOrdersRes, machinesRes, wastageRes] = await Promise.all([
        api.get('/production/work-orders'),
        api.get('/production/machines'),
        api.get('/production/analytics/wastage')
      ]);
      
      const wos = workOrdersRes.data;
      const machines = machinesRes.data;
      
      setStats({
        total_work_orders: wos.length,
        in_progress: wos.filter(w => w.status === 'in_progress').length,
        completed: wos.filter(w => w.status === 'completed').length,
        planned: wos.filter(w => w.status === 'planned').length,
        total_machines: machines.length,
        active_machines: machines.filter(m => m.status === 'active').length,
        today_output: wos.reduce((sum, w) => sum + (w.quantity_made || 0), 0),
        wastage_percent: wastageRes.data.length > 0 
          ? (wastageRes.data.reduce((sum, w) => sum + (w.wastage_percentage || 0), 0) / wastageRes.data.length).toFixed(1)
          : 0
      });
      setRecentWOs(wos.slice(0, 5));
    } catch (error) {
      console.error('Failed to load production stats', error);
    } finally {
      setLoading(false);
    }
  };

  const statusColors = {
    planned: 'bg-slate-100 text-slate-800',
    in_progress: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    on_hold: 'bg-yellow-100 text-yellow-800'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="production-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Production Dashboard</h2>
          <p className="text-slate-600 mt-1 font-inter">Work orders, machine management & output tracking</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/production/work-orders')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Factory className="h-6 w-6 text-blue-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">{stats.total_work_orders}</div>
                <p className="text-sm text-slate-500">Work Orders</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-yellow-100 flex items-center justify-center">
                <Activity className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-yellow-600">{stats.in_progress}</div>
                <p className="text-sm text-slate-500">In Progress</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/production/machines')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-purple-100 flex items-center justify-center">
                <Cog className="h-6 w-6 text-purple-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-purple-600">{stats.active_machines}/{stats.total_machines}</div>
                <p className="text-sm text-slate-500">Active Machines</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-red-100 flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-red-600">{stats.wastage_percent}%</div>
                <p className="text-sm text-slate-500">Avg Wastage</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Work Order Status Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="font-manrope">Work Order Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-slate-400"></div>
                  <span className="text-sm text-slate-600">Planned</span>
                </div>
                <span className="font-semibold">{stats.planned}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-blue-500"></div>
                  <span className="text-sm text-slate-600">In Progress</span>
                </div>
                <span className="font-semibold">{stats.in_progress}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-green-500"></div>
                  <span className="text-sm text-slate-600">Completed</span>
                </div>
                <span className="font-semibold">{stats.completed}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-manrope">Recent Work Orders</CardTitle>
            <Button variant="outline" size="sm" onClick={() => navigate('/production/work-orders')}>View All</Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentWOs.length === 0 ? (
                <p className="text-center text-slate-500 py-4">No work orders yet</p>
              ) : (
                recentWOs.map((wo) => (
                  <div key={wo.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50">
                    <div>
                      <p className="font-semibold text-slate-900 font-mono">{wo.wo_number}</p>
                      <p className="text-sm text-slate-500">{wo.machine_id}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-mono">{wo.quantity_made}/{wo.quantity_to_make}</p>
                      <Badge className={statusColors[wo.status]}>{wo.status?.replace('_', ' ')}</Badge>
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
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/production/work-orders')}>
              <Factory className="h-6 w-6" />
              <span>Work Orders</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/production/machines')}>
              <Cog className="h-6 w-6" />
              <span>Machines</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/production/entries')}>
              <Package className="h-6 w-6" />
              <span>Production Entry</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/production/analytics')}>
              <BarChart3 className="h-6 w-6" />
              <span>Analytics</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== WORK ORDERS LIST ====================
const WorkOrdersList = () => {
  const [workOrders, setWorkOrders] = useState([]);
  const [machines, setMachines] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({ status: 'all', machine_id: 'all' });
  const [formData, setFormData] = useState({
    sales_order_id: '', item_id: '', quantity_to_make: '',
    machine_id: '', thickness: '', color: '', width: '', length: '',
    brand: '', priority: 'normal'
  });

  useEffect(() => { fetchData(); }, [filters]);

  const fetchData = async () => {
    try {
      let url = '/production/work-orders?';
      if (filters.status !== 'all') url += `status=${filters.status}&`;
      if (filters.machine_id !== 'all') url += `machine_id=${filters.machine_id}&`;

      const [wosRes, machinesRes, itemsRes] = await Promise.all([
        api.get(url),
        api.get('/production/machines'),
        api.get('/inventory/items')
      ]);
      setWorkOrders(wosRes.data);
      setMachines(machinesRes.data);
      setItems(itemsRes.data);
    } catch (error) {
      toast.error('Failed to load work orders');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        quantity_to_make: parseFloat(formData.quantity_to_make) || 0,
        thickness: formData.thickness ? parseFloat(formData.thickness) : null,
        width: formData.width ? parseFloat(formData.width) : null,
        length: formData.length ? parseFloat(formData.length) : null
      };
      await api.post('/production/work-orders', payload);
      toast.success('Work order created');
      setOpen(false);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create work order');
    }
  };

  const handleStart = async (woId) => {
    try {
      await api.put(`/production/work-orders/${woId}/start`);
      toast.success('Work order started');
      fetchData();
    } catch (error) {
      toast.error('Failed to start work order');
    }
  };

  const resetForm = () => {
    setFormData({
      sales_order_id: '', item_id: '', quantity_to_make: '',
      machine_id: '', thickness: '', color: '', width: '', length: '',
      brand: '', priority: 'normal'
    });
  };

  const statusColors = {
    planned: 'bg-slate-100 text-slate-800',
    in_progress: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    on_hold: 'bg-yellow-100 text-yellow-800'
  };

  const priorityColors = {
    low: 'bg-slate-100 text-slate-800',
    normal: 'bg-blue-100 text-blue-800',
    high: 'bg-orange-100 text-orange-800',
    urgent: 'bg-red-100 text-red-800'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="work-orders-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Work Orders</h2>
          <p className="text-slate-600 mt-1 font-inter">{workOrders.length} work orders</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="create-wo-button">
              <Plus className="h-4 w-4 mr-2" />Create Work Order
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-manrope">Create Work Order</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Sales Order (Optional)</Label>
                  <Input value={formData.sales_order_id} onChange={(e) => setFormData({...formData, sales_order_id: e.target.value})} placeholder="SO-001" />
                </div>
                <div className="space-y-2">
                  <Label>Item *</Label>
                  <ItemSearchSelect
                    value={formData.item_id}
                    onChange={(item) => {
                      if (item) {
                        setFormData({
                          ...formData,
                          item_id: item.id,
                          thickness: item.specifications?.thickness || formData.thickness,
                          width: item.specifications?.width || formData.width,
                          length: item.specifications?.length || formData.length,
                          color: item.specifications?.color || formData.color,
                          brand: item.brand || formData.brand
                        });
                      } else {
                        setFormData({...formData, item_id: ''});
                      }
                    }}
                    placeholder="Search items..."
                  />
                </div>
                <div className="space-y-2">
                  <Label>Quantity *</Label>
                  <Input type="number" value={formData.quantity_to_make} onChange={(e) => setFormData({...formData, quantity_to_make: e.target.value})} required />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Machine *</Label>
                  <Select value={formData.machine_id} onValueChange={(v) => setFormData({...formData, machine_id: v})}>
                    <SelectTrigger><SelectValue placeholder="Select machine" /></SelectTrigger>
                    <SelectContent>
                      {machines.map(m => (
                        <SelectItem key={m.id} value={m.id}>{m.machine_code} - {m.machine_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Priority</Label>
                  <Select value={formData.priority} onValueChange={(v) => setFormData({...formData, priority: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="normal">Normal</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="urgent">Urgent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Brand</Label>
                  <Input value={formData.brand} onChange={(e) => setFormData({...formData, brand: e.target.value})} />
                </div>
              </div>

              <div className="grid grid-cols-4 gap-4">
                <div className="space-y-2">
                  <Label>Thickness (micron)</Label>
                  <Input type="number" step="0.1" value={formData.thickness} onChange={(e) => setFormData({...formData, thickness: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Width (mm)</Label>
                  <Input type="number" value={formData.width} onChange={(e) => setFormData({...formData, width: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Length (m)</Label>
                  <Input type="number" value={formData.length} onChange={(e) => setFormData({...formData, length: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Color</Label>
                  <Select value={formData.color} onValueChange={(v) => setFormData({...formData, color: v})}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Transparent">Transparent</SelectItem>
                      <SelectItem value="Brown">Brown</SelectItem>
                      <SelectItem value="White">White</SelectItem>
                      <SelectItem value="Black">Black</SelectItem>
                      <SelectItem value="Custom">Custom</SelectItem>
                    </SelectContent>
                  </Select>
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

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={filters.status} onValueChange={(v) => setFilters({...filters, status: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="planned">Planned</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters.machine_id} onValueChange={(v) => setFilters({...filters, machine_id: v})}>
          <SelectTrigger className="w-[180px]"><SelectValue placeholder="Machine" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Machines</SelectItem>
            {machines.map(m => (
              <SelectItem key={m.id} value={m.id}>{m.machine_code}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Work Orders Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">WO Number</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Item</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Specs</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Machine</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Progress</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Priority</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {workOrders.length === 0 ? (
                  <tr><td colSpan="8" className="px-4 py-12 text-center text-slate-500">No work orders found</td></tr>
                ) : (
                  workOrders.map((wo) => {
                    const progress = wo.quantity_to_make > 0 ? (wo.quantity_made / wo.quantity_to_make) * 100 : 0;
                    return (
                      <tr key={wo.id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{wo.wo_number}</td>
                        <td className="px-4 py-3 text-sm text-slate-900">{wo.item_id}</td>
                        <td className="px-4 py-3 text-sm text-slate-600 font-mono">
                          {wo.thickness && `${wo.thickness}µ`}
                          {wo.width && ` × ${wo.width}mm`}
                          {wo.length && ` × ${wo.length}m`}
                        </td>
                        <td className="px-4 py-3 text-sm text-slate-600">{wo.machine_id}</td>
                        <td className="px-4 py-3">
                          <div className="w-32">
                            <div className="flex justify-between text-xs mb-1">
                              <span>{wo.quantity_made}/{wo.quantity_to_make}</span>
                              <span>{progress.toFixed(0)}%</span>
                            </div>
                            <Progress value={progress} className="h-2" />
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge className={priorityColors[wo.priority]}>{wo.priority}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          <Badge className={statusColors[wo.status]}>{wo.status?.replace('_', ' ')}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex gap-1">
                            <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
                            {wo.status === 'planned' && (
                              <Button variant="outline" size="sm" onClick={() => handleStart(wo.id)} className="text-green-600">
                                <Play className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </td>
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

// ==================== MACHINES LIST ====================
const MachinesList = () => {
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    machine_code: '', machine_name: '', machine_type: 'Slitting',
    capacity: '', location: 'BWD'
  });

  useEffect(() => { fetchMachines(); }, []);

  const fetchMachines = async () => {
    try {
      const response = await api.get('/production/machines');
      setMachines(response.data);
    } catch (error) {
      toast.error('Failed to load machines');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/production/machines', {
        ...formData,
        capacity: parseFloat(formData.capacity) || 0
      });
      toast.success('Machine added');
      setOpen(false);
      fetchMachines();
      setFormData({ machine_code: '', machine_name: '', machine_type: 'Slitting', capacity: '', location: 'BWD' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add machine');
    }
  };

  const typeIcons = {
    Slitting: <Settings className="h-5 w-5" />,
    Coating: <Factory className="h-5 w-5" />,
    Rewinding: <RefreshCw className="h-5 w-5" />,
    Printing: <Target className="h-5 w-5" />
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="machines-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Machines</h2>
          <p className="text-slate-600 mt-1 font-inter">{machines.length} machines</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90">
              <Plus className="h-4 w-4 mr-2" />Add Machine
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Machine</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Machine Code *</Label>
                  <Input value={formData.machine_code} onChange={(e) => setFormData({...formData, machine_code: e.target.value})} placeholder="SLIT-001" required />
                </div>
                <div className="space-y-2">
                  <Label>Machine Name *</Label>
                  <Input value={formData.machine_name} onChange={(e) => setFormData({...formData, machine_name: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label>Machine Type *</Label>
                  <Select value={formData.machine_type} onValueChange={(v) => setFormData({...formData, machine_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Slitting">Slitting</SelectItem>
                      <SelectItem value="Coating">Coating</SelectItem>
                      <SelectItem value="Rewinding">Rewinding</SelectItem>
                      <SelectItem value="Printing">Printing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Capacity (units/hr)</Label>
                  <Input type="number" value={formData.capacity} onChange={(e) => setFormData({...formData, capacity: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Location *</Label>
                  <Select value={formData.location} onValueChange={(v) => setFormData({...formData, location: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BWD">BWD (Bhiwandi)</SelectItem>
                      <SelectItem value="SGM">SGM (Silvassa)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Add Machine</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Machines Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {machines.length === 0 ? (
          <Card className="col-span-full border-slate-200">
            <CardContent className="p-12 text-center text-slate-500">
              No machines added yet. Click "Add Machine" to get started.
            </CardContent>
          </Card>
        ) : (
          machines.map((machine) => (
            <Card key={machine.id} className="border-slate-200 shadow-sm hover:shadow-md transition-all">
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-4">
                  <div className="h-12 w-12 rounded-lg bg-purple-100 flex items-center justify-center text-purple-600">
                    {typeIcons[machine.machine_type] || <Cog className="h-5 w-5" />}
                  </div>
                  <Badge className={machine.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-800'}>
                    {machine.status}
                  </Badge>
                </div>
                <h3 className="font-semibold text-slate-900">{machine.machine_name}</h3>
                <p className="text-sm text-slate-500 font-mono mb-3">{machine.machine_code}</p>
                <div className="space-y-1 text-sm text-slate-600">
                  <div className="flex justify-between">
                    <span>Type:</span>
                    <span className="font-medium">{machine.machine_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Location:</span>
                    <span className="font-medium">{machine.location}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Capacity:</span>
                    <span className="font-medium font-mono">{machine.capacity} units/hr</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

// ==================== PRODUCTION ENTRIES ====================
const ProductionEntries = () => {
  const [entries, setEntries] = useState([]);
  const [workOrders, setWorkOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    wo_id: '', quantity_produced: '', wastage: '0',
    start_time: '', end_time: '', operator: '', notes: ''
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [entriesRes, wosRes] = await Promise.all([
        api.get('/production/production-entries'),
        api.get('/production/work-orders?status=in_progress')
      ]);
      setEntries(entriesRes.data);
      setWorkOrders(wosRes.data);
    } catch (error) {
      toast.error('Failed to load production entries');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/production/production-entries', {
        ...formData,
        quantity_produced: parseFloat(formData.quantity_produced) || 0,
        wastage: parseFloat(formData.wastage) || 0
      });
      toast.success('Production entry recorded');
      setOpen(false);
      fetchData();
      setFormData({ wo_id: '', quantity_produced: '', wastage: '0', start_time: '', end_time: '', operator: '', notes: '' });
    } catch (error) {
      const msg = error.response?.data?.detail;
      if (msg && msg.includes('Approval required')) {
        toast.error('Approval required. Please approve in Approvals Inbox, then record again.');
        return;
      }
      toast.error(msg || 'Failed to record entry');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="production-entries">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Production Entries</h2>
          <p className="text-slate-600 mt-1 font-inter">{entries.length} entries</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90">
              <Plus className="h-4 w-4 mr-2" />Record Entry
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Record Production Entry</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Work Order *</Label>
                <Select value={formData.wo_id} onValueChange={(v) => setFormData({...formData, wo_id: v})}>
                  <SelectTrigger><SelectValue placeholder="Select work order" /></SelectTrigger>
                  <SelectContent>
                    {workOrders.map(wo => (
                      <SelectItem key={wo.id} value={wo.id}>{wo.wo_number}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Quantity Produced *</Label>
                  <Input type="number" value={formData.quantity_produced} onChange={(e) => setFormData({...formData, quantity_produced: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label>Wastage</Label>
                  <Input type="number" value={formData.wastage} onChange={(e) => setFormData({...formData, wastage: e.target.value})} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Start Time *</Label>
                  <Input type="datetime-local" value={formData.start_time} onChange={(e) => setFormData({...formData, start_time: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label>End Time *</Label>
                  <Input type="datetime-local" value={formData.end_time} onChange={(e) => setFormData({...formData, end_time: e.target.value})} required />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Operator *</Label>
                <Input value={formData.operator} onChange={(e) => setFormData({...formData, operator: e.target.value})} required />
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Record</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Entries Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Batch #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Work Order</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Produced</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Wastage</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Duration</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Operator</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {entries.length === 0 ? (
                  <tr><td colSpan="7" className="px-4 py-12 text-center text-slate-500">No production entries yet</td></tr>
                ) : (
                  entries.map((entry) => (
                    <tr key={entry.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{entry.batch_number}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{entry.wo_id}</td>
                      <td className="px-4 py-3 font-mono font-semibold text-green-600">{entry.quantity_produced}</td>
                      <td className="px-4 py-3 font-mono text-red-600">{entry.wastage}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">
                        {entry.start_time?.split('T')[1]?.slice(0, 5)} - {entry.end_time?.split('T')[1]?.slice(0, 5)}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">{entry.operator}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{entry.created_at?.split('T')[0]}</td>
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

// ==================== ANALYTICS ====================
const ProductionAnalytics = () => {
  const [wastageData, setWastageData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const res = await api.get('/production/analytics/wastage');
      setWastageData(res.data);
    } catch (error) {
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="production-analytics">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Production Analytics</h2>
          <p className="text-slate-600 mt-1 font-inter">Wastage analysis & performance metrics</p>
        </div>
        <Button variant="outline" size="sm"><Download className="h-4 w-4 mr-2" />Export</Button>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="font-manrope">Wastage by Work Order</CardTitle>
        </CardHeader>
        <CardContent>
          {wastageData.length === 0 ? (
            <p className="text-center text-slate-500 py-8">No production data available</p>
          ) : (
            <div className="space-y-4">
              {wastageData.map((item, idx) => (
                <div key={idx} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono font-semibold">{item.wo_id}</span>
                    <Badge className={item.wastage_percentage > 5 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}>
                      {item.wastage_percentage?.toFixed(1)}% wastage
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-slate-500">Produced:</span>
                      <span className="ml-2 font-mono font-semibold text-green-600">{item.total_produced}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Wastage:</span>
                      <span className="ml-2 font-mono font-semibold text-red-600">{item.total_wastage}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Efficiency:</span>
                      <span className="ml-2 font-mono font-semibold">{(100 - (item.wastage_percentage || 0)).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== MAIN PRODUCTION COMPONENT ====================
const Production = () => {
  return (
    <Routes>
      <Route index element={<ProductionDashboard />} />
      <Route path="work-orders" element={<WorkOrdersList />} />
      <Route path="machines" element={<MachinesList />} />
      <Route path="entries" element={<ProductionEntries />} />
      <Route path="analytics" element={<ProductionAnalytics />} />
    </Routes>
  );
};

export default Production;
