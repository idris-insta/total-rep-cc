import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  Warehouse, Save, ArrowLeft, MapPin, Building2, Phone, Mail, 
  CreditCard, FileText, RefreshCw, Settings
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import api from '../lib/api';
import { toast } from 'sonner';

const WarehouseForm = () => {
  const navigate = useNavigate();
  const { warehouseId } = useParams();
  const isEdit = warehouseId && warehouseId !== 'new';
  
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [loadingGeo, setLoadingGeo] = useState(false);
  
  const [formData, setFormData] = useState({
    warehouse_code: '',
    warehouse_name: '',
    prefix: '',
    gstin: '',
    pincode: '',
    state: '',
    city: '',
    address: '',
    bank_name: '',
    bank_account: '',
    ifsc_code: '',
    bank_branch: '',
    email: '',
    phone: '',
    contact_person: '',
    is_active: true
  });

  useEffect(() => {
    if (isEdit) {
      fetchWarehouse();
    }
  }, [warehouseId]);

  const fetchWarehouse = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/warehouse/warehouses/${warehouseId}`);
      setFormData(res.data);
    } catch (error) {
      toast.error('Failed to load warehouse');
      navigate('/inventory/warehouses');
    } finally {
      setLoading(false);
    }
  };

  const handlePincodeChange = async (pincode) => {
    setFormData({ ...formData, pincode });
    
    if (pincode.length === 6) {
      setLoadingGeo(true);
      try {
        const res = await fetch(`https://api.postalpincode.in/pincode/${pincode}`);
        const data = await res.json();
        if (data[0]?.Status === 'Success' && data[0]?.PostOffice?.length > 0) {
          const po = data[0].PostOffice[0];
          setFormData(prev => ({
            ...prev,
            state: po.State,
            city: po.District
          }));
          toast.success(`Location: ${po.District}, ${po.State}`);
        }
      } catch (error) {
        console.error('Pincode lookup failed:', error);
      } finally {
        setLoadingGeo(false);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.warehouse_code || !formData.warehouse_name || !formData.prefix) {
      toast.error('Please fill all required fields');
      return;
    }
    
    setSaving(true);
    try {
      if (isEdit) {
        await api.put(`/warehouse/warehouses/${warehouseId}`, formData);
        toast.success('Warehouse updated successfully');
      } else {
        await api.post('/warehouse/warehouses', formData);
        toast.success('Warehouse created successfully');
      }
      navigate('/inventory/warehouses');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save warehouse');
    } finally {
      setSaving(false);
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
    <div className="space-y-6" data-testid="warehouse-form">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/inventory/warehouses')}>
            <ArrowLeft className="h-4 w-4 mr-2" />Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 font-manrope">
              {isEdit ? 'Edit Warehouse' : 'Add New Warehouse'}
            </h1>
            <p className="text-slate-600 font-inter">Configure GST location and bank details</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="ghost" 
            onClick={() => window.open('/field-registry?module=inventory&entity=warehouses', '_blank')}
          >
            <Settings className="h-4 w-4 mr-2" />Customize Fields
          </Button>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-manrope flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-accent" />
                  Basic Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Warehouse Code *</Label>
                    <Input 
                      value={formData.warehouse_code}
                      onChange={(e) => setFormData({...formData, warehouse_code: e.target.value.toUpperCase()})}
                      placeholder="e.g., WH-GJ-01"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Warehouse Name *</Label>
                    <Input 
                      value={formData.warehouse_name}
                      onChange={(e) => setFormData({...formData, warehouse_name: e.target.value})}
                      placeholder="e.g., Gujarat Main Warehouse"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Document Prefix *</Label>
                    <Input 
                      value={formData.prefix}
                      onChange={(e) => setFormData({...formData, prefix: e.target.value.toUpperCase()})}
                      placeholder="e.g., GJ, MH, DL"
                      required
                    />
                    <p className="text-xs text-slate-500">Used for invoice/quote serial numbers</p>
                  </div>
                  <div className="space-y-2">
                    <Label>GSTIN *</Label>
                    <Input 
                      value={formData.gstin}
                      onChange={(e) => setFormData({...formData, gstin: e.target.value.toUpperCase()})}
                      placeholder="22AAAAA0000A1Z5"
                      maxLength={15}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-manrope flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-accent" />
                  Address Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Pincode</Label>
                    <div className="relative">
                      <Input 
                        value={formData.pincode}
                        onChange={(e) => handlePincodeChange(e.target.value)}
                        placeholder="000000"
                        maxLength={6}
                      />
                      {loadingGeo && (
                        <RefreshCw className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-accent" />
                      )}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>State</Label>
                    <Input 
                      value={formData.state}
                      onChange={(e) => setFormData({...formData, state: e.target.value})}
                      placeholder="Auto-filled from pincode"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>City</Label>
                    <Input 
                      value={formData.city}
                      onChange={(e) => setFormData({...formData, city: e.target.value})}
                      placeholder="Auto-filled from pincode"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Full Address</Label>
                  <Textarea 
                    value={formData.address}
                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                    placeholder="Enter complete address..."
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-manrope flex items-center gap-2">
                  <CreditCard className="h-5 w-5 text-accent" />
                  Bank Details
                </CardTitle>
                <CardDescription>Bank details will appear on invoices for this warehouse</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Bank Name</Label>
                    <Input 
                      value={formData.bank_name}
                      onChange={(e) => setFormData({...formData, bank_name: e.target.value})}
                      placeholder="e.g., HDFC Bank"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Account Number</Label>
                    <Input 
                      value={formData.bank_account}
                      onChange={(e) => setFormData({...formData, bank_account: e.target.value})}
                      placeholder="Enter account number"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>IFSC Code</Label>
                    <Input 
                      value={formData.ifsc_code}
                      onChange={(e) => setFormData({...formData, ifsc_code: e.target.value.toUpperCase()})}
                      placeholder="e.g., HDFC0001234"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Branch</Label>
                    <Input 
                      value={formData.bank_branch}
                      onChange={(e) => setFormData({...formData, bank_branch: e.target.value})}
                      placeholder="Branch name"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-manrope flex items-center gap-2">
                  <Phone className="h-5 w-5 text-accent" />
                  Contact Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Contact Person</Label>
                  <Input 
                    value={formData.contact_person}
                    onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                    placeholder="Manager name"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phone Number</Label>
                  <Input 
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    placeholder="+91 00000 00000"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Email Address</Label>
                  <Input 
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    placeholder="warehouse@company.com"
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-manrope">Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Active Warehouse</p>
                    <p className="text-sm text-slate-500">Enable for transactions</p>
                  </div>
                  <Switch 
                    checked={formData.is_active !== false}
                    onCheckedChange={(checked) => setFormData({...formData, is_active: checked})}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <Card>
              <CardContent className="p-4">
                <Button 
                  type="submit" 
                  className="w-full bg-accent hover:bg-accent/90"
                  disabled={saving}
                >
                  {saving ? (
                    <><RefreshCw className="h-4 w-4 mr-2 animate-spin" />Saving...</>
                  ) : (
                    <><Save className="h-4 w-4 mr-2" />{isEdit ? 'Update' : 'Create'} Warehouse</>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

export default WarehouseForm;
