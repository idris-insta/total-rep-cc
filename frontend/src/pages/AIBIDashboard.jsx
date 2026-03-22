import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import { 
  Brain, Search, Lightbulb, TrendingUp, AlertTriangle, Send, 
  RefreshCw, Sparkles, MessageSquare, History, Zap, Target,
  BarChart3, PieChart, LineChart, Clock, CheckCircle, XCircle
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

const AIBIDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('query');
  
  // Natural Language Query
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);
  
  // Insights
  const [insightsFocus, setInsightsFocus] = useState('all');
  const [insightsPeriod, setInsightsPeriod] = useState('month');
  const [insightsResult, setInsightsResult] = useState(null);
  
  // Predictions
  const [predictionMetric, setPredictionMetric] = useState('sales');
  const [predictionHorizon, setPredictionHorizon] = useState(30);
  const [predictionResult, setPredictionResult] = useState(null);
  
  // Smart Alerts
  const [alertsType, setAlertsType] = useState('all');
  const [alertsResult, setAlertsResult] = useState(null);

  useEffect(() => {
    fetchQueryHistory();
  }, []);

  const fetchQueryHistory = async () => {
    try {
      const res = await api.get('/ai/query-history?limit=10');
      setQueryHistory(res.data || []);
    } catch (error) {
      console.error('Failed to fetch history');
    }
  };

  const handleNLQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await api.post('/ai/nl-query', { query });
      setQueryResult(res.data);
      fetchQueryHistory();
      toast.success('Query processed successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateInsights = async () => {
    setLoading(true);
    try {
      const res = await api.post('/ai/generate-insights', {
        focus_area: insightsFocus,
        time_period: insightsPeriod
      });
      setInsightsResult(res.data);
      toast.success('Insights generated');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate insights');
    } finally {
      setLoading(false);
    }
  };

  const handlePredict = async () => {
    setLoading(true);
    try {
      const res = await api.post('/ai/predict', {
        metric: predictionMetric,
        horizon_days: predictionHorizon
      });
      setPredictionResult(res.data);
      toast.success('Prediction generated');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckAlerts = async () => {
    setLoading(true);
    try {
      const res = await api.post('/ai/smart-alerts', {
        check_type: alertsType
      });
      setAlertsResult(res.data);
      toast.success('Alerts analyzed');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Alert check failed');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount || 0);
  };

  const suggestedQueries = [
    "What were our top 5 products this month?",
    "How much do customers owe us?",
    "Which items need to be reordered?",
    "What's our current scrap rate?",
    "Show me the cash position summary"
  ];

  return (
    <div className="space-y-6 p-6 bg-gradient-to-br from-indigo-950 via-purple-950 to-slate-900 min-h-screen" data-testid="ai-bi-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl animate-pulse">
            <Brain className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white font-manrope flex items-center gap-2">
              AI Business Intelligence
              <Sparkles className="h-6 w-6 text-yellow-400" />
            </h1>
            <p className="text-slate-400">Powered by Gemini AI • Ask anything about your business</p>
          </div>
        </div>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-slate-800/50 border border-slate-700 p-1">
          <TabsTrigger value="query" className="data-[state=active]:bg-purple-500 data-[state=active]:text-white gap-2">
            <MessageSquare className="h-4 w-4" />Ask AI
          </TabsTrigger>
          <TabsTrigger value="insights" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white gap-2">
            <Lightbulb className="h-4 w-4" />Insights
          </TabsTrigger>
          <TabsTrigger value="predict" className="data-[state=active]:bg-green-500 data-[state=active]:text-white gap-2">
            <TrendingUp className="h-4 w-4" />Predict
          </TabsTrigger>
          <TabsTrigger value="alerts" className="data-[state=active]:bg-red-500 data-[state=active]:text-white gap-2">
            <AlertTriangle className="h-4 w-4" />Smart Alerts
          </TabsTrigger>
        </TabsList>

        {/* Natural Language Query Tab */}
        <TabsContent value="query">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Search className="h-5 w-5 text-purple-400" />
                    Ask Your Business Data
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <Input
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="e.g., What were our top selling products last month?"
                      className="bg-slate-700 border-slate-600 text-white flex-1"
                      onKeyDown={(e) => e.key === 'Enter' && handleNLQuery()}
                    />
                    <Button onClick={handleNLQuery} disabled={loading} className="bg-purple-500 hover:bg-purple-600">
                      {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    </Button>
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    {suggestedQueries.map((sq, idx) => (
                      <button
                        key={idx}
                        onClick={() => setQuery(sq)}
                        className="text-xs px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-full transition-colors"
                      >
                        {sq}
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {queryResult && (
                <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/30">
                  <CardHeader>
                    <CardTitle className="text-white text-sm flex items-center gap-2">
                      <Zap className="h-4 w-4 text-yellow-400" />
                      AI Response
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-invert max-w-none">
                      <div className="text-slate-200 whitespace-pre-wrap text-sm leading-relaxed">
                        {queryResult.answer}
                      </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-slate-700 flex gap-4 text-xs text-slate-400">
                      <span>MTD Sales: {formatCurrency(queryResult.data_snapshot?.mtd_sales)}</span>
                      <span>AR: {formatCurrency(queryResult.data_snapshot?.ar)}</span>
                      <span>AP: {formatCurrency(queryResult.data_snapshot?.ap)}</span>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            <div>
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white text-sm flex items-center gap-2">
                    <History className="h-4 w-4" />Recent Queries
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {queryHistory.length > 0 ? (
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {queryHistory.map((q, idx) => (
                        <button
                          key={idx}
                          onClick={() => setQuery(q.query)}
                          className="w-full text-left p-2 bg-slate-700/50 hover:bg-slate-700 rounded text-xs text-slate-300 truncate"
                        >
                          {q.query}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 text-sm">No queries yet</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* AI Insights Tab */}
        <TabsContent value="insights">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-sm">Generate Insights</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-slate-300">Focus Area</Label>
                  <Select value={insightsFocus} onValueChange={setInsightsFocus}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Areas</SelectItem>
                      <SelectItem value="sales">Sales</SelectItem>
                      <SelectItem value="inventory">Inventory</SelectItem>
                      <SelectItem value="production">Production</SelectItem>
                      <SelectItem value="finance">Finance</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-300">Time Period</Label>
                  <Select value={insightsPeriod} onValueChange={setInsightsPeriod}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="week">This Week</SelectItem>
                      <SelectItem value="month">This Month</SelectItem>
                      <SelectItem value="quarter">This Quarter</SelectItem>
                      <SelectItem value="year">This Year</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleGenerateInsights} disabled={loading} className="w-full bg-blue-500 hover:bg-blue-600">
                  {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Lightbulb className="h-4 w-4 mr-2" />}
                  Generate Insights
                </Button>
              </CardContent>
            </Card>

            <div className="lg:col-span-2">
              {insightsResult ? (
                <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/30 h-full">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Lightbulb className="h-5 w-5 text-yellow-400" />
                      AI Insights: {insightsResult.focus_area.toUpperCase()}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-invert max-w-none">
                      <div className="text-slate-200 whitespace-pre-wrap text-sm leading-relaxed">
                        {insightsResult.insights}
                      </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-slate-700 grid grid-cols-4 gap-4 text-center">
                      <div>
                        <p className="text-xs text-slate-400">Total Sales</p>
                        <p className="text-sm font-bold text-white">{formatCurrency(insightsResult.data_basis?.total_sales)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Customers</p>
                        <p className="text-sm font-bold text-white">{insightsResult.data_basis?.customers}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Low Stock</p>
                        <p className="text-sm font-bold text-orange-400">{insightsResult.data_basis?.low_stock_count}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400">Scrap Rate</p>
                        <p className="text-sm font-bold text-white">{insightsResult.data_basis?.scrap_rate}%</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-slate-800/50 border-slate-700 h-full flex items-center justify-center">
                  <div className="text-center p-8">
                    <Lightbulb className="h-16 w-16 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">Select focus area and generate insights</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Predictions Tab */}
        <TabsContent value="predict">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-sm">Predictive Analytics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-slate-300">What to Predict</Label>
                  <Select value={predictionMetric} onValueChange={setPredictionMetric}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="sales">Sales Forecast</SelectItem>
                      <SelectItem value="inventory">Inventory Needs</SelectItem>
                      <SelectItem value="cash_flow">Cash Flow</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-slate-300">Forecast Horizon (Days)</Label>
                  <Select value={String(predictionHorizon)} onValueChange={(v) => setPredictionHorizon(parseInt(v))}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="7">7 Days</SelectItem>
                      <SelectItem value="14">14 Days</SelectItem>
                      <SelectItem value="30">30 Days</SelectItem>
                      <SelectItem value="60">60 Days</SelectItem>
                      <SelectItem value="90">90 Days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handlePredict} disabled={loading} className="w-full bg-green-500 hover:bg-green-600">
                  {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <TrendingUp className="h-4 w-4 mr-2" />}
                  Generate Prediction
                </Button>
              </CardContent>
            </Card>

            <div className="lg:col-span-2">
              {predictionResult ? (
                <Card className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30 h-full">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Target className="h-5 w-5 text-green-400" />
                      {predictionResult.metric.toUpperCase()} Forecast ({predictionResult.horizon_days} days)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-invert max-w-none">
                      <div className="text-slate-200 whitespace-pre-wrap text-sm leading-relaxed">
                        {predictionResult.prediction}
                      </div>
                    </div>
                    {predictionResult.historical_data && (
                      <div className="mt-4 pt-4 border-t border-slate-700">
                        <p className="text-xs text-slate-400 mb-2">Historical Data (Last 6 Months)</p>
                        <div className="flex gap-2">
                          {predictionResult.historical_data.map((d, idx) => (
                            <div key={idx} className="flex-1 text-center p-2 bg-slate-700/50 rounded">
                              <p className="text-[10px] text-slate-400">{d.month}</p>
                              <p className="text-xs font-bold text-white">{formatCurrency(d.sales)}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-slate-800/50 border-slate-700 h-full flex items-center justify-center">
                  <div className="text-center p-8">
                    <LineChart className="h-16 w-16 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">Select metric and generate prediction</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Smart Alerts Tab */}
        <TabsContent value="alerts">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white text-sm">Smart Alert Scanner</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-slate-300">Check Type</Label>
                  <Select value={alertsType} onValueChange={setAlertsType}>
                    <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Areas</SelectItem>
                      <SelectItem value="sales">Sales</SelectItem>
                      <SelectItem value="inventory">Inventory</SelectItem>
                      <SelectItem value="production">Production</SelectItem>
                      <SelectItem value="payments">Payments</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={handleCheckAlerts} disabled={loading} className="w-full bg-red-500 hover:bg-red-600">
                  {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <AlertTriangle className="h-4 w-4 mr-2" />}
                  Scan for Issues
                </Button>
                
                {alertsResult && (
                  <div className="mt-4 space-y-2 text-xs">
                    <div className="flex justify-between p-2 bg-slate-700/50 rounded">
                      <span className="text-slate-400">Overdue Invoices</span>
                      <span className="text-red-400 font-bold">{alertsResult.summary?.overdue_invoices}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-slate-700/50 rounded">
                      <span className="text-slate-400">Overdue Amount</span>
                      <span className="text-red-400 font-bold">{formatCurrency(alertsResult.summary?.overdue_amount)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-slate-700/50 rounded">
                      <span className="text-slate-400">Low Stock Items</span>
                      <span className="text-orange-400 font-bold">{alertsResult.summary?.low_stock_items}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-slate-700/50 rounded">
                      <span className="text-slate-400">Scrap Rate</span>
                      <span className={cn("font-bold", alertsResult.summary?.scrap_rate > 7 ? "text-red-400" : "text-green-400")}>
                        {alertsResult.summary?.scrap_rate}%
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="lg:col-span-2">
              {alertsResult ? (
                <Card className="bg-gradient-to-br from-red-500/10 to-orange-500/10 border-red-500/30 h-full">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Zap className="h-5 w-5 text-yellow-400" />
                      AI Alert Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-invert max-w-none">
                      <div className="text-slate-200 whitespace-pre-wrap text-sm leading-relaxed">
                        {alertsResult.alerts}
                      </div>
                    </div>
                    <div className="mt-4 pt-4 border-t border-slate-700 text-xs text-slate-400">
                      Generated at: {new Date(alertsResult.generated_at).toLocaleString()}
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card className="bg-slate-800/50 border-slate-700 h-full flex items-center justify-center">
                  <div className="text-center p-8">
                    <AlertTriangle className="h-16 w-16 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">Scan your business for potential issues</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AIBIDashboard;
