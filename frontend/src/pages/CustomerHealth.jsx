import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Heart, AlertTriangle, AlertCircle, CheckCircle, Star,
  Phone, MessageSquare, Search, RefreshCw, TrendingDown,
  DollarSign, Clock, ShoppingCart, Filter
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const CustomerHealth = () => {
  const [scores, setScores] = useState([]);
  const [summary, setSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');

  useEffect(() => {
    fetchHealthScores();
  }, []);

  const fetchHealthScores = async () => {
    setLoading(true);
    try {
      const response = await api.get('/customer-health/scores?limit=100');
      setScores(response.data.scores || []);
      setSummary(response.data.summary || {});
    } catch (error) {
      toast.error('Failed to load customer health scores');
    } finally {
      setLoading(false);
    }
  };

  const statusConfig = {
    CRITICAL: { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-100', border: 'border-red-300', label: 'Critical' },
    AT_RISK: { icon: AlertCircle, color: 'text-amber-600', bg: 'bg-amber-100', border: 'border-amber-300', label: 'At Risk' },
    HEALTHY: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', border: 'border-green-300', label: 'Healthy' },
    EXCELLENT: { icon: Star, color: 'text-blue-600', bg: 'bg-blue-100', border: 'border-blue-300', label: 'Excellent' }
  };

  const buyingStatusColors = {
    URGENT_FOLLOWUP: 'bg-red-100 text-red-800',
    GENTLE_REMINDER: 'bg-amber-100 text-amber-800',
    PRE_EMPTIVE_CHECK: 'bg-blue-100 text-blue-800',
    NO_ACTION: 'bg-green-100 text-green-800',
    NO_DATA: 'bg-slate-100 text-slate-600'
  };

  const debtorSegmentColors = {
    GOLD: 'bg-amber-100 text-amber-800 border-amber-300',
    SILVER: 'bg-slate-200 text-slate-700 border-slate-300',
    BRONZE: 'bg-orange-100 text-orange-800 border-orange-300',
    BLOCKED: 'bg-red-100 text-red-800 border-red-300',
    NEW: 'bg-purple-100 text-purple-800 border-purple-300'
  };

  const filteredScores = scores.filter(s => {
    const matchesSearch = s.account_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || s.health_status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="customer-health-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope">
            <Heart className="inline h-8 w-8 mr-2 text-red-500" />
            Customer Health Scores
          </h1>
          <p className="text-slate-600 mt-1 font-inter">Combined buying patterns & payment behavior analysis</p>
        </div>
        <Button onClick={fetchHealthScores} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="border-slate-200 col-span-1">
          <CardContent className="p-4 text-center">
            <div className="text-4xl font-bold text-slate-900">{summary.avg_health_score || 0}</div>
            <p className="text-sm text-slate-500">Avg Score</p>
            <Progress value={summary.avg_health_score || 0} className="h-2 mt-2" />
          </CardContent>
        </Card>
        
        {Object.entries(statusConfig).map(([status, config]) => {
          const Icon = config.icon;
          const count = summary[status.toLowerCase()] || 0;
          return (
            <Card 
              key={status} 
              className={`border-2 ${config.border} ${config.bg} cursor-pointer hover:shadow-md transition-all ${filterStatus === status ? 'ring-2 ring-accent' : ''}`}
              onClick={() => setFilterStatus(filterStatus === status ? 'all' : status)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className={`text-3xl font-bold ${config.color}`}>{count}</div>
                    <p className="text-sm text-slate-600">{config.label}</p>
                  </div>
                  <Icon className={`h-8 w-8 ${config.color} opacity-50`} />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* At Risk Outstanding Alert */}
      {summary.total_at_risk_outstanding > 0 && (
        <Card className="bg-red-50 border-red-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <TrendingDown className="h-6 w-6 text-red-600" />
                <div>
                  <p className="font-semibold text-red-800">Total At-Risk Outstanding</p>
                  <p className="text-sm text-red-600">From CRITICAL + AT_RISK customers</p>
                </div>
              </div>
              <div className="text-3xl font-bold text-red-700 font-mono">
                ₹{(summary.total_at_risk_outstanding || 0).toLocaleString('en-IN')}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Search customer..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Button
            variant={filterStatus === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterStatus('all')}
            className={filterStatus === 'all' ? 'bg-accent' : ''}
          >
            All ({summary.total_customers})
          </Button>
        </div>
      </div>

      {/* Customer List */}
      <Card className="border-slate-200">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">#</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Health Score</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Buying Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Payment</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Outstanding</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Risk Factors</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredScores.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-slate-400">
                      No customers found
                    </td>
                  </tr>
                ) : (
                  filteredScores.map((customer) => {
                    const config = statusConfig[customer.health_status];
                    const StatusIcon = config.icon;
                    return (
                      <tr key={customer.account_id} className={`hover:bg-slate-50 ${customer.health_status === 'CRITICAL' ? 'bg-red-50/30' : ''}`}>
                        <td className="px-4 py-3 text-sm text-slate-500">#{customer.priority_rank}</td>
                        <td className="px-4 py-3">
                          <div>
                            <p className="font-semibold text-slate-900">{customer.account_name}</p>
                            {customer.contact_name && (
                              <p className="text-xs text-slate-500">{customer.contact_name}</p>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className={`p-1 rounded ${config.bg}`}>
                              <StatusIcon className={`h-4 w-4 ${config.color}`} />
                            </div>
                            <div>
                              <div className="font-bold text-lg">{customer.health_score}</div>
                              <Badge className={`text-xs ${config.bg} ${config.color} border-0`}>
                                {config.label}
                              </Badge>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <Badge className={buyingStatusColors[customer.buying_status]}>
                            {customer.buying_status.replace(/_/g, ' ')}
                          </Badge>
                          {customer.days_since_last_order !== null && (
                            <p className="text-xs text-slate-500 mt-1">
                              {customer.days_since_last_order}d since order
                            </p>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <Badge className={`border ${debtorSegmentColors[customer.debtor_segment]}`}>
                            {customer.debtor_segment}
                          </Badge>
                          <p className="text-xs text-slate-500 mt-1">Score: {customer.payment_score}</p>
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-mono">
                            <p className="font-semibold">₹{customer.total_outstanding.toLocaleString('en-IN')}</p>
                            {customer.overdue_amount > 0 && (
                              <p className="text-xs text-red-600">₹{customer.overdue_amount.toLocaleString('en-IN')} overdue</p>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 max-w-xs">
                          <ul className="text-xs text-slate-600 space-y-1">
                            {customer.risk_factors.slice(0, 2).map((rf, i) => (
                              <li key={i} className="flex items-start gap-1">
                                <span className="text-amber-500">•</span>
                                <span>{rf}</span>
                              </li>
                            ))}
                          </ul>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1">
                            {customer.contact_phone && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => window.open(`tel:${customer.contact_phone}`)}
                                  title="Call"
                                >
                                  <Phone className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="text-green-600"
                                  onClick={() => {
                                    const phone = customer.contact_phone.replace(/\D/g, '');
                                    window.open(`https://wa.me/${phone.startsWith('91') ? phone : '91' + phone}`);
                                  }}
                                  title="WhatsApp"
                                >
                                  <MessageSquare className="h-4 w-4" />
                                </Button>
                              </>
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

export default CustomerHealth;
