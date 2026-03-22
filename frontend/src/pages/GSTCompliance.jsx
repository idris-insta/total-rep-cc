import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { 
  FileText, Download, RefreshCw, CheckCircle, AlertTriangle, Clock,
  FileCheck, QrCode, Truck, Receipt, Calculator, TrendingUp, Building2
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const GSTCompliance = () => {
  const [loading, setLoading] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [gstr1Data, setGstr1Data] = useState(null);
  const [gstr3bData, setGstr3bData] = useState(null);
  const [itcData, setItcData] = useState(null);
  const [hsnData, setHsnData] = useState(null);
  const [eInvoices, setEInvoices] = useState([]);
  const [ewayBills, setEwayBills] = useState([]);

  // Generate period options (last 12 months)
  const getPeriodOptions = () => {
    const options = [];
    const now = new Date();
    for (let i = 0; i < 12; i++) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const period = `${String(date.getMonth() + 1).padStart(2, '0')}${date.getFullYear()}`;
      const label = date.toLocaleDateString('en-IN', { month: 'long', year: 'numeric' });
      options.push({ value: period, label });
    }
    return options;
  };

  useEffect(() => {
    const now = new Date();
    const currentPeriod = `${String(now.getMonth() + 1).padStart(2, '0')}${now.getFullYear()}`;
    setSelectedPeriod(currentPeriod);
  }, []);

  useEffect(() => {
    if (selectedPeriod) {
      fetchGSTData();
    }
  }, [selectedPeriod]);

  const fetchGSTData = async () => {
    setLoading(true);
    try {
      const [gstr1Res, gstr3bRes, itcRes, hsnRes, ewbRes] = await Promise.all([
        api.get(`/gst/gstr1/${selectedPeriod}`).catch(() => ({ data: null })),
        api.get(`/gst/gstr3b/${selectedPeriod}`).catch(() => ({ data: null })),
        api.get(`/gst/itc/${selectedPeriod}`).catch(() => ({ data: null })),
        api.get(`/gst/hsn-summary/${selectedPeriod}`).catch(() => ({ data: null })),
        api.get('/gst/eway-bills').catch(() => ({ data: [] }))
      ]);
      
      setGstr1Data(gstr1Res.data);
      setGstr3bData(gstr3bRes.data);
      setItcData(itcRes.data);
      setHsnData(hsnRes.data);
      setEwayBills(ewbRes.data || []);
    } catch (error) {
      toast.error('Failed to load GST data');
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

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope">GST Compliance</h1>
          <p className="text-slate-600 mt-1">Complete GST management - Returns, E-Invoice, E-Way Bill, ITC</p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select Period" />
            </SelectTrigger>
            <SelectContent>
              {getPeriodOptions().map(opt => (
                <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={fetchGSTData} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <TrendingUp className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Output Tax (GSTR-1)</p>
                <p className="text-xl font-bold text-slate-900">
                  {formatCurrency(gstr1Data?.summary?.total_tax)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-green-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Receipt className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Input Tax Credit</p>
                <p className="text-xl font-bold text-slate-900">
                  {formatCurrency(itcData?.summary?.eligible_itc?.total)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Calculator className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Net Tax Liability</p>
                <p className="text-xl font-bold text-slate-900">
                  {formatCurrency(gstr3bData?.summary?.net_tax_liability)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Truck className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">E-Way Bills</p>
                <p className="text-xl font-bold text-slate-900">{ewayBills.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue="gstr1" className="space-y-4">
        <TabsList className="grid grid-cols-5 w-full max-w-3xl">
          <TabsTrigger value="gstr1" className="gap-2">
            <FileText className="h-4 w-4" />GSTR-1
          </TabsTrigger>
          <TabsTrigger value="gstr3b" className="gap-2">
            <FileCheck className="h-4 w-4" />GSTR-3B
          </TabsTrigger>
          <TabsTrigger value="itc" className="gap-2">
            <Receipt className="h-4 w-4" />ITC
          </TabsTrigger>
          <TabsTrigger value="einvoice" className="gap-2">
            <QrCode className="h-4 w-4" />E-Invoice
          </TabsTrigger>
          <TabsTrigger value="ewb" className="gap-2">
            <Truck className="h-4 w-4" />E-Way Bill
          </TabsTrigger>
        </TabsList>

        {/* GSTR-1 Tab */}
        <TabsContent value="gstr1">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>GSTR-1 - Outward Supplies</CardTitle>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />Export JSON
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {gstr1Data ? (
                <div className="space-y-6">
                  {/* Summary */}
                  <div className="grid grid-cols-4 gap-4 p-4 bg-slate-50 rounded-lg">
                    <div>
                      <p className="text-sm text-slate-600">Total Invoices</p>
                      <p className="text-2xl font-bold">{gstr1Data.summary.total_invoices}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">Taxable Value</p>
                      <p className="text-2xl font-bold">{formatCurrency(gstr1Data.summary.total_taxable_value)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">IGST</p>
                      <p className="text-2xl font-bold text-blue-600">{formatCurrency(gstr1Data.summary.total_igst)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600">CGST + SGST</p>
                      <p className="text-2xl font-bold text-green-600">
                        {formatCurrency(gstr1Data.summary.total_cgst + gstr1Data.summary.total_sgst)}
                      </p>
                    </div>
                  </div>

                  {/* Tables */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 border rounded-lg">
                      <h4 className="font-semibold mb-2">B2B Invoices (Table 4)</h4>
                      <p className="text-3xl font-bold text-blue-600">{gstr1Data.tables.b2b.count}</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <h4 className="font-semibold mb-2">B2C Large (Table 5)</h4>
                      <p className="text-3xl font-bold text-green-600">{gstr1Data.tables.b2c_large.count}</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <h4 className="font-semibold mb-2">B2C Small (Table 7)</h4>
                      <p className="text-3xl font-bold text-orange-600">{gstr1Data.tables.b2c_small.count}</p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <h4 className="font-semibold mb-2">Credit/Debit Notes (Table 9)</h4>
                      <p className="text-3xl font-bold text-purple-600">{gstr1Data.tables.cdnr.count}</p>
                    </div>
                  </div>

                  {/* HSN Summary */}
                  <div>
                    <h4 className="font-semibold mb-3">HSN Summary (Table 12)</h4>
                    <div className="border rounded-lg overflow-hidden">
                      <table className="w-full text-sm">
                        <thead className="bg-slate-100">
                          <tr>
                            <th className="px-4 py-2 text-left">HSN Code</th>
                            <th className="px-4 py-2 text-left">Description</th>
                            <th className="px-4 py-2 text-right">Quantity</th>
                            <th className="px-4 py-2 text-right">Taxable Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {gstr1Data.tables.hsn_summary.data.slice(0, 10).map((hsn, idx) => (
                            <tr key={idx} className="border-t">
                              <td className="px-4 py-2 font-mono">{hsn.hsn_code}</td>
                              <td className="px-4 py-2">{hsn.description?.substring(0, 30)}</td>
                              <td className="px-4 py-2 text-right">{hsn.total_quantity}</td>
                              <td className="px-4 py-2 text-right">{formatCurrency(hsn.taxable_value)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  Select a period to view GSTR-1 data
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* GSTR-3B Tab */}
        <TabsContent value="gstr3b">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>GSTR-3B - Summary Return</CardTitle>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />Export
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {gstr3bData ? (
                <div className="space-y-6">
                  {/* Tax Summary */}
                  <div className="grid grid-cols-3 gap-6">
                    <Card className="bg-blue-50 border-blue-200">
                      <CardContent className="pt-4">
                        <h4 className="font-semibold text-blue-800 mb-2">Output Tax</h4>
                        <p className="text-3xl font-bold text-blue-600">
                          {formatCurrency(gstr3bData.summary.total_output_tax)}
                        </p>
                      </CardContent>
                    </Card>
                    <Card className="bg-green-50 border-green-200">
                      <CardContent className="pt-4">
                        <h4 className="font-semibold text-green-800 mb-2">Input Tax (ITC)</h4>
                        <p className="text-3xl font-bold text-green-600">
                          {formatCurrency(gstr3bData.summary.total_input_tax)}
                        </p>
                      </CardContent>
                    </Card>
                    <Card className={`${gstr3bData.summary.net_tax_liability > 0 ? 'bg-red-50 border-red-200' : 'bg-emerald-50 border-emerald-200'}`}>
                      <CardContent className="pt-4">
                        <h4 className={`font-semibold ${gstr3bData.summary.net_tax_liability > 0 ? 'text-red-800' : 'text-emerald-800'} mb-2`}>
                          {gstr3bData.summary.net_tax_liability > 0 ? 'Tax Payable' : 'ITC Credit'}
                        </h4>
                        <p className={`text-3xl font-bold ${gstr3bData.summary.net_tax_liability > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                          {formatCurrency(Math.abs(gstr3bData.summary.net_tax_liability || gstr3bData.summary.itc_credit))}
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Detailed Breakup */}
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-slate-100">
                        <tr>
                          <th className="px-4 py-3 text-left">Description</th>
                          <th className="px-4 py-3 text-right">IGST</th>
                          <th className="px-4 py-3 text-right">CGST</th>
                          <th className="px-4 py-3 text-right">SGST</th>
                          <th className="px-4 py-3 text-right">Cess</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-t">
                          <td className="px-4 py-3 font-medium">3.1 Outward Taxable Supplies</td>
                          <td className="px-4 py-3 text-right">{formatCurrency(gstr3bData.table_3_1.details.a_outward_taxable.igst)}</td>
                          <td className="px-4 py-3 text-right">{formatCurrency(gstr3bData.table_3_1.details.a_outward_taxable.cgst)}</td>
                          <td className="px-4 py-3 text-right">{formatCurrency(gstr3bData.table_3_1.details.a_outward_taxable.sgst)}</td>
                          <td className="px-4 py-3 text-right">{formatCurrency(gstr3bData.table_3_1.details.a_outward_taxable.cess)}</td>
                        </tr>
                        <tr className="border-t bg-green-50">
                          <td className="px-4 py-3 font-medium">4. Eligible ITC</td>
                          <td className="px-4 py-3 text-right text-green-600">{formatCurrency(gstr3bData.table_4.details.net_itc.igst)}</td>
                          <td className="px-4 py-3 text-right text-green-600">{formatCurrency(gstr3bData.table_4.details.net_itc.cgst)}</td>
                          <td className="px-4 py-3 text-right text-green-600">{formatCurrency(gstr3bData.table_4.details.net_itc.sgst)}</td>
                          <td className="px-4 py-3 text-right text-green-600">{formatCurrency(gstr3bData.table_4.details.net_itc.cess)}</td>
                        </tr>
                        <tr className="border-t bg-slate-100 font-semibold">
                          <td className="px-4 py-3">6. Tax Payable</td>
                          <td className="px-4 py-3 text-right">{formatCurrency(gstr3bData.table_6.tax_payable.igst)}</td>
                          <td className="px-4 py-3 text-right">{formatCurrency(gstr3bData.table_6.tax_payable.cgst)}</td>
                          <td className="px-4 py-3 text-right">{formatCurrency(gstr3bData.table_6.tax_payable.sgst)}</td>
                          <td className="px-4 py-3 text-right">{formatCurrency(gstr3bData.table_6.tax_payable.cess)}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  Select a period to view GSTR-3B data
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ITC Tab */}
        <TabsContent value="itc">
          <Card>
            <CardHeader>
              <CardTitle>Input Tax Credit (ITC) Register</CardTitle>
            </CardHeader>
            <CardContent>
              {itcData ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-600">Total ITC Available</p>
                      <p className="text-2xl font-bold text-blue-700">{formatCurrency(itcData.summary.total_itc_available.total)}</p>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg">
                      <p className="text-sm text-green-600">Eligible ITC</p>
                      <p className="text-2xl font-bold text-green-700">{formatCurrency(itcData.summary.eligible_itc.total)}</p>
                    </div>
                    <div className="p-4 bg-red-50 rounded-lg">
                      <p className="text-sm text-red-600">Ineligible ITC</p>
                      <p className="text-2xl font-bold text-red-700">{formatCurrency(itcData.summary.ineligible_itc.total)}</p>
                    </div>
                  </div>

                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-100">
                        <tr>
                          <th className="px-4 py-2 text-left">Invoice</th>
                          <th className="px-4 py-2 text-left">Supplier</th>
                          <th className="px-4 py-2 text-left">GSTIN</th>
                          <th className="px-4 py-2 text-right">Taxable</th>
                          <th className="px-4 py-2 text-right">Tax</th>
                          <th className="px-4 py-2 text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {itcData.entries.slice(0, 20).map((entry, idx) => (
                          <tr key={idx} className="border-t">
                            <td className="px-4 py-2 font-mono text-xs">{entry.invoice_number}</td>
                            <td className="px-4 py-2">{entry.supplier_name?.substring(0, 20)}</td>
                            <td className="px-4 py-2 font-mono text-xs">{entry.supplier_gstin || '-'}</td>
                            <td className="px-4 py-2 text-right">{formatCurrency(entry.taxable_value)}</td>
                            <td className="px-4 py-2 text-right">{formatCurrency(entry.igst + entry.cgst + entry.sgst)}</td>
                            <td className="px-4 py-2 text-center">
                              <Badge variant={entry.itc_eligible ? 'default' : 'destructive'}>
                                {entry.itc_eligible ? 'Eligible' : 'Ineligible'}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">Select a period to view ITC data</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* E-Invoice Tab */}
        <TabsContent value="einvoice">
          <Card>
            <CardHeader>
              <CardTitle>E-Invoice Management</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <QrCode className="h-16 w-16 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-slate-600">E-Invoice Generation</h3>
                <p className="text-slate-500 mt-2">Generate IRN and QR code for GST-compliant invoices</p>
                <p className="text-sm text-slate-400 mt-4">E-invoicing is mandatory for businesses with turnover &gt; ₹5 Cr</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* E-Way Bill Tab */}
        <TabsContent value="ewb">
          <Card>
            <CardHeader>
              <CardTitle>E-Way Bill Register</CardTitle>
            </CardHeader>
            <CardContent>
              {ewayBills.length > 0 ? (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="px-4 py-2 text-left">EWB Number</th>
                        <th className="px-4 py-2 text-left">Date</th>
                        <th className="px-4 py-2 text-left">From</th>
                        <th className="px-4 py-2 text-left">To</th>
                        <th className="px-4 py-2 text-left">Vehicle</th>
                        <th className="px-4 py-2 text-left">Valid Until</th>
                        <th className="px-4 py-2 text-center">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ewayBills.map((ewb, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-4 py-2 font-mono">{ewb.ewb_number}</td>
                          <td className="px-4 py-2">{ewb.ewb_date?.split('T')[0]}</td>
                          <td className="px-4 py-2">{ewb.from_place}</td>
                          <td className="px-4 py-2">{ewb.to_place}</td>
                          <td className="px-4 py-2 font-mono">{ewb.vehicle_no}</td>
                          <td className="px-4 py-2">{ewb.valid_upto?.split('T')[0]}</td>
                          <td className="px-4 py-2 text-center">
                            <Badge variant={ewb.status === 'generated' ? 'default' : 'secondary'}>
                              {ewb.status}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Truck className="h-16 w-16 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-slate-600">No E-Way Bills</h3>
                  <p className="text-slate-500 mt-2">E-Way bills will appear here when generated for invoices &gt; ₹50,000</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default GSTCompliance;
