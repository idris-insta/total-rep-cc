import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { 
  FileText, QrCode, Truck, Settings, CheckCircle, XCircle, AlertTriangle,
  RefreshCw, Download, Eye, Loader2, FileCheck, Ban, Clock, Search
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const EInvoice = () => {
  const [activeTab, setActiveTab] = useState('einvoice');
  const [pendingInvoices, setPendingInvoices] = useState([]);
  const [summary, setSummary] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [selectedInvoices, setSelectedInvoices] = useState([]);
  const [showCredentials, setShowCredentials] = useState(false);
  const [showEwayBill, setShowEwayBill] = useState(null);
  const [showCancel, setShowCancel] = useState(null);
  
  const [credentials, setCredentials] = useState({
    gstin: '', username: '', password: '', client_id: '', client_secret: '', environment: 'sandbox'
  });
  
  const [ewayForm, setEwayForm] = useState({
    transporter_id: '', transporter_name: '', trans_doc_no: '', trans_doc_date: '',
    vehicle_no: '', vehicle_type: 'R', trans_mode: '1'
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [pendingRes, summaryRes, logsRes] = await Promise.all([
        api.get('/einvoice/pending-invoices'),
        api.get('/einvoice/summary'),
        api.get('/einvoice/logs?limit=50')
      ]);
      setPendingInvoices(pendingRes.data || []);
      setSummary(summaryRes.data);
      setLogs(logsRes.data || []);
    } catch (err) {
      console.error('Failed to fetch data', err);
    } finally {
      setLoading(false);
    }
  };

  const generateIRN = async (invoiceId) => {
    setProcessing(true);
    try {
      const res = await api.post('/einvoice/generate-irn', { invoice_id: invoiceId });
      toast.success(`IRN Generated: ${res.data.irn.substring(0, 20)}...`);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate IRN');
    } finally {
      setProcessing(false);
    }
  };

  const generateBulkIRN = async () => {
    if (selectedInvoices.length === 0) {
      toast.error('Please select invoices to process');
      return;
    }
    setProcessing(true);
    try {
      const res = await api.post('/einvoice/generate-irn/bulk', { invoice_ids: selectedInvoices });
      toast.success(res.data.message);
      setSelectedInvoices([]);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Bulk generation failed');
    } finally {
      setProcessing(false);
    }
  };

  const cancelIRN = async (irn, reason, remarks) => {
    setProcessing(true);
    try {
      await api.post('/einvoice/cancel-irn', { irn, cancel_reason: reason, cancel_remarks: remarks });
      toast.success('IRN cancelled successfully');
      setShowCancel(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to cancel IRN');
    } finally {
      setProcessing(false);
    }
  };

  const generateEwayBill = async () => {
    if (!showEwayBill) return;
    setProcessing(true);
    try {
      const res = await api.post('/einvoice/generate-eway-bill', {
        invoice_id: showEwayBill.id,
        ...ewayForm
      });
      toast.success(`E-Way Bill Generated: ${res.data.eway_bill_no}`);
      setShowEwayBill(null);
      setEwayForm({ transporter_id: '', transporter_name: '', trans_doc_no: '', trans_doc_date: '', vehicle_no: '', vehicle_type: 'R', trans_mode: '1' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate E-Way Bill');
    } finally {
      setProcessing(false);
    }
  };

  const saveCredentials = async () => {
    try {
      await api.post('/einvoice/credentials', credentials);
      toast.success('Credentials saved successfully');
      setShowCredentials(false);
    } catch (err) {
      toast.error('Failed to save credentials');
    }
  };

  const toggleInvoiceSelection = (id) => {
    setSelectedInvoices(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const selectAllInvoices = () => {
    if (selectedInvoices.length === pendingInvoices.length) {
      setSelectedInvoices([]);
    } else {
      setSelectedInvoices(pendingInvoices.map(inv => inv.id));
    }
  };

  return (
    <div className="space-y-6" data-testid="einvoice-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope">
            <FileText className="inline h-8 w-8 mr-2 text-accent" />
            GST E-Invoice & E-Way Bill
          </h1>
          <p className="text-slate-600 mt-1 font-inter">Generate IRN and E-Way Bills for GST compliance</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />Refresh
          </Button>
          <Dialog open={showCredentials} onOpenChange={setShowCredentials}>
            <DialogTrigger asChild>
              <Button variant="outline"><Settings className="h-4 w-4 mr-2" />API Settings</Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>NIC E-Invoice API Credentials</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>Currently running in <strong>Mock/Sandbox</strong> mode. Connect your NIC credentials for production.</AlertDescription>
                </Alert>
                <div className="grid grid-cols-2 gap-4">
                  <div><Label>GSTIN</Label><Input value={credentials.gstin} onChange={e => setCredentials({...credentials, gstin: e.target.value})} placeholder="Your GST Number" /></div>
                  <div><Label>Environment</Label>
                    <Select value={credentials.environment} onValueChange={v => setCredentials({...credentials, environment: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sandbox">Sandbox (Testing)</SelectItem>
                        <SelectItem value="production">Production (Live)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div><Label>Username</Label><Input value={credentials.username} onChange={e => setCredentials({...credentials, username: e.target.value})} /></div>
                  <div><Label>Password</Label><Input type="password" value={credentials.password} onChange={e => setCredentials({...credentials, password: e.target.value})} /></div>
                  <div><Label>Client ID</Label><Input value={credentials.client_id} onChange={e => setCredentials({...credentials, client_id: e.target.value})} /></div>
                  <div><Label>Client Secret</Label><Input type="password" value={credentials.client_secret} onChange={e => setCredentials({...credentials, client_secret: e.target.value})} /></div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowCredentials(false)}>Cancel</Button>
                <Button onClick={saveCredentials}>Save Credentials</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="border-slate-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Total Invoices</p>
                  <p className="text-2xl font-bold text-slate-900">{summary.total_invoices}</p>
                </div>
                <FileText className="h-8 w-8 text-slate-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">IRN Generated</p>
                  <p className="text-2xl font-bold text-green-600">{summary.irn_generated}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">IRN Pending</p>
                  <p className="text-2xl font-bold text-amber-600">{summary.irn_pending}</p>
                </div>
                <Clock className="h-8 w-8 text-amber-500" />
              </div>
            </CardContent>
          </Card>
          <Card className="border-slate-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">E-Way Bills</p>
                  <p className="text-2xl font-bold text-blue-600">{summary.eway_generated}</p>
                </div>
                <Truck className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 max-w-lg">
          <TabsTrigger value="einvoice"><QrCode className="h-4 w-4 mr-2" />E-Invoice</TabsTrigger>
          <TabsTrigger value="ewaybill"><Truck className="h-4 w-4 mr-2" />E-Way Bill</TabsTrigger>
          <TabsTrigger value="logs"><FileCheck className="h-4 w-4 mr-2" />Activity Logs</TabsTrigger>
        </TabsList>

        <TabsContent value="einvoice" className="space-y-4">
          <Card className="border-slate-200">
            <CardHeader className="flex-row items-center justify-between">
              <div>
                <CardTitle>Pending E-Invoices</CardTitle>
                <CardDescription>Invoices waiting for IRN generation</CardDescription>
              </div>
              {pendingInvoices.length > 0 && (
                <Button onClick={generateBulkIRN} disabled={selectedInvoices.length === 0 || processing}>
                  {processing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <QrCode className="h-4 w-4 mr-2" />}
                  Generate IRN ({selectedInvoices.length})
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {pendingInvoices.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                  <p>All invoices have IRN generated!</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-4 py-2 text-left">
                          <input type="checkbox" checked={selectedInvoices.length === pendingInvoices.length} onChange={selectAllInvoices} />
                        </th>
                        <th className="px-4 py-2 text-left text-sm font-medium">Invoice #</th>
                        <th className="px-4 py-2 text-left text-sm font-medium">Date</th>
                        <th className="px-4 py-2 text-left text-sm font-medium">Customer</th>
                        <th className="px-4 py-2 text-right text-sm font-medium">Amount</th>
                        <th className="px-4 py-2 text-center text-sm font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pendingInvoices.map(inv => (
                        <tr key={inv.id} className="border-b hover:bg-slate-50">
                          <td className="px-4 py-3">
                            <input type="checkbox" checked={selectedInvoices.includes(inv.id)} onChange={() => toggleInvoiceSelection(inv.id)} />
                          </td>
                          <td className="px-4 py-3 font-medium">{inv.invoice_number}</td>
                          <td className="px-4 py-3 text-slate-600">{inv.invoice_date}</td>
                          <td className="px-4 py-3 text-slate-600">{inv.account_name}</td>
                          <td className="px-4 py-3 text-right font-medium">₹{inv.grand_total?.toLocaleString('en-IN')}</td>
                          <td className="px-4 py-3 text-center">
                            <Button size="sm" onClick={() => generateIRN(inv.id)} disabled={processing}>
                              {processing ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Generate IRN'}
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ewaybill" className="space-y-4">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle>E-Way Bill Generation</CardTitle>
              <CardDescription>Generate E-Way Bills for invoices above ₹50,000</CardDescription>
            </CardHeader>
            <CardContent>
              <Alert className="mb-4">
                <Truck className="h-4 w-4" />
                <AlertTitle>E-Way Bill Requirement</AlertTitle>
                <AlertDescription>E-Way Bill is mandatory for transportation of goods valued above ₹50,000. Generate from the invoice list below.</AlertDescription>
              </Alert>
              
              <p className="text-sm text-slate-500 text-center py-8">
                Select an invoice from the main Accounts module to generate E-Way Bill
              </p>
            </CardContent>
          </Card>

          {/* E-Way Bill Form Dialog */}
          <Dialog open={!!showEwayBill} onOpenChange={() => setShowEwayBill(null)}>
            <DialogContent className="max-w-lg">
              <DialogHeader><DialogTitle>Generate E-Way Bill</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div><Label>Transporter ID (GSTIN)</Label><Input value={ewayForm.transporter_id} onChange={e => setEwayForm({...ewayForm, transporter_id: e.target.value})} /></div>
                  <div><Label>Transporter Name</Label><Input value={ewayForm.transporter_name} onChange={e => setEwayForm({...ewayForm, transporter_name: e.target.value})} /></div>
                  <div><Label>Transport Doc No</Label><Input value={ewayForm.trans_doc_no} onChange={e => setEwayForm({...ewayForm, trans_doc_no: e.target.value})} /></div>
                  <div><Label>Transport Doc Date</Label><Input type="date" value={ewayForm.trans_doc_date} onChange={e => setEwayForm({...ewayForm, trans_doc_date: e.target.value})} /></div>
                  <div><Label>Vehicle Number</Label><Input value={ewayForm.vehicle_no} onChange={e => setEwayForm({...ewayForm, vehicle_no: e.target.value})} placeholder="TN01AB1234" /></div>
                  <div><Label>Vehicle Type</Label>
                    <Select value={ewayForm.vehicle_type} onValueChange={v => setEwayForm({...ewayForm, vehicle_type: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="R">Regular</SelectItem>
                        <SelectItem value="O">Over Dimensional Cargo</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-2"><Label>Transport Mode</Label>
                    <Select value={ewayForm.trans_mode} onValueChange={v => setEwayForm({...ewayForm, trans_mode: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">Road</SelectItem>
                        <SelectItem value="2">Rail</SelectItem>
                        <SelectItem value="3">Air</SelectItem>
                        <SelectItem value="4">Ship</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowEwayBill(null)}>Cancel</Button>
                <Button onClick={generateEwayBill} disabled={processing}>
                  {processing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Truck className="h-4 w-4 mr-2" />}
                  Generate E-Way Bill
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle>Activity Logs</CardTitle>
              <CardDescription>Recent E-Invoice and E-Way Bill activities</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm font-medium">Timestamp</th>
                      <th className="px-4 py-2 text-left text-sm font-medium">Invoice</th>
                      <th className="px-4 py-2 text-left text-sm font-medium">Action</th>
                      <th className="px-4 py-2 text-left text-sm font-medium">IRN/E-Way Bill</th>
                      <th className="px-4 py-2 text-left text-sm font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map(log => (
                      <tr key={log.id} className="border-b hover:bg-slate-50">
                        <td className="px-4 py-3 text-sm text-slate-600">{new Date(log.created_at).toLocaleString('en-IN')}</td>
                        <td className="px-4 py-3 font-medium">{log.invoice_number}</td>
                        <td className="px-4 py-3">
                          <Badge variant={log.action === 'generate_irn' ? 'default' : log.action === 'cancel_irn' ? 'destructive' : 'secondary'}>
                            {log.action?.replace('_', ' ').toUpperCase()}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-sm font-mono">{log.irn?.substring(0, 20)}...</td>
                        <td className="px-4 py-3">
                          {log.status === 'success' ? (
                            <Badge className="bg-green-100 text-green-700"><CheckCircle className="h-3 w-3 mr-1" />Success</Badge>
                          ) : (
                            <Badge className="bg-red-100 text-red-700"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                    {logs.length === 0 && (
                      <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-500">No activity logs yet</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Cancel IRN Dialog */}
      <Dialog open={!!showCancel} onOpenChange={() => setShowCancel(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Cancel IRN</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>IRN can only be cancelled within 24 hours of generation. This action cannot be undone.</AlertDescription>
            </Alert>
            <div><Label>Cancel Reason</Label>
              <Select>
                <SelectTrigger><SelectValue placeholder="Select reason" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Duplicate</SelectItem>
                  <SelectItem value="2">Data Entry Mistake</SelectItem>
                  <SelectItem value="3">Order Cancelled</SelectItem>
                  <SelectItem value="4">Others</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div><Label>Remarks (Optional)</Label><Input placeholder="Additional remarks" /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCancel(null)}>Cancel</Button>
            <Button variant="destructive" disabled={processing}>
              {processing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Ban className="h-4 w-4 mr-2" />}
              Cancel IRN
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EInvoice;
