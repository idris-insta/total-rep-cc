import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, Beaker, Users as UsersIcon, Building2, 
  TrendingUp, Clock, RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import api from '../../lib/api';
import { toast } from 'sonner';

const CRMOverview = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ 
    leads: 0, accounts: 0, quotations: 0, samples: 0,
    pending_quotations: 0, pending_samples: 0, quote_conversion_rate: 0,
    total_quote_value: 0, leads_by_status: {}, leads_by_source: {},
    quotes_by_status: {}, accounts_by_state: {}, top_outstanding: []
  });
  const [loading, setLoading] = useState(true);
  const [recentLeads, setRecentLeads] = useState([]);
  const [recentQuotes, setRecentQuotes] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, leadsRes, quotesRes] = await Promise.all([
        api.get('/crm/stats/overview'),
        api.get('/crm/leads'),
        api.get('/crm/quotations')
      ]);
      setStats(statsRes.data);
      setRecentLeads(leadsRes.data.slice(0, 5));
      setRecentQuotes(quotesRes.data.slice(0, 5));
    } catch (error) {
      toast.error('Failed to load CRM data');
    } finally {
      setLoading(false);
    }
  };

  const statusColors = {
    new: 'bg-blue-500', contacted: 'bg-yellow-500', qualified: 'bg-green-500',
    proposal: 'bg-purple-500', negotiation: 'bg-orange-500', converted: 'bg-emerald-500', lost: 'bg-red-500',
    draft: 'bg-slate-400', sent: 'bg-blue-500', accepted: 'bg-green-500', rejected: 'bg-red-500', expired: 'bg-yellow-500'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="crm-overview">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">CRM Dashboard</h2>
          <p className="text-slate-600 mt-1 font-inter">Complete sales pipeline analytics</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/crm/leads')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <UsersIcon className="h-6 w-6 text-blue-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">{stats.leads}</div>
                <p className="text-sm text-slate-500">Leads</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/crm/accounts')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                <Building2 className="h-6 w-6 text-green-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-green-600">{stats.accounts}</div>
                <p className="text-sm text-slate-500">Accounts</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/crm/quotations')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-purple-100 flex items-center justify-center">
                <FileText className="h-6 w-6 text-purple-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-purple-600">{stats.quotations}</div>
                <p className="text-sm text-slate-500">Quotations</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/crm/samples')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center">
                <Beaker className="h-6 w-6 text-orange-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-orange-600">{stats.samples}</div>
                <p className="text-sm text-slate-500">Samples</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-600">Conversion Rate</span>
              <TrendingUp className="h-4 w-4 text-green-500" />
            </div>
            <div className="text-2xl font-bold text-green-600">{stats.quote_conversion_rate}%</div>
            <div className="h-2 bg-slate-100 rounded-full mt-2">
              <div className="h-full bg-green-500 rounded-full" style={{width: `${stats.quote_conversion_rate}%`}}></div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-600">Total Quote Value</span>
              <FileText className="h-4 w-4 text-purple-500" />
            </div>
            <div className="text-2xl font-bold text-purple-600 font-mono">₹{(stats.total_quote_value || 0).toLocaleString('en-IN')}</div>
            <p className="text-xs text-slate-500 mt-1">{stats.pending_quotations} pending quotes</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-600">Samples Pending</span>
              <Clock className="h-4 w-4 text-orange-500" />
            </div>
            <div className="text-2xl font-bold text-orange-600">{stats.pending_samples}</div>
            <p className="text-xs text-slate-500 mt-1">Awaiting feedback</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Leads by Status */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-manrope">Leads by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.leads_by_status || {}).map(([status, count]) => (
                <div key={status} className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${statusColors[status] || 'bg-slate-400'}`}></div>
                  <span className="flex-1 text-sm capitalize">{status}</span>
                  <span className="font-semibold">{count}</span>
                  <div className="w-24 h-2 bg-slate-100 rounded-full">
                    <div className={`h-full rounded-full ${statusColors[status] || 'bg-slate-400'}`} 
                         style={{width: `${(count / stats.leads) * 100}%`}}></div>
                  </div>
                </div>
              ))}
              {Object.keys(stats.leads_by_status || {}).length === 0 && (
                <p className="text-slate-400 text-center py-4">No leads data</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Leads by Source */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-manrope">Leads by Source</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.leads_by_source || {}).map(([source, count]) => (
                <div key={source} className="flex items-center gap-3">
                  <span className="flex-1 text-sm">{source}</span>
                  <span className="font-semibold">{count}</span>
                  <div className="w-24 h-2 bg-slate-100 rounded-full">
                    <div className="h-full bg-blue-500 rounded-full" 
                         style={{width: `${(count / stats.leads) * 100}%`}}></div>
                  </div>
                </div>
              ))}
              {Object.keys(stats.leads_by_source || {}).length === 0 && (
                <p className="text-slate-400 text-center py-4">No source data</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quotations Analysis & Top Outstanding */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-manrope">Quotations by Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.quotes_by_status || {}).map(([status, data]) => (
                <div key={status} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${statusColors[status] || 'bg-slate-400'}`}></div>
                    <span className="text-sm capitalize">{status}</span>
                  </div>
                  <div className="text-right">
                    <span className="font-semibold">{data.count}</span>
                    <span className="text-sm text-slate-500 ml-2 font-mono">₹{(data.total || 0).toLocaleString('en-IN')}</span>
                  </div>
                </div>
              ))}
              {Object.keys(stats.quotes_by_status || {}).length === 0 && (
                <p className="text-slate-400 text-center py-4">No quotation data</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-manrope">Top Outstanding Accounts</CardTitle>
          </CardHeader>
          <CardContent>
            {(stats.top_outstanding || []).length === 0 ? (
              <p className="text-slate-400 text-center py-4">No outstanding accounts</p>
            ) : (
              <div className="space-y-3">
                {stats.top_outstanding.map((acc, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-red-50 rounded">
                    <div>
                      <p className="font-semibold text-sm">{acc.customer_name}</p>
                      <p className="text-xs text-slate-500">{acc.billing_city}</p>
                    </div>
                    <span className="font-bold text-red-600 font-mono">₹{(acc.receivable_amount || 0).toLocaleString('en-IN')}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-manrope">Recent Leads</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => navigate('/crm/leads')}>View All</Button>
            </div>
          </CardHeader>
          <CardContent>
            {recentLeads.length === 0 ? (
              <p className="text-slate-400 text-center py-4">No leads yet</p>
            ) : (
              <div className="space-y-2">
                {recentLeads.map((lead) => (
                  <div key={lead.id} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                    <div>
                      <p className="font-semibold text-sm">{lead.company_name}</p>
                      <p className="text-xs text-slate-500">{lead.contact_person}</p>
                    </div>
                    <Badge className={`text-xs ${
                      lead.status === 'new' ? 'bg-blue-100 text-blue-800' :
                      lead.status === 'qualified' ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-800'
                    }`}>{lead.status}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-manrope">Recent Quotations</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => navigate('/crm/quotations')}>View All</Button>
            </div>
          </CardHeader>
          <CardContent>
            {recentQuotes.length === 0 ? (
              <p className="text-slate-400 text-center py-4">No quotations yet</p>
            ) : (
              <div className="space-y-2">
                {recentQuotes.map((quote) => (
                  <div key={quote.id} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                    <div>
                      <p className="font-semibold text-sm font-mono">{quote.quote_number}</p>
                      <p className="text-xs text-slate-500">{quote.account_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-sm font-mono">₹{(quote.grand_total || 0).toLocaleString('en-IN')}</p>
                      <Badge className={`text-xs ${
                        quote.status === 'accepted' ? 'bg-green-100 text-green-800' :
                        quote.status === 'sent' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-800'
                      }`}>{quote.status}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default CRMOverview;
