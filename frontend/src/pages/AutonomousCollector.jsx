import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { 
  DollarSign, Users, TrendingUp, TrendingDown, AlertTriangle, 
  Shield, Zap, Clock, RefreshCw, Send, Lock, Unlock, AlertCircle,
  BarChart3, Ban, CheckCircle, Phone, Mail, MessageSquare
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const AutonomousCollector = () => {
  const [segmentation, setSegmentation] = useState(null);
  const [reminders, setReminders] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [emergencyStatus, setEmergencyStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [emergencyDialogOpen, setEmergencyDialogOpen] = useState(false);
  const [emergencyForm, setEmergencyForm] = useState({
    action: 'FREEZE_ORDERS',
    scope: 'ALL',
    reason: '',
    duration_hours: 24
  });

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [segRes, remRes, analyticsRes, emergRes] = await Promise.all([
        api.get('/collector/debtors/segmentation').catch(() => ({ data: null })),
        api.get('/collector/reminders/pending').catch(() => ({ data: { reminders: [] } })),
        api.get('/collector/analytics/collection?period=month').catch(() => ({ data: null })),
        api.get('/collector/emergency/status').catch(() => ({ data: { emergency_active: false } }))
      ]);
      setSegmentation(segRes.data);
      setReminders(remRes.data?.reminders || []);
      setAnalytics(analyticsRes.data);
      setEmergencyStatus(emergRes.data);
    } catch (error) {
      console.error('Failed to fetch collector data');
    } finally {
      setLoading(false);
    }
  };

  const handleBlockDebtor = async (accountId, reason) => {
    try {
      await api.post(`/collector/debtors/${accountId}/block?reason=${encodeURIComponent(reason)}`);
      toast.success('Account blocked successfully');
      fetchAllData();
    } catch (error) {
      toast.error('Failed to block account');
    }
  };

  const handleUnblockDebtor = async (accountId) => {
    try {
      await api.post(`/collector/debtors/${accountId}/unblock`);
      toast.success('Account unblocked');
      fetchAllData();
    } catch (error) {
      toast.error('Failed to unblock account');
    }
  };

  const handleActivateEmergency = async () => {
    try {
      await api.post('/collector/emergency/activate', emergencyForm);
      toast.success('Emergency control activated');
      setEmergencyDialogOpen(false);
      fetchAllData();
    } catch (error) {
      toast.error('Failed to activate emergency control');
    }
  };

  const handleDeactivateEmergency = async (emergencyId) => {
    try {
      await api.post(`/collector/emergency/deactivate/${emergencyId}`);
      toast.success('Emergency control deactivated');
      fetchAllData();
    } catch (error) {
      toast.error('Failed to deactivate');
    }
  };

  const segmentColors = {
    GOLD: 'bg-amber-100 text-amber-800 border-amber-300',
    SILVER: 'bg-slate-100 text-slate-700 border-slate-300',
    BRONZE: 'bg-orange-100 text-orange-800 border-orange-300',
    BLOCKED: 'bg-red-100 text-red-800 border-red-300'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="autonomous-collector">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope">
            <Zap className="inline h-8 w-8 mr-2 text-amber-500" />
            Autonomous Collector
          </h1>
          <p className="text-slate-600 mt-1 font-inter">AI-powered revenue hunting and debt collection</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchAllData} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
          <Dialog open={emergencyDialogOpen} onOpenChange={setEmergencyDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-red-600 hover:bg-red-700" data-testid="emergency-button">
                <Shield className="h-4 w-4 mr-2" />Emergency Controls
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2 text-red-600">
                  <AlertTriangle className="h-5 w-5" />
                  Emergency Business Controls
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <p className="text-sm text-red-700">
                    <strong>Warning:</strong> These controls will immediately affect business operations. Use only in critical situations.
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Action Type</Label>
                  <Select value={emergencyForm.action} onValueChange={(v) => setEmergencyForm({...emergencyForm, action: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="HALT_PRODUCTION">Halt Production</SelectItem>
                      <SelectItem value="FREEZE_ORDERS">Freeze New Orders</SelectItem>
                      <SelectItem value="BLOCK_SHIPPING">Block Shipping</SelectItem>
                      <SelectItem value="LOCKDOWN">Full Lockdown</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Scope</Label>
                  <Select value={emergencyForm.scope} onValueChange={(v) => setEmergencyForm({...emergencyForm, scope: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ALL">All Branches</SelectItem>
                      <SelectItem value="BRANCH">Specific Branch</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Reason *</Label>
                  <Textarea 
                    value={emergencyForm.reason} 
                    onChange={(e) => setEmergencyForm({...emergencyForm, reason: e.target.value})}
                    placeholder="Reason for emergency action..."
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Duration (hours)</Label>
                  <Input 
                    type="number" 
                    value={emergencyForm.duration_hours} 
                    onChange={(e) => setEmergencyForm({...emergencyForm, duration_hours: parseInt(e.target.value)})}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setEmergencyDialogOpen(false)}>Cancel</Button>
                <Button className="bg-red-600 hover:bg-red-700" onClick={handleActivateEmergency} disabled={!emergencyForm.reason}>
                  Activate Emergency Control
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Emergency Alert Banner */}
      {emergencyStatus?.emergency_active && (
        <Card className="bg-red-50 border-red-300">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-6 w-6 text-red-600 animate-pulse" />
                <div>
                  <p className="font-bold text-red-800">EMERGENCY CONTROL ACTIVE</p>
                  <p className="text-sm text-red-600">{emergencyStatus.active_controls?.[0]?.action}: {emergencyStatus.active_controls?.[0]?.reason}</p>
                </div>
              </div>
              <Button variant="outline" className="border-red-300 text-red-700" onClick={() => handleDeactivateEmergency(emergencyStatus.active_controls?.[0]?.id)}>
                Deactivate
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Outstanding</p>
                <p className="text-2xl font-bold text-slate-900 font-mono">₹{(segmentation?.summary?.total_outstanding || 0).toLocaleString('en-IN')}</p>
              </div>
              <DollarSign className="h-10 w-10 text-blue-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Overdue Amount</p>
                <p className="text-2xl font-bold text-red-600 font-mono">₹{(segmentation?.summary?.total_overdue || 0).toLocaleString('en-IN')}</p>
              </div>
              <AlertCircle className="h-10 w-10 text-red-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Collection Efficiency</p>
                <p className="text-2xl font-bold text-green-600">{analytics?.collection_efficiency || 0}%</p>
              </div>
              <TrendingUp className="h-10 w-10 text-green-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Avg Collection Days</p>
                <p className="text-2xl font-bold text-amber-600">{analytics?.avg_collection_days || 0}</p>
              </div>
              <Clock className="h-10 w-10 text-amber-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="segmentation" className="space-y-4">
        <TabsList className="bg-white border border-slate-200">
          <TabsTrigger value="segmentation">Debtor Segmentation</TabsTrigger>
          <TabsTrigger value="reminders">Payment Reminders ({reminders.length})</TabsTrigger>
          <TabsTrigger value="analytics">Collection Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="segmentation">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {['GOLD', 'SILVER', 'BRONZE', 'BLOCKED'].map(segment => (
              <Card key={segment} className={`border-2 ${segmentColors[segment]}`}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{segment} Customers</CardTitle>
                    <Badge className={segmentColors[segment]}>{segmentation?.segment_counts?.[segment] || 0}</Badge>
                  </div>
                  <CardDescription>
                    {segment === 'GOLD' && 'Pays within terms, score 80-100'}
                    {segment === 'SILVER' && 'Occasional delays, score 50-79'}
                    {segment === 'BRONZE' && 'Frequent delays, score 20-49'}
                    {segment === 'BLOCKED' && 'Auto-blocked for non-payment'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {(segmentation?.segments?.[segment] || []).slice(0, 5).map(debtor => (
                      <div key={debtor.account_id} className="flex items-center justify-between p-2 bg-white/50 rounded-lg">
                        <div>
                          <p className="font-semibold text-sm">{debtor.account_name}</p>
                          <p className="text-xs text-slate-500">
                            Outstanding: ₹{debtor.total_outstanding?.toLocaleString('en-IN')} | Score: {debtor.payment_score}
                          </p>
                        </div>
                        {segment === 'BLOCKED' ? (
                          <Button size="sm" variant="ghost" onClick={() => handleUnblockDebtor(debtor.account_id)}>
                            <Unlock className="h-4 w-4" />
                          </Button>
                        ) : segment !== 'GOLD' && (
                          <Button size="sm" variant="ghost" className="text-red-600" onClick={() => handleBlockDebtor(debtor.account_id, 'Manual block by admin')}>
                            <Lock className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    ))}
                    {(segmentation?.segments?.[segment] || []).length === 0 && (
                      <p className="text-sm text-center py-4 text-slate-400">No customers in this segment</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="reminders">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle>Pending Payment Reminders</CardTitle>
              <CardDescription>Auto-generated reminders for upcoming and overdue payments</CardDescription>
            </CardHeader>
            <CardContent>
              {reminders.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <CheckCircle className="h-12 w-12 mx-auto mb-3 text-green-400" />
                  <p>All payments are on track! No reminders needed.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {reminders.map((reminder, idx) => (
                    <div key={idx} className={`p-4 rounded-lg border ${
                      reminder.priority === 'HIGH' ? 'bg-red-50 border-red-200' : 
                      reminder.type === 'GENTLE_REMINDER' ? 'bg-blue-50 border-blue-200' : 'bg-amber-50 border-amber-200'
                    }`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge className={
                              reminder.priority === 'HIGH' ? 'bg-red-100 text-red-800' : 
                              reminder.type === 'GENTLE_REMINDER' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'
                            }>
                              {reminder.type.replace(/_/g, ' ')}
                            </Badge>
                            <span className="text-sm font-mono">{reminder.invoice_number}</span>
                          </div>
                          <p className="font-semibold">{reminder.account_name}</p>
                          <p className="text-sm text-slate-600">
                            Amount: <span className="font-mono font-bold">₹{reminder.amount?.toLocaleString('en-IN')}</span>
                            {reminder.days_overdue ? ` | ${reminder.days_overdue} days overdue` : ` | Due in ${reminder.days_until_due} days`}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          {reminder.phone && (
                            <Button size="sm" variant="ghost" title={`Call ${reminder.phone}`}>
                              <Phone className="h-4 w-4" />
                            </Button>
                          )}
                          {reminder.email && (
                            <Button size="sm" variant="ghost" title={`Email ${reminder.email}`}>
                              <Mail className="h-4 w-4" />
                            </Button>
                          )}
                          <Button size="sm" variant="ghost" className="text-green-600" title="Send WhatsApp">
                            <MessageSquare className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="mt-2 p-2 bg-white/50 rounded text-xs text-slate-600 font-mono">
                        {reminder.message_template}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle>Collection Summary</CardTitle>
                <CardDescription>Last {analytics?.period || 'month'}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <span className="text-slate-600">Total Invoiced</span>
                    <span className="font-bold font-mono">₹{(analytics?.total_invoiced || 0).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <span className="text-slate-600">Total Collected</span>
                    <span className="font-bold font-mono text-green-600">₹{(analytics?.total_collected || 0).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                    <span className="text-slate-600">Pending Collection</span>
                    <span className="font-bold font-mono text-amber-600">₹{(analytics?.pending_collection || 0).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                    <span className="text-slate-600">Payment Count</span>
                    <span className="font-bold">{analytics?.payment_count || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-600">Collection Efficiency</span>
                      <span className="font-bold text-green-600">{analytics?.collection_efficiency || 0}%</span>
                    </div>
                    <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500 rounded-full transition-all duration-500"
                        style={{ width: `${analytics?.collection_efficiency || 0}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-slate-600">Avg Collection Days</span>
                      <span className="font-bold">{analytics?.avg_collection_days || 0} days</span>
                    </div>
                    <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 ${
                          (analytics?.avg_collection_days || 0) <= 30 ? 'bg-green-500' :
                          (analytics?.avg_collection_days || 0) <= 45 ? 'bg-amber-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(100, ((analytics?.avg_collection_days || 0) / 60) * 100)}%` }}
                      />
                    </div>
                    <p className="text-xs text-slate-400 mt-1">Target: 30 days</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AutonomousCollector;
