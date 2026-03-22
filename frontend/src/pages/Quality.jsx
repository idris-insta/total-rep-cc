import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { 
  Plus, Search, Edit, Eye, ClipboardCheck, AlertTriangle, 
  CheckCircle, XCircle, RefreshCw, Download, FileText, Package,
  BarChart3, TrendingUp, MessageSquare, Shield, Activity
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import api from '../lib/api';
import { toast } from 'sonner';

// ==================== QUALITY DASHBOARD ====================
const QualityDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_inspections: 0, passed: 0, failed: 0, pass_rate: 0,
    open_complaints: 0, resolved_complaints: 0, by_type: {}
  });
  const [loading, setLoading] = useState(true);
  const [recentInspections, setRecentInspections] = useState([]);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [summaryRes, inspectionsRes] = await Promise.all([
        api.get('/quality/reports/quality-summary'),
        api.get('/quality/inspections')
      ]);
      setStats({
        total_inspections: summaryRes.data.inspections.total,
        passed: summaryRes.data.inspections.passed,
        failed: summaryRes.data.inspections.failed,
        pass_rate: summaryRes.data.inspections.pass_rate,
        open_complaints: summaryRes.data.complaints.open,
        resolved_complaints: summaryRes.data.complaints.resolved,
        by_type: summaryRes.data.inspections.by_type
      });
      setRecentInspections(inspectionsRes.data.slice(0, 5));
    } catch (error) {
      console.error('Failed to load quality stats', error);
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
    <div className="space-y-6" data-testid="quality-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Quality Control</h2>
          <p className="text-slate-600 mt-1 font-inter">Inspections, complaints & batch traceability</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/quality/inspections')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <ClipboardCheck className="h-6 w-6 text-blue-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">{stats.total_inspections}</div>
                <p className="text-sm text-slate-500">Inspections</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-green-600">{stats.passed}</div>
                <p className="text-sm text-slate-500">Passed</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-red-100 flex items-center justify-center">
                <XCircle className="h-6 w-6 text-red-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-red-600">{stats.failed}</div>
                <p className="text-sm text-slate-500">Failed</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-emerald-100 flex items-center justify-center">
                <TrendingUp className="h-6 w-6 text-emerald-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-emerald-600">{stats.pass_rate}%</div>
                <p className="text-sm text-slate-500">Pass Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/quality/complaints')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center">
                <MessageSquare className="h-6 w-6 text-orange-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-orange-600">{stats.open_complaints}</div>
                <p className="text-sm text-slate-500">Open Complaints</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Inspection by Type */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="font-manrope">Inspections by Type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.by_type).map(([type, data]) => (
                <div key={type} className="p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-slate-900 capitalize">{type.replace('_', ' ')}</span>
                    <span className="text-sm text-slate-500">{data.total} inspections</span>
                  </div>
                  <div className="flex gap-4 text-sm">
                    <span className="text-green-600">✓ {data.passed} passed</span>
                    <span className="text-red-600">✗ {data.failed} failed</span>
                  </div>
                </div>
              ))}
              {Object.keys(stats.by_type).length === 0 && (
                <p className="text-center text-slate-500 py-4">No inspections yet</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="font-manrope">Recent Inspections</CardTitle>
            <Button variant="outline" size="sm" onClick={() => navigate('/quality/inspections')}>View All</Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {recentInspections.length === 0 ? (
                <p className="text-center text-slate-500 py-4">No inspections yet</p>
              ) : (
                recentInspections.map((insp) => (
                  <div key={insp.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50">
                    <div>
                      <p className="font-semibold text-slate-900 font-mono">{insp.inspection_number}</p>
                      <p className="text-sm text-slate-500 capitalize">{insp.inspection_type}</p>
                    </div>
                    <Badge className={insp.result === 'pass' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                      {insp.result}
                    </Badge>
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
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/quality/inspections')}>
              <ClipboardCheck className="h-6 w-6" />
              <span>Inspections</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/quality/complaints')}>
              <MessageSquare className="h-6 w-6" />
              <span>Complaints</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/quality/batch-trace')}>
              <Package className="h-6 w-6" />
              <span>Batch Trace</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/quality/tds')}>
              <FileText className="h-6 w-6" />
              <span>TDS/COA</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== QC INSPECTIONS ====================
const QCInspections = () => {
  const [inspections, setInspections] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({ inspection_type: 'all', result: 'all' });
  const [formData, setFormData] = useState({
    inspection_type: 'incoming', reference_type: 'GRN', reference_id: '',
    item_id: '', batch_number: '',
    test_parameters: [
      { name: 'Adhesive Strength', standard: '≥15 N/25mm', actual: '', result: 'pass' },
      { name: 'Tack', standard: 'Good', actual: '', result: 'pass' },
      { name: 'Thickness', standard: '40±5 micron', actual: '', result: 'pass' }
    ],
    inspector: '', notes: ''
  });

  useEffect(() => { fetchData(); }, [filters]);

  const fetchData = async () => {
    try {
      let url = '/quality/inspections?';
      if (filters.inspection_type !== 'all') url += `inspection_type=${filters.inspection_type}&`;
      if (filters.result !== 'all') url += `result=${filters.result}&`;

      const [inspectionsRes, itemsRes] = await Promise.all([
        api.get(url),
        api.get('/inventory/items')
      ]);
      setInspections(inspectionsRes.data);
      setItems(itemsRes.data);
    } catch (error) {
      toast.error('Failed to load inspections');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/quality/inspections', formData);
      toast.success('Inspection created');
      setOpen(false);
      fetchData();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create inspection');
    }
  };

  const resetForm = () => {
    setFormData({
      inspection_type: 'incoming', reference_type: 'GRN', reference_id: '',
      item_id: '', batch_number: '',
      test_parameters: [
        { name: 'Adhesive Strength', standard: '≥15 N/25mm', actual: '', result: 'pass' },
        { name: 'Tack', standard: 'Good', actual: '', result: 'pass' },
        { name: 'Thickness', standard: '40±5 micron', actual: '', result: 'pass' }
      ],
      inspector: '', notes: ''
    });
  };

  const addTestParameter = () => {
    setFormData({
      ...formData,
      test_parameters: [...formData.test_parameters, { name: '', standard: '', actual: '', result: 'pass' }]
    });
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="qc-inspections">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">QC Inspections</h2>
          <p className="text-slate-600 mt-1 font-inter">{inspections.length} inspections</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="create-inspection-button">
              <Plus className="h-4 w-4 mr-2" />New Inspection
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-manrope">Create QC Inspection</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Inspection Type *</Label>
                  <Select value={formData.inspection_type} onValueChange={(v) => setFormData({...formData, inspection_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="incoming">Incoming (RM)</SelectItem>
                      <SelectItem value="in_process">In-Process</SelectItem>
                      <SelectItem value="final">Final (FG)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Reference Type</Label>
                  <Select value={formData.reference_type} onValueChange={(v) => setFormData({...formData, reference_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="GRN">GRN</SelectItem>
                      <SelectItem value="Work Order">Work Order</SelectItem>
                      <SelectItem value="Production">Production</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Reference ID</Label>
                  <Input value={formData.reference_id} onChange={(e) => setFormData({...formData, reference_id: e.target.value})} placeholder="GRN-001" />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Item *</Label>
                  <Select value={formData.item_id} onValueChange={(v) => setFormData({...formData, item_id: v})}>
                    <SelectTrigger><SelectValue placeholder="Select item" /></SelectTrigger>
                    <SelectContent>
                      {items.map(item => (
                        <SelectItem key={item.id} value={item.id}>{item.item_code} - {item.item_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Batch Number</Label>
                  <Input value={formData.batch_number} onChange={(e) => setFormData({...formData, batch_number: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Inspector *</Label>
                  <Input value={formData.inspector} onChange={(e) => setFormData({...formData, inspector: e.target.value})} required />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Test Parameters</Label>
                  <Button type="button" variant="outline" size="sm" onClick={addTestParameter}>
                    <Plus className="h-4 w-4 mr-1" />Add Test
                  </Button>
                </div>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Test Parameter</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Standard</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600">Actual</th>
                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-600 w-24">Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {formData.test_parameters.map((param, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-2 py-2">
                            <Input className="h-9" value={param.name} onChange={(e) => {
                              const newParams = [...formData.test_parameters];
                              newParams[idx].name = e.target.value;
                              setFormData({...formData, test_parameters: newParams});
                            }} />
                          </td>
                          <td className="px-2 py-2">
                            <Input className="h-9" value={param.standard} onChange={(e) => {
                              const newParams = [...formData.test_parameters];
                              newParams[idx].standard = e.target.value;
                              setFormData({...formData, test_parameters: newParams});
                            }} />
                          </td>
                          <td className="px-2 py-2">
                            <Input className="h-9" value={param.actual} onChange={(e) => {
                              const newParams = [...formData.test_parameters];
                              newParams[idx].actual = e.target.value;
                              setFormData({...formData, test_parameters: newParams});
                            }} />
                          </td>
                          <td className="px-2 py-2">
                            <Select value={param.result} onValueChange={(v) => {
                              const newParams = [...formData.test_parameters];
                              newParams[idx].result = v;
                              setFormData({...formData, test_parameters: newParams});
                            }}>
                              <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                              <SelectContent>
                                <SelectItem value="pass">Pass</SelectItem>
                                <SelectItem value="fail">Fail</SelectItem>
                              </SelectContent>
                            </Select>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Create Inspection</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={filters.inspection_type} onValueChange={(v) => setFilters({...filters, inspection_type: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="incoming">Incoming</SelectItem>
            <SelectItem value="in_process">In-Process</SelectItem>
            <SelectItem value="final">Final</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters.result} onValueChange={(v) => setFilters({...filters, result: v})}>
          <SelectTrigger className="w-[130px]"><SelectValue placeholder="Result" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Results</SelectItem>
            <SelectItem value="pass">Passed</SelectItem>
            <SelectItem value="fail">Failed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Inspections Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Inspection #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Reference</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Batch</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Inspector</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Result</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {inspections.length === 0 ? (
                  <tr><td colSpan="8" className="px-4 py-12 text-center text-slate-500">No inspections found</td></tr>
                ) : (
                  inspections.map((insp) => (
                    <tr key={insp.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{insp.inspection_number}</td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="capitalize">{insp.inspection_type?.replace('_', ' ')}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">{insp.reference_type}: {insp.reference_id}</td>
                      <td className="px-4 py-3 text-sm font-mono text-slate-600">{insp.batch_number || '-'}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{insp.inspector}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{insp.created_at?.split('T')[0]}</td>
                      <td className="px-4 py-3">
                        <Badge className={insp.result === 'pass' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {insp.result === 'pass' ? '✓ Pass' : '✗ Fail'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
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

// ==================== COMPLAINTS ====================
const ComplaintsList = () => {
  const [complaints, setComplaints] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({ status: 'all', severity: 'all' });
  const [formData, setFormData] = useState({
    account_id: '', invoice_id: '', batch_number: '',
    complaint_type: 'quality', description: '', severity: 'medium'
  });

  useEffect(() => { fetchData(); }, [filters]);

  const fetchData = async () => {
    try {
      let url = '/quality/complaints?';
      if (filters.status !== 'all') url += `status=${filters.status}&`;
      if (filters.severity !== 'all') url += `severity=${filters.severity}&`;

      const [complaintsRes, accountsRes] = await Promise.all([
        api.get(url),
        api.get('/crm/accounts')
      ]);
      setComplaints(complaintsRes.data);
      setAccounts(accountsRes.data);
    } catch (error) {
      toast.error('Failed to load complaints');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/quality/complaints', formData);
      toast.success('Complaint registered');
      setOpen(false);
      fetchData();
      setFormData({ account_id: '', invoice_id: '', batch_number: '', complaint_type: 'quality', description: '', severity: 'medium' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to register complaint');
    }
  };

  const handleResolve = async (complaintId) => {
    const resolution = window.prompt('Enter resolution details:');
    if (!resolution) return;
    try {
      await api.put(`/quality/complaints/${complaintId}/resolve?resolution=${encodeURIComponent(resolution)}`);
      toast.success('Complaint resolved');
      fetchData();
    } catch (error) {
      toast.error('Failed to resolve complaint');
    }
  };

  const getAccountName = (accId) => {
    const acc = accounts.find(a => a.id === accId);
    return acc ? acc.customer_name : 'Unknown';
  };

  const statusColors = {
    open: 'bg-red-100 text-red-800',
    in_progress: 'bg-yellow-100 text-yellow-800',
    resolved: 'bg-green-100 text-green-800'
  };

  const severityColors = {
    low: 'bg-blue-100 text-blue-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    critical: 'bg-red-100 text-red-800'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="complaints-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Customer Complaints</h2>
          <p className="text-slate-600 mt-1 font-inter">{complaints.length} complaints</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="register-complaint-button">
              <Plus className="h-4 w-4 mr-2" />Register Complaint
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="font-manrope">Register Complaint</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Customer *</Label>
                <Select value={formData.account_id} onValueChange={(v) => setFormData({...formData, account_id: v})}>
                  <SelectTrigger><SelectValue placeholder="Select customer" /></SelectTrigger>
                  <SelectContent>
                    {accounts.map(acc => (
                      <SelectItem key={acc.id} value={acc.id}>{acc.customer_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Invoice ID</Label>
                  <Input value={formData.invoice_id} onChange={(e) => setFormData({...formData, invoice_id: e.target.value})} placeholder="INV-001" />
                </div>
                <div className="space-y-2">
                  <Label>Batch Number</Label>
                  <Input value={formData.batch_number} onChange={(e) => setFormData({...formData, batch_number: e.target.value})} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Complaint Type *</Label>
                  <Select value={formData.complaint_type} onValueChange={(v) => setFormData({...formData, complaint_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="quality">Quality Issue</SelectItem>
                      <SelectItem value="delivery">Delivery Issue</SelectItem>
                      <SelectItem value="packaging">Packaging Issue</SelectItem>
                      <SelectItem value="documentation">Documentation Issue</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Severity *</Label>
                  <Select value={formData.severity} onValueChange={(v) => setFormData({...formData, severity: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="low">Low</SelectItem>
                      <SelectItem value="medium">Medium</SelectItem>
                      <SelectItem value="high">High</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description *</Label>
                <Textarea value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} rows={3} required />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Register</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <Select value={filters.status} onValueChange={(v) => setFilters({...filters, status: v})}>
          <SelectTrigger className="w-[140px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters.severity} onValueChange={(v) => setFilters({...filters, severity: v})}>
          <SelectTrigger className="w-[130px]"><SelectValue placeholder="Severity" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Severity</SelectItem>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Complaints Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Complaint #</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Batch</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Severity</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {complaints.length === 0 ? (
                  <tr><td colSpan="8" className="px-4 py-12 text-center text-slate-500">No complaints found</td></tr>
                ) : (
                  complaints.map((complaint) => (
                    <tr key={complaint.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{complaint.complaint_number}</td>
                      <td className="px-4 py-3 text-sm text-slate-900">{getAccountName(complaint.account_id)}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 capitalize">{complaint.complaint_type}</td>
                      <td className="px-4 py-3 text-sm font-mono text-slate-600">{complaint.batch_number || '-'}</td>
                      <td className="px-4 py-3">
                        <Badge className={severityColors[complaint.severity]}>{complaint.severity}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={statusColors[complaint.status]}>{complaint.status}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">{complaint.created_at?.split('T')[0]}</td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
                          {complaint.status !== 'resolved' && (
                            <Button variant="outline" size="sm" onClick={() => handleResolve(complaint.id)} className="text-green-600">
                              <CheckCircle className="h-4 w-4" />
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

// ==================== BATCH TRACE ====================
const BatchTrace = () => {
  const [batchNumber, setBatchNumber] = useState('');
  const [traceData, setTraceData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!batchNumber) {
      toast.error('Please enter a batch number');
      return;
    }
    setLoading(true);
    try {
      const res = await api.get(`/quality/batch-trace/${batchNumber}`);
      setTraceData(res.data);
    } catch (error) {
      toast.error('Batch not found');
      setTraceData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="batch-trace">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 font-manrope">Batch Traceability</h2>
        <p className="text-slate-600 mt-1 font-inter">Track batch from production to delivery</p>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-6">
          <div className="flex gap-4 max-w-md">
            <Input 
              placeholder="Enter batch number..." 
              value={batchNumber} 
              onChange={(e) => setBatchNumber(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch} disabled={loading}>
              {loading ? 'Searching...' : 'Search'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {traceData && (
        <div className="space-y-4">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="font-manrope">Batch: {traceData.batch_number}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Production Info */}
              {traceData.production && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-2">Production Details</h4>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div><span className="text-slate-500">Work Order:</span> <span className="font-mono">{traceData.work_order?.wo_number}</span></div>
                    <div><span className="text-slate-500">Quantity:</span> {traceData.production.quantity_produced}</div>
                    <div><span className="text-slate-500">Operator:</span> {traceData.production.operator}</div>
                  </div>
                </div>
              )}

              {/* QC Inspections */}
              {traceData.qc_inspections?.length > 0 && (
                <div className="p-4 bg-green-50 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-2">QC Inspections ({traceData.qc_inspections.length})</h4>
                  <div className="space-y-2">
                    {traceData.qc_inspections.map((insp, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-white rounded">
                        <span className="font-mono text-sm">{insp.inspection_number}</span>
                        <Badge className={insp.result === 'pass' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {insp.result}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Complaints */}
              {traceData.complaints?.length > 0 && (
                <div className="p-4 bg-red-50 rounded-lg">
                  <h4 className="font-semibold text-red-800 mb-2">Related Complaints ({traceData.complaints.length})</h4>
                  <div className="space-y-2">
                    {traceData.complaints.map((complaint, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-white rounded">
                        <span className="font-mono text-sm">{complaint.complaint_number}</span>
                        <Badge className={complaint.status === 'resolved' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {complaint.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

// ==================== TDS/COA ====================
const TDSDocuments = () => {
  const [documents, setDocuments] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    item_id: '', document_type: 'TDS', document_url: '', version: '1.0', notes: ''
  });

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [docsRes, itemsRes] = await Promise.all([
        api.get('/quality/tds'),
        api.get('/inventory/items')
      ]);
      setDocuments(docsRes.data);
      setItems(itemsRes.data);
    } catch (error) {
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/quality/tds', formData);
      toast.success('Document added');
      setOpen(false);
      fetchData();
      setFormData({ item_id: '', document_type: 'TDS', document_url: '', version: '1.0', notes: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add document');
    }
  };

  const getItemName = (itemId) => {
    const item = items.find(i => i.id === itemId);
    return item ? `${item.item_code} - ${item.item_name}` : 'Unknown';
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="tds-documents">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">TDS & COA Documents</h2>
          <p className="text-slate-600 mt-1 font-inter">Technical data sheets & certificates</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90">
              <Plus className="h-4 w-4 mr-2" />Add Document
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Document</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Item *</Label>
                <Select value={formData.item_id} onValueChange={(v) => setFormData({...formData, item_id: v})}>
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
                  <Label>Document Type *</Label>
                  <Select value={formData.document_type} onValueChange={(v) => setFormData({...formData, document_type: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="TDS">Technical Data Sheet</SelectItem>
                      <SelectItem value="COA">Certificate of Analysis</SelectItem>
                      <SelectItem value="MSDS">Safety Data Sheet</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Version</Label>
                  <Input value={formData.version} onChange={(e) => setFormData({...formData, version: e.target.value})} />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Document URL *</Label>
                <Input value={formData.document_url} onChange={(e) => setFormData({...formData, document_url: e.target.value})} placeholder="https://..." required />
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Add</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Documents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.length === 0 ? (
          <Card className="col-span-full border-slate-200">
            <CardContent className="p-12 text-center text-slate-500">
              No documents uploaded yet
            </CardContent>
          </Card>
        ) : (
          documents.map((doc) => (
            <Card key={doc.id} className="border-slate-200 shadow-sm hover:shadow-md transition-all">
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
                    <FileText className="h-5 w-5 text-blue-600" />
                  </div>
                  <Badge variant="outline">{doc.document_type}</Badge>
                </div>
                <p className="font-semibold text-slate-900 text-sm mb-1">{getItemName(doc.item_id)}</p>
                <p className="text-xs text-slate-500 mb-3">Version {doc.version}</p>
                <Button variant="outline" size="sm" className="w-full" onClick={() => window.open(doc.document_url, '_blank')}>
                  <Download className="h-4 w-4 mr-2" />View Document
                </Button>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

// ==================== MAIN QUALITY COMPONENT ====================
const Quality = () => {
  return (
    <Routes>
      <Route index element={<QualityDashboard />} />
      <Route path="inspections" element={<QCInspections />} />
      <Route path="complaints" element={<ComplaintsList />} />
      <Route path="batch-trace" element={<BatchTrace />} />
      <Route path="tds" element={<TDSDocuments />} />
    </Routes>
  );
};

export default Quality;
