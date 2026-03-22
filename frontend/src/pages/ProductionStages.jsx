import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { 
  Plus, Search, Edit, Eye, Factory, Settings, Play, Pause, CheckCircle,
  Clock, AlertTriangle, RefreshCw, Download, BarChart3, TrendingUp,
  Package, Cog, Calendar, Zap, Activity, Target, Truck, Box, Scissors,
  RotateCcw, PackageCheck, Send, Check, MessageSquare, ChevronRight,
  Filter, SortAsc, SortDesc, MoreHorizontal, Video
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../components/ui/dropdown-menu';
import api from '../lib/api';
import { toast } from 'sonner';

// Stage configuration
const STAGES = [
  { id: 'coating', name: 'Coating', icon: Factory, color: 'bg-purple-500', desc: 'Base + Adhesive → Jumbo Roll' },
  { id: 'slitting', name: 'Slitting', icon: Scissors, color: 'bg-blue-500', desc: 'Jumbo → Cut Rolls' },
  { id: 'rewinding', name: 'Rewinding', icon: RotateCcw, color: 'bg-cyan-500', desc: 'Jumbo → Log Rolls' },
  { id: 'cutting', name: 'Cutting', icon: Box, color: 'bg-green-500', desc: 'Log → Cut Width' },
  { id: 'packing', name: 'Packing', icon: PackageCheck, color: 'bg-yellow-500', desc: 'Cut Rolls → Packed' },
  { id: 'ready_to_deliver', name: 'Ready to Deliver', icon: Send, color: 'bg-orange-500', desc: 'Dispatch Ready' },
  { id: 'delivered', name: 'Delivered', icon: Check, color: 'bg-emerald-500', desc: 'Completed' }
];

const MACHINE_TYPES = [
  { value: 'coating', label: 'Coating Machine' },
  { value: 'slitting', label: 'Slitting Machine' },
  { value: 'rewinding', label: 'Rewinding Machine' },
  { value: 'cutting', label: 'Cutting Machine' },
  { value: 'packing', label: 'Packing Line' },
  { value: 'quality_control', label: 'Quality Control' },
  { value: 'despatch', label: 'Despatch' }
];

const priorityColors = {
  urgent: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  normal: 'bg-blue-100 text-blue-800 border-blue-200',
  low: 'bg-slate-100 text-slate-800 border-slate-200'
};

const statusColors = {
  pending: 'bg-slate-100 text-slate-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  on_hold: 'bg-yellow-100 text-yellow-800',
  cancelled: 'bg-red-100 text-red-800'
};

// ==================== PRODUCTION STAGES DASHBOARD ====================
const ProductionStagesDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchDashboard(); }, []);

  const fetchDashboard = async () => {
    try {
      const res = await api.get('/production-stages/dashboard');
      setStats(res.data);
    } catch (error) {
      console.error('Failed to load dashboard', error);
      toast.error('Failed to load production dashboard');
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
    <div className="space-y-6" data-testid="production-stages-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Production Control Center</h2>
          <p className="text-slate-600 mt-1 font-inter">7-Stage Manufacturing Workflow & Order Management</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => navigate('/production-stages/machines')} variant="outline">
            <Cog className="h-4 w-4 mr-2" />Machine Master
          </Button>
          <Button onClick={() => navigate('/production-stages/order-sheets')} variant="outline">
            <Package className="h-4 w-4 mr-2" />Order Sheets
          </Button>
          <Button onClick={fetchDashboard} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-purple-100 flex items-center justify-center">
                <Package className="h-6 w-6 text-purple-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-purple-600">{stats?.summary?.total_sku || 0}</div>
                <div className="text-xs text-slate-500">Total SKUs</div>
              </div>
            </div>
            <div className="mt-2 text-sm text-slate-600">
              <span className="font-medium text-purple-600">{stats?.summary?.sku_in_process || 0}</span> in process
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Target className="h-6 w-6 text-blue-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">{stats?.summary?.total_pcs_in_process || 0}</div>
                <div className="text-xs text-slate-500">PCS in Process</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                <BarChart3 className="h-6 w-6 text-green-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-green-600">{stats?.summary?.total_sqm_in_process || 0}</div>
                <div className="text-xs text-slate-500">SQM in Process</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-orange-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-orange-600">{stats?.summary?.overall_progress || 0}%</div>
                <div className="text-xs text-slate-500">Overall Progress</div>
              </div>
            </div>
            <Progress value={stats?.summary?.overall_progress || 0} className="mt-2 h-2" />
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-cyan-100 flex items-center justify-center">
                <Cog className="h-6 w-6 text-cyan-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-cyan-600">{stats?.machines?.total || 0}</div>
                <div className="text-xs text-slate-500">Machines</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Priority Overview */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-semibold">Priority Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-sm">Urgent: <strong>{stats?.priority?.urgent || 0}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-500"></div>
              <span className="text-sm">High: <strong>{stats?.priority?.high || 0}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-sm">Normal: <strong>{stats?.priority?.normal || 0}</strong></span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-slate-400"></div>
              <span className="text-sm">Low: <strong>{stats?.priority?.low || 0}</strong></span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stage Pipeline */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-semibold">Production Pipeline</CardTitle>
          <CardDescription>Click on any stage to view details</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-2">
            {STAGES.map((stage, idx) => {
              const stageStats = stats?.stages?.[stage.id] || { pending: 0, in_progress: 0, completed: 0, total: 0 };
              const StageIcon = stage.icon;
              
              return (
                <div
                  key={stage.id}
                  className="relative cursor-pointer group"
                  onClick={() => navigate(`/production-stages/stage/${stage.id}`)}
                >
                  <div className={`p-4 rounded-lg border-2 border-slate-200 hover:border-slate-400 transition-all ${stageStats.in_progress > 0 ? 'ring-2 ring-blue-300' : ''}`}>
                    <div className={`h-10 w-10 rounded-lg ${stage.color} flex items-center justify-center mx-auto mb-2`}>
                      <StageIcon className="h-5 w-5 text-white" />
                    </div>
                    <div className="text-center">
                      <div className="text-sm font-medium text-slate-800">{stage.name}</div>
                      <div className="text-xs text-slate-500 mt-1">{stage.desc}</div>
                      <div className="flex justify-center gap-1 mt-2">
                        <Badge variant="outline" className="text-xs px-1">{stageStats.pending} pending</Badge>
                        <Badge variant="outline" className="text-xs px-1 bg-blue-50">{stageStats.in_progress} active</Badge>
                      </div>
                      <div className="text-lg font-bold text-slate-700 mt-1">{stageStats.total}</div>
                    </div>
                  </div>
                  {idx < STAGES.length - 1 && (
                    <ChevronRight className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 h-5 w-5 text-slate-300 z-10" />
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Work Order Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Work Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Pending</span>
                <Badge variant="outline">{stats?.work_orders?.pending || 0}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">In Progress</span>
                <Badge className="bg-blue-100 text-blue-800">{stats?.work_orders?.in_progress || 0}</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Completed</span>
                <Badge className="bg-green-100 text-green-800">{stats?.work_orders?.completed || 0}</Badge>
              </div>
              <div className="flex justify-between items-center pt-2 border-t">
                <span className="text-sm font-medium text-slate-800">Total</span>
                <Badge className="bg-slate-800 text-white">{stats?.work_orders?.total || 0}</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Order Sheets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Active</span>
                <Badge className="bg-blue-100 text-blue-800">{stats?.order_sheets?.active || 0}</Badge>
              </div>
              <div className="flex justify-between items-center pt-2 border-t">
                <span className="text-sm font-medium text-slate-800">Total</span>
                <Badge className="bg-slate-800 text-white">{stats?.order_sheets?.total || 0}</Badge>
              </div>
            </div>
            <Button 
              className="w-full mt-4" 
              variant="outline"
              onClick={() => navigate('/production-stages/order-sheets')}
            >
              View All Order Sheets
            </Button>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button 
              className="w-full justify-start" 
              variant="outline"
              onClick={() => navigate('/production-stages/order-sheets/new')}
            >
              <Plus className="h-4 w-4 mr-2" />Create Order Sheet
            </Button>
            <Button 
              className="w-full justify-start" 
              variant="outline"
              onClick={() => navigate('/production-stages/machines')}
            >
              <Cog className="h-4 w-4 mr-2" />Manage Machines
            </Button>
            <Button 
              className="w-full justify-start" 
              variant="outline"
              onClick={() => navigate('/production-stages/reports')}
            >
              <BarChart3 className="h-4 w-4 mr-2" />View Reports
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ==================== MACHINE MASTER ====================
const MachineMaster = () => {
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDialog, setShowDialog] = useState(false);
  const [editingMachine, setEditingMachine] = useState(null);
  const [filter, setFilter] = useState({ type: 'all', location: 'all' });
  const [formData, setFormData] = useState({
    machine_code: '',
    machine_name: '',
    machine_type: '',
    capacity: '',
    capacity_uom: 'pcs/hour',
    location: '',
    wastage_norm_percent: 2.0,
    notes: ''
  });

  useEffect(() => { fetchMachines(); }, []);

  const fetchMachines = async () => {
    try {
      const res = await api.get('/production-stages/machines');
      setMachines(res.data);
    } catch (error) {
      toast.error('Failed to load machines');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingMachine) {
        await api.put(`/production-stages/machines/${editingMachine.id}`, formData);
        toast.success('Machine updated');
      } else {
        await api.post('/production-stages/machines', formData);
        toast.success('Machine created');
      }
      setShowDialog(false);
      setEditingMachine(null);
      resetForm();
      fetchMachines();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save machine');
    }
  };

  const resetForm = () => {
    setFormData({
      machine_code: '',
      machine_name: '',
      machine_type: '',
      capacity: '',
      capacity_uom: 'pcs/hour',
      location: '',
      wastage_norm_percent: 2.0,
      notes: ''
    });
  };

  const openEdit = (machine) => {
    setEditingMachine(machine);
    setFormData({
      machine_code: machine.machine_code,
      machine_name: machine.machine_name,
      machine_type: machine.machine_type,
      capacity: machine.capacity,
      capacity_uom: machine.capacity_uom || 'pcs/hour',
      location: machine.location,
      wastage_norm_percent: machine.wastage_norm_percent || 2.0,
      notes: machine.notes || ''
    });
    setShowDialog(true);
  };

  const filteredMachines = machines.filter(m => {
    if (filter.type !== 'all' && m.machine_type !== filter.type) return false;
    if (filter.location !== 'all' && m.location !== filter.location) return false;
    return true;
  });

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;
  }

  return (
    <div className="space-y-6" data-testid="machine-master">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Machine Master</h2>
          <p className="text-slate-600 mt-1 font-inter">Configure machines with wastage norms for each production stage</p>
        </div>
        <Button onClick={() => { resetForm(); setEditingMachine(null); setShowDialog(true); }}>
          <Plus className="h-4 w-4 mr-2" />Add Machine
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={filter.type} onValueChange={(v) => setFilter({ ...filter, type: v })}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {MACHINE_TYPES.map(t => (
              <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={filter.location} onValueChange={(v) => setFilter({ ...filter, location: v })}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Filter by location" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Locations</SelectItem>
            <SelectItem value="BWD">BWD</SelectItem>
            <SelectItem value="SGM">SGM</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Machine Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {filteredMachines.map(machine => (
          <Card key={machine.id} className="border-slate-200 shadow-sm hover:shadow-md transition-all">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="h-10 w-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <Cog className="h-5 w-5 text-slate-600" />
                </div>
                <Badge className={machine.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-800'}>
                  {machine.status}
                </Badge>
              </div>
              <div className="mt-3">
                <div className="text-lg font-semibold text-slate-800">{machine.machine_name}</div>
                <div className="text-sm text-slate-500">{machine.machine_code}</div>
              </div>
              <div className="mt-2 space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Type:</span>
                  <span className="font-medium capitalize">{machine.machine_type?.replace('_', ' ')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Location:</span>
                  <span className="font-medium">{machine.location}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Capacity:</span>
                  <span className="font-medium">{machine.capacity} {machine.capacity_uom}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Wastage Norm:</span>
                  <span className="font-medium text-orange-600">{machine.wastage_norm_percent}%</span>
                </div>
              </div>
              <Button className="w-full mt-3" variant="outline" size="sm" onClick={() => openEdit(machine)}>
                <Edit className="h-4 w-4 mr-2" />Edit
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredMachines.length === 0 && (
        <div className="text-center py-12 text-slate-500">
          No machines found. Add your first machine to get started.
        </div>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingMachine ? 'Edit Machine' : 'Add New Machine'}</DialogTitle>
            <DialogDescription>Configure machine details and wastage norms</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Machine Code *</Label>
                <Input 
                  value={formData.machine_code} 
                  onChange={(e) => setFormData({...formData, machine_code: e.target.value})}
                  placeholder="e.g., COAT-01"
                  required
                  disabled={!!editingMachine}
                />
              </div>
              <div className="space-y-2">
                <Label>Machine Name *</Label>
                <Input 
                  value={formData.machine_name} 
                  onChange={(e) => setFormData({...formData, machine_name: e.target.value})}
                  placeholder="e.g., Coating Line 1"
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Machine Type *</Label>
                <Select value={formData.machine_type} onValueChange={(v) => setFormData({...formData, machine_type: v})} required>
                  <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                  <SelectContent>
                    {MACHINE_TYPES.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Location *</Label>
                <Select value={formData.location} onValueChange={(v) => setFormData({...formData, location: v})} required>
                  <SelectTrigger><SelectValue placeholder="Select location" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BWD">BWD</SelectItem>
                    <SelectItem value="SGM">SGM</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Capacity *</Label>
                <Input 
                  type="number"
                  value={formData.capacity} 
                  onChange={(e) => setFormData({...formData, capacity: e.target.value})}
                  placeholder="e.g., 120"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Capacity UOM</Label>
                <Select value={formData.capacity_uom} onValueChange={(v) => setFormData({...formData, capacity_uom: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pcs/hour">PCS/Hour</SelectItem>
                    <SelectItem value="sqm/hour">SQM/Hour</SelectItem>
                    <SelectItem value="kg/hour">KG/Hour</SelectItem>
                    <SelectItem value="rolls/hour">Rolls/Hour</SelectItem>
                    <SelectItem value="ctn/shift">CTN/Shift</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Wastage Norm (%)</Label>
              <Input 
                type="number"
                step="0.1"
                value={formData.wastage_norm_percent} 
                onChange={(e) => setFormData({...formData, wastage_norm_percent: parseFloat(e.target.value)})}
                placeholder="e.g., 2.0"
              />
              <p className="text-xs text-slate-500">Alert will trigger if actual wastage exceeds this norm</p>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea 
                value={formData.notes} 
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
                rows={2}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowDialog(false)}>Cancel</Button>
              <Button type="submit">{editingMachine ? 'Update' : 'Create'} Machine</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ==================== ORDER SHEETS LIST ====================
const OrderSheetsList = () => {
  const navigate = useNavigate();
  const [orderSheets, setOrderSheets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [salesOrders, setSalesOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [creating, setCreating] = useState(false);

  useEffect(() => { fetchOrderSheets(); }, []);

  const fetchOrderSheets = async () => {
    try {
      const res = await api.get('/production-stages/order-sheets');
      setOrderSheets(res.data);
    } catch (error) {
      toast.error('Failed to load order sheets');
    } finally {
      setLoading(false);
    }
  };

  const fetchSalesOrders = async () => {
    try {
      const res = await api.get('/production-stages/sales-orders/available');
      setSalesOrders(res.data);
    } catch (error) {
      toast.error('Failed to load sales orders');
    }
  };

  const openCreateDialog = () => {
    fetchSalesOrders();
    setSelectedOrder(null);
    setShowCreateDialog(true);
  };

  const handleCreateOrderSheet = async () => {
    if (!selectedOrder) {
      toast.error('Please select a sales order');
      return;
    }

    setCreating(true);
    try {
      const payload = {
        sales_order_id: selectedOrder.id,
        customer_id: selectedOrder.account_id,
        customer_name: selectedOrder.account_name,
        order_date: selectedOrder.created_at?.split('T')[0] || new Date().toISOString().split('T')[0],
        delivery_date: selectedOrder.delivery_date || null,
        priority: 'normal',
        items: selectedOrder.items || [],
        notes: `Auto-created from SO: ${selectedOrder.order_number}`
      };

      const res = await api.post('/production-stages/order-sheets', payload);
      toast.success(`Order Sheet created with ${res.data.work_orders_created} work orders`);
      setShowCreateDialog(false);
      fetchOrderSheets();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create order sheet');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;
  }

  return (
    <div className="space-y-6" data-testid="order-sheets-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Order Sheets</h2>
          <p className="text-slate-600 mt-1 font-inter">Sales orders converted to production work orders</p>
        </div>
        <Button onClick={openCreateDialog}>
          <Plus className="h-4 w-4 mr-2" />New Order Sheet
        </Button>
      </div>

      <Card className="border-slate-200">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Order Sheet #</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Order Date</TableHead>
              <TableHead>Items</TableHead>
              <TableHead>Progress</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {orderSheets.map(os => (
              <TableRow key={os.id} className="cursor-pointer hover:bg-slate-50" onClick={() => navigate(`/production-stages/order-sheets/${os.id}`)}>
                <TableCell className="font-medium">{os.order_sheet_no}</TableCell>
                <TableCell>{os.customer_name}</TableCell>
                <TableCell>{new Date(os.order_date).toLocaleDateString()}</TableCell>
                <TableCell>{os.total_items} items</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Progress value={os.progress_percent || 0} className="w-20 h-2" />
                    <span className="text-sm">{os.progress_percent || 0}%</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge className={statusColors[os.status]}>{os.status}</Badge>
                </TableCell>
                <TableCell>
                  <Button variant="ghost" size="sm">
                    <Eye className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {orderSheets.length === 0 && (
        <div className="text-center py-12 text-slate-500">
          No order sheets found. Create your first order sheet from a sales order.
        </div>
      )}

      {/* Create Order Sheet Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Order Sheet from Sales Order</DialogTitle>
            <DialogDescription>Select a sales order to convert into production work orders</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {salesOrders.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <Package className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                <p>No pending sales orders available</p>
                <p className="text-sm mt-1">Create a quotation and convert it to a sales order first</p>
              </div>
            ) : (
              <div className="space-y-2">
                <Label>Select Sales Order</Label>
                <div className="grid gap-2 max-h-60 overflow-y-auto">
                  {salesOrders.map(so => (
                    <div
                      key={so.id}
                      onClick={() => setSelectedOrder(so)}
                      className={`p-3 border rounded-lg cursor-pointer transition-all ${
                        selectedOrder?.id === so.id 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium">{so.order_number}</div>
                          <div className="text-sm text-slate-600">{so.account_name}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-medium text-green-600">₹{(so.grand_total || 0).toLocaleString()}</div>
                          <div className="text-xs text-slate-500">{so.items?.length || 0} items</div>
                        </div>
                      </div>
                      <div className="flex gap-2 mt-2">
                        <Badge variant="outline" className="text-xs">{so.status}</Badge>
                        <span className="text-xs text-slate-500">{new Date(so.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedOrder && (
              <div className="mt-4 p-4 bg-slate-50 rounded-lg">
                <h4 className="font-medium mb-2">Selected Order Items:</h4>
                <div className="space-y-1 text-sm">
                  {(selectedOrder.items || []).map((item, idx) => (
                    <div key={idx} className="flex justify-between">
                      <span>{item.item_name || item.description}</span>
                      <span className="text-slate-600">{item.quantity} {item.unit || 'pcs'}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-2 pt-2 border-t text-sm text-slate-500">
                  Work orders will be created for: Coating → Slitting → Rewinding → Cutting → Packing → Ready to Deliver
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
            <Button onClick={handleCreateOrderSheet} disabled={!selectedOrder || creating}>
              {creating ? 'Creating...' : 'Create Order Sheet'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ==================== STAGE DETAIL VIEW ====================
const StageDetailView = () => {
  const { stageId } = useParams();
  const navigate = useNavigate();
  const [stageData, setStageData] = useState(null);
  const [loading, setLoading] = useState(true);

  const stage = STAGES.find(s => s.id === stageId);

  useEffect(() => { 
    if (stageId) fetchStageData(); 
  }, [stageId]);

  const fetchStageData = async () => {
    try {
      const res = await api.get(`/production-stages/stages/${stageId}/dashboard`);
      setStageData(res.data);
    } catch (error) {
      toast.error('Failed to load stage data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;
  }

  if (!stage) {
    return <div className="text-center py-12">Invalid stage</div>;
  }

  const StageIcon = stage.icon;

  return (
    <div className="space-y-6" data-testid={`stage-${stageId}-view`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`h-12 w-12 rounded-lg ${stage.color} flex items-center justify-center`}>
            <StageIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900 font-manrope">{stage.name}</h2>
            <p className="text-slate-600 font-inter">{stage.desc}</p>
          </div>
        </div>
        <Button onClick={fetchStageData} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="text-sm text-slate-500">Pending</div>
            <div className="text-2xl font-bold text-slate-800">{stageData?.summary?.pending || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="text-sm text-slate-500">In Progress</div>
            <div className="text-2xl font-bold text-blue-600">{stageData?.summary?.in_progress || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="text-sm text-slate-500">Completed</div>
            <div className="text-2xl font-bold text-green-600">{stageData?.summary?.completed || 0}</div>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="text-sm text-slate-500">Wastage %</div>
            <div className="text-2xl font-bold text-orange-600">{stageData?.quantities?.wastage_percent || 0}%</div>
          </CardContent>
        </Card>
      </div>

      {/* Quantities */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="text-lg">Production Quantities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-slate-500">Target</div>
              <div className="text-xl font-bold">{stageData?.quantities?.total_target || 0}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500">Completed</div>
              <div className="text-xl font-bold text-green-600">{stageData?.quantities?.total_completed || 0}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500">Wastage</div>
              <div className="text-xl font-bold text-red-600">{stageData?.quantities?.total_wastage || 0}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500">Hourly Avg</div>
              <div className="text-xl font-bold text-blue-600">{stageData?.hourly_production?.hourly_avg || 0}</div>
            </div>
          </div>
          <Progress value={stageData?.quantities?.completion_percent || 0} className="mt-4 h-3" />
          <div className="text-sm text-center mt-1 text-slate-500">{stageData?.quantities?.completion_percent || 0}% Complete</div>
        </CardContent>
      </Card>

      {/* Work Orders Table */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="text-lg">Work Orders</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>WO #</TableHead>
                <TableHead>Item</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>Completed</TableHead>
                <TableHead>Wastage</TableHead>
                <TableHead>Machine</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(stageData?.work_orders || []).map(wo => (
                <TableRow key={wo.id}>
                  <TableCell className="font-medium">{wo.wo_number}</TableCell>
                  <TableCell>{wo.item_name}</TableCell>
                  <TableCell>{wo.target_qty} {wo.target_uom}</TableCell>
                  <TableCell>{wo.completed_qty}</TableCell>
                  <TableCell className={wo.actual_wastage_percent > 5 ? 'text-red-600 font-medium' : ''}>{wo.actual_wastage_percent || 0}%</TableCell>
                  <TableCell>{wo.machine_name || '-'}</TableCell>
                  <TableCell><Badge className={priorityColors[wo.priority]}>{wo.priority}</Badge></TableCell>
                  <TableCell><Badge className={statusColors[wo.status]}>{wo.status}</Badge></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== ORDER SHEET DETAIL VIEW ====================
const OrderSheetDetail = () => {
  const { orderSheetId } = useParams();
  const navigate = useNavigate();
  const [orderSheet, setOrderSheet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('order');

  useEffect(() => { 
    if (orderSheetId) fetchOrderSheet(); 
  }, [orderSheetId]);

  const fetchOrderSheet = async () => {
    try {
      const res = await api.get(`/production-stages/order-sheets/${orderSheetId}`);
      setOrderSheet(res.data);
    } catch (error) {
      toast.error('Failed to load order sheet');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;
  }

  if (!orderSheet) {
    return <div className="text-center py-12">Order sheet not found</div>;
  }

  const { order_sheet, work_orders, views } = orderSheet;

  return (
    <div className="space-y-6" data-testid="order-sheet-detail">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">{order_sheet.order_sheet_no}</h2>
          <p className="text-slate-600 font-inter">{order_sheet.customer_name} • {order_sheet.total_items} items</p>
        </div>
        <div className="flex gap-2">
          <Badge className={order_sheet.progress_percent >= 100 ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}>
            {order_sheet.progress_percent || 0}% Complete
          </Badge>
          <Button onClick={fetchOrderSheet} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* 3 Tabs: Order-wise, Product-wise, Machine-wise */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="order" className="flex items-center gap-2">
            <Package className="h-4 w-4" />Order-wise
          </TabsTrigger>
          <TabsTrigger value="product" className="flex items-center gap-2">
            <Box className="h-4 w-4" />Product-wise
          </TabsTrigger>
          <TabsTrigger value="machine" className="flex items-center gap-2">
            <Cog className="h-4 w-4" />Machine-wise
          </TabsTrigger>
        </TabsList>

        {/* Order-wise Tab */}
        <TabsContent value="order" className="mt-4">
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Orders & Status</CardTitle>
                  <CardDescription>View order details and track progress by sales order</CardDescription>
                </div>
                <Badge variant="outline">{(views.order_wise || []).length} orders</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {(views.order_wise || []).map(order => {
                const progressPercent = (order.total_completed / Math.max(order.total_target, 1)) * 100;
                const pendingCount = order.work_orders.filter(w => w.status === 'pending').length;
                const inProgressCount = order.work_orders.filter(w => w.status === 'in_progress').length;
                const completedCount = order.work_orders.filter(w => w.status === 'completed').length;
                
                return (
                  <div key={order.sales_order_id} className="p-4 border rounded-lg hover:border-blue-300 transition-colors">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <div className="font-semibold text-slate-800">{order.sales_order_id}</div>
                          <Badge className={progressPercent >= 100 ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}>
                            {progressPercent.toFixed(0)}%
                          </Badge>
                        </div>
                        <div className="text-sm text-slate-600">{order.customer_name}</div>
                      </div>
                      <div className="text-right text-sm">
                        <div>Target: <span className="font-medium">{order.total_target}</span></div>
                        <div className="text-green-600">Completed: <span className="font-medium">{order.total_completed}</span></div>
                      </div>
                    </div>
                    <Progress value={progressPercent} className="h-2 mb-3" />
                    <div className="flex gap-2 mb-3">
                      <Badge variant="outline" className="text-xs">{pendingCount} Pending</Badge>
                      <Badge className="bg-blue-100 text-blue-800 text-xs">{inProgressCount} In Progress</Badge>
                      <Badge className="bg-green-100 text-green-800 text-xs">{completedCount} Completed</Badge>
                    </div>
                    <div className="grid gap-2">
                      {order.work_orders.slice(0, 5).map(wo => (
                        <div 
                          key={wo.id} 
                          className="flex justify-between items-center text-sm p-2 bg-slate-50 rounded hover:bg-slate-100 cursor-pointer transition-colors"
                          onClick={() => navigate(`/production-stages/work-order/${wo.id}`)}
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs">{wo.wo_number}</span>
                            <Badge variant="outline" className="text-xs capitalize">{wo.stage}</Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-500">{wo.completed_qty}/{wo.target_qty}</span>
                            <Badge className={statusColors[wo.status]} size="sm">{wo.status}</Badge>
                          </div>
                        </div>
                      ))}
                      {order.work_orders.length > 5 && (
                        <div className="text-center text-xs text-slate-500 mt-1">
                          +{order.work_orders.length - 5} more work orders
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Product-wise Tab */}
        <TabsContent value="product" className="mt-4">
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Product-wise Stages</CardTitle>
                  <CardDescription>Track each product through all 7 production stages</CardDescription>
                </div>
                <Badge variant="outline">{(views.product_wise || []).length} products</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {(views.product_wise || []).map(product => {
                const totalWOs = Object.values(product.stages).flat().length;
                const completedWOs = Object.values(product.stages).flat().filter(w => w.status === 'completed').length;
                
                return (
                  <div key={product.item_id} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <div className="font-semibold text-slate-800">{product.item_name}</div>
                        <div className="text-sm text-slate-500 font-mono">{product.item_code}</div>
                      </div>
                      <div className="text-right">
                        <Badge variant="outline">{completedWOs}/{totalWOs} stages done</Badge>
                      </div>
                    </div>
                    {/* Stage Pipeline Visualization */}
                    <div className="flex items-center gap-1 mb-2">
                      {STAGES.filter(s => s.id !== 'delivered').map((stage, idx) => {
                        const stageWOs = product.stages[stage.id] || [];
                        const hasWO = stageWOs.length > 0;
                        const allCompleted = hasWO && stageWOs.every(w => w.status === 'completed');
                        const anyInProgress = stageWOs.some(w => w.status === 'in_progress');
                        const StageIcon = stage.icon;
                        
                        return (
                          <React.Fragment key={stage.id}>
                            <div 
                              className={`flex-1 p-2 text-center rounded-lg transition-all ${
                                allCompleted ? 'bg-green-100 border border-green-300' :
                                anyInProgress ? 'bg-blue-100 border border-blue-300 animate-pulse' :
                                hasWO ? 'bg-yellow-100 border border-yellow-300' :
                                'bg-slate-100 border border-slate-200'
                              }`}
                            >
                              <StageIcon className={`h-4 w-4 mx-auto mb-1 ${
                                allCompleted ? 'text-green-600' :
                                anyInProgress ? 'text-blue-600' :
                                hasWO ? 'text-yellow-600' :
                                'text-slate-400'
                              }`} />
                              <div className="text-xs font-medium truncate">{stage.name.split(' ')[0]}</div>
                              {hasWO && (
                                <div className={`text-xs font-bold ${
                                  allCompleted ? 'text-green-700' :
                                  anyInProgress ? 'text-blue-700' :
                                  'text-yellow-700'
                                }`}>
                                  {stageWOs.length}
                                </div>
                              )}
                            </div>
                            {idx < STAGES.length - 2 && (
                              <ChevronRight className={`h-4 w-4 flex-shrink-0 ${
                                allCompleted ? 'text-green-400' : 'text-slate-300'
                              }`} />
                            )}
                          </React.Fragment>
                        );
                      })}
                    </div>
                    {/* Stage Details Expandable */}
                    <div className="grid grid-cols-2 gap-2 mt-3">
                      {STAGES.filter(s => s.id !== 'delivered').map(stage => {
                        const stageWOs = product.stages[stage.id] || [];
                        if (!stageWOs.length) return null;
                        
                        return stageWOs.map(wo => (
                          <div 
                            key={wo.id}
                            className="text-xs p-2 bg-slate-50 rounded flex justify-between items-center cursor-pointer hover:bg-slate-100"
                            onClick={() => navigate(`/production-stages/work-order/${wo.id}`)}
                          >
                            <span className="font-mono">{wo.wo_number}</span>
                            <Badge className={statusColors[wo.status]} size="sm">{wo.status}</Badge>
                          </div>
                        ));
                      })}
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Machine-wise Tab */}
        <TabsContent value="machine" className="mt-4">
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Machine-wise Load</CardTitle>
                  <CardDescription>View work assigned to each machine and their utilization</CardDescription>
                </div>
                <Badge variant="outline">{(views.machine_wise || []).length} machines</Badge>
              </div>
            </CardHeader>
            <CardContent>
              {(views.machine_wise || []).length === 0 ? (
                <div className="text-center py-12">
                  <Cog className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                  <div className="text-slate-500 font-medium">No Machines Assigned Yet</div>
                  <div className="text-sm text-slate-400 mt-1">
                    Assign machines to work orders to see them here
                  </div>
                  <Button 
                    variant="outline" 
                    className="mt-4"
                    onClick={() => navigate('/production-stages/machines')}
                  >
                    <Cog className="h-4 w-4 mr-2" />Go to Machine Master
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {views.machine_wise.map(machine => {
                    const progressPercent = (machine.total_completed / Math.max(machine.total_target, 1)) * 100;
                    const pendingCount = machine.work_orders.filter(w => w.status === 'pending').length;
                    const inProgressCount = machine.work_orders.filter(w => w.status === 'in_progress').length;
                    const completedCount = machine.work_orders.filter(w => w.status === 'completed').length;
                    
                    return (
                      <div key={machine.machine_id} className="p-4 border rounded-lg hover:border-cyan-300 transition-colors">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-cyan-100 flex items-center justify-center">
                              <Cog className="h-5 w-5 text-cyan-600" />
                            </div>
                            <div>
                              <div className="font-semibold text-slate-800">{machine.machine_name}</div>
                              <div className="text-sm text-slate-500">{machine.work_orders.length} work orders assigned</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-bold text-cyan-600">{progressPercent.toFixed(0)}%</div>
                            <div className="text-xs text-slate-500">Utilization</div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-4 mb-3 text-center">
                          <div className="p-2 bg-slate-50 rounded">
                            <div className="text-lg font-bold text-slate-700">{machine.total_target}</div>
                            <div className="text-xs text-slate-500">Target</div>
                          </div>
                          <div className="p-2 bg-green-50 rounded">
                            <div className="text-lg font-bold text-green-600">{machine.total_completed}</div>
                            <div className="text-xs text-slate-500">Completed</div>
                          </div>
                          <div className="p-2 bg-blue-50 rounded">
                            <div className="text-lg font-bold text-blue-600">{machine.total_target - machine.total_completed}</div>
                            <div className="text-xs text-slate-500">Remaining</div>
                          </div>
                        </div>
                        
                        <Progress value={progressPercent} className="h-2 mb-3" />
                        
                        <div className="flex gap-2 mb-3">
                          <Badge variant="outline" className="text-xs">{pendingCount} Pending</Badge>
                          <Badge className="bg-blue-100 text-blue-800 text-xs">{inProgressCount} Active</Badge>
                          <Badge className="bg-green-100 text-green-800 text-xs">{completedCount} Done</Badge>
                        </div>
                        
                        {/* Work Order List */}
                        <div className="grid gap-2 max-h-40 overflow-y-auto">
                          {machine.work_orders.map(wo => (
                            <div 
                              key={wo.id}
                              className="flex justify-between items-center text-sm p-2 bg-slate-50 rounded hover:bg-slate-100 cursor-pointer transition-colors"
                              onClick={() => navigate(`/production-stages/work-order/${wo.id}`)}
                            >
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-xs">{wo.wo_number}</span>
                                <Badge variant="outline" className="text-xs capitalize">{wo.stage}</Badge>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-slate-500">{wo.item_name?.substring(0, 20)}</span>
                                <Badge className={statusColors[wo.status]} size="sm">{wo.status}</Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* All Work Orders */}
      <Card className="border-slate-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">All Work Orders ({work_orders.length})</CardTitle>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />Export
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>WO #</TableHead>
                <TableHead>Stage</TableHead>
                <TableHead>Item</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>Completed</TableHead>
                <TableHead>Wastage</TableHead>
                <TableHead>Machine</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {work_orders.map(wo => (
                <TableRow key={wo.id} className="cursor-pointer hover:bg-slate-50">
                  <TableCell className="font-mono text-sm">{wo.wo_number}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="capitalize">{wo.stage}</Badge>
                  </TableCell>
                  <TableCell className="max-w-32 truncate">{wo.item_name}</TableCell>
                  <TableCell>{wo.target_qty} {wo.target_uom}</TableCell>
                  <TableCell className="text-green-600 font-medium">{wo.completed_qty}</TableCell>
                  <TableCell className={wo.actual_wastage_percent > 5 ? 'text-red-600 font-medium' : 'text-slate-600'}>
                    {wo.actual_wastage_percent || 0}%
                  </TableCell>
                  <TableCell>{wo.machine_name || <span className="text-slate-400">Not assigned</span>}</TableCell>
                  <TableCell><Badge className={priorityColors[wo.priority]}>{wo.priority}</Badge></TableCell>
                  <TableCell><Badge className={statusColors[wo.status]}>{wo.status}</Badge></TableCell>
                  <TableCell>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => navigate(`/production-stages/work-order/${wo.id}`)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

// Stage-specific form field configurations
const STAGE_FORM_FIELDS = {
  coating: {
    title: 'Coating Entry',
    description: 'Base Film + Adhesive → Jumbo Roll',
    inputUom: 'kg',
    outputUom: 'rolls',
    fields: [
      { key: 'jumbo_roll_width', label: 'Jumbo Roll Width (mm)', type: 'number', required: true },
      { key: 'jumbo_roll_length', label: 'Jumbo Roll Length (m)', type: 'number', required: true },
      { key: 'jumbo_roll_weight', label: 'Jumbo Roll Weight (kg)', type: 'number' },
      { key: 'sqm_produced', label: 'SQM Produced', type: 'number', computed: true },
      { key: 'base_film_consumption', label: 'Base Film Used (kg)', type: 'number' },
      { key: 'adhesive_consumption', label: 'Adhesive Used (kg)', type: 'number' },
      { key: 'liner_consumption', label: 'Liner Used (kg)', type: 'number' },
      { key: 'coating_speed', label: 'Coating Speed (m/min)', type: 'number' },
      { key: 'drying_temp', label: 'Drying Temp (°C)', type: 'number' }
    ]
  },
  slitting: {
    title: 'Slitting Entry',
    description: 'Jumbo Roll → Cut Rolls',
    inputUom: 'sqm',
    outputUom: 'pcs',
    fields: [
      { key: 'parent_roll_id', label: 'Parent Roll / Batch No', type: 'text' },
      { key: 'sqm_input', label: 'Input SQM', type: 'number', required: true },
      { key: 'no_of_slits', label: 'Number of Slits', type: 'number', required: true },
      { key: 'slit_widths', label: 'Slit Widths (mm, comma-separated)', type: 'text', placeholder: 'e.g., 48, 72, 96' },
      { key: 'edge_trim_width', label: 'Edge Trim Width (mm)', type: 'number' },
      { key: 'sqm_output', label: 'Output SQM', type: 'number', required: true }
    ]
  },
  rewinding: {
    title: 'Rewinding Entry',
    description: 'Jumbo Roll → Log Rolls',
    inputUom: 'mtr',
    outputUom: 'pcs',
    fields: [
      { key: 'parent_roll_id', label: 'Parent Roll / Batch No', type: 'text' },
      { key: 'no_of_logs', label: 'Number of Logs', type: 'number', required: true },
      { key: 'log_length', label: 'Length per Log (m)', type: 'number', required: true },
      { key: 'core_size', label: 'Core Size', type: 'select', options: ['1"', '1.5"', '2"', '3"'] },
      { key: 'tension_setting', label: 'Tension Setting', type: 'number' }
    ]
  },
  cutting: {
    title: 'Cutting Entry',
    description: 'Log Rolls → Cut Width Rolls',
    inputUom: 'pcs',
    outputUom: 'pcs',
    fields: [
      { key: 'parent_roll_id', label: 'Parent Log / Batch No', type: 'text' },
      { key: 'cut_length', label: 'Cut Length (m)', type: 'number', required: true },
      { key: 'pieces_per_log', label: 'Pieces per Log', type: 'number', required: true },
      { key: 'total_pieces', label: 'Total Pieces Produced', type: 'number', required: true }
    ]
  },
  packing: {
    title: 'Packing Entry',
    description: 'Cut Rolls → Packed Cartons',
    inputUom: 'pcs',
    outputUom: 'pcs',
    fields: [
      { key: 'packing_type', label: 'Packing Type', type: 'select', options: ['shrink', 'carton', 'pallet', 'pouch'] },
      { key: 'pieces_per_carton', label: 'Pieces per Carton', type: 'number', required: true },
      { key: 'cartons_packed', label: 'Cartons Packed', type: 'number', required: true },
      { key: 'net_weight', label: 'Net Weight (kg)', type: 'number' },
      { key: 'gross_weight', label: 'Gross Weight (kg)', type: 'number' },
      { key: 'qc_status', label: 'QC Status', type: 'select', options: ['pass', 'fail', 'conditional'] },
      { key: 'qc_video_url', label: 'QC Video URL', type: 'text', placeholder: 'Upload link or paste URL' }
    ]
  },
  ready_to_deliver: {
    title: 'Ready to Deliver Entry',
    description: 'Dispatch Preparation',
    inputUom: 'pcs',
    outputUom: 'pcs',
    fields: [
      { key: 'cartons_packed', label: 'Cartons Ready', type: 'number' },
      { key: 'gross_weight', label: 'Total Weight (kg)', type: 'number' }
    ]
  }
};

// ==================== WORK ORDER DETAIL & ENTRY ====================
const WorkOrderDetail = () => {
  const { workOrderId } = useParams();
  const navigate = useNavigate();
  const [workOrder, setWorkOrder] = useState(null);
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEntryDialog, setShowEntryDialog] = useState(false);
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  // Initialize with empty entry form - will be populated based on stage
  const getInitialFormState = (stage) => {
    const stageConfig = STAGE_FORM_FIELDS[stage] || {};
    const baseForm = {
      operator_id: '',
      start_time: '',
      end_time: '',
      input_qty: '',
      input_uom: stageConfig.inputUom || 'pcs',
      output_qty: '',
      output_uom: stageConfig.outputUom || 'pcs',
      wastage_qty: '',
      wastage_reason: '',
      notes: ''
    };
    // Add stage-specific fields
    (stageConfig.fields || []).forEach(field => {
      baseForm[field.key] = '';
    });
    return baseForm;
  };
  
  const [entryForm, setEntryForm] = useState({
    operator_id: '',
    start_time: '',
    end_time: '',
    input_qty: '',
    input_uom: 'pcs',
    output_qty: '',
    output_uom: 'pcs',
    wastage_qty: '',
    wastage_reason: '',
    notes: ''
  });

  useEffect(() => { 
    if (workOrderId) {
      fetchWorkOrder();
      fetchMachines();
    }
  }, [workOrderId]);

  const fetchWorkOrder = async () => {
    try {
      const res = await api.get(`/production-stages/work-order-stages/${workOrderId}`);
      setWorkOrder(res.data);
    } catch (error) {
      toast.error('Failed to load work order');
    } finally {
      setLoading(false);
    }
  };

  const fetchMachines = async () => {
    try {
      const res = await api.get('/production-stages/machines');
      setMachines(res.data);
    } catch (error) {
      console.error('Failed to load machines');
    }
  };

  const handleAssignMachine = async (machineId) => {
    try {
      await api.put(`/production-stages/work-order-stages/${workOrderId}/assign-machine?machine_id=${machineId}`);
      toast.success('Machine assigned');
      setShowAssignDialog(false);
      fetchWorkOrder();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign machine');
    }
  };

  const handleStartWorkOrder = async () => {
    try {
      await api.put(`/production-stages/work-order-stages/${workOrderId}/start`);
      toast.success('Work order started');
      fetchWorkOrder();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start work order');
    }
  };

  const handleSubmitEntry = async (e) => {
    e.preventDefault();
    if (!entryForm.input_qty || !entryForm.output_qty) {
      toast.error('Please fill in input and output quantities');
      return;
    }

    setSubmitting(true);
    try {
      // Build payload with base fields
      const payload = {
        work_order_stage_id: workOrderId,
        operator_id: entryForm.operator_id || 'default',
        start_time: entryForm.start_time || new Date().toISOString(),
        end_time: entryForm.end_time || new Date().toISOString(),
        input_qty: parseFloat(entryForm.input_qty),
        input_uom: entryForm.input_uom,
        output_qty: parseFloat(entryForm.output_qty),
        output_uom: entryForm.output_uom,
        wastage_qty: parseFloat(entryForm.wastage_qty || 0),
        wastage_reason: entryForm.wastage_reason,
        notes: entryForm.notes
      };
      
      // Add stage-specific fields
      const stageConfig = STAGE_FORM_FIELDS[workOrder?.stage];
      if (stageConfig) {
        stageConfig.fields.forEach(field => {
          const value = entryForm[field.key];
          if (value !== undefined && value !== '') {
            // Handle special types
            if (field.key === 'slit_widths' && typeof value === 'string') {
              // Convert comma-separated to array
              payload[field.key] = value.split(',').map(v => parseFloat(v.trim())).filter(v => !isNaN(v));
            } else if (field.type === 'number') {
              payload[field.key] = parseFloat(value);
            } else {
              payload[field.key] = value;
            }
          }
        });
      }

      const res = await api.post(`/production-stages/work-order-stages/${workOrderId}/entry`, payload);
      
      if (res.data.wastage_exceeded) {
        toast.warning(`Wastage (${res.data.entry.wastage_percent}%) exceeds norm (${res.data.wastage_norm}%)`);
      } else {
        toast.success('Production entry recorded');
      }
      
      setShowEntryDialog(false);
      // Reset form with stage-specific defaults
      setEntryForm(getInitialFormState(workOrder?.stage));
      fetchWorkOrder();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit entry');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;
  }

  if (!workOrder) {
    return <div className="text-center py-12">Work order not found</div>;
  }

  const stage = STAGES.find(s => s.id === workOrder.stage);
  const StageIcon = stage?.icon || Factory;
  const filteredMachines = machines.filter(m => m.machine_type === workOrder.stage && m.status === 'active');
  const progress = (workOrder.completed_qty / Math.max(workOrder.target_qty, 1)) * 100;

  return (
    <div className="space-y-6" data-testid="work-order-detail">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`h-12 w-12 rounded-lg ${stage?.color || 'bg-slate-500'} flex items-center justify-center`}>
            <StageIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900 font-manrope">{workOrder.wo_number}</h2>
            <p className="text-slate-600 font-inter">{workOrder.item_name} • {stage?.name || workOrder.stage}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Badge className={priorityColors[workOrder.priority]}>{workOrder.priority}</Badge>
          <Badge className={statusColors[workOrder.status]}>{workOrder.status}</Badge>
        </div>
      </div>

      {/* Progress Card */}
      <Card className="border-slate-200">
        <CardContent className="p-6">
          <div className="grid grid-cols-4 gap-6 mb-4">
            <div>
              <div className="text-sm text-slate-500">Target</div>
              <div className="text-2xl font-bold">{workOrder.target_qty} {workOrder.target_uom}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500">Completed</div>
              <div className="text-2xl font-bold text-green-600">{workOrder.completed_qty}</div>
            </div>
            <div>
              <div className="text-sm text-slate-500">Wastage</div>
              <div className="text-2xl font-bold text-red-600">{workOrder.wastage_qty} ({workOrder.actual_wastage_percent}%)</div>
            </div>
            <div>
              <div className="text-sm text-slate-500">Machine</div>
              <div className="text-lg font-medium">{workOrder.machine_name || <span className="text-slate-400">Not assigned</span>}</div>
            </div>
          </div>
          <Progress value={progress} className="h-3" />
          <div className="text-sm text-center mt-1 text-slate-500">{progress.toFixed(1)}% Complete</div>
        </CardContent>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-3">
        {!workOrder.machine_id && (
          <Button onClick={() => setShowAssignDialog(true)}>
            <Cog className="h-4 w-4 mr-2" />Assign Machine
          </Button>
        )}
        {workOrder.machine_id && workOrder.status === 'pending' && (
          <Button onClick={handleStartWorkOrder} className="bg-green-600 hover:bg-green-700">
            <Play className="h-4 w-4 mr-2" />Start Production
          </Button>
        )}
        {workOrder.status === 'in_progress' && (
          <Button onClick={() => setShowEntryDialog(true)}>
            <Plus className="h-4 w-4 mr-2" />Add Production Entry
          </Button>
        )}
      </div>

      {/* Production Entries */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="text-lg">Production Entries</CardTitle>
        </CardHeader>
        <CardContent>
          {(workOrder.entries || []).length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              No production entries yet. Start the work order and add entries as production progresses.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Batch #</TableHead>
                  <TableHead>Date/Time</TableHead>
                  <TableHead>Input</TableHead>
                  <TableHead>Output</TableHead>
                  <TableHead>Wastage</TableHead>
                  <TableHead>Wastage %</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {workOrder.entries.map(entry => (
                  <TableRow key={entry.id}>
                    <TableCell className="font-medium">{entry.batch_no}</TableCell>
                    <TableCell>{new Date(entry.created_at).toLocaleString()}</TableCell>
                    <TableCell>{entry.input_qty} {entry.input_uom}</TableCell>
                    <TableCell className="text-green-600">{entry.output_qty} {entry.output_uom}</TableCell>
                    <TableCell className="text-red-600">{entry.wastage_qty}</TableCell>
                    <TableCell className={entry.wastage_exceeded ? 'text-red-600 font-medium' : ''}>
                      {entry.wastage_percent}%
                      {entry.wastage_exceeded && <AlertTriangle className="h-4 w-4 inline ml-1" />}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Assign Machine Dialog */}
      <Dialog open={showAssignDialog} onOpenChange={setShowAssignDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Machine</DialogTitle>
            <DialogDescription>Select a {workOrder.stage} machine for this work order</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            {filteredMachines.length === 0 ? (
              <div className="text-center py-4 text-slate-500">
                No active {workOrder.stage} machines found. Add machines in Machine Master.
              </div>
            ) : (
              filteredMachines.map(machine => (
                <div
                  key={machine.id}
                  onClick={() => handleAssignMachine(machine.id)}
                  className="p-3 border rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all"
                >
                  <div className="flex justify-between">
                    <div>
                      <div className="font-medium">{machine.machine_name}</div>
                      <div className="text-sm text-slate-500">{machine.machine_code} • {machine.location}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm">{machine.capacity} {machine.capacity_uom}</div>
                      <div className="text-xs text-orange-600">Wastage norm: {machine.wastage_norm_percent}%</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Production Entry Dialog - Stage Specific */}
      <Dialog open={showEntryDialog} onOpenChange={setShowEntryDialog}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <div className={`h-8 w-8 rounded-lg ${stage?.color || 'bg-slate-500'} flex items-center justify-center`}>
                <StageIcon className="h-4 w-4 text-white" />
              </div>
              {STAGE_FORM_FIELDS[workOrder.stage]?.title || 'Add Production Entry'}
            </DialogTitle>
            <DialogDescription>
              {STAGE_FORM_FIELDS[workOrder.stage]?.description || `Record production output for ${workOrder.wo_number}`}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitEntry} className="space-y-4">
            {/* Time & Operator Section */}
            <div className="p-3 bg-slate-50 rounded-lg space-y-3">
              <div className="text-sm font-medium text-slate-700">Time & Operator</div>
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <Label className="text-xs">Operator ID</Label>
                  <Input 
                    value={entryForm.operator_id}
                    onChange={(e) => setEntryForm({...entryForm, operator_id: e.target.value})}
                    placeholder="e.g., OP001"
                    className="h-9"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Start Time</Label>
                  <Input 
                    type="datetime-local"
                    value={entryForm.start_time}
                    onChange={(e) => setEntryForm({...entryForm, start_time: e.target.value})}
                    className="h-9"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">End Time</Label>
                  <Input 
                    type="datetime-local"
                    value={entryForm.end_time}
                    onChange={(e) => setEntryForm({...entryForm, end_time: e.target.value})}
                    className="h-9"
                  />
                </div>
              </div>
            </div>

            {/* Input/Output Section */}
            <div className="p-3 bg-blue-50 rounded-lg space-y-3">
              <div className="text-sm font-medium text-blue-800">Input & Output Quantities</div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Input Quantity *</Label>
                  <div className="flex gap-2">
                    <Input 
                      type="number"
                      value={entryForm.input_qty}
                      onChange={(e) => setEntryForm({...entryForm, input_qty: e.target.value})}
                      placeholder="e.g., 100"
                      required
                      className="flex-1"
                    />
                    <Select value={entryForm.input_uom} onValueChange={(v) => setEntryForm({...entryForm, input_uom: v})}>
                      <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pcs">PCS</SelectItem>
                        <SelectItem value="kg">KG</SelectItem>
                        <SelectItem value="sqm">SQM</SelectItem>
                        <SelectItem value="rolls">Rolls</SelectItem>
                        <SelectItem value="mtr">MTR</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Output Quantity *</Label>
                  <div className="flex gap-2">
                    <Input 
                      type="number"
                      value={entryForm.output_qty}
                      onChange={(e) => setEntryForm({...entryForm, output_qty: e.target.value})}
                      placeholder="e.g., 95"
                      required
                      className="flex-1"
                    />
                    <Select value={entryForm.output_uom} onValueChange={(v) => setEntryForm({...entryForm, output_uom: v})}>
                      <SelectTrigger className="w-24"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pcs">PCS</SelectItem>
                        <SelectItem value="kg">KG</SelectItem>
                        <SelectItem value="sqm">SQM</SelectItem>
                        <SelectItem value="rolls">Rolls</SelectItem>
                        <SelectItem value="mtr">MTR</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            </div>

            {/* Stage-Specific Fields */}
            {STAGE_FORM_FIELDS[workOrder.stage]?.fields && (
              <div className="p-3 bg-purple-50 rounded-lg space-y-3">
                <div className="text-sm font-medium text-purple-800 capitalize">{workOrder.stage} Stage Details</div>
                <div className="grid grid-cols-2 gap-3">
                  {STAGE_FORM_FIELDS[workOrder.stage].fields.map(field => (
                    <div key={field.key} className={`space-y-1 ${field.key === 'qc_video_url' ? 'col-span-2' : ''}`}>
                      <Label className="text-xs">{field.label}{field.required && ' *'}</Label>
                      {field.type === 'select' ? (
                        <Select 
                          value={entryForm[field.key] || ''} 
                          onValueChange={(v) => setEntryForm({...entryForm, [field.key]: v})}
                        >
                          <SelectTrigger className="h-9">
                            <SelectValue placeholder={`Select ${field.label.toLowerCase()}`} />
                          </SelectTrigger>
                          <SelectContent>
                            {field.options?.map(opt => (
                              <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      ) : (
                        <Input 
                          type={field.type || 'text'}
                          value={entryForm[field.key] || ''}
                          onChange={(e) => setEntryForm({...entryForm, [field.key]: e.target.value})}
                          placeholder={field.placeholder || ''}
                          required={field.required}
                          className="h-9"
                          readOnly={field.computed}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Wastage Section */}
            <div className="p-3 bg-red-50 rounded-lg space-y-3">
              <div className="text-sm font-medium text-red-800">Wastage Tracking</div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Wastage Quantity</Label>
                  <Input 
                    type="number"
                    value={entryForm.wastage_qty}
                    onChange={(e) => setEntryForm({...entryForm, wastage_qty: e.target.value})}
                    placeholder="e.g., 5"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Wastage Reason</Label>
                  <Select value={entryForm.wastage_reason} onValueChange={(v) => setEntryForm({...entryForm, wastage_reason: v})}>
                    <SelectTrigger><SelectValue placeholder="Select reason" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="setup">Machine Setup</SelectItem>
                      <SelectItem value="defect">Quality Defect</SelectItem>
                      <SelectItem value="material">Material Issue</SelectItem>
                      <SelectItem value="trim">Edge Trim</SelectItem>
                      <SelectItem value="adhesive">Adhesive Issue</SelectItem>
                      <SelectItem value="core">Core Defect</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {entryForm.input_qty && entryForm.wastage_qty && (
                <div className={`text-sm p-2 rounded ${(parseFloat(entryForm.wastage_qty) / parseFloat(entryForm.input_qty) * 100) > 5 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                  Calculated Wastage: {((parseFloat(entryForm.wastage_qty) / parseFloat(entryForm.input_qty)) * 100).toFixed(2)}%
                </div>
              )}
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <Label>Notes / Remarks</Label>
              <Textarea 
                value={entryForm.notes}
                onChange={(e) => setEntryForm({...entryForm, notes: e.target.value})}
                rows={2}
                placeholder="Add any additional notes about this production entry..."
              />
            </div>
            
            <DialogFooter className="pt-4 border-t">
              <Button type="button" variant="outline" onClick={() => setShowEntryDialog(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting} className="min-w-32">
                {submitting ? 'Saving...' : 'Save Production Entry'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// ==================== DPR REPORTS ====================
const DPRReports = () => {
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);
  const [dprData, setDprData] = useState(null);
  const [weeklyData, setWeeklyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('daily');
  const [selectedStage, setSelectedStage] = useState('all');

  useEffect(() => { fetchDPR(); }, [reportDate]);
  useEffect(() => { if (activeTab === 'weekly') fetchWeeklyDPR(); }, [activeTab]);

  const fetchDPR = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/production-stages/dpr/${reportDate}`);
      setDprData(res.data);
    } catch (error) {
      console.error('Failed to load DPR', error);
      toast.error('Failed to load Daily Production Report');
    } finally {
      setLoading(false);
    }
  };

  const fetchWeeklyDPR = async () => {
    try {
      const res = await api.get('/production-stages/dpr/summary/weekly');
      setWeeklyData(res.data);
    } catch (error) {
      console.error('Failed to load weekly summary', error);
    }
  };

  if (loading && !dprData) {
    return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;
  }

  const stageList = ['coating', 'slitting', 'rewinding', 'cutting', 'packing'];

  return (
    <div className="space-y-6" data-testid="dpr-reports">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Daily Production Report (DPR)</h2>
          <p className="text-slate-600 mt-1 font-inter">Stage-wise production analysis with wastage tracking</p>
        </div>
        <div className="flex gap-2 items-center">
          <Input 
            type="date" 
            value={reportDate} 
            onChange={(e) => setReportDate(e.target.value)}
            className="w-40"
          />
          <Button onClick={fetchDPR} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />Export
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="daily">Daily Report</TabsTrigger>
          <TabsTrigger value="weekly">Weekly Trend</TabsTrigger>
          <TabsTrigger value="stage">Stage Details</TabsTrigger>
        </TabsList>

        {/* Daily Report Tab */}
        <TabsContent value="daily" className="mt-4 space-y-4">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <Card className="border-slate-200">
              <CardContent className="p-4">
                <div className="text-sm text-slate-500">Total Entries</div>
                <div className="text-2xl font-bold text-slate-800">{dprData?.summary?.total_entries || 0}</div>
              </CardContent>
            </Card>
            <Card className="border-slate-200">
              <CardContent className="p-4">
                <div className="text-sm text-slate-500">Work Orders Active</div>
                <div className="text-2xl font-bold text-blue-600">{dprData?.summary?.total_work_orders_active || 0}</div>
              </CardContent>
            </Card>
            <Card className="border-slate-200">
              <CardContent className="p-4">
                <div className="text-sm text-slate-500">Total Output</div>
                <div className="text-2xl font-bold text-green-600">{dprData?.summary?.total_output || 0}</div>
              </CardContent>
            </Card>
            <Card className="border-slate-200">
              <CardContent className="p-4">
                <div className="text-sm text-slate-500">Total Wastage</div>
                <div className="text-2xl font-bold text-red-600">{dprData?.summary?.total_wastage || 0}</div>
              </CardContent>
            </Card>
            <Card className="border-slate-200">
              <CardContent className="p-4">
                <div className="text-sm text-slate-500">Hours Worked</div>
                <div className="text-2xl font-bold text-purple-600">{dprData?.summary?.total_hours_worked || 0}</div>
              </CardContent>
            </Card>
          </div>

          {/* Stage-wise Summary */}
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Stage-wise Production Summary</CardTitle>
              <CardDescription>Production metrics for {reportDate}</CardDescription>
            </CardHeader>
            <CardContent>
              {Object.keys(dprData?.stages || {}).length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  No production data for this date. Select a different date or add production entries.
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Stage</TableHead>
                      <TableHead>Entries</TableHead>
                      <TableHead>Input</TableHead>
                      <TableHead>Output</TableHead>
                      <TableHead>Wastage</TableHead>
                      <TableHead>Wastage %</TableHead>
                      <TableHead>Hours</TableHead>
                      <TableHead>Hourly Avg</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stageList.map(stage => {
                      const data = dprData?.stages?.[stage];
                      if (!data) return null;
                      const StageIcon = STAGES.find(s => s.id === stage)?.icon || Factory;
                      
                      return (
                        <TableRow key={stage}>
                          <TableCell className="font-medium">
                            <div className="flex items-center gap-2">
                              <StageIcon className="h-4 w-4 text-slate-500" />
                              <span className="capitalize">{stage}</span>
                            </div>
                          </TableCell>
                          <TableCell>{data.summary?.total_entries || 0}</TableCell>
                          <TableCell>{data.production?.total_input || 0}</TableCell>
                          <TableCell className="text-green-600 font-medium">{data.production?.total_output || 0}</TableCell>
                          <TableCell className="text-red-600">{data.production?.total_wastage || 0}</TableCell>
                          <TableCell>
                            <Badge className={data.production?.wastage_percent > 4 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}>
                              {data.production?.wastage_percent || 0}%
                            </Badge>
                          </TableCell>
                          <TableCell>{data.production?.total_hours || 0}</TableCell>
                          <TableCell className="text-blue-600 font-medium">{data.production?.hourly_avg || 0}</TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Machine-wise Production for each stage */}
          {Object.entries(dprData?.stages || {}).map(([stage, data]) => (
            data.machine_production?.length > 0 && (
              <Card key={stage} className="border-slate-200">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base capitalize">{stage} - Machine Production</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Machine</TableHead>
                        <TableHead>Entries</TableHead>
                        <TableHead>Output</TableHead>
                        <TableHead>Wastage</TableHead>
                        <TableHead>Wastage %</TableHead>
                        <TableHead>Norm</TableHead>
                        <TableHead>Hours</TableHead>
                        <TableHead>Hourly Avg</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {data.machine_production.map((machine, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-medium">{machine.machine_name}</TableCell>
                          <TableCell>{machine.entries}</TableCell>
                          <TableCell className="text-green-600">{machine.output}</TableCell>
                          <TableCell className="text-red-600">{machine.wastage}</TableCell>
                          <TableCell>
                            <Badge className={machine.above_norm ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}>
                              {machine.wastage_percent}%
                            </Badge>
                          </TableCell>
                          <TableCell className="text-slate-500">{machine.wastage_norm}%</TableCell>
                          <TableCell>{machine.hours?.toFixed(1)}</TableCell>
                          <TableCell className="text-blue-600">{machine.hourly_avg}</TableCell>
                          <TableCell>
                            {machine.above_norm ? (
                              <Badge className="bg-red-100 text-red-800"><AlertTriangle className="h-3 w-3 mr-1" />Above Norm</Badge>
                            ) : (
                              <Badge className="bg-green-100 text-green-800"><Check className="h-3 w-3 mr-1" />OK</Badge>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )
          ))}
        </TabsContent>

        {/* Weekly Trend Tab */}
        <TabsContent value="weekly" className="mt-4 space-y-4">
          {weeklyData ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="border-slate-200">
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-500">Total Output (7 days)</div>
                    <div className="text-2xl font-bold text-green-600">{weeklyData.totals?.total_output || 0}</div>
                  </CardContent>
                </Card>
                <Card className="border-slate-200">
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-500">Total Wastage</div>
                    <div className="text-2xl font-bold text-red-600">{weeklyData.totals?.total_wastage || 0}</div>
                  </CardContent>
                </Card>
                <Card className="border-slate-200">
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-500">Avg Daily Output</div>
                    <div className="text-2xl font-bold text-blue-600">{weeklyData.totals?.avg_daily_output || 0}</div>
                  </CardContent>
                </Card>
                <Card className="border-slate-200">
                  <CardContent className="p-4">
                    <div className="text-sm text-slate-500">Avg Wastage %</div>
                    <div className="text-2xl font-bold text-orange-600">{weeklyData.totals?.avg_wastage_percent || 0}%</div>
                  </CardContent>
                </Card>
              </div>

              <Card className="border-slate-200">
                <CardHeader>
                  <CardTitle className="text-lg">Daily Trend ({weeklyData.start_date} to {weeklyData.end_date})</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Entries</TableHead>
                        <TableHead>Output</TableHead>
                        <TableHead>Wastage</TableHead>
                        <TableHead>Wastage %</TableHead>
                        <TableHead>Hours</TableHead>
                        <TableHead>Hourly Avg</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {(weeklyData.daily_data || []).map(day => (
                        <TableRow key={day.date}>
                          <TableCell className="font-medium">{day.date}</TableCell>
                          <TableCell>{day.entries}</TableCell>
                          <TableCell className="text-green-600">{day.output}</TableCell>
                          <TableCell className="text-red-600">{day.wastage}</TableCell>
                          <TableCell>
                            <Badge className={day.wastage_percent > 4 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}>
                              {day.wastage_percent}%
                            </Badge>
                          </TableCell>
                          <TableCell>{day.hours}</TableCell>
                          <TableCell className="text-blue-600">{day.hourly_avg}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          ) : (
            <div className="text-center py-8 text-slate-500">Loading weekly data...</div>
          )}
        </TabsContent>

        {/* Stage Details Tab */}
        <TabsContent value="stage" className="mt-4 space-y-4">
          <div className="flex gap-2 mb-4">
            <Select value={selectedStage} onValueChange={setSelectedStage}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select stage" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Stages</SelectItem>
                {stageList.map(stage => (
                  <SelectItem key={stage} value={stage} className="capitalize">{stage}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {stageList.filter(s => selectedStage === 'all' || s === selectedStage).map(stage => {
            const data = dprData?.stages?.[stage];
            if (!data) return null;
            
            return (
              <Card key={stage} className="border-slate-200">
                <CardHeader>
                  <CardTitle className="text-lg capitalize">{stage} Stage - Detailed Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Stage-specific metrics */}
                    {Object.entries(data.stage_metrics || {}).map(([key, value]) => (
                      <div key={key} className="p-3 bg-slate-50 rounded-lg">
                        <div className="text-xs text-slate-500 capitalize">{key.replace(/_/g, ' ')}</div>
                        <div className="text-lg font-bold text-slate-800">
                          {typeof value === 'object' ? JSON.stringify(value) : value}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </TabsContent>
      </Tabs>
    </div>
  );
};

// ==================== MAIN COMPONENT ====================
const ProductionStages = () => {
  return (
    <div className="p-6">
      <Routes>
        <Route index element={<ProductionStagesDashboard />} />
        <Route path="machines" element={<MachineMaster />} />
        <Route path="order-sheets" element={<OrderSheetsList />} />
        <Route path="order-sheets/:orderSheetId" element={<OrderSheetDetail />} />
        <Route path="work-order/:workOrderId" element={<WorkOrderDetail />} />
        <Route path="stage/:stageId" element={<StageDetailView />} />
        <Route path="reports" element={<DPRReports />} />
      </Routes>
    </div>
  );
};

export default ProductionStages;
