import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  TrendingUp, Package, Factory, DollarSign, Users, AlertTriangle, CheckCircle, 
  Clock, Sparkles, Zap, FileText, Settings, Shield, ArrowRight, Bell, Wand2,
  Database, UserPlus, BarChart3, AlertCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import api from '../lib/api';
import { toast } from 'sonner';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const StatCard = ({ title, value, change, icon: Icon, color }) => (
  <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all" data-testid={`stat-card-${title.toLowerCase().replace(/\s+/g, '-')}`}>
    <CardHeader className="flex flex-row items-center justify-between pb-2">
      <CardTitle className="text-sm font-medium text-slate-600 font-inter">{title}</CardTitle>
      <div className={`h-10 w-10 rounded-lg ${color} flex items-center justify-center`}>
        <Icon className="h-5 w-5 text-white" strokeWidth={2} />
      </div>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold text-slate-900 font-manrope">{value}</div>
      {change && (
        <p className="text-xs text-slate-500 mt-1 font-inter">
          <span className={change > 0 ? 'text-success' : 'text-destructive'}>
            {change > 0 ? '+' : ''}{change}%
          </span>
          {' '}from last month
        </p>
      )}
    </CardContent>
  </Card>
);

const AIInsightsCard = ({ loading, insights }) => (
  <Card className="border-slate-200 shadow-sm col-span-full" data-testid="ai-insights-card">
    <CardHeader>
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-accent" />
        <CardTitle className="font-manrope">AI-Powered Business Insights</CardTitle>
      </div>
      <CardDescription className="font-inter">Real-time analysis and recommendations</CardDescription>
    </CardHeader>
    <CardContent>
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-accent border-t-transparent rounded-full"></div>
        </div>
      ) : (
        <div className="prose prose-sm max-w-none">
          <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg p-6 border border-orange-200">
            <pre className="whitespace-pre-wrap text-sm text-slate-800 font-inter leading-relaxed">{insights}</pre>
          </div>
        </div>
      )}
    </CardContent>
  </Card>
);

// Quick Actions Widget - Surfaces most-used features
const QuickActionsWidget = ({ actions, navigate }) => {
  const iconMap = {
    DollarSign: DollarSign,
    CheckCircle: CheckCircle,
    Package: Package,
    Factory: Factory,
    Users: Users,
    FileText: FileText,
    Settings: Settings,
    Bell: Bell,
    AlertTriangle: AlertTriangle
  };

  const colorMap = {
    red: 'bg-red-100 text-red-700 border-red-200',
    orange: 'bg-orange-100 text-orange-700 border-orange-200',
    amber: 'bg-amber-100 text-amber-700 border-amber-200',
    purple: 'bg-purple-100 text-purple-700 border-purple-200',
    blue: 'bg-blue-100 text-blue-700 border-blue-200',
    green: 'bg-green-100 text-green-700 border-green-200'
  };

  const quickLinks = [
    { label: 'Add Lead', icon: UserPlus, link: '/crm/leads', color: 'blue' },
    { label: 'Create Quotation', icon: FileText, link: '/crm/quotations', color: 'purple' },
    { label: 'New Invoice', icon: DollarSign, link: '/accounts', color: 'green' },
    { label: 'Run Report', icon: BarChart3, link: '/analytics', color: 'orange' },
    { label: 'Custom Fields', icon: Wand2, link: '/customization', color: 'purple' },
    { label: 'AI Dashboard', icon: Sparkles, link: '/ai-dashboard', color: 'amber' }
  ];

  return (
    <Card className="border-slate-200 shadow-sm" data-testid="quick-actions-widget">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-amber-500" />
            <CardTitle className="text-lg font-manrope">Quick Actions</CardTitle>
          </div>
          <Badge variant="outline" className="text-xs">{actions?.length || 0} items need attention</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Action Items */}
        {actions && actions.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Needs Attention</p>
            <div className="grid grid-cols-2 gap-2">
              {actions.slice(0, 4).map((action) => {
                const IconComponent = iconMap[action.icon] || AlertCircle;
                return (
                  <button
                    key={action.id}
                    onClick={() => navigate(action.link)}
                    className={`flex items-center gap-3 p-3 rounded-lg border ${colorMap[action.color] || 'bg-slate-100'} hover:shadow-md transition-all text-left group`}
                    data-testid={`quick-action-${action.id}`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <IconComponent className="h-4 w-4" />
                        <span className="text-2xl font-bold">{action.count}</span>
                      </div>
                      <p className="text-xs mt-1">{action.label}</p>
                    </div>
                    <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Quick Links */}
        <div className="space-y-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Quick Links</p>
          <div className="grid grid-cols-3 gap-2">
            {quickLinks.map((link) => (
              <button
                key={link.label}
                onClick={() => navigate(link.link)}
                className="flex flex-col items-center gap-1 p-3 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-all"
                data-testid={`quick-link-${link.label.toLowerCase().replace(/\s+/g, '-')}`}
              >
                <link.icon className="h-5 w-5 text-slate-600" />
                <span className="text-xs text-slate-600 text-center">{link.label}</span>
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [aiInsights, setAiInsights] = useState(null);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [revenueData, setRevenueData] = useState(null);
  const [quickActions, setQuickActions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [overviewRes, revenueRes, actionsRes] = await Promise.all([
        api.get('/dashboard/overview'),
        api.get('/dashboard/revenue-analytics?period=month'),
        api.get('/collector/quick-actions').catch(() => ({ data: { actions: [] } }))
      ]);
      setOverview(overviewRes.data);
      setRevenueData(revenueRes.data);
      setQuickActions(actionsRes.data?.actions || []);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const fetchAIInsights = async () => {
    try {
      setLoadingInsights(true);
      const response = await api.get('/dashboard/ai-insights');
      setAiInsights(response.data.insights);
    } catch (error) {
      toast.error('Failed to load AI insights');
      setAiInsights('AI insights temporarily unavailable.');
    } finally {
      setLoadingInsights(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  const pieData = overview ? [
    { name: 'Received', value: overview.revenue.received, color: '#10b981' },
    { name: 'Pending', value: overview.revenue.pending, color: '#f59e0b' }
  ] : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope" data-testid="dashboard-title">Executive Dashboard</h1>
          <p className="text-slate-600 mt-1 font-inter">Real-time business intelligence and analytics</p>
        </div>
        <Button
          onClick={fetchAIInsights}
          disabled={loadingInsights}
          className="bg-accent hover:bg-accent/90 font-inter"
          data-testid="generate-insights-button"
        >
          <Sparkles className="h-4 w-4 mr-2" />
          {loadingInsights ? 'Generating...' : 'Generate AI Insights'}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Revenue"
          value={`₹${(overview?.revenue?.total_billed || 0).toLocaleString('en-IN')}`}
          icon={DollarSign}
          color="bg-gradient-to-br from-emerald-500 to-emerald-600"
        />
        <StatCard
          title="Active Leads"
          value={overview?.crm?.leads || 0}
          icon={TrendingUp}
          color="bg-gradient-to-br from-blue-500 to-blue-600"
        />
        <StatCard
          title="Production WOs"
          value={overview?.production?.wo_in_progress || 0}
          icon={Factory}
          color="bg-gradient-to-br from-purple-500 to-purple-600"
        />
        <StatCard
          title="Low Stock Items"
          value={overview?.inventory?.low_stock_items || 0}
          icon={Package}
          color="bg-gradient-to-br from-orange-500 to-orange-600"
        />
      </div>

      {/* Quick Actions Widget */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <QuickActionsWidget actions={quickActions} navigate={navigate} />
        </div>
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-emerald-500" />
              <CardTitle className="text-lg font-manrope">System Health</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between p-2 bg-emerald-50 rounded-lg">
              <span className="text-sm text-emerald-700">All services operational</span>
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2 bg-slate-50 rounded">
                <p className="text-slate-500">Uptime</p>
                <p className="font-bold text-slate-900">99.9%</p>
              </div>
              <div className="p-2 bg-slate-50 rounded">
                <p className="text-slate-500">Response</p>
                <p className="font-bold text-slate-900">&lt;100ms</p>
              </div>
            </div>
            <Button variant="outline" size="sm" className="w-full" onClick={() => navigate('/director-center')}>
              <Database className="h-4 w-4 mr-2" />
              Director Command Center
            </Button>
          </CardContent>
        </Card>
      </div>

      {aiInsights && (
        <AIInsightsCard loading={loadingInsights} insights={aiInsights} />
      )}

      <Tabs defaultValue="revenue" className="space-y-4">
        <TabsList className="bg-white border border-slate-200">
          <TabsTrigger value="revenue" className="font-inter" data-testid="tab-revenue">Revenue</TabsTrigger>
          <TabsTrigger value="production" className="font-inter" data-testid="tab-production">Production</TabsTrigger>
          <TabsTrigger value="quality" className="font-inter" data-testid="tab-quality">Quality</TabsTrigger>
        </TabsList>

        <TabsContent value="revenue" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <Card className="lg:col-span-2 border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle className="font-manrope">Revenue Overview</CardTitle>
                <CardDescription className="font-inter">Monthly revenue breakdown</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={Object.entries(revenueData?.daily_revenue || {}).map(([date, amount]) => ({ date: date.slice(5), amount }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" stroke="#64748b" style={{ fontSize: '12px' }} />
                    <YAxis stroke="#64748b" style={{ fontSize: '12px' }} />
                    <Tooltip />
                    <Line type="monotone" dataKey="amount" stroke="#f97316" strokeWidth={2} dot={{ fill: '#f97316', r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle className="font-manrope">Collection Status</CardTitle>
                <CardDescription className="font-inter">Revenue received vs pending</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {pieData.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                        <span className="text-slate-600 font-inter">{item.name}</span>
                      </div>
                      <span className="font-semibold text-slate-900 font-mono">₹{item.value.toLocaleString('en-IN')}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="production" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-manrope">Work Orders</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600 font-inter">In Progress</span>
                    <span className="text-2xl font-bold text-blue-600 font-manrope">{overview?.production?.wo_in_progress || 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600 font-inter">Completed</span>
                    <span className="text-2xl font-bold text-success font-manrope">{overview?.production?.wo_completed || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-manrope">Wastage Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-4xl font-bold text-orange-600 font-manrope">{overview?.production?.wastage_percentage || 0}%</div>
                  <p className="text-sm text-slate-600 mt-2 font-inter">Overall wastage rate</p>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-manrope">Employees</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-4xl font-bold text-purple-600 font-manrope">{overview?.hrms?.active_employees || 0}</div>
                  <p className="text-sm text-slate-600 mt-2 font-inter">Active workforce</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="quality" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle className="font-manrope">QC Pass Rate</CardTitle>
                <CardDescription className="font-inter">Quality control performance</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center h-40">
                  <div className="text-center">
                    <div className="text-6xl font-bold text-success font-manrope">{overview?.quality?.qc_pass_rate || 0}%</div>
                    <p className="text-sm text-slate-600 mt-2 font-inter">Overall pass rate</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-slate-200 shadow-sm">
              <CardHeader>
                <CardTitle className="font-manrope">Customer Complaints</CardTitle>
                <CardDescription className="font-inter">Open issues requiring attention</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center h-40">
                  <div className="text-center">
                    <div className="text-6xl font-bold text-destructive font-manrope">{overview?.quality?.open_complaints || 0}</div>
                    <p className="text-sm text-slate-600 mt-2 font-inter">Open complaints</p>
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

export default Dashboard;