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
  FileText, Plus, Upload, CheckCircle, AlertTriangle, User, 
  Laptop, Car, CreditCard, RefreshCw, Eye, Trash2, Shield
} from 'lucide-react';

const API_URL = import.meta.env.VITE_BACKEND_URL;

const EmployeeVault = () => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [vaultSummary, setVaultSummary] = useState(null);
  const [documentTypes, setDocumentTypes] = useState([]);
  const [expiringDocs, setExpiringDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [showAsset, setShowAsset] = useState(false);
  const [activeTab, setActiveTab] = useState('documents');

  const token = localStorage.getItem('token');
  const headers = { 'Authorization': `Bearer ${token}` };

  const [newDocument, setNewDocument] = useState({
    employee_id: '',
    document_type: '',
    document_number: '',
    issue_date: '',
    expiry_date: '',
    issuing_authority: '',
    notes: ''
  });

  const [newAsset, setNewAsset] = useState({
    employee_id: '',
    asset_type: 'laptop',
    asset_code: '',
    asset_name: '',
    serial_number: '',
    assigned_date: new Date().toISOString().slice(0, 10),
    condition_at_assignment: 'good',
    value: 0,
    notes: ''
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [empRes, typesRes, expiringRes] = await Promise.all([
        fetch(`${API_URL}/api/hrms/employees`, { headers }),
        fetch(`${API_URL}/api/employee-vault/document-types`, { headers }),
        fetch(`${API_URL}/api/employee-vault/documents/expiring?days=30`, { headers })
      ]);

      if (empRes.ok) setEmployees(await empRes.json());
      if (typesRes.ok) {
        const data = await typesRes.json();
        setDocumentTypes(data.document_types || []);
      }
      if (expiringRes.ok) setExpiringDocs(await expiringRes.json());
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  const fetchVaultSummary = async (employeeId) => {
    try {
      const response = await fetch(`${API_URL}/api/employee-vault/${employeeId}/vault-summary`, { headers });
      if (response.ok) {
        const data = await response.json();
        setVaultSummary(data);
      }
    } catch (error) {
      console.error('Error fetching vault summary:', error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedEmployee) {
      fetchVaultSummary(selectedEmployee.id);
      setNewDocument({ ...newDocument, employee_id: selectedEmployee.id });
      setNewAsset({ ...newAsset, employee_id: selectedEmployee.id });
    }
  }, [selectedEmployee]);

  const handleUploadDocument = async () => {
    try {
      const formData = new FormData();
      Object.entries(newDocument).forEach(([key, value]) => {
        if (value) formData.append(key, value);
      });

      const response = await fetch(`${API_URL}/api/employee-vault/documents`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        setShowUpload(false);
        fetchVaultSummary(selectedEmployee.id);
        setNewDocument({
          employee_id: selectedEmployee.id,
          document_type: '',
          document_number: '',
          issue_date: '',
          expiry_date: '',
          issuing_authority: '',
          notes: ''
        });
      }
    } catch (error) {
      console.error('Error uploading document:', error);
    }
  };

  const handleAssignAsset = async () => {
    try {
      const response = await fetch(`${API_URL}/api/employee-vault/assets`, {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify(newAsset)
      });

      if (response.ok) {
        setShowAsset(false);
        fetchVaultSummary(selectedEmployee.id);
        setNewAsset({
          employee_id: selectedEmployee.id,
          asset_type: 'laptop',
          asset_code: '',
          asset_name: '',
          serial_number: '',
          assigned_date: new Date().toISOString().slice(0, 10),
          condition_at_assignment: 'good',
          value: 0,
          notes: ''
        });
      }
    } catch (error) {
      console.error('Error assigning asset:', error);
    }
  };

  const handleVerifyDocument = async (docId) => {
    try {
      await fetch(`${API_URL}/api/employee-vault/documents/${docId}/verify`, {
        method: 'PUT',
        headers
      });
      fetchVaultSummary(selectedEmployee.id);
    } catch (error) {
      console.error('Error verifying document:', error);
    }
  };

  const handleReturnAsset = async (assetId) => {
    try {
      await fetch(`${API_URL}/api/employee-vault/assets/${assetId}/return?condition=good`, {
        method: 'PUT',
        headers
      });
      fetchVaultSummary(selectedEmployee.id);
    } catch (error) {
      console.error('Error returning asset:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const getAssetIcon = (type) => {
    const icons = {
      laptop: Laptop,
      mobile: CreditCard,
      vehicle: Car,
      id_card: CreditCard,
      default: FileText
    };
    const Icon = icons[type] || icons.default;
    return <Icon className="h-5 w-5" />;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Employee Document Vault</h1>
          <p className="text-sm text-gray-500">Manage employee documents and assets</p>
        </div>
        <Button variant="outline" onClick={fetchData}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Expiring Documents Alert */}
      {expiringDocs.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="p-4 flex items-center gap-4">
            <AlertTriangle className="h-6 w-6 text-orange-500" />
            <div className="flex-1">
              <p className="font-medium text-orange-800">Documents Expiring Soon</p>
              <p className="text-sm text-orange-600">{expiringDocs.length} documents expiring in next 30 days</p>
            </div>
            <Badge variant="outline" className="text-orange-600 border-orange-300">{expiringDocs.length}</Badge>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Employee List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Employees</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {employees.map(emp => (
                <div 
                  key={emp.id}
                  onClick={() => setSelectedEmployee(emp)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    selectedEmployee?.id === emp.id 
                      ? 'bg-primary text-white' 
                      : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                      selectedEmployee?.id === emp.id ? 'bg-white/20' : 'bg-primary/10'
                    }`}>
                      <User className={`h-5 w-5 ${selectedEmployee?.id === emp.id ? 'text-white' : 'text-primary'}`} />
                    </div>
                    <div>
                      <p className="font-medium">{emp.name}</p>
                      <p className={`text-sm ${selectedEmployee?.id === emp.id ? 'text-white/70' : 'text-gray-500'}`}>
                        {emp.employee_code || emp.id.slice(0, 8)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Vault Details */}
        <Card className="lg:col-span-2">
          {selectedEmployee ? (
            <>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>{selectedEmployee.name}'s Vault</CardTitle>
                  <p className="text-sm text-gray-500">{selectedEmployee.department || 'No Department'}</p>
                </div>
                <div className="flex gap-2">
                  <Dialog open={showUpload} onOpenChange={setShowUpload}>
                    <DialogTrigger asChild>
                      <Button size="sm"><Upload className="h-4 w-4 mr-1" /> Upload Doc</Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Upload Document</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <Label>Document Type *</Label>
                          <Select 
                            value={newDocument.document_type}
                            onValueChange={(v) => setNewDocument({...newDocument, document_type: v})}
                          >
                            <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                            <SelectContent>
                              {documentTypes.map(type => (
                                <SelectItem key={type} value={type}>
                                  {type.replace(/_/g, ' ').toUpperCase()}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Document Number</Label>
                          <Input 
                            value={newDocument.document_number}
                            onChange={(e) => setNewDocument({...newDocument, document_number: e.target.value})}
                            placeholder="e.g., XXXX-XXXX-XXXX"
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label>Issue Date</Label>
                            <Input 
                              type="date"
                              value={newDocument.issue_date}
                              onChange={(e) => setNewDocument({...newDocument, issue_date: e.target.value})}
                            />
                          </div>
                          <div>
                            <Label>Expiry Date</Label>
                            <Input 
                              type="date"
                              value={newDocument.expiry_date}
                              onChange={(e) => setNewDocument({...newDocument, expiry_date: e.target.value})}
                            />
                          </div>
                        </div>
                        <div>
                          <Label>Issuing Authority</Label>
                          <Input 
                            value={newDocument.issuing_authority}
                            onChange={(e) => setNewDocument({...newDocument, issuing_authority: e.target.value})}
                          />
                        </div>
                        <div>
                          <Label>Notes</Label>
                          <Input 
                            value={newDocument.notes}
                            onChange={(e) => setNewDocument({...newDocument, notes: e.target.value})}
                          />
                        </div>
                        <Button onClick={handleUploadDocument} className="w-full">
                          <Upload className="h-4 w-4 mr-2" /> Upload Document
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>

                  <Dialog open={showAsset} onOpenChange={setShowAsset}>
                    <DialogTrigger asChild>
                      <Button size="sm" variant="outline"><Laptop className="h-4 w-4 mr-1" /> Assign Asset</Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Assign Asset</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <Label>Asset Type *</Label>
                          <Select 
                            value={newAsset.asset_type}
                            onValueChange={(v) => setNewAsset({...newAsset, asset_type: v})}
                          >
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="laptop">Laptop</SelectItem>
                              <SelectItem value="mobile">Mobile Phone</SelectItem>
                              <SelectItem value="vehicle">Vehicle</SelectItem>
                              <SelectItem value="id_card">ID Card</SelectItem>
                              <SelectItem value="key">Keys</SelectItem>
                              <SelectItem value="uniform">Uniform</SelectItem>
                              <SelectItem value="other">Other</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label>Asset Code *</Label>
                            <Input 
                              value={newAsset.asset_code}
                              onChange={(e) => setNewAsset({...newAsset, asset_code: e.target.value})}
                              placeholder="e.g., LAP-001"
                            />
                          </div>
                          <div>
                            <Label>Asset Name *</Label>
                            <Input 
                              value={newAsset.asset_name}
                              onChange={(e) => setNewAsset({...newAsset, asset_name: e.target.value})}
                              placeholder="e.g., Dell Laptop"
                            />
                          </div>
                        </div>
                        <div>
                          <Label>Serial Number</Label>
                          <Input 
                            value={newAsset.serial_number}
                            onChange={(e) => setNewAsset({...newAsset, serial_number: e.target.value})}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label>Assigned Date</Label>
                            <Input 
                              type="date"
                              value={newAsset.assigned_date}
                              onChange={(e) => setNewAsset({...newAsset, assigned_date: e.target.value})}
                            />
                          </div>
                          <div>
                            <Label>Value (₹)</Label>
                            <Input 
                              type="number"
                              value={newAsset.value}
                              onChange={(e) => setNewAsset({...newAsset, value: parseFloat(e.target.value)})}
                            />
                          </div>
                        </div>
                        <div>
                          <Label>Condition</Label>
                          <Select 
                            value={newAsset.condition_at_assignment}
                            onValueChange={(v) => setNewAsset({...newAsset, condition_at_assignment: v})}
                          >
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="new">New</SelectItem>
                              <SelectItem value="good">Good</SelectItem>
                              <SelectItem value="fair">Fair</SelectItem>
                              <SelectItem value="damaged">Damaged</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <Button onClick={handleAssignAsset} className="w-full">
                          <Laptop className="h-4 w-4 mr-2" /> Assign Asset
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent>
                {vaultSummary ? (
                  <>
                    {/* Summary Stats */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                      <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <FileText className="h-6 w-6 mx-auto text-blue-500 mb-2" />
                        <p className="text-2xl font-bold">{vaultSummary.documents?.total || 0}</p>
                        <p className="text-sm text-gray-500">Documents</p>
                      </div>
                      <div className="text-center p-4 bg-green-50 rounded-lg">
                        <CheckCircle className="h-6 w-6 mx-auto text-green-500 mb-2" />
                        <p className="text-2xl font-bold">{vaultSummary.documents?.verified || 0}</p>
                        <p className="text-sm text-gray-500">Verified</p>
                      </div>
                      <div className="text-center p-4 bg-purple-50 rounded-lg">
                        <Laptop className="h-6 w-6 mx-auto text-purple-500 mb-2" />
                        <p className="text-2xl font-bold">{vaultSummary.assets?.total || 0}</p>
                        <p className="text-sm text-gray-500">Assets ({formatCurrency(vaultSummary.assets?.total_value)})</p>
                      </div>
                    </div>

                    {/* Document Checklist */}
                    <div className="mb-6">
                      <h4 className="font-medium mb-2">Document Checklist</h4>
                      <div className="flex flex-wrap gap-2">
                        {vaultSummary.documents?.checklist?.map((item, idx) => (
                          <Badge 
                            key={idx}
                            variant={item.uploaded ? 'default' : 'outline'}
                            className={item.verified ? 'bg-green-500' : ''}
                          >
                            {item.verified && <CheckCircle className="h-3 w-3 mr-1" />}
                            {item.document_type.replace(/_/g, ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <Tabs value={activeTab} onValueChange={setActiveTab}>
                      <TabsList className="mb-4">
                        <TabsTrigger value="documents">Documents</TabsTrigger>
                        <TabsTrigger value="assets">Assets</TabsTrigger>
                      </TabsList>

                      <TabsContent value="documents">
                        <div className="space-y-3">
                          {vaultSummary.documents?.list?.length > 0 ? (
                            vaultSummary.documents.list.map(doc => (
                              <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-center gap-3">
                                  <FileText className="h-5 w-5 text-gray-400" />
                                  <div>
                                    <p className="font-medium">{doc.document_type.replace(/_/g, ' ').toUpperCase()}</p>
                                    <p className="text-sm text-gray-500">
                                      {doc.document_number || 'No number'}
                                      {doc.expiry_date && ` • Expires: ${doc.expiry_date}`}
                                    </p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-2">
                                  {doc.is_verified ? (
                                    <Badge className="bg-green-100 text-green-800"><Shield className="h-3 w-3 mr-1" />Verified</Badge>
                                  ) : (
                                    <Button size="sm" variant="outline" onClick={() => handleVerifyDocument(doc.id)}>
                                      <CheckCircle className="h-4 w-4 mr-1" /> Verify
                                    </Button>
                                  )}
                                </div>
                              </div>
                            ))
                          ) : (
                            <p className="text-center text-gray-500 py-4">No documents uploaded</p>
                          )}
                        </div>
                      </TabsContent>

                      <TabsContent value="assets">
                        <div className="space-y-3">
                          {vaultSummary.assets?.list?.length > 0 ? (
                            vaultSummary.assets.list.map(asset => (
                              <div key={asset.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-center gap-3">
                                  {getAssetIcon(asset.asset_type)}
                                  <div>
                                    <p className="font-medium">{asset.asset_name}</p>
                                    <p className="text-sm text-gray-500">
                                      {asset.asset_code} • {asset.serial_number || 'No S/N'}
                                    </p>
                                  </div>
                                </div>
                                <div className="flex items-center gap-4">
                                  <span className="font-medium">{formatCurrency(asset.value)}</span>
                                  <Badge variant="outline">{asset.condition_at_assignment}</Badge>
                                  {asset.status === 'assigned' && (
                                    <Button size="sm" variant="outline" onClick={() => handleReturnAsset(asset.id)}>
                                      Return
                                    </Button>
                                  )}
                                </div>
                              </div>
                            ))
                          ) : (
                            <p className="text-center text-gray-500 py-4">No assets assigned</p>
                          )}
                        </div>
                      </TabsContent>
                    </Tabs>
                  </>
                ) : (
                  <div className="flex justify-center p-8">
                    <RefreshCw className="h-8 w-8 animate-spin text-primary" />
                  </div>
                )}
              </CardContent>
            </>
          ) : (
            <CardContent className="p-8 text-center">
              <User className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500">Select an employee to view their vault</p>
            </CardContent>
          )}
        </Card>
      </div>
    </div>
  );
};

export default EmployeeVault;
