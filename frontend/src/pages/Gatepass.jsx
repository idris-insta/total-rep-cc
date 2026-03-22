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
  Truck, Plus, Search, Filter, ArrowDownLeft, ArrowUpRight, 
  CheckCircle, Clock, Package, User, Phone, FileText, RefreshCw
} from 'lucide-react';

const API_URL = import.meta.env.VITE_BACKEND_URL;

const Gatepass = () => {
  const [gatepasses, setGatepasses] = useState([]);
  const [transporters, setTransporters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [showNewGatepass, setShowNewGatepass] = useState(false);
  const [showNewTransporter, setShowNewTransporter] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [warehouses, setWarehouses] = useState([]);

  const token = localStorage.getItem('token');
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const [newGatepass, setNewGatepass] = useState({
    gatepass_type: 'inward',
    reference_type: 'GRN',
    vehicle_no: '',
    driver_name: '',
    driver_phone: '',
    transporter_id: '',
    lr_no: '',
    party_name: '',
    warehouse_id: '',
    items: [{ item_id: '', item_name: '', quantity: 1, uom: 'PCS', remarks: '' }],
    purpose: '',
    remarks: ''
  });

  const [newTransporter, setNewTransporter] = useState({
    transporter_name: '',
    contact_person: '',
    phone: '',
    gstin: '',
    address: '',
    city: '',
    state: ''
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [gpRes, transRes, whRes] = await Promise.all([
        fetch(`${API_URL}/api/gatepass/`, { headers }),
        fetch(`${API_URL}/api/gatepass/transporters`, { headers }),
        fetch(`${API_URL}/api/inventory/warehouses`, { headers })
      ]);

      if (gpRes.ok) setGatepasses(await gpRes.json());
      if (transRes.ok) setTransporters(await transRes.json());
      if (whRes.ok) setWarehouses(await whRes.json());
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateGatepass = async () => {
    try {
      const response = await fetch(`${API_URL}/api/gatepass/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(newGatepass)
      });

      if (response.ok) {
        setShowNewGatepass(false);
        setNewGatepass({
          gatepass_type: 'inward',
          reference_type: 'GRN',
          vehicle_no: '',
          driver_name: '',
          driver_phone: '',
          transporter_id: '',
          lr_no: '',
          party_name: '',
          warehouse_id: '',
          items: [{ item_id: '', item_name: '', quantity: 1, uom: 'PCS', remarks: '' }],
          purpose: '',
          remarks: ''
        });
        fetchData();
      }
    } catch (error) {
      console.error('Error creating gatepass:', error);
    }
  };

  const handleCreateTransporter = async () => {
    try {
      const response = await fetch(`${API_URL}/api/gatepass/transporters`, {
        method: 'POST',
        headers,
        body: JSON.stringify(newTransporter)
      });

      if (response.ok) {
        setShowNewTransporter(false);
        setNewTransporter({
          transporter_name: '',
          contact_person: '',
          phone: '',
          gstin: '',
          address: '',
          city: '',
          state: ''
        });
        fetchData();
      }
    } catch (error) {
      console.error('Error creating transporter:', error);
    }
  };

  const handleApprove = async (id) => {
    try {
      await fetch(`${API_URL}/api/gatepass/${id}/approve`, {
        method: 'PUT',
        headers
      });
      fetchData();
    } catch (error) {
      console.error('Error approving gatepass:', error);
    }
  };

  const handleComplete = async (id) => {
    try {
      await fetch(`${API_URL}/api/gatepass/${id}/complete`, {
        method: 'PUT',
        headers
      });
      fetchData();
    } catch (error) {
      console.error('Error completing gatepass:', error);
    }
  };

  const filteredGatepasses = gatepasses.filter(gp => {
    if (activeTab !== 'all' && gp.gatepass_type !== activeTab) return false;
    if (searchTerm) {
      return gp.gatepass_no?.toLowerCase().includes(searchTerm.toLowerCase()) ||
             gp.vehicle_no?.toLowerCase().includes(searchTerm.toLowerCase()) ||
             gp.party_name?.toLowerCase().includes(searchTerm.toLowerCase());
    }
    return true;
  });

  const getStatusBadge = (status) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      approved: 'bg-blue-100 text-blue-800',
      in_transit: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      returned: 'bg-purple-100 text-purple-800'
    };
    return <Badge className={colors[status] || 'bg-gray-100'}>{status?.replace('_', ' ').toUpperCase()}</Badge>;
  };

  const addItem = () => {
    setNewGatepass({
      ...newGatepass,
      items: [...newGatepass.items, { item_id: '', item_name: '', quantity: 1, uom: 'PCS', remarks: '' }]
    });
  };

  const updateItem = (index, field, value) => {
    const updated = [...newGatepass.items];
    updated[index][field] = value;
    setNewGatepass({ ...newGatepass, items: updated });
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Gatepass Management</h1>
          <p className="text-sm text-gray-500">Track inward and outward material movement</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={showNewTransporter} onOpenChange={setShowNewTransporter}>
            <DialogTrigger asChild>
              <Button variant="outline"><Truck className="h-4 w-4 mr-2" />Add Transporter</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Transporter</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Transporter Name *</Label>
                  <Input 
                    value={newTransporter.transporter_name}
                    onChange={(e) => setNewTransporter({...newTransporter, transporter_name: e.target.value})}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Contact Person</Label>
                    <Input 
                      value={newTransporter.contact_person}
                      onChange={(e) => setNewTransporter({...newTransporter, contact_person: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Phone</Label>
                    <Input 
                      value={newTransporter.phone}
                      onChange={(e) => setNewTransporter({...newTransporter, phone: e.target.value})}
                    />
                  </div>
                </div>
                <div>
                  <Label>GSTIN</Label>
                  <Input 
                    value={newTransporter.gstin}
                    onChange={(e) => setNewTransporter({...newTransporter, gstin: e.target.value})}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>City</Label>
                    <Input 
                      value={newTransporter.city}
                      onChange={(e) => setNewTransporter({...newTransporter, city: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>State</Label>
                    <Input 
                      value={newTransporter.state}
                      onChange={(e) => setNewTransporter({...newTransporter, state: e.target.value})}
                    />
                  </div>
                </div>
                <Button onClick={handleCreateTransporter} className="w-full">Create Transporter</Button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={showNewGatepass} onOpenChange={setShowNewGatepass}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />New Gatepass</Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New Gatepass</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Gatepass Type *</Label>
                    <Select 
                      value={newGatepass.gatepass_type}
                      onValueChange={(v) => setNewGatepass({...newGatepass, gatepass_type: v})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="inward">Inward</SelectItem>
                        <SelectItem value="outward">Outward</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Reference Type *</Label>
                    <Select 
                      value={newGatepass.reference_type}
                      onValueChange={(v) => setNewGatepass({...newGatepass, reference_type: v})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="GRN">GRN</SelectItem>
                        <SelectItem value="DeliveryNote">Delivery Note</SelectItem>
                        <SelectItem value="StockTransfer">Stock Transfer</SelectItem>
                        <SelectItem value="Returnable">Returnable</SelectItem>
                        <SelectItem value="NonReturnable">Non-Returnable</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Vehicle No *</Label>
                    <Input 
                      placeholder="MH 01 AB 1234"
                      value={newGatepass.vehicle_no}
                      onChange={(e) => setNewGatepass({...newGatepass, vehicle_no: e.target.value.toUpperCase()})}
                    />
                  </div>
                  <div>
                    <Label>LR Number</Label>
                    <Input 
                      value={newGatepass.lr_no}
                      onChange={(e) => setNewGatepass({...newGatepass, lr_no: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Driver Name</Label>
                    <Input 
                      value={newGatepass.driver_name}
                      onChange={(e) => setNewGatepass({...newGatepass, driver_name: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Driver Phone</Label>
                    <Input 
                      value={newGatepass.driver_phone}
                      onChange={(e) => setNewGatepass({...newGatepass, driver_phone: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Transporter</Label>
                    <Select 
                      value={newGatepass.transporter_id}
                      onValueChange={(v) => setNewGatepass({...newGatepass, transporter_id: v})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select transporter" />
                      </SelectTrigger>
                      <SelectContent>
                        {transporters.map(t => (
                          <SelectItem key={t.id} value={t.id}>{t.transporter_name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Warehouse *</Label>
                    <Select 
                      value={newGatepass.warehouse_id}
                      onValueChange={(v) => setNewGatepass({...newGatepass, warehouse_id: v})}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select warehouse" />
                      </SelectTrigger>
                      <SelectContent>
                        {warehouses.map(w => (
                          <SelectItem key={w.id} value={w.id}>{w.warehouse_name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label>Party Name</Label>
                  <Input 
                    value={newGatepass.party_name}
                    onChange={(e) => setNewGatepass({...newGatepass, party_name: e.target.value})}
                  />
                </div>

                <div>
                  <Label>Items</Label>
                  <div className="border rounded p-3 space-y-2">
                    {newGatepass.items.map((item, idx) => (
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
                        <Select 
                          value={item.uom}
                          onValueChange={(v) => updateItem(idx, 'uom', v)}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="PCS">PCS</SelectItem>
                            <SelectItem value="KG">KG</SelectItem>
                            <SelectItem value="MTR">MTR</SelectItem>
                            <SelectItem value="CTN">CTN</SelectItem>
                          </SelectContent>
                        </Select>
                        <Input 
                          placeholder="Remarks"
                          value={item.remarks}
                          onChange={(e) => updateItem(idx, 'remarks', e.target.value)}
                        />
                      </div>
                    ))}
                    <Button variant="outline" size="sm" onClick={addItem}>
                      <Plus className="h-4 w-4 mr-1" /> Add Item
                    </Button>
                  </div>
                </div>

                <div>
                  <Label>Purpose / Remarks</Label>
                  <Input 
                    value={newGatepass.remarks}
                    onChange={(e) => setNewGatepass({...newGatepass, remarks: e.target.value})}
                  />
                </div>

                <Button onClick={handleCreateGatepass} className="w-full">Create Gatepass</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-full">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Gatepasses</p>
              <p className="text-2xl font-bold">{gatepasses.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-full">
              <ArrowDownLeft className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Inward</p>
              <p className="text-2xl font-bold">{gatepasses.filter(g => g.gatepass_type === 'inward').length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-full">
              <ArrowUpRight className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Outward</p>
              <p className="text-2xl font-bold">{gatepasses.filter(g => g.gatepass_type === 'outward').length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-full">
              <Truck className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Transporters</p>
              <p className="text-2xl font-bold">{transporters.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filter */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input 
            placeholder="Search by gatepass no, vehicle no, party name..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Button variant="outline" onClick={fetchData}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="inward">Inward</TabsTrigger>
          <TabsTrigger value="outward">Outward</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          {loading ? (
            <div className="flex justify-center p-8">
              <RefreshCw className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : filteredGatepasses.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Package className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">No gatepasses found</p>
                <Button className="mt-4" onClick={() => setShowNewGatepass(true)}>
                  <Plus className="h-4 w-4 mr-2" /> Create First Gatepass
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredGatepasses.map(gp => (
                <Card key={gp.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className={`p-3 rounded-full ${gp.gatepass_type === 'inward' ? 'bg-green-100' : 'bg-orange-100'}`}>
                          {gp.gatepass_type === 'inward' ? 
                            <ArrowDownLeft className={`h-6 w-6 text-green-600`} /> :
                            <ArrowUpRight className={`h-6 w-6 text-orange-600`} />
                          }
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-bold text-lg">{gp.gatepass_no}</p>
                            {getStatusBadge(gp.status)}
                            <Badge variant="outline">{gp.reference_type}</Badge>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2 text-sm text-gray-600">
                            <div className="flex items-center gap-1">
                              <Truck className="h-4 w-4" />
                              <span>{gp.vehicle_no}</span>
                            </div>
                            {gp.driver_name && (
                              <div className="flex items-center gap-1">
                                <User className="h-4 w-4" />
                                <span>{gp.driver_name}</span>
                              </div>
                            )}
                            {gp.party_name && (
                              <div className="flex items-center gap-1">
                                <Package className="h-4 w-4" />
                                <span>{gp.party_name}</span>
                              </div>
                            )}
                            {gp.lr_no && (
                              <div className="flex items-center gap-1">
                                <FileText className="h-4 w-4" />
                                <span>LR: {gp.lr_no}</span>
                              </div>
                            )}
                          </div>
                          <p className="text-xs text-gray-400 mt-2">
                            {gp.gatepass_type === 'inward' ? 'In Time' : 'Out Time'}: {gp.in_time || gp.out_time || 'N/A'}
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {gp.status === 'draft' && (
                          <Button size="sm" variant="outline" onClick={() => handleApprove(gp.id)}>
                            <CheckCircle className="h-4 w-4 mr-1" /> Approve
                          </Button>
                        )}
                        {gp.status === 'approved' && (
                          <Button size="sm" onClick={() => handleComplete(gp.id)}>
                            Complete
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Gatepass;
