import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { 
  Dna, Phone, MessageSquare, Mail, Clock, TrendingUp, Users, 
  AlertTriangle, CheckCircle, RefreshCw, Send, Calendar, DollarSign,
  ArrowRight, Copy, ExternalLink
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const BuyingDNA = () => {
  const [patterns, setPatterns] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAction, setFilterAction] = useState('all');
  const [selectedPattern, setSelectedPattern] = useState(null);
  const [whatsappDialogOpen, setWhatsappDialogOpen] = useState(false);

  useEffect(() => {
    fetchPatterns();
  }, []);

  const fetchPatterns = async () => {
    setLoading(true);
    try {
      const response = await api.get('/buying-dna/patterns');
      setPatterns(response.data.patterns || []);
      setSummary(response.data.summary || {});
    } catch (error) {
      toast.error('Failed to load buying patterns');
    } finally {
      setLoading(false);
    }
  };

  const logFollowup = async (accountId, actionType) => {
    try {
      await api.post(`/buying-dna/followup-log?account_id=${accountId}&action_type=${actionType}`);
      toast.success('Follow-up logged');
    } catch (error) {
      toast.error('Failed to log follow-up');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Message copied to clipboard');
  };

  const openWhatsApp = (phone, message) => {
    if (!phone) {
      toast.error('No phone number available');
      return;
    }
    const cleanPhone = phone.replace(/\D/g, '');
    const url = `https://wa.me/${cleanPhone.startsWith('91') ? cleanPhone : '91' + cleanPhone}?text=${encodeURIComponent(message)}`;
    window.open(url, '_blank');
    logFollowup(selectedPattern?.account_id, 'whatsapp_sent');
  };

  const filteredPatterns = patterns.filter(p => {
    const matchesSearch = p.account_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterAction === 'all' || p.suggested_action === filterAction;
    return matchesSearch && matchesFilter;
  });

  const actionColors = {
    URGENT_FOLLOWUP: 'bg-red-100 text-red-800 border-red-300',
    GENTLE_REMINDER: 'bg-amber-100 text-amber-800 border-amber-300',
    PRE_EMPTIVE_CHECK: 'bg-blue-100 text-blue-800 border-blue-300',
    NO_ACTION: 'bg-green-100 text-green-800 border-green-300'
  };

  const actionLabels = {
    URGENT_FOLLOWUP: '🚨 Urgent Follow-up',
    GENTLE_REMINDER: '📞 Gentle Reminder',
    PRE_EMPTIVE_CHECK: '👀 Pre-emptive Check',
    NO_ACTION: '✅ On Track'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="buying-dna">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope">
            <Dna className="inline h-8 w-8 mr-2 text-purple-600" />
            Buying DNA Sales Hunter
          </h1>
          <p className="text-slate-600 mt-1 font-inter">AI-powered purchase rhythm tracking & automated follow-ups</p>
        </div>
        <Button onClick={fetchPatterns} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-red-600">Urgent Follow-up</p>
                <p className="text-3xl font-bold text-red-700">{summary.urgent_followup || 0}</p>
              </div>
              <AlertTriangle className="h-10 w-10 text-red-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-amber-600">Gentle Reminder</p>
                <p className="text-3xl font-bold text-amber-700">{summary.gentle_reminder || 0}</p>
              </div>
              <Phone className="h-10 w-10 text-amber-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600">Pre-emptive Check</p>
                <p className="text-3xl font-bold text-blue-700">{summary.preemptive_check || 0}</p>
              </div>
              <Clock className="h-10 w-10 text-blue-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-green-200 bg-green-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-600">On Track</p>
                <p className="text-3xl font-bold text-green-700">{summary.no_action || 0}</p>
              </div>
              <CheckCircle className="h-10 w-10 text-green-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search customer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
        </div>
        <div className="flex gap-2">
          {['all', 'URGENT_FOLLOWUP', 'GENTLE_REMINDER', 'PRE_EMPTIVE_CHECK'].map(filter => (
            <Button
              key={filter}
              variant={filterAction === filter ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilterAction(filter)}
              className={filterAction === filter ? 'bg-accent' : ''}
            >
              {filter === 'all' ? 'All' : actionLabels[filter]?.split(' ')[0]}
            </Button>
          ))}
        </div>
      </div>

      {/* WhatsApp Dialog */}
      <Dialog open={whatsappDialogOpen} onOpenChange={setWhatsappDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-green-600" />
              WhatsApp Message for {selectedPattern?.account_name}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <pre className="whitespace-pre-wrap text-sm font-sans">{selectedPattern?.whatsapp_draft}</pre>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Phone className="h-4 w-4" />
              <span>{selectedPattern?.contact_phone || 'No phone available'}</span>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => copyToClipboard(selectedPattern?.whatsapp_draft)}>
              <Copy className="h-4 w-4 mr-2" />Copy Message
            </Button>
            <Button className="bg-green-600 hover:bg-green-700" onClick={() => openWhatsApp(selectedPattern?.contact_phone, selectedPattern?.whatsapp_draft)}>
              <ExternalLink className="h-4 w-4 mr-2" />Open WhatsApp
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Patterns List */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle>Customer Buying Patterns</CardTitle>
          <CardDescription>{filteredPatterns.length} customers tracked</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Avg Interval</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Days Since Order</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Avg Order Value</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredPatterns.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                      No patterns found. Customers need at least 2 orders to calculate buying rhythm.
                    </td>
                  </tr>
                ) : (
                  filteredPatterns.map((pattern) => (
                    <tr key={pattern.account_id} className={`hover:bg-slate-50 ${pattern.is_overdue ? 'bg-red-50/30' : ''}`}>
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-semibold text-slate-900">{pattern.account_name}</p>
                          <p className="text-xs text-slate-500">{pattern.contact_name}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-slate-400" />
                          <span className="font-mono">{pattern.avg_order_interval_days} days</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col">
                          <span className={`font-bold ${pattern.is_overdue ? 'text-red-600' : 'text-slate-900'}`}>
                            {pattern.days_since_last_order} days
                          </span>
                          {pattern.is_overdue && (
                            <span className="text-xs text-red-500">{pattern.overdue_days} days overdue</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={actionColors[pattern.suggested_action]}>
                          {actionLabels[pattern.suggested_action]}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-mono text-slate-700">₹{pattern.avg_order_value?.toLocaleString('en-IN')}</span>
                      </td>
                      <td className="px-4 py-3">
                        {pattern.suggested_action !== 'NO_ACTION' && (
                          <div className="flex items-center gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-green-600"
                              onClick={() => {
                                setSelectedPattern(pattern);
                                setWhatsappDialogOpen(true);
                              }}
                              title="Send WhatsApp"
                            >
                              <MessageSquare className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                if (pattern.contact_phone) {
                                  window.open(`tel:${pattern.contact_phone}`);
                                  logFollowup(pattern.account_id, 'call_made');
                                }
                              }}
                              title="Call"
                            >
                              <Phone className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
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

export default BuyingDNA;
