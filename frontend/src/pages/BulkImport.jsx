import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { 
  Upload, Download, FileSpreadsheet, Users, Package, DollarSign,
  CheckCircle, XCircle, AlertTriangle, FileText, ArrowRight, Loader2
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const BulkImport = () => {
  const [activeTab, setActiveTab] = useState('customers');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [importResult, setImportResult] = useState(null);

  const downloadTemplate = async (type) => {
    try {
      const response = await api.get(`/bulk-import/templates/${type}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type}_import_template.xlsx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Template downloaded');
    } catch (err) {
      toast.error('Failed to download template');
    }
  };

  const handleFileUpload = async (e, endpoint) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      toast.error('Please upload an Excel file (.xlsx or .xls)');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setImportResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.post(endpoint, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        }
      });

      setImportResult(response.data);
      toast.success(response.data.message);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Import failed');
      setImportResult({ error: err.response?.data?.detail || 'Import failed' });
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const ImportCard = ({ title, description, icon: Icon, templateType, endpoint, color }) => (
    <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className={`h-12 w-12 rounded-lg flex items-center justify-center ${color}`}>
            <Icon className="h-6 w-6 text-white" />
          </div>
          <div>
            <CardTitle className="text-lg font-manrope">{title}</CardTitle>
            <CardDescription className="font-inter">{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => downloadTemplate(templateType)} className="flex-1">
            <Download className="h-4 w-4 mr-2" />Download Template
          </Button>
          <div className="flex-1 relative">
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => handleFileUpload(e, endpoint)}
              className="absolute inset-0 opacity-0 cursor-pointer"
              disabled={uploading}
            />
            <Button size="sm" className="w-full" disabled={uploading}>
              {uploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
              {uploading ? 'Importing...' : 'Upload & Import'}
            </Button>
          </div>
        </div>
        
        {uploading && (
          <div className="space-y-2">
            <Progress value={uploadProgress} className="h-2" />
            <p className="text-xs text-slate-500 text-center">{uploadProgress}% uploaded</p>
          </div>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6" data-testid="bulk-import-page">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 font-manrope">
          <Upload className="inline h-8 w-8 mr-2 text-accent" />
          Bulk Import
        </h1>
        <p className="text-slate-600 mt-1 font-inter">Import data from Excel files</p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 max-w-2xl">
          <TabsTrigger value="customers"><Users className="h-4 w-4 mr-2" />Customers</TabsTrigger>
          <TabsTrigger value="items"><Package className="h-4 w-4 mr-2" />Items</TabsTrigger>
          <TabsTrigger value="opening-balance"><DollarSign className="h-4 w-4 mr-2" />Opening Balance</TabsTrigger>
          <TabsTrigger value="opening-stock"><FileSpreadsheet className="h-4 w-4 mr-2" />Opening Stock</TabsTrigger>
        </TabsList>

        <TabsContent value="customers" className="space-y-4">
          <ImportCard
            title="Customer/Vendor Import"
            description="Import customers and vendors with contact details, addresses, and GST information"
            icon={Users}
            templateType="customers"
            endpoint="/bulk-import/customers"
            color="bg-blue-500"
          />
          
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-sm font-inter">Import Guidelines</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600 space-y-2">
              <p>• <strong>Account Name</strong> is mandatory and must be unique</p>
              <p>• <strong>GSTIN</strong> should be a valid 15-character GST number</p>
              <p>• Set <strong>Is Customer</strong> and <strong>Is Vendor</strong> to Y or N</p>
              <p>• <strong>Credit Limit</strong> and <strong>Payment Terms</strong> are numeric values</p>
              <p>• Duplicate account names will be skipped automatically</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="items" className="space-y-4">
          <ImportCard
            title="Items/Products Import"
            description="Import inventory items with specifications, pricing, and stock parameters"
            icon={Package}
            templateType="items"
            endpoint="/bulk-import/items"
            color="bg-green-500"
          />
          
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-sm font-inter">Import Guidelines</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600 space-y-2">
              <p>• <strong>Item Code</strong>, <strong>Item Name</strong>, <strong>Category</strong>, and <strong>UOM</strong> are mandatory</p>
              <p>• Tape specifications: Thickness (microns), Width (mm), Length (mtrs)</p>
              <p>• Set <strong>Reorder Level</strong> and <strong>Safety Stock</strong> for auto alerts</p>
              <p>• HSN codes are required for GST compliance</p>
              <p>• Duplicate item codes will be skipped</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="opening-balance" className="space-y-4">
          <ImportCard
            title="Opening Balance Import"
            description="Set opening balances for customers and vendors for a new financial year"
            icon={DollarSign}
            templateType="opening_balance"
            endpoint="/bulk-import/opening-balance"
            color="bg-purple-500"
          />
          
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-sm font-inter">Import Guidelines</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600 space-y-2">
              <p>• <strong>Account Name</strong> must exactly match an existing customer/vendor</p>
              <p>• <strong>Balance Type</strong>: Dr (Debit/Receivable) or Cr (Credit/Payable)</p>
              <p>• <strong>As On Date</strong>: Usually the first day of financial year (e.g., 2024-04-01)</p>
              <p>• A ledger entry will be created for each opening balance</p>
              <p>• Accounts not found in the system will be listed in the error report</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="opening-stock" className="space-y-4">
          <ImportCard
            title="Opening Stock Import"
            description="Set opening inventory quantities and values for items"
            icon={FileSpreadsheet}
            templateType="opening_stock"
            endpoint="/bulk-import/opening-stock"
            color="bg-orange-500"
          />
          
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-sm font-inter">Import Guidelines</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-600 space-y-2">
              <p>• <strong>Item Code</strong> must exactly match an existing inventory item</p>
              <p>• <strong>Warehouse/Location</strong>: BWD, VPT, or your warehouse code</p>
              <p>• <strong>Rate</strong>: If not provided, standard cost from item master will be used</p>
              <p>• <strong>Batch No</strong> and <strong>Expiry Date</strong> are optional</p>
              <p>• Stock entries will be created with transaction type "opening_stock"</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Import Results */}
      {importResult && (
        <Card className="border-slate-200">
          <CardHeader>
            <CardTitle className="text-lg font-manrope flex items-center gap-2">
              {importResult.error ? (
                <><XCircle className="h-5 w-5 text-red-500" />Import Failed</>
              ) : (
                <><CheckCircle className="h-5 w-5 text-green-500" />Import Complete</>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {importResult.error ? (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{importResult.error}</AlertDescription>
              </Alert>
            ) : (
              <>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-600">{importResult.details?.success || 0}</p>
                    <p className="text-sm text-green-700">Successfully Imported</p>
                  </div>
                  <div className="text-center p-4 bg-amber-50 rounded-lg">
                    <p className="text-2xl font-bold text-amber-600">{importResult.details?.skipped || 0}</p>
                    <p className="text-sm text-amber-700">Skipped (Duplicates)</p>
                  </div>
                  <div className="text-center p-4 bg-red-50 rounded-lg">
                    <p className="text-2xl font-bold text-red-600">{importResult.details?.errors?.length || 0}</p>
                    <p className="text-sm text-red-700">Errors</p>
                  </div>
                </div>

                {importResult.details?.not_found?.length > 0 && (
                  <Alert>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertTitle>Items Not Found ({importResult.details.not_found.length})</AlertTitle>
                    <AlertDescription>
                      <div className="mt-2 max-h-40 overflow-auto">
                        {importResult.details.not_found.map((item, idx) => (
                          <div key={idx} className="text-sm">
                            Row {item.row}: {item.account_name || item.item_code} not found in system
                          </div>
                        ))}
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                {importResult.details?.errors?.length > 0 && (
                  <Alert variant="destructive">
                    <XCircle className="h-4 w-4" />
                    <AlertTitle>Errors ({importResult.details.errors.length})</AlertTitle>
                    <AlertDescription>
                      <div className="mt-2 max-h-40 overflow-auto">
                        {importResult.details.errors.map((err, idx) => (
                          <div key={idx} className="text-sm">
                            Row {err.row}: {err.error}
                          </div>
                        ))}
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Quick Tips */}
      <Card className="border-slate-200 bg-gradient-to-r from-slate-50 to-slate-100">
        <CardContent className="py-4">
          <div className="flex items-start gap-4">
            <FileText className="h-8 w-8 text-accent flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-slate-900">Quick Tips for Successful Import</h3>
              <ul className="mt-2 space-y-1 text-sm text-slate-600">
                <li className="flex items-center gap-2"><ArrowRight className="h-3 w-3" />Always download and use the provided template</li>
                <li className="flex items-center gap-2"><ArrowRight className="h-3 w-3" />Delete sample rows before adding your data</li>
                <li className="flex items-center gap-2"><ArrowRight className="h-3 w-3" />Keep column headers unchanged</li>
                <li className="flex items-center gap-2"><ArrowRight className="h-3 w-3" />Use date format YYYY-MM-DD (e.g., 2024-04-01)</li>
                <li className="flex items-center gap-2"><ArrowRight className="h-3 w-3" />Maximum 5000 rows per import</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BulkImport;
