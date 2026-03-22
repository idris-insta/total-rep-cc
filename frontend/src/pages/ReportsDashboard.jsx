import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator, DropdownMenuLabel } from '../components/ui/dropdown-menu';
import { 
  TrendingUp, TrendingDown, DollarSign, ShoppingCart, Users, Package,
  BarChart3, PieChart, RefreshCw, Download, ArrowUpRight, ArrowDownRight,
  Calendar, Target, AlertTriangle, FileText, FileSpreadsheet
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const ReportsDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState('month');
  const [kpis, setKpis] = useState(null);
  const [salesSummary, setSalesSummary] = useState(null);
  const [salesTrend, setSalesTrend] = useState(null);
  const [topProducts, setTopProducts] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [purchaseSummary, setPurchaseSummary] = useState(null);
  const [inventorySummary, setInventorySummary] = useState(null);
  const [profitLoss, setProfitLoss] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, [period]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [kpisRes, salesRes, trendRes, productsRes, customersRes, purchaseRes, invRes, plRes] = await Promise.all([
        api.get('/analytics/dashboard/kpis'),
        api.get(`/analytics/sales/summary?period=${period}`),
        api.get('/analytics/sales/trend?period=daily&months=3'),
        api.get('/analytics/sales/top-products?limit=5'),
        api.get('/analytics/sales/top-customers?limit=5'),
        api.get('/analytics/purchases/summary'),
        api.get('/analytics/inventory/summary'),
        api.get(`/analytics/financial/profit-loss?period=${period}`)
      ]);

      setKpis(kpisRes.data);
      setSalesSummary(salesRes.data);
      setSalesTrend(trendRes.data);
      setTopProducts(productsRes.data?.top_products || []);
      setTopCustomers(customersRes.data?.top_customers || []);
      setPurchaseSummary(purchaseRes.data);
      setInventorySummary(invRes.data);
      setProfitLoss(plRes.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const formatPercent = (value) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value?.toFixed(1) || 0}%`;
  };

  const handleExport = async (reportType, format) => {
    try {
      toast.info(`Generating ${format.toUpperCase()} report...`);
      const response = await api.get(`/analytics/export/${format}/${reportType}?period=${period}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const timestamp = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `${reportType}_report_${timestamp}.${format === 'pdf' ? 'pdf' : 'xlsx'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success(`${reportType.charAt(0).toUpperCase() + reportType.slice(1)} report downloaded!`);
    } catch (error) {
      toast.error('Failed to export report');
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope">Reports & Analytics</h1>
          <p className="text-slate-600 mt-1">Comprehensive business intelligence dashboard</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={period} onValueChange={setPeriod}>
            <SelectTrigger className="w-[150px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="today">Today</SelectItem>
              <SelectItem value="week">This Week</SelectItem>
              <SelectItem value="month">This Month</SelectItem>
              <SelectItem value="quarter">This Quarter</SelectItem>
              <SelectItem value="year">This Year</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={fetchDashboardData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Download className="h-4 w-4 mr-2" />Export
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Sales Reports</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => handleExport('sales', 'pdf')}>
                <FileText className="h-4 w-4 mr-2 text-red-500" />
                Sales Report (PDF)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport('sales', 'excel')}>
                <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
                Sales Report (Excel)
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Inventory Reports</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => handleExport('inventory', 'pdf')}>
                <FileText className="h-4 w-4 mr-2 text-red-500" />
                Inventory Report (PDF)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport('inventory', 'excel')}>
                <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
                Inventory Report (Excel)
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Customer Reports</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => handleExport('customers', 'pdf')}>
                <FileText className="h-4 w-4 mr-2 text-red-500" />
                Customer Report (PDF)
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleExport('customers', 'excel')}>
                <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
                Customer Report (Excel)
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Today's Sales</p>
                <p className="text-3xl font-bold mt-1">{formatCurrency(kpis?.today_sales)}</p>
                <p className="text-blue-100 text-sm mt-1">{kpis?.today_orders || 0} orders</p>
              </div>
              <DollarSign className="h-12 w-12 text-blue-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm">Month Sales</p>
                <p className="text-3xl font-bold mt-1">{formatCurrency(kpis?.month_sales)}</p>
                <p className="text-green-100 text-sm mt-1">{kpis?.month_orders || 0} orders</p>
              </div>
              <TrendingUp className="h-12 w-12 text-green-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-orange-100 text-sm">Pending POs</p>
                <p className="text-3xl font-bold mt-1">{kpis?.pending_pos || 0}</p>
                <p className="text-orange-100 text-sm mt-1">Awaiting approval</p>
              </div>
              <ShoppingCart className="h-12 w-12 text-orange-200" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-red-500 to-red-600 text-white">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-100 text-sm">Alerts</p>
                <p className="text-3xl font-bold mt-1">{(kpis?.low_stock_items || 0) + (kpis?.overdue_invoices || 0)}</p>
                <p className="text-red-100 text-sm mt-1">
                  {kpis?.low_stock_items || 0} low stock, {kpis?.overdue_invoices || 0} overdue
                </p>
              </div>
              <AlertTriangle className="h-12 w-12 text-red-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sales Analysis with Growth */}
      {salesSummary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Sales Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-6">
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">Current Period Sales</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">
                  {formatCurrency(salesSummary.current_period.total_sales)}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  {salesSummary.current_period.invoice_count} invoices
                </p>
              </div>
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">Previous Period</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">
                  {formatCurrency(salesSummary.previous_period.total_sales)}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  {salesSummary.previous_period.invoice_count} invoices
                </p>
              </div>
              <div className={`text-center p-4 rounded-lg ${salesSummary.growth.sales_growth_percent >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                <p className="text-sm text-slate-600">Growth</p>
                <p className={`text-3xl font-bold mt-2 flex items-center justify-center gap-2 ${salesSummary.growth.sales_growth_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {salesSummary.growth.sales_growth_percent >= 0 ? <ArrowUpRight className="h-6 w-6" /> : <ArrowDownRight className="h-6 w-6" />}
                  {formatPercent(salesSummary.growth.sales_growth_percent)}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  {formatCurrency(salesSummary.growth.sales_growth_amount)}
                </p>
              </div>
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-slate-600">Avg Order Value</p>
                <p className="text-3xl font-bold text-blue-600 mt-2">
                  {formatCurrency(salesSummary.current_period.average_order_value)}
                </p>
                <p className="text-sm text-slate-500 mt-1">per invoice</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Top Selling Products
            </CardTitle>
          </CardHeader>
          <CardContent>
            {topProducts.length > 0 ? (
              <div className="space-y-3">
                {topProducts.map((product, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="w-8 h-8 bg-accent text-white rounded-full flex items-center justify-center font-semibold">
                        {idx + 1}
                      </span>
                      <div>
                        <p className="font-medium text-slate-900">{product.item_name?.substring(0, 25) || 'Unknown'}</p>
                        <p className="text-sm text-slate-500">{product.quantity_sold} units sold</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-slate-900">{formatCurrency(product.total_revenue)}</p>
                      <p className="text-sm text-slate-500">Avg: {formatCurrency(product.avg_price)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">No sales data available</div>
            )}
          </CardContent>
        </Card>

        {/* Top Customers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Top Customers
            </CardTitle>
          </CardHeader>
          <CardContent>
            {topCustomers.length > 0 ? (
              <div className="space-y-3">
                {topCustomers.map((customer, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-semibold">
                        {idx + 1}
                      </span>
                      <div>
                        <p className="font-medium text-slate-900">{customer.customer_name?.substring(0, 25) || 'Unknown'}</p>
                        <p className="text-sm text-slate-500">{customer.order_count} orders</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-slate-900">{formatCurrency(customer.total_purchases)}</p>
                      <p className="text-sm text-slate-500">Avg: {formatCurrency(customer.avg_order_value)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500">No customer data available</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Profit & Loss Summary */}
      {profitLoss && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Profit & Loss Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-4">
              <div className="text-center p-4 border rounded-lg">
                <p className="text-sm text-slate-600">Revenue</p>
                <p className="text-2xl font-bold text-green-600 mt-2">{formatCurrency(profitLoss.revenue.total_revenue)}</p>
                <p className="text-xs text-slate-500">{profitLoss.revenue.invoice_count} invoices</p>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <p className="text-sm text-slate-600">COGS</p>
                <p className="text-2xl font-bold text-red-600 mt-2">{formatCurrency(profitLoss.cost_of_goods_sold)}</p>
              </div>
              <div className="text-center p-4 border rounded-lg bg-blue-50">
                <p className="text-sm text-slate-600">Gross Profit</p>
                <p className="text-2xl font-bold text-blue-600 mt-2">{formatCurrency(profitLoss.gross_profit)}</p>
                <p className="text-xs text-slate-500">{profitLoss.gross_margin_percent}% margin</p>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <p className="text-sm text-slate-600">Expenses</p>
                <p className="text-2xl font-bold text-orange-600 mt-2">{formatCurrency(profitLoss.operating_expenses.total)}</p>
              </div>
              <div className={`text-center p-4 border rounded-lg ${profitLoss.net_profit >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
                <p className="text-sm text-slate-600">Net Profit</p>
                <p className={`text-2xl font-bold mt-2 ${profitLoss.net_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(profitLoss.net_profit)}
                </p>
                <p className="text-xs text-slate-500">{profitLoss.net_margin_percent}% margin</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Inventory Summary */}
      {inventorySummary && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Inventory Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">Total Items</p>
                <p className="text-3xl font-bold text-slate-900 mt-2">{inventorySummary.total_items}</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-slate-600">Stock Value</p>
                <p className="text-3xl font-bold text-green-600 mt-2">{formatCurrency(inventorySummary.total_stock_value)}</p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <p className="text-sm text-slate-600">Low Stock</p>
                <p className="text-3xl font-bold text-orange-600 mt-2">{inventorySummary.low_stock_items}</p>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <p className="text-sm text-slate-600">Out of Stock</p>
                <p className="text-3xl font-bold text-red-600 mt-2">{inventorySummary.out_of_stock_items}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ReportsDashboard;
