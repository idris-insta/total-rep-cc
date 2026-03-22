import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { 
  Ship, Plus, Calculator, DollarSign, FileText, CheckCircle, 
  Globe, RefreshCw, TrendingUp, Package, Anchor
} from 'lucide-react';

const API_URL = import.meta.env.VITE_BACKEND_URL;

const ImportBridge = () => {
  const [importPOs, setImportPOs] = useState([]);
  const [exchangeRates, setExchangeRates] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showNewPO, setShowNewPO] = useState(false);
  const [showLandingCost, setShowLandingCost] = useState(false);
  const [selectedPO, setSelectedPO] = useState(null);
  const [landingCostResult, setLandingCostResult] = useState(null);

  const token = localStorage.getItem('token');
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const [newPO, setNewPO] = useState({
    supplier_id: '',
    po_date: new Date().toISOString().slice(0, 10),
    expected_arrival: '',
    items: [{ item_id: '', item_name: '', quantity: 0, uom: 'KG', foreign_unit_price: 0, foreign_currency: 'USD' }],
    foreign_currency: 'USD',
    exchange_rate: 83.5,
    port_of_loading: '',
    port_of_discharge: 'JNPT',
    shipping_terms: 'FOB',
    container_type: '20ft',
    payment_terms: 'LC',
    lc_number: '',
    bank_name: ''
  });

  const [landingCost, setLandingCost] = useState({
    import_po_id: '',
    basic_customs_duty: 0,
    social_welfare_cess: 0,
    igst: 0,
    anti_dumping_duty: 0,
    safeguard_duty: 0,
    ocean_freight: 0,
    insurance: 0,
    local_freight: 0,
    cha_charges: 0,
    port_charges: 0,
    container_detention: 0,
    documentation_charges: 0,
    bank_charges: 0,
    other_charges: 0,
    settlement_exchange_rate: 0
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [posRes, ratesRes] = await Promise.all([
        fetch(`${API_URL}/api/imports/purchase-orders`, { headers }),
        fetch(`${API_URL}/api/imports/exchange-rates`, { headers })
      ]);

      if (posRes.ok) setImportPOs(await posRes.json());
      if (ratesRes.ok) setExchangeRates(await ratesRes.json());
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreatePO = async () => {
    try {
      const response = await fetch(`${API_URL}/api/imports/purchase-orders`, {
        method: 'POST',
        headers,
        body: JSON.stringify(newPO)
      });

      if (response.ok) {
        setShowNewPO(false);
        fetchData();
      }
    } catch (error) {
      console.error('Error creating import PO:', error);
    }
  };

  const handleCalculateLanding = async () => {
    try {
      const response = await fetch(`${API_URL}/api/imports/landing-cost`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ ...landingCost, import_po_id: selectedPO.id })
      });

      if (response.ok) {
        const result = await response.json();
        setLandingCostResult(result);
      }
    } catch (error) {
      console.error('Error calculating landing cost:', error);
    }
  };

  const handleFinalizeLanding = async (costId) => {
    try {
      const response = await fetch(`${API_URL}/api/imports/landing-cost/${costId}/finalize`, {
        method: 'PUT',
        headers
      });

      if (response.ok) {
        alert('Landing cost finalized! MSP updated for all items.');
        setShowLandingCost(false);
        setLandingCostResult(null);
        fetchData();
      }
    } catch (error) {
      console.error('Error finalizing landing cost:', error);
    }
  };

  const formatCurrency = (amount, currency = 'INR') => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency,
      maximumFractionDigits: 2
    }).format(amount || 0);
  };

  const getStatusBadge = (status) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      confirmed: 'bg-blue-100 text-blue-800',
      shipped: 'bg-yellow-100 text-yellow-800',
      in_transit: 'bg-orange-100 text-orange-800',
      customs: 'bg-purple-100 text-purple-800',
      delivered: 'bg-green-100 text-green-800',
      completed: 'bg-green-200 text-green-900'
    };
    return <Badge className={colors[status] || 'bg-gray-100'}>{status?.replace('_', ' ').toUpperCase()}</Badge>;
  };

  const openLandingCost = (po) => {
    setSelectedPO(po);
    setLandingCost({
      ...landingCost,
      import_po_id: po.id,
      settlement_exchange_rate: po.exchange_rate
    });
    setLandingCostResult(null);
    setShowLandingCost(true);
  };

  const addItem = () => {
    setNewPO({
      ...newPO,
      items: [...newPO.items, { item_id: '', item_name: '', quantity: 0, uom: 'KG', foreign_unit_price: 0, foreign_currency: 'USD' }]
    });
  };

  const updateItem = (index, field, value) => {
    const updated = [...newPO.items];
    updated[index][field] = value;
    setNewPO({ ...newPO, items: updated });
  };

  const totalForeignValue = importPOs.reduce((sum, po) => sum + (po.total_foreign_value || 0), 0);
  const totalINRValue = importPOs.reduce((sum, po) => sum + (po.total_inr_value || 0), 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Import Bridge</h1>
          <p className="text-sm text-gray-500">Manage import purchases and calculate landed costs</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={showNewPO} onOpenChange={setShowNewPO}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Import PO</Button>
            </DialogTrigger>
            <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Import Purchase Order</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>PO Date</Label>
                    <Input 
                      type="date"
                      value={newPO.po_date}
                      onChange={(e) => setNewPO({...newPO, po_date: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Expected Arrival</Label>
                    <Input 
                      type="date"
                      value={newPO.expected_arrival}
                      onChange={(e) => setNewPO({...newPO, expected_arrival: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Currency</Label>
                    <Select 
                      value={newPO.foreign_currency}
                      onValueChange={(v) => setNewPO({...newPO, foreign_currency: v})}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="USD">USD - US Dollar</SelectItem>
                        <SelectItem value="EUR">EUR - Euro</SelectItem>
                        <SelectItem value="GBP">GBP - British Pound</SelectItem>
                        <SelectItem value="CNY">CNY - Chinese Yuan</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Exchange Rate (INR)</Label>
                    <Input 
                      type="number"
                      step="0.01"
                      value={newPO.exchange_rate}
                      onChange={(e) => setNewPO({...newPO, exchange_rate: parseFloat(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>Supplier ID</Label>
                    <Input 
                      value={newPO.supplier_id}
                      onChange={(e) => setNewPO({...newPO, supplier_id: e.target.value})}
                      placeholder="Enter supplier ID"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Port of Loading</Label>
                    <Input 
                      value={newPO.port_of_loading}
                      onChange={(e) => setNewPO({...newPO, port_of_loading: e.target.value})}
                      placeholder="e.g., Shanghai, Ningbo"
                    />
                  </div>
                  <div>
                    <Label>Port of Discharge</Label>
                    <Select 
                      value={newPO.port_of_discharge}
                      onValueChange={(v) => setNewPO({...newPO, port_of_discharge: v})}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="JNPT">JNPT (Nhava Sheva)</SelectItem>
                        <SelectItem value="Mundra">Mundra</SelectItem>
                        <SelectItem value="Chennai">Chennai</SelectItem>
                        <SelectItem value="Kolkata">Kolkata</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Shipping Terms</Label>
                    <Select 
                      value={newPO.shipping_terms}
                      onValueChange={(v) => setNewPO({...newPO, shipping_terms: v})}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="FOB">FOB</SelectItem>
                        <SelectItem value="CIF">CIF</SelectItem>
                        <SelectItem value="CNF">CNF</SelectItem>
                        <SelectItem value="EXW">EXW</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Container Type</Label>
                    <Select 
                      value={newPO.container_type}
                      onValueChange={(v) => setNewPO({...newPO, container_type: v})}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="20ft">20ft Container</SelectItem>
                        <SelectItem value="40ft">40ft Container</SelectItem>
                        <SelectItem value="LCL">LCL</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Payment Terms</Label>
                    <Select 
                      value={newPO.payment_terms}
                      onValueChange={(v) => setNewPO({...newPO, payment_terms: v})}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="LC">Letter of Credit</SelectItem>
                        <SelectItem value="TT">Telegraphic Transfer</SelectItem>
                        <SelectItem value="DA">Documents Against Acceptance</SelectItem>
                        <SelectItem value="DP">Documents Against Payment</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Items</Label>
                  <div className="border rounded p-3 space-y-2">
                    {newPO.items.map((item, idx) => (
                      <div key={idx} className="grid grid-cols-4 gap-2">
                        <Input 
                          placeholder="Item Name"
                          value={item.item_name}
                          onChange={(e) => updateItem(idx, 'item_name', e.target.value)}
                        />
                        <Input 
                          type="number"
                          placeholder="Qty"
                          value={item.quantity}
                          onChange={(e) => updateItem(idx, 'quantity', parseFloat(e.target.value))}
                        />
                        <Input 
                          type="number"
                          step="0.01"
                          placeholder="Unit Price"
                          value={item.foreign_unit_price}
                          onChange={(e) => updateItem(idx, 'foreign_unit_price', parseFloat(e.target.value))}
                        />
                        <Select 
                          value={item.uom}
                          onValueChange={(v) => updateItem(idx, 'uom', v)}
                        >
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="KG">KG</SelectItem>
                            <SelectItem value="MT">MT</SelectItem>
                            <SelectItem value="LTR">LTR</SelectItem>
                            <SelectItem value="PCS">PCS</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    ))}
                    <Button variant="outline" size="sm" onClick={addItem}>
                      <Plus className="h-4 w-4 mr-1" /> Add Item
                    </Button>
                  </div>
                </div>

                <Button onClick={handleCreatePO} className="w-full">
                  <Ship className="h-4 w-4 mr-2" /> Create Import PO
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Exchange Rates Card */}
      {exchangeRates && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Globe className="h-5 w-5" /> Exchange Rates (INR)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-6">
              {Object.entries(exchangeRates.rates || {}).map(([currency, rate]) => (
                <div key={currency} className="text-center">
                  <p className="text-sm text-gray-500">{currency}</p>
                  <p className="text-lg font-bold">₹{rate}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-full">
              <Ship className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Import POs</p>
              <p className="text-2xl font-bold">{importPOs.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-full">
              <DollarSign className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Foreign Value</p>
              <p className="text-2xl font-bold">${totalForeignValue.toFixed(2)}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-full">
              <TrendingUp className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total INR Value</p>
              <p className="text-2xl font-bold">{formatCurrency(totalINRValue)}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-full">
              <Anchor className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">In Transit</p>
              <p className="text-2xl font-bold">{importPOs.filter(p => p.status === 'in_transit').length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Import PO List */}
      {loading ? (
        <div className="flex justify-center p-8">
          <RefreshCw className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : importPOs.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Ship className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No import purchase orders yet</p>
            <Button className="mt-4" onClick={() => setShowNewPO(true)}>
              <Plus className="h-4 w-4 mr-2" /> Create First Import PO
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Import Purchase Orders</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {importPOs.map(po => (
                <div key={po.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-bold text-lg">{po.po_number}</p>
                        {getStatusBadge(po.status)}
                        <Badge variant="outline">{po.foreign_currency}</Badge>
                        <Badge variant="outline">{po.shipping_terms}</Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2 text-sm text-gray-600">
                        <div>
                          <span className="text-gray-400">Supplier:</span> {po.supplier_name || po.supplier_id}
                        </div>
                        <div>
                          <span className="text-gray-400">Route:</span> {po.port_of_loading} → {po.port_of_discharge}
                        </div>
                        <div>
                          <span className="text-gray-400">Foreign:</span> {po.foreign_currency} {po.total_foreign_value?.toFixed(2)}
                        </div>
                        <div>
                          <span className="text-gray-400">INR:</span> {formatCurrency(po.total_inr_value)}
                        </div>
                      </div>
                      <p className="text-xs text-gray-400 mt-2">
                        Expected: {po.expected_arrival} | Payment: {po.payment_terms}
                        {po.bl_number && ` | BL: ${po.bl_number}`}
                      </p>
                    </div>
                    <Button size="sm" onClick={() => openLandingCost(po)}>
                      <Calculator className="h-4 w-4 mr-1" /> Calculate Landing
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Landing Cost Calculator Dialog */}
      <Dialog open={showLandingCost} onOpenChange={setShowLandingCost}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Landing Cost Calculator - {selectedPO?.po_number}</DialogTitle>
          </DialogHeader>
          
          {selectedPO && (
            <div className="space-y-6">
              {/* PO Summary */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-gray-500">Foreign Value</p>
                    <p className="font-bold">{selectedPO.foreign_currency} {selectedPO.total_foreign_value?.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">PO Exchange Rate</p>
                    <p className="font-bold">₹{selectedPO.exchange_rate}</p>
                  </div>
                  <div>
                    <p className="text-gray-500">PO INR Value</p>
                    <p className="font-bold">{formatCurrency(selectedPO.total_inr_value)}</p>
                  </div>
                  <div>
                    <Label>Settlement Rate</Label>
                    <Input 
                      type="number"
                      step="0.01"
                      value={landingCost.settlement_exchange_rate}
                      onChange={(e) => setLandingCost({...landingCost, settlement_exchange_rate: parseFloat(e.target.value)})}
                    />
                  </div>
                </div>
              </div>

              {/* Duties & Taxes */}
              <div>
                <h4 className="font-bold mb-3">Duties & Taxes (INR)</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Basic Customs Duty</Label>
                    <Input type="number" value={landingCost.basic_customs_duty} onChange={(e) => setLandingCost({...landingCost, basic_customs_duty: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Social Welfare Cess</Label>
                    <Input type="number" value={landingCost.social_welfare_cess} onChange={(e) => setLandingCost({...landingCost, social_welfare_cess: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>IGST</Label>
                    <Input type="number" value={landingCost.igst} onChange={(e) => setLandingCost({...landingCost, igst: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Anti-Dumping Duty</Label>
                    <Input type="number" value={landingCost.anti_dumping_duty} onChange={(e) => setLandingCost({...landingCost, anti_dumping_duty: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Safeguard Duty</Label>
                    <Input type="number" value={landingCost.safeguard_duty} onChange={(e) => setLandingCost({...landingCost, safeguard_duty: parseFloat(e.target.value) || 0})} />
                  </div>
                </div>
              </div>

              {/* Freight & Insurance */}
              <div>
                <h4 className="font-bold mb-3">Freight & Insurance (INR)</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Ocean Freight</Label>
                    <Input type="number" value={landingCost.ocean_freight} onChange={(e) => setLandingCost({...landingCost, ocean_freight: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Insurance</Label>
                    <Input type="number" value={landingCost.insurance} onChange={(e) => setLandingCost({...landingCost, insurance: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Local Freight</Label>
                    <Input type="number" value={landingCost.local_freight} onChange={(e) => setLandingCost({...landingCost, local_freight: parseFloat(e.target.value) || 0})} />
                  </div>
                </div>
              </div>

              {/* Handling Charges */}
              <div>
                <h4 className="font-bold mb-3">Handling & Other Charges (INR)</h4>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <Label>CHA Charges</Label>
                    <Input type="number" value={landingCost.cha_charges} onChange={(e) => setLandingCost({...landingCost, cha_charges: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Port Charges</Label>
                    <Input type="number" value={landingCost.port_charges} onChange={(e) => setLandingCost({...landingCost, port_charges: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Container Detention</Label>
                    <Input type="number" value={landingCost.container_detention} onChange={(e) => setLandingCost({...landingCost, container_detention: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Documentation</Label>
                    <Input type="number" value={landingCost.documentation_charges} onChange={(e) => setLandingCost({...landingCost, documentation_charges: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Bank Charges</Label>
                    <Input type="number" value={landingCost.bank_charges} onChange={(e) => setLandingCost({...landingCost, bank_charges: parseFloat(e.target.value) || 0})} />
                  </div>
                  <div>
                    <Label>Other Charges</Label>
                    <Input type="number" value={landingCost.other_charges} onChange={(e) => setLandingCost({...landingCost, other_charges: parseFloat(e.target.value) || 0})} />
                  </div>
                </div>
              </div>

              <Button onClick={handleCalculateLanding} className="w-full">
                <Calculator className="h-4 w-4 mr-2" /> Calculate Final Landed Cost
              </Button>

              {/* Results */}
              {landingCostResult && (
                <div className="border-t pt-6 space-y-4">
                  <h4 className="font-bold text-lg">Landing Cost Summary</h4>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-sm text-gray-500">Total Duties</p>
                        <p className="text-xl font-bold text-red-600">{formatCurrency(landingCostResult.total_duties)}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-sm text-gray-500">Total Freight</p>
                        <p className="text-xl font-bold text-orange-600">{formatCurrency(landingCostResult.total_freight)}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-sm text-gray-500">Total Handling</p>
                        <p className="text-xl font-bold text-purple-600">{formatCurrency(landingCostResult.total_handling)}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-sm text-gray-500">Forex Gain/Loss</p>
                        <p className={`text-xl font-bold ${landingCostResult.forex_gain_loss >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(landingCostResult.forex_gain_loss)}
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  <Card className="bg-green-50">
                    <CardContent className="p-6 text-center">
                      <p className="text-sm text-gray-600">Final Landed INR Value</p>
                      <p className="text-3xl font-bold text-green-600">{formatCurrency(landingCostResult.landed_inr_value)}</p>
                    </CardContent>
                  </Card>

                  {/* Per Item Breakdown */}
                  {landingCostResult.landed_rate_per_unit && (
                    <div>
                      <h5 className="font-bold mb-2">Item-wise Landed Rate</h5>
                      <div className="space-y-2">
                        {Object.entries(landingCostResult.landed_rate_per_unit).map(([itemId, data]) => (
                          <div key={itemId} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                            <div>
                              <p className="font-medium">{data.item_name}</p>
                              <p className="text-sm text-gray-500">Qty: {data.quantity}</p>
                            </div>
                            <div className="text-right">
                              <p className="font-bold text-green-600">{formatCurrency(data.landed_rate_per_unit)}/unit</p>
                              <p className="text-sm text-gray-500">Total: {formatCurrency(data.total_landed_inr)}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <Button onClick={() => handleFinalizeLanding(landingCostResult.id)} className="w-full bg-green-600 hover:bg-green-700">
                    <CheckCircle className="h-4 w-4 mr-2" /> Finalize & Update MSP
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ImportBridge;
