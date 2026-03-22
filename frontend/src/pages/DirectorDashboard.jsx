import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { 
  Gauge, DollarSign, TrendingUp, TrendingDown, Package, AlertTriangle, 
  Factory, RefreshCw, ArrowUpRight, ArrowDownRight, Wallet, Scale,
  Shield, Users, Calculator, Ship, Zap, Check, X, AlertCircle, Target
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

const DirectorCockpit = () => {
  const [pulse, setPulse] = useState(null);
  const [pendingOverrides, setPendingOverrides] = useState([]);
  const [lateCustomers, setLateCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [overrideDialogOpen, setOverrideDialogOpen] = useState(false);
  const [selectedOverride, setSelectedOverride] = useState(null);
  const [overrideReason, setOverrideReason] = useState('');

  // Unit Conversion
  const [conversionForm, setConversionForm] = useState({
    from_unit: 'KG', to_unit: 'SQM', quantity: 100,
    thickness_micron: 40, width_mm: 48, length_m: 65
  });
  const [conversionResult, setConversionResult] = useState(null);

  // Landed Cost
  const [landedCostForm, setLandedCostForm] = useState({
    fob_value_usd: 10000, exchange_rate: 83.5, freight_usd: 500,
    insurance_percent: 1.1, basic_customs_duty_percent: 10,
    igst_percent: 18, clearing_charges_inr: 15000,
    transport_to_warehouse_inr: 10000, quantity_units: 1000, uom: 'KG'
  });
  const [landedCostResult, setLandedCostResult] = useState(null);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [pulseRes, overridesRes, lateRes] = await Promise.all([
        api.get('/core/cockpit/pulse').catch(() => ({ data: null })),
        api.get('/core/cockpit/overrides-pending').catch(() => ({ data: { pending_overrides: [] } })),
        api.get('/core/buying-dna/late-customers').catch(() => ({ data: [] }))
      ]);
      setPulse(pulseRes.data);
      setPendingOverrides(overridesRes.data?.pending_overrides || []);
      setLateCustomers(lateRes.data || []);
    } catch (error) {
      console.error('Failed to fetch cockpit data');
    } finally {
      setLoading(false);
    }
  };

  const handleConvert = async () => {
    try {
      const res = await api.post('/core/physics/convert', conversionForm);
      setConversionResult(res.data);
    } catch (error) {
      toast.error('Conversion failed');
    }
  };

  const handleCalculateLandedCost = async () => {
    try {
      const res = await api.post('/core/import-bridge/landed-cost', landedCostForm);
      setLandedCostResult(res.data);
    } catch (error) {
      toast.error('Calculation failed');
    }
  };

  const handleApproveOverride = async () => {
    if (!selectedOverride || !overrideReason) return;
    try {
      await api.post(`/core/redline/override?wo_id=${selectedOverride.wo_id}&override_reason=${encodeURIComponent(overrideReason)}`);
      toast.success('Override approved');
      setOverrideDialogOpen(false);
      setSelectedOverride(null);
      setOverrideReason('');
      fetchAllData();
    } catch (error) {
      toast.error('Failed to approve override');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount || 0);
  };

  if (loading && !pulse) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 min-h-screen" data-testid="director-cockpit">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-orange-500 to-red-600 rounded-xl">
            <Gauge className="h-8 w-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white font-manrope">Director Cockpit</h1>
            <p className="text-slate-400">The 6 Pillars • Real-time Business Pulse</p>
          </div>
        </div>
        <Button onClick={fetchAllData} variant="outline" className="bg-white/10 border-white/20 text-white hover:bg-white/20">
          <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />Refresh
        </Button>
      </div>

      {/* Pulse Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Cash Pulse */}
        <Card className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border-emerald-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-emerald-300 text-sm font-medium">Cash Position</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {formatCurrency(pulse?.cash_pulse?.net_position)}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <Badge className={cn("text-xs", pulse?.cash_pulse?.health === "GOOD" ? "bg-emerald-500" : "bg-orange-500")}>
                    {pulse?.cash_pulse?.health}
                  </Badge>
                </div>
              </div>
              <Wallet className="h-12 w-12 text-emerald-400 opacity-50" />
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
              <div className="text-emerald-300">AR: {formatCurrency(pulse?.cash_pulse?.receivables)}</div>
              <div className="text-red-300">AP: {formatCurrency(pulse?.cash_pulse?.payables)}</div>
            </div>
          </CardContent>
        </Card>

        {/* Production Pulse */}
        <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border-blue-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-300 text-sm font-medium">Production Scrap</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {pulse?.production_pulse?.avg_scrap_percent}%
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <Badge className={cn("text-xs", pulse?.production_pulse?.scrap_status === "OK" ? "bg-emerald-500" : "bg-red-500")}>
                    {pulse?.production_pulse?.scrap_status} (Limit: {pulse?.production_pulse?.scrap_limit}%)
                  </Badge>
                </div>
              </div>
              <Factory className="h-12 w-12 text-blue-400 opacity-50" />
            </div>
            <div className="mt-4 text-sm text-blue-300">
              {pulse?.production_pulse?.work_orders_active} Active WOs
              {pulse?.production_pulse?.redline_alerts?.length > 0 && (
                <span className="text-red-400 ml-2">• {pulse?.production_pulse?.redline_alerts?.length} Redline</span>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Sales Pulse */}
        <Card className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 border-purple-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-300 text-sm font-medium">MTD Sales</p>
                <p className="text-3xl font-bold text-white mt-1">
                  {formatCurrency(pulse?.sales_pulse?.mtd_sales)}
                </p>
                <div className="mt-2">
                  <Badge className="text-xs bg-purple-500">
                    {pulse?.sales_pulse?.mtd_orders} Orders
                  </Badge>
                </div>
              </div>
              <TrendingUp className="h-12 w-12 text-purple-400 opacity-50" />
            </div>
          </CardContent>
        </Card>

        {/* Override Queue */}
        <Card className="bg-gradient-to-br from-red-500/20 to-red-600/10 border-red-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-300 text-sm font-medium">Override Queue</p>
                <p className="text-3xl font-bold text-white mt-1">{pendingOverrides.length}</p>
                <div className="mt-2">
                  <Badge className={cn("text-xs", pendingOverrides.length > 0 ? "bg-red-500 animate-pulse" : "bg-slate-500")}>
                    {pendingOverrides.length > 0 ? "ACTION REQUIRED" : "All Clear"}
                  </Badge>
                </div>
              </div>
              <AlertTriangle className="h-12 w-12 text-red-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue="redline" className="space-y-4">
        <TabsList className="bg-slate-800/50 border border-slate-700">
          <TabsTrigger value="redline" className="data-[state=active]:bg-red-500 data-[state=active]:text-white">
            <Shield className="h-4 w-4 mr-2" />Redline Control
          </TabsTrigger>
          <TabsTrigger value="physics" className="data-[state=active]:bg-blue-500 data-[state=active]:text-white">
            <Scale className="h-4 w-4 mr-2" />Physics Engine
          </TabsTrigger>
          <TabsTrigger value="buyingdna" className="data-[state=active]:bg-purple-500 data-[state=active]:text-white">
            <Users className="h-4 w-4 mr-2" />Buying DNA
          </TabsTrigger>
          <TabsTrigger value="import" className="data-[state=active]:bg-orange-500 data-[state=active]:text-white">
            <Ship className="h-4 w-4 mr-2" />Import Bridge
          </TabsTrigger>
        </TabsList>

        {/* Redline Control Tab */}
        <TabsContent value="redline">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Shield className="h-5 w-5 text-red-400" />
                Production Redline - 7% Scrap Guardrail
              </CardTitle>
            </CardHeader>
            <CardContent>
              {pendingOverrides.length > 0 ? (
                <div className="space-y-3">
                  {pendingOverrides.map((item, idx) => (
                    <div key={idx} className="flex items-center justify-between p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                      <div>
                        <p className="font-semibold text-white">{item.wo_number}</p>
                        <p className="text-sm text-slate-400">{item.item_name} • Machine: {item.machine}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-red-400">{item.scrap_percent}%</p>
                        <p className="text-xs text-slate-400">+{item.excess_scrap}% over limit</p>
                      </div>
                      <Dialog open={overrideDialogOpen && selectedOverride?.wo_id === item.wo_id} onOpenChange={(open) => {
                        setOverrideDialogOpen(open);
                        if (!open) setSelectedOverride(null);
                      }}>
                        <DialogTrigger asChild>
                          <Button onClick={() => setSelectedOverride(item)} className="bg-red-500 hover:bg-red-600">
                            Override
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>Approve Redline Override</DialogTitle>
                          </DialogHeader>
                          <div className="space-y-4">
                            <div className="p-4 bg-red-50 rounded-lg">
                              <p className="font-semibold">WO: {selectedOverride?.wo_number}</p>
                              <p className="text-sm text-slate-600">Scrap: {selectedOverride?.scrap_percent}% (Limit: 7%)</p>
                            </div>
                            <div className="space-y-2">
                              <Label>Override Reason *</Label>
                              <Textarea
                                value={overrideReason}
                                onChange={(e) => setOverrideReason(e.target.value)}
                                placeholder="Enter reason for approving this override..."
                                rows={3}
                              />
                            </div>
                          </div>
                          <DialogFooter>
                            <Button variant="outline" onClick={() => setOverrideDialogOpen(false)}>Cancel</Button>
                            <Button onClick={handleApproveOverride} className="bg-red-500">Approve Override</Button>
                          </DialogFooter>
                        </DialogContent>
                      </Dialog>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Check className="h-16 w-16 text-emerald-400 mx-auto mb-4" />
                  <p className="text-white text-lg">All Production Within Limits</p>
                  <p className="text-slate-400">No redline overrides needed</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Physics Engine Tab */}
        <TabsContent value="physics">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Scale className="h-5 w-5 text-blue-400" />
                Physics Engine - Unit Conversion (KG ↔ SQM ↔ PCS)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label className="text-slate-300">From</Label>
                      <Select value={conversionForm.from_unit} onValueChange={(v) => setConversionForm({...conversionForm, from_unit: v})}>
                        <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="KG">KG</SelectItem>
                          <SelectItem value="SQM">SQM</SelectItem>
                          <SelectItem value="PCS">PCS/ROL</SelectItem>
                          <SelectItem value="MTR">MTR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Quantity</Label>
                      <Input
                        type="number"
                        value={conversionForm.quantity}
                        onChange={(e) => setConversionForm({...conversionForm, quantity: parseFloat(e.target.value) || 0})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">To</Label>
                      <Select value={conversionForm.to_unit} onValueChange={(v) => setConversionForm({...conversionForm, to_unit: v})}>
                        <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="KG">KG</SelectItem>
                          <SelectItem value="SQM">SQM</SelectItem>
                          <SelectItem value="PCS">PCS/ROL</SelectItem>
                          <SelectItem value="MTR">MTR</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label className="text-slate-300">Thickness (µm)</Label>
                      <Input
                        type="number"
                        value={conversionForm.thickness_micron}
                        onChange={(e) => setConversionForm({...conversionForm, thickness_micron: parseFloat(e.target.value) || 0})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Width (mm)</Label>
                      <Input
                        type="number"
                        value={conversionForm.width_mm}
                        onChange={(e) => setConversionForm({...conversionForm, width_mm: parseFloat(e.target.value) || 0})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Length (m)</Label>
                      <Input
                        type="number"
                        value={conversionForm.length_m}
                        onChange={(e) => setConversionForm({...conversionForm, length_m: parseFloat(e.target.value) || 0})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                  </div>
                  <Button onClick={handleConvert} className="w-full bg-blue-500 hover:bg-blue-600">
                    <Calculator className="h-4 w-4 mr-2" />Convert
                  </Button>
                </div>
                
                {conversionResult && (
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-6">
                    <p className="text-blue-300 text-sm mb-2">Result</p>
                    <p className="text-4xl font-bold text-white">
                      {conversionResult.to_value.toLocaleString()} {conversionResult.to_unit}
                    </p>
                    <p className="text-sm text-slate-400 mt-2">
                      {conversionResult.from_value} {conversionResult.from_unit} = {conversionResult.to_value} {conversionResult.to_unit}
                    </p>
                    <p className="text-xs text-slate-500 mt-4">{conversionResult.formula_used}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Buying DNA Tab */}
        <TabsContent value="buyingdna">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Users className="h-5 w-5 text-purple-400" />
                Buying DNA - Late Customer Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              {lateCustomers.length > 0 ? (
                <div className="space-y-3">
                  {lateCustomers.slice(0, 10).map((customer, idx) => (
                    <div key={idx} className="flex items-center justify-between p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                      <div>
                        <p className="font-semibold text-white">{customer.customer_name}</p>
                        <p className="text-sm text-slate-400">Avg interval: {customer.avg_interval} days • Avg order: {formatCurrency(customer.avg_order_value)}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-purple-400">+{customer.days_late} days</p>
                        <p className="text-xs text-slate-400">late</p>
                      </div>
                      <Button size="sm" variant="outline" className="border-purple-400 text-purple-400 hover:bg-purple-400 hover:text-white">
                        Send Follow-up
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Check className="h-16 w-16 text-emerald-400 mx-auto mb-4" />
                  <p className="text-white text-lg">All Customers On Schedule</p>
                  <p className="text-slate-400">No late orders detected</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Import Bridge Tab */}
        <TabsContent value="import">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Ship className="h-5 w-5 text-orange-400" />
                Import Bridge - Landed Cost Calculator
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-slate-300">FOB Value (USD)</Label>
                      <Input
                        type="number"
                        value={landedCostForm.fob_value_usd}
                        onChange={(e) => setLandedCostForm({...landedCostForm, fob_value_usd: parseFloat(e.target.value) || 0})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Exchange Rate</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={landedCostForm.exchange_rate}
                        onChange={(e) => setLandedCostForm({...landedCostForm, exchange_rate: parseFloat(e.target.value) || 83})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Freight (USD)</Label>
                      <Input
                        type="number"
                        value={landedCostForm.freight_usd}
                        onChange={(e) => setLandedCostForm({...landedCostForm, freight_usd: parseFloat(e.target.value) || 0})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Customs Duty %</Label>
                      <Input
                        type="number"
                        value={landedCostForm.basic_customs_duty_percent}
                        onChange={(e) => setLandedCostForm({...landedCostForm, basic_customs_duty_percent: parseFloat(e.target.value) || 0})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Quantity</Label>
                      <Input
                        type="number"
                        value={landedCostForm.quantity_units}
                        onChange={(e) => setLandedCostForm({...landedCostForm, quantity_units: parseFloat(e.target.value) || 1})}
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">UOM</Label>
                      <Select value={landedCostForm.uom} onValueChange={(v) => setLandedCostForm({...landedCostForm, uom: v})}>
                        <SelectTrigger className="bg-slate-700 border-slate-600 text-white">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="KG">KG</SelectItem>
                          <SelectItem value="MT">MT</SelectItem>
                          <SelectItem value="PCS">PCS</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <Button onClick={handleCalculateLandedCost} className="w-full bg-orange-500 hover:bg-orange-600">
                    <Calculator className="h-4 w-4 mr-2" />Calculate Landed Cost
                  </Button>
                </div>
                
                {landedCostResult && (
                  <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-6 space-y-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="text-slate-400">CIF Value:</div>
                      <div className="text-white font-mono">{formatCurrency(landedCostResult.cif_value_inr)}</div>
                      <div className="text-slate-400">Total Duties:</div>
                      <div className="text-white font-mono">{formatCurrency(landedCostResult.total_duties)}</div>
                      <div className="text-slate-400">Other Charges:</div>
                      <div className="text-white font-mono">{formatCurrency(landedCostResult.clearing_charges + landedCostResult.transport_charges)}</div>
                    </div>
                    <div className="border-t border-slate-600 pt-4">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-300">Total Landed Cost:</span>
                        <span className="text-2xl font-bold text-white">{formatCurrency(landedCostResult.total_landed_cost)}</span>
                      </div>
                      <div className="flex justify-between items-center mt-2">
                        <span className="text-slate-300">Cost per {landedCostForm.uom}:</span>
                        <span className="text-xl font-bold text-orange-400">{formatCurrency(landedCostResult.landed_cost_per_unit)}</span>
                      </div>
                    </div>
                    <div className="border-t border-slate-600 pt-4">
                      <p className="text-slate-400 text-sm mb-2">Selling Price Recommendations:</p>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-yellow-500/20 rounded p-3">
                          <p className="text-yellow-300 text-xs">Minimum (15% margin)</p>
                          <p className="text-xl font-bold text-white">{formatCurrency(landedCostResult.minimum_selling_price)}</p>
                        </div>
                        <div className="bg-emerald-500/20 rounded p-3">
                          <p className="text-emerald-300 text-xs">Recommended (25% margin)</p>
                          <p className="text-xl font-bold text-white">{formatCurrency(landedCostResult.recommended_selling_price)}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DirectorCockpit;
