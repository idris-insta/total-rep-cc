import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Users as UsersIcon, Building2, FileText, Beaker, TrendingUp, 
  Clock, RefreshCw
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import api from '../../../lib/api';
import { toast } from 'sonner';
import CustomerHealthWidget from '../../../components/CustomerHealthWidget';

const STATUS_COLORS = {
  new: 'bg-blue-500', contacted: 'bg-yellow-500', qualified: 'bg-green-500',
  proposal: 'bg-purple-500', negotiation: 'bg-orange-500', converted: 'bg-emerald-500', lost: 'bg-red-500',
  draft: 'bg-slate-400', sent: 'bg-blue-500', accepted: 'bg-green-500', rejected: 'bg-red-500', expired: 'bg-yellow-500'
};

const StatCard = ({ icon: Icon, iconBgClass, iconTextClass, value, label, onClick }) => (
  <Card 
    className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" 
    onClick={onClick}
    data-testid={`stat-card-${label.toLowerCase()}`}
  >
    <CardContent className="p-4">
      <div className="flex items-center justify-between">
        <div className={`h-12 w-12 rounded-lg ${iconBgClass} flex items-center justify-center`}>
          <Icon className={`h-6 w-6 ${iconTextClass}`} />
        </div>
        <div className="text-right">
          <div className={`text-3xl font-bold ${iconTextClass}`}>{value}</div>
          <p className="text-sm text-slate-500">{label}</p>
        </div>
      </div>
    </CardContent>
  </Card>
);

const MetricCard = ({ title, value, icon: Icon, iconClass, subtitle, showProgress, progressValue }) => (
  <Card className="border-slate-200 shadow-sm">
    <CardContent className="p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-slate-600">{title}</span>
        <Icon className={`h-4 w-4 ${iconClass}`} />
      </div>
      <div className={`text-2xl font-bold ${iconClass.replace('text-', 'text-').replace('-500', '-600')}`}>
        {value}
      </div>
      {showProgress && (
        <div className="h-2 bg-slate-100 rounded-full mt-2">
          <div className={`h-full ${iconClass.replace('text-', 'bg-')} rounded-full`} 
               style={{width: `${progressValue}%`}}></div>
        </div>
      )}
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </CardContent>
  </Card>
);

const DistributionChart = ({ title, data, total, colors = STATUS_COLORS, showValue = false }) => (
  <Card className="border-slate-200 shadow-sm">
    <CardHeader className="pb-2">
      <CardTitle className="text-base font-manrope">{title}</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="space-y-3">
        {Object.entries(data || {}).map(([key, value]) => {
          const count = typeof value === 'object' ? value.count : value;
          const valueAmount = typeof value === 'object' ? value.total : null;
          return (
            <div key={key} className={`flex items-center ${showValue ? 'justify-between p-2 bg-slate-50 rounded' : 'gap-3'}`}>
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${colors[key] || 'bg-slate-400'}`}></div>
                <span className="text-sm capitalize">{key}</span>
              </div>
              <div className={showValue ? 'text-right' : 'flex items-center gap-2 ml-auto'}>
                <span className="font-semibold">{count}</span>
                {valueAmount !== null && (
                  <span className="text-sm text-slate-500 ml-2 font-mono">₹{(valueAmount || 0).toLocaleString('en-IN')}</span>
                )}
                {!showValue && (
                  <div className="w-24 h-2 bg-slate-100 rounded-full">
                    <div className={`h-full rounded-full ${colors[key] || 'bg-slate-400'}`} 
                         style={{width: `${total ? (count / total) * 100 : 0}%`}}></div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {Object.keys(data || {}).length === 0 && (
          <p className="text-slate-400 text-center py-4">No data available</p>
        )}
      </div>
    </CardContent>
  </Card>
);

const RecentItemsList = ({ title, items, onViewAll, renderItem, emptyMessage = "No items yet" }) => (
  <Card className="border-slate-200 shadow-sm">
    <CardHeader className="pb-2">
      <div className="flex items-center justify-between">
        <CardTitle className="text-base font-manrope">{title}</CardTitle>
        <Button variant="ghost" size="sm" onClick={onViewAll}>View All</Button>
      </div>
    </CardHeader>
    <CardContent>
      {items.length === 0 ? (
        <p className="text-slate-400 text-center py-4">{emptyMessage}</p>
      ) : (
        <div className="space-y-2">
          {items.map(renderItem)}
        </div>
      )}
    </CardContent>
  </Card>
);

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
        <StatCard icon={UsersIcon} iconBgClass="bg-blue-100" iconTextClass="text-blue-600" 
                  value={stats.leads} label="Leads" onClick={() => navigate('/crm/leads')} />
        <StatCard icon={Building2} iconBgClass="bg-green-100" iconTextClass="text-green-600"
                  value={stats.accounts} label="Accounts" onClick={() => navigate('/crm/accounts')} />
        <StatCard icon={FileText} iconBgClass="bg-purple-100" iconTextClass="text-purple-600"
                  value={stats.quotations} label="Quotations" onClick={() => navigate('/crm/quotations')} />
        <StatCard icon={Beaker} iconBgClass="bg-orange-100" iconTextClass="text-orange-600"
                  value={stats.samples} label="Samples" onClick={() => navigate('/crm/samples')} />
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard title="Conversion Rate" value={`${stats.quote_conversion_rate}%`} 
                    icon={TrendingUp} iconClass="text-green-500" 
                    showProgress progressValue={stats.quote_conversion_rate} />
        <MetricCard title="Total Quote Value" 
                    value={`₹${(stats.total_quote_value || 0).toLocaleString('en-IN')}`}
                    icon={FileText} iconClass="text-purple-500" 
                    subtitle={`${stats.pending_quotations} pending quotes`} />
        <MetricCard title="Samples Pending" value={stats.pending_samples}
                    icon={Clock} iconClass="text-orange-500" subtitle="Awaiting feedback" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DistributionChart title="Leads by Status" data={stats.leads_by_status} total={stats.leads} />
        <DistributionChart title="Leads by Source" data={stats.leads_by_source} total={stats.leads} 
                           colors={{}} />
      </div>

      {/* Quotations & Outstanding */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DistributionChart title="Quotations by Status" data={stats.quotes_by_status} showValue />
        
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
                    <span className="font-bold text-red-600 font-mono">
                      ₹{(acc.receivable_amount || 0).toLocaleString('en-IN')}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <RecentItemsList 
          title="Recent Leads"
          items={recentLeads}
          onViewAll={() => navigate('/crm/leads')}
          emptyMessage="No leads yet"
          renderItem={(lead) => (
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
          )}
        />
        
        <RecentItemsList 
          title="Recent Quotations"
          items={recentQuotes}
          onViewAll={() => navigate('/crm/quotations')}
          emptyMessage="No quotations yet"
          renderItem={(quote) => (
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
          )}
        />

        <CustomerHealthWidget />
      </div>
    </div>
  );
};

export default CRMOverview;
