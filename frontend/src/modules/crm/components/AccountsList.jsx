import React, { useState, useEffect } from 'react';
import { 
  Plus, Search, Edit, Trash2, X, Settings
} from 'lucide-react';
import { Card, CardContent } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../../../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Textarea } from '../../../components/ui/textarea';
import api from '../../../lib/api';
import { toast } from 'sonner';
import useFieldRegistry from '../../../hooks/useFieldRegistry';
import DynamicFormFields from '../../../components/DynamicRegistryForm';

const AccountsList = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({ industry: 'all', state: 'all', hasOutstanding: 'all' });
  const [loadingGeo, setLoadingGeo] = useState(false);

  const [formData, setFormData] = useState({
    customer_name: '', account_type: 'Customer', gstin: '', pan: '',
    billing_address: '', billing_country: 'India', billing_state: '', billing_district: '', billing_city: '', billing_pincode: '',
    shipping_addresses: [{ label: 'Default', address: '', city: '', state: '', pincode: '', country: 'India' }],
    contacts: [{ name: '', designation: '', email: '', phone: '', mobile: '', is_primary: true }],
    credit_limit: '', credit_days: '30', credit_control: 'Warn',
    payment_terms: '30 days', industry: '', website: '', location: '', notes: '',
    aadhar_no: '', opening_balance: '', bank_details: ''
  });

  const { 
    formFields: registryFields, 
    loading: registryLoading, 
    sectionLabels 
  } = useFieldRegistry('crm', 'customer_accounts');
  
  const useDynamicForm = registryFields && registryFields.length > 0;

  useEffect(() => { fetchAccounts(); }, []);

  const fetchAccounts = async () => {
    try {
      const response = await api.get('/crm/accounts');
      setAccounts(response.data);
    } catch (error) {
      toast.error('Failed to load accounts');
    } finally {
      setLoading(false);
    }
  };

  const tryAutoFillBillingFromPincode = async (pincode) => {
    if (!pincode || pincode.length !== 6) return;
    if ((formData.billing_country || 'India').toLowerCase() !== 'india') return;

    setLoadingGeo(true);
    try {
      const res = await api.get(`/crm/geo/pincode/${pincode}`);
      setFormData((prev) => ({
        ...prev,
        billing_country: res.data?.country || prev.billing_country,
        billing_state: res.data?.state || prev.billing_state,
        billing_district: res.data?.district || prev.billing_district,
        billing_city: res.data?.city || prev.billing_city
      }));
    } catch (e) {
      // ignore
    } finally {
      setLoadingGeo(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        credit_limit: formData.credit_limit ? parseFloat(formData.credit_limit) : 0,
        credit_days: parseInt(formData.credit_days) || 30
      };
      
      if (editingAccount) {
        await api.put(`/crm/accounts/${editingAccount.id}`, payload);
        toast.success('Account updated successfully');
      } else {
        await api.post('/crm/accounts', payload);
        toast.success('Account created successfully');
      }
      setOpen(false);
      setEditingAccount(null);
      fetchAccounts();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save account');
    }
  };

  const handleEdit = (account) => {
    setEditingAccount(account);
    setFormData({
      customer_name: account.customer_name || '',
      account_type: account.account_type || 'Customer',
      gstin: account.gstin || '',
      pan: account.pan || '',
      billing_address: account.billing_address || '',
      billing_country: account.billing_country || 'India',
      billing_state: account.billing_state || '',
      billing_district: account.billing_district || '',
      billing_city: account.billing_city || '',
      billing_pincode: account.billing_pincode || '',
      shipping_addresses: account.shipping_addresses?.length > 0 ? account.shipping_addresses : [{ label: 'Default', address: '', city: '', state: '', pincode: '', country: 'India' }],
      contacts: account.contacts?.length > 0 ? account.contacts : [{ name: '', designation: '', email: '', phone: '', mobile: '', is_primary: true }],
      credit_limit: account.credit_limit || '',
      credit_days: account.credit_days?.toString() || '30',
      credit_control: account.credit_control || 'Warn',
      payment_terms: account.payment_terms || '30 days',
      industry: account.industry || '',
      website: account.website || '',
      location: account.location || '',
      notes: account.notes || '',
      aadhar_no: account.aadhar_no || '',
      opening_balance: account.opening_balance || '',
      bank_details: account.bank_details || ''
    });
    setOpen(true);
  };

  const handleDelete = async (accountId) => {
    if (!window.confirm('Are you sure you want to deactivate this account?')) return;
    try {
      await api.delete(`/crm/accounts/${accountId}`);
      toast.success('Account deactivated');
      fetchAccounts();
    } catch (error) {
      toast.error('Failed to deactivate account');
    }
  };

  const resetForm = () => {
    setFormData({
      customer_name: '', account_type: 'Customer', gstin: '', pan: '',
      billing_address: '', billing_country: 'India', billing_state: '', billing_district: '', billing_city: '', billing_pincode: '',
      shipping_addresses: [{ label: 'Default', address: '', city: '', state: '', pincode: '', country: 'India' }],
      contacts: [{ name: '', designation: '', email: '', phone: '', mobile: '', is_primary: true }],
      credit_limit: '', credit_days: '30', credit_control: 'Warn',
      payment_terms: '30 days', industry: '', website: '', location: '', notes: '',
      aadhar_no: '', opening_balance: '', bank_details: ''
    });
  };

  const addShippingAddress = () => {
    setFormData({
      ...formData,
      shipping_addresses: [...formData.shipping_addresses, { label: '', address: '', city: '', state: '', pincode: '', country: 'India' }]
    });
  };

  const addContact = () => {
    setFormData({
      ...formData,
      contacts: [...formData.contacts, { name: '', designation: '', email: '', phone: '', mobile: '', is_primary: false }]
    });
  };

  const filteredAccounts = accounts.filter(acc => {
    const matchesSearch = acc.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      acc.gstin.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesIndustry = filters.industry === 'all' || acc.industry === filters.industry;
    const matchesState = filters.state === 'all' || acc.billing_state?.includes(filters.state);
    const matchesOutstanding = filters.hasOutstanding === 'all' || 
      (filters.hasOutstanding === 'yes' && (acc.receivable_amount || 0) > 0) ||
      (filters.hasOutstanding === 'no' && (acc.receivable_amount || 0) === 0);
    return matchesSearch && matchesIndustry && matchesState && matchesOutstanding;
  });

  if (loading || registryLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="accounts-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Customer Accounts</h2>
          <p className="text-slate-600 mt-1 font-inter">{accounts.length} total accounts</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) { setEditingAccount(null); resetForm(); } }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90 font-inter" data-testid="add-account-button">
              <Plus className="h-4 w-4 mr-2" />Add Account
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <div className="flex items-center justify-between">
                <DialogTitle className="font-manrope">{editingAccount ? 'Edit' : 'Create'} Account</DialogTitle>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open('/field-registry?module=crm&entity=accounts', '_blank')}
                  className="text-slate-500 hover:text-accent"
                  title="Customize form fields"
                >
                  <Settings className="h-4 w-4 mr-1" />
                  Customize Fields
                </Button>
              </div>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-6">
              <Tabs defaultValue="basic" className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                  <TabsTrigger value="basic">Basic Info</TabsTrigger>
                  <TabsTrigger value="address">Addresses</TabsTrigger>
                  <TabsTrigger value="contacts">Contacts</TabsTrigger>
                  <TabsTrigger value="credit">Credit & Terms</TabsTrigger>
                </TabsList>

                <TabsContent value="basic" className="space-y-4 mt-4">
                  {useDynamicForm ? (
                    <DynamicFormFields
                      fields={registryFields.filter(f => f.section === 'basic' || !f.section)}
                      formData={formData}
                      onChange={setFormData}
                      sectionLabels={sectionLabels}
                      groupBySection={false}
                      columns={3}
                    />
                  ) : (
                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label className="font-inter">Customer Name *</Label>
                        <Input value={formData.customer_name} onChange={(e) => setFormData({...formData, customer_name: e.target.value})} required data-testid="account-customer-name" />
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">Account Type</Label>
                        <Select value={formData.account_type} onValueChange={(value) => setFormData({...formData, account_type: value})}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Customer">Customer</SelectItem>
                            <SelectItem value="Prospect">Prospect</SelectItem>
                            <SelectItem value="Partner">Partner</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">Industry</Label>
                        <Select value={formData.industry} onValueChange={(value) => setFormData({...formData, industry: value})}>
                          <SelectTrigger><SelectValue placeholder="Select industry" /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Manufacturing">Manufacturing</SelectItem>
                            <SelectItem value="Packaging">Packaging</SelectItem>
                            <SelectItem value="Construction">Construction</SelectItem>
                            <SelectItem value="Automotive">Automotive</SelectItem>
                            <SelectItem value="Electronics">Electronics</SelectItem>
                            <SelectItem value="FMCG">FMCG</SelectItem>
                            <SelectItem value="Pharmaceutical">Pharmaceutical</SelectItem>
                            <SelectItem value="Other">Other</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">GSTIN *</Label>
                        <div className="flex gap-2">
                          <Input value={formData.gstin} onChange={(e) => setFormData({...formData, gstin: e.target.value.toUpperCase()})} placeholder="27XXXXX0000X1ZX" required data-testid="account-gstin" className="flex-1" />
                          <Button type="button" variant="outline" size="sm" onClick={async () => {
                            if (formData.gstin.length === 15) {
                              try {
                                const res = await api.get(`/crm/accounts/gst-lookup/${formData.gstin}`);
                                if (res.data.valid) {
                                  setFormData({...formData, 
                                    billing_state: res.data.state_name || formData.billing_state,
                                    pan: res.data.pan || formData.pan
                                  });
                                  toast.success(`State: ${res.data.state_name}`);
                                }
                              } catch (e) { toast.error('Invalid GSTIN'); }
                            } else { toast.error('Enter valid 15-char GSTIN'); }
                          }}>Verify</Button>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">PAN</Label>
                        <Input value={formData.pan} onChange={(e) => setFormData({...formData, pan: e.target.value.toUpperCase()})} placeholder="AAAAA0000A" />
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">Website</Label>
                        <Input value={formData.website} onChange={(e) => setFormData({...formData, website: e.target.value})} placeholder="https://example.com" />
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">Aadhar No</Label>
                        <Input value={formData.aadhar_no} onChange={(e) => setFormData({...formData, aadhar_no: e.target.value})} placeholder="0000 0000 0000" />
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">Opening Balance (₹)</Label>
                        <Input type="number" value={formData.opening_balance} onChange={(e) => setFormData({...formData, opening_balance: e.target.value})} placeholder="0.00" />
                      </div>
                      <div className="col-span-3 space-y-2">
                        <Label className="font-inter">Bank Details</Label>
                        <Textarea value={formData.bank_details} onChange={(e) => setFormData({...formData, bank_details: e.target.value})} rows={2} placeholder="Bank Name, A/C No, IFSC Code" />
                      </div>
                      <div className="col-span-3 space-y-2">
                        <Label className="font-inter">Notes</Label>
                        <Textarea value={formData.notes} onChange={(e) => setFormData({...formData, notes: e.target.value})} rows={2} />
                      </div>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="address" className="space-y-4 mt-4">
                  <div className="space-y-4">
                    <h4 className="font-semibold text-slate-900">Billing Address</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="col-span-2 space-y-2">
                        <Label className="font-inter">Address *</Label>
                        <Textarea value={formData.billing_address} onChange={(e) => setFormData({...formData, billing_address: e.target.value})} required rows={2} />
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">Country</Label>
                        <Input value={formData.billing_country} onChange={(e) => setFormData({...formData, billing_country: e.target.value})} placeholder="India" />
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">State</Label>
                        <Input value={formData.billing_state} onChange={(e) => setFormData({...formData, billing_state: e.target.value})} />
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">District</Label>
                        <Input value={formData.billing_district} onChange={(e) => setFormData({...formData, billing_district: e.target.value})} />
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">City</Label>
                        <Input value={formData.billing_city} onChange={(e) => setFormData({...formData, billing_city: e.target.value})} />
                      </div>
                      <div className="space-y-2">
                        <Label className="font-inter">Pincode</Label>
                        <Input value={formData.billing_pincode} onChange={(e) => {
                          const v = e.target.value.replace(/\D/g, '').slice(0, 6);
                          setFormData({...formData, billing_pincode: v});
                          if (v.length === 6) {
                            tryAutoFillBillingFromPincode(v);
                          }
                        }} />
                        {loadingGeo && <div className="text-xs text-slate-500">Auto-filling location…</div>}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4 border-t pt-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-slate-900">Shipping Addresses</h4>
                      <Button type="button" variant="outline" size="sm" onClick={addShippingAddress}>
                        <Plus className="h-4 w-4 mr-1" />Add Address
                      </Button>
                    </div>
                    {formData.shipping_addresses.map((addr, idx) => (
                      <div key={idx} className="p-4 border rounded-lg space-y-3">
                        <div className="flex items-center justify-between">
                          <Label className="font-inter font-semibold">Address {idx + 1}</Label>
                          {idx > 0 && (
                            <Button type="button" variant="ghost" size="sm" onClick={() => {
                              const newAddrs = formData.shipping_addresses.filter((_, i) => i !== idx);
                              setFormData({...formData, shipping_addresses: newAddrs});
                            }}>
                              <X className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                        <div className="grid grid-cols-4 gap-3">
                          <div className="space-y-2">
                            <Label className="font-inter text-sm">Label</Label>
                            <Input value={addr.label} onChange={(e) => {
                              const newAddrs = [...formData.shipping_addresses];
                              newAddrs[idx].label = e.target.value;
                              setFormData({...formData, shipping_addresses: newAddrs});
                            }} placeholder="Factory, Warehouse..." />
                          </div>
                          <div className="col-span-3 space-y-2">
                            <Label className="font-inter text-sm">Address</Label>
                            <Input value={addr.address} onChange={(e) => {
                              const newAddrs = [...formData.shipping_addresses];
                              newAddrs[idx].address = e.target.value;
                              setFormData({...formData, shipping_addresses: newAddrs});
                            }} />
                          </div>
                          <div className="space-y-2">
                            <Label className="font-inter text-sm">City</Label>
                            <Input value={addr.city} onChange={(e) => {
                              const newAddrs = [...formData.shipping_addresses];
                              newAddrs[idx].city = e.target.value;
                              setFormData({...formData, shipping_addresses: newAddrs});
                            }} />
                          </div>
                          <div className="space-y-2">
                            <Label className="font-inter text-sm">State</Label>
                            <Input value={addr.state} onChange={(e) => {
                              const newAddrs = [...formData.shipping_addresses];
                              newAddrs[idx].state = e.target.value;
                              setFormData({...formData, shipping_addresses: newAddrs});
                            }} />
                          </div>
                          <div className="space-y-2">
                            <Label className="font-inter text-sm">Pincode</Label>
                            <Input value={addr.pincode} onChange={(e) => {
                              const newAddrs = [...formData.shipping_addresses];
                              newAddrs[idx].pincode = e.target.value;
                              setFormData({...formData, shipping_addresses: newAddrs});
                            }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="contacts" className="space-y-4 mt-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-slate-900">Contact Persons</h4>
                    <Button type="button" variant="outline" size="sm" onClick={addContact}>
                      <Plus className="h-4 w-4 mr-1" />Add Contact
                    </Button>
                  </div>
                  {formData.contacts.map((contact, idx) => (
                    <div key={idx} className="p-4 border rounded-lg space-y-3">
                      <div className="flex items-center justify-between">
                        <Label className="font-inter font-semibold">Contact {idx + 1}</Label>
                        <div className="flex items-center gap-2">
                          <label className="flex items-center gap-2 text-sm">
                            <input type="checkbox" checked={contact.is_primary} onChange={(e) => {
                              const newContacts = formData.contacts.map((c, i) => ({...c, is_primary: i === idx ? e.target.checked : false}));
                              setFormData({...formData, contacts: newContacts});
                            }} />
                            Primary
                          </label>
                          {idx > 0 && (
                            <Button type="button" variant="ghost" size="sm" onClick={() => {
                              const newContacts = formData.contacts.filter((_, i) => i !== idx);
                              setFormData({...formData, contacts: newContacts});
                            }}>
                              <X className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        <div className="space-y-2">
                          <Label className="font-inter text-sm">Name</Label>
                          <Input value={contact.name} onChange={(e) => {
                            const newContacts = [...formData.contacts];
                            newContacts[idx].name = e.target.value;
                            setFormData({...formData, contacts: newContacts});
                          }} />
                        </div>
                        <div className="space-y-2">
                          <Label className="font-inter text-sm">Designation</Label>
                          <Input value={contact.designation} onChange={(e) => {
                            const newContacts = [...formData.contacts];
                            newContacts[idx].designation = e.target.value;
                            setFormData({...formData, contacts: newContacts});
                          }} />
                        </div>
                        <div className="space-y-2">
                          <Label className="font-inter text-sm">Email</Label>
                          <Input type="email" value={contact.email} onChange={(e) => {
                            const newContacts = [...formData.contacts];
                            newContacts[idx].email = e.target.value;
                            setFormData({...formData, contacts: newContacts});
                          }} />
                        </div>
                        <div className="space-y-2">
                          <Label className="font-inter text-sm">Phone</Label>
                          <Input value={contact.phone} onChange={(e) => {
                            const newContacts = [...formData.contacts];
                            newContacts[idx].phone = e.target.value;
                            setFormData({...formData, contacts: newContacts});
                          }} />
                        </div>
                        <div className="space-y-2">
                          <Label className="font-inter text-sm">Mobile</Label>
                          <Input value={contact.mobile} onChange={(e) => {
                            const newContacts = [...formData.contacts];
                            newContacts[idx].mobile = e.target.value;
                            setFormData({...formData, contacts: newContacts});
                          }} />
                        </div>
                      </div>
                    </div>
                  ))}
                </TabsContent>

                <TabsContent value="credit" className="space-y-4 mt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label className="font-inter">Credit Limit (₹)</Label>
                      <Input type="number" value={formData.credit_limit} onChange={(e) => setFormData({...formData, credit_limit: e.target.value})} placeholder="100000" />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Credit Days</Label>
                      <Input type="number" value={formData.credit_days} onChange={(e) => setFormData({...formData, credit_days: e.target.value})} placeholder="30" />
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Credit Control</Label>
                      <Select value={formData.credit_control} onValueChange={(value) => setFormData({...formData, credit_control: value})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Ignore">Ignore (No Check)</SelectItem>
                          <SelectItem value="Warn">Warn (Show Alert)</SelectItem>
                          <SelectItem value="Block">Block (Prevent Order)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Payment Terms</Label>
                      <Select value={formData.payment_terms} onValueChange={(value) => setFormData({...formData, payment_terms: value})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Advance">Advance</SelectItem>
                          <SelectItem value="Cash">Cash</SelectItem>
                          <SelectItem value="7 days">7 Days</SelectItem>
                          <SelectItem value="15 days">15 Days</SelectItem>
                          <SelectItem value="30 days">30 Days</SelectItem>
                          <SelectItem value="45 days">45 Days</SelectItem>
                          <SelectItem value="60 days">60 Days</SelectItem>
                          <SelectItem value="90 days">90 Days</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label className="font-inter">Location</Label>
                      <Input value={formData.location} onChange={(e) => setFormData({...formData, location: e.target.value})} placeholder="Mumbai, Delhi..." />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setOpen(false); setEditingAccount(null); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90" data-testid="account-submit-button">{editingAccount ? 'Update' : 'Create'}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder="Search by name or GSTIN..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" data-testid="account-search" />
        </div>
        <Select value={filters?.industry || 'all'} onValueChange={(v) => setFilters({...filters, industry: v})}>
          <SelectTrigger className="w-[140px]"><SelectValue placeholder="Industry" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Industries</SelectItem>
            <SelectItem value="Manufacturing">Manufacturing</SelectItem>
            <SelectItem value="Packaging">Packaging</SelectItem>
            <SelectItem value="Construction">Construction</SelectItem>
            <SelectItem value="Automotive">Automotive</SelectItem>
            <SelectItem value="FMCG">FMCG</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters?.state || 'all'} onValueChange={(v) => setFilters({...filters, state: v})}>
          <SelectTrigger className="w-[140px]"><SelectValue placeholder="State" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All States</SelectItem>
            <SelectItem value="Maharashtra">Maharashtra</SelectItem>
            <SelectItem value="Gujarat">Gujarat</SelectItem>
            <SelectItem value="Delhi">Delhi</SelectItem>
            <SelectItem value="Karnataka">Karnataka</SelectItem>
            <SelectItem value="Tamil Nadu">Tamil Nadu</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters?.hasOutstanding || 'all'} onValueChange={(v) => setFilters({...filters, hasOutstanding: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Outstanding" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Accounts</SelectItem>
            <SelectItem value="yes">With Outstanding</SelectItem>
            <SelectItem value="no">No Outstanding</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Customer</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">City/State</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">GSTIN</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Outstanding</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Credit</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Avg Days</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Salesperson</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredAccounts.length === 0 ? (
                  <tr><td colSpan="8" className="px-4 py-12 text-center text-slate-500 font-inter">
                    {searchTerm ? 'No accounts found' : 'No accounts yet. Click "Add Account" to create one.'}
                  </td></tr>
                ) : (
                  filteredAccounts.map((acc) => (
                    <tr key={acc.id} className="hover:bg-slate-50 transition-colors" data-testid={`account-row-${acc.id}`}>
                      <td className="px-3 py-3">
                        <div className="font-semibold text-slate-900 font-inter text-sm">{acc.customer_name}</div>
                        <div className="text-xs text-slate-500 font-inter">{acc.industry || '-'}</div>
                      </td>
                      <td className="px-3 py-3">
                        <div className="text-sm text-slate-900">{acc.billing_city || '-'}</div>
                        <div className="text-xs text-slate-500">{acc.billing_state || '-'}</div>
                      </td>
                      <td className="px-3 py-3 font-mono text-xs text-slate-600">{acc.gstin}</td>
                      <td className="px-3 py-3">
                        <div className={`font-mono text-sm font-semibold ${(acc.receivable_amount || 0) > 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {(acc.receivable_amount || 0) > 0 ? `₹${acc.receivable_amount?.toLocaleString('en-IN')}` : '₹0'}
                        </div>
                        {(acc.payable_amount || 0) > 0 && (
                          <div className="text-xs text-blue-600 font-mono">Pay: ₹{acc.payable_amount?.toLocaleString('en-IN')}</div>
                        )}
                      </td>
                      <td className="px-3 py-3">
                        <div className="font-mono text-sm">₹{acc.credit_limit?.toLocaleString('en-IN') || '0'}</div>
                        <Badge className="bg-slate-100 text-slate-700 text-xs">{acc.payment_terms}</Badge>
                      </td>
                      <td className="px-3 py-3 font-mono text-sm text-slate-600">
                        {acc.avg_payment_days ? `${Math.round(acc.avg_payment_days)} days` : '-'}
                      </td>
                      <td className="px-3 py-3 text-sm text-slate-600">
                        {acc.salesperson_name || '-'}
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex items-center gap-1">
                          <Button variant="ghost" size="sm" onClick={() => handleEdit(acc)} data-testid={`edit-account-${acc.id}`}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="sm" onClick={() => handleDelete(acc.id)} className="text-destructive" data-testid={`delete-account-${acc.id}`}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AccountsList;
