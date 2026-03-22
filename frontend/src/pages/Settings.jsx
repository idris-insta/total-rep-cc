import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Plus, Users as UsersIcon, Key, Building2, Shield } from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';

const ROLES = [
  { value: 'admin', label: 'Administrator', description: 'Full system access' },
  { value: 'sales_manager', label: 'Sales Manager', description: 'CRM access + team visibility' },
  { value: 'sales_team_leader', label: 'Sales Team Leader', description: 'CRM access for own + direct reports' },
  { value: 'salesperson', label: 'Sales Person', description: 'CRM access for own assigned leads' },
  { value: 'production_manager', label: 'Production Manager', description: 'Production, Inventory, Quality' },
  { value: 'purchase_manager', label: 'Purchase Manager', description: 'Procurement, Suppliers, Inventory view' },
  { value: 'accounts_manager', label: 'Accounts Manager', description: 'Accounts, Finance, Reports' },
  { value: 'hr_manager', label: 'HR Manager', description: 'HRMS, Attendance, Payroll' },
  { value: 'quality_manager', label: 'Quality Manager', description: 'Quality, Inspections, Complaints' },
  { value: 'warehouse_user', label: 'Warehouse User', description: 'Inventory, Stock transfers (specific location)' },
  { value: 'factory_operator', label: 'Factory Operator', description: 'Production entry (specific machine)' },
  { value: 'viewer', label: 'Viewer', description: 'Read-only access to dashboards' }
];

const PERMISSIONS = {
  admin: ['all'],
  sales_manager: ['crm:* (all leads)', 'accounts:read', 'dashboard:read'],
  sales_team_leader: ['crm:* (team leads)', 'dashboard:read'],
  salesperson: ['crm:* (assigned leads)', 'dashboard:read'],
  production_manager: ['production:*', 'inventory:read', 'quality:*', 'dashboard:read'],
  purchase_manager: ['procurement:*', 'inventory:read', 'dashboard:read'],
  accounts_manager: ['accounts:*', 'dashboard:read'],
  hr_manager: ['hrms:*', 'dashboard:read'],
  quality_manager: ['quality:*', 'production:read', 'dashboard:read'],
  warehouse_user: ['inventory:read', 'inventory:update'],
  factory_operator: ['production:read', 'production:create'],
  viewer: ['dashboard:read', '*:read']
};

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    role: 'viewer',
    location: '',
    department: '',
    team: '',
    reports_to: ''
  });
  const { user: currentUser } = useAuth();

  const fetchUsers = async () => {
    try {
      const response = await api.get('/settings/users');
      setUsers(response.data);
    } catch (error) {
      toast.error('Failed to load users');
    }
  };

  useEffect(() => {
    if (currentUser?.role === 'admin') {
      fetchUsers();
    }
  }, [currentUser]);

  // (removed stray duplicate fetch logic)

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/auth/register', formData);
      toast.success('User created successfully');
      setOpen(false);
      fetchUsers();
      setFormData({ email: '', password: '', name: '', role: 'viewer', location: '', department: '', team: '', reports_to: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    }
  };

  const getRoleBadge = (role) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-800',
      sales_manager: 'bg-blue-100 text-blue-800',
      production_manager: 'bg-orange-100 text-orange-800',
      purchase_manager: 'bg-green-100 text-green-800',
      accounts_manager: 'bg-emerald-100 text-emerald-800',
      hr_manager: 'bg-pink-100 text-pink-800',
      quality_manager: 'bg-indigo-100 text-indigo-800',
      warehouse_user: 'bg-yellow-100 text-yellow-800',
      factory_operator: 'bg-cyan-100 text-cyan-800',
      viewer: 'bg-gray-100 text-gray-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  if (currentUser?.role !== 'admin') {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-6">
          <p className="text-slate-600 font-inter">You don’t have permission to manage users. Contact your administrator.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-slate-900 font-manrope">User Management</h3>
          <p className="text-slate-600 text-sm mt-1 font-inter">Manage user accounts and roles</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90 font-inter" data-testid="add-user-button">
              <Plus className="h-4 w-4 mr-2" />
              Add User
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle className="font-manrope">Create New User</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name" className="font-inter">Full Name</Label>
                  <Input id="name" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} required data-testid="user-name-input" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email" className="font-inter">Email</Label>
                  <Input id="email" type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password" className="font-inter">Password</Label>
                  <Input id="password" type="password" value={formData.password} onChange={(e) => setFormData({...formData, password: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role" className="font-inter">Role</Label>
                  <Select value={formData.role} onValueChange={(value) => setFormData({...formData, role: value})} required>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {ROLES.map(role => (
                        <SelectItem key={role.value} value={role.value}>
                          <div>
                            <div className="font-medium">{role.label}</div>
                            <div className="text-xs text-slate-500">{role.description}</div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="location" className="font-inter">Location (Optional)</Label>
                  <Select value={formData.location} onValueChange={(value) => setFormData({...formData, location: value})}>
                    <SelectTrigger><SelectValue placeholder="Select location" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BWD">BWD Warehouse</SelectItem>
                      <SelectItem value="SGM">SGM Factory</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="department" className="font-inter">Department (Optional)</Label>
                  <Select value={formData.department} onValueChange={(value) => setFormData({...formData, department: value})}>
                    <SelectTrigger><SelectValue placeholder="Select department" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Sales">Sales</SelectItem>
                      <SelectItem value="Production">Production</SelectItem>
                      <SelectItem value="Purchase">Purchase</SelectItem>
                      <SelectItem value="Accounts">Accounts</SelectItem>
                      <SelectItem value="HR">HR</SelectItem>
                      <SelectItem value="Quality">Quality</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="team" className="font-inter">Team (Optional)</Label>
                  <Input id="team" value={formData.team} onChange={(e) => setFormData({...formData, team: e.target.value})} placeholder="e.g., West Sales" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="reports_to" className="font-inter">Reports To (User ID) (Optional)</Label>
                  <Input id="reports_to" value={formData.reports_to} onChange={(e) => setFormData({...formData, reports_to: e.target.value})} placeholder="Manager user_id" />
                </div>

              </div>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800 font-medium font-inter mb-1">Permissions for {ROLES.find(r => r.value === formData.role)?.label}:</p>
                <div className="flex flex-wrap gap-1">
                  {PERMISSIONS[formData.role]?.map((perm, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs bg-white">{perm}</Badge>
                  ))}
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90" data-testid="submit-user-button">Create User</Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">User</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Role</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Location</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Department</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider font-inter">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-slate-50 transition-colors" data-testid="user-row">
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-semibold text-slate-900 font-inter">{user.name}</div>
                        <div className="text-sm text-slate-500 font-inter">{user.email}</div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge className={`${getRoleBadge(user.role)} font-inter`}>
                        {ROLES.find(r => r.value === user.role)?.label || user.role}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600 font-inter">{user.location || '-'}</td>
                    <td className="px-4 py-3 text-sm text-slate-600 font-inter">{user.department || '-'}</td>
                    <td className="px-4 py-3 text-sm text-slate-500 font-mono">{new Date(user.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const RolePermissions = () => {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xl font-bold text-slate-900 font-manrope">Role Permissions</h3>
        <p className="text-slate-600 text-sm mt-1 font-inter">View and understand access levels for each role</p>
      </div>

      <div className="grid gap-4">
        {ROLES.map(role => (
          <Card key={role.value} className="border-slate-200 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base font-manrope">{role.label}</CardTitle>
                  <CardDescription className="font-inter">{role.description}</CardDescription>
                </div>
                <Shield className="h-5 w-5 text-slate-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {PERMISSIONS[role.value]?.map((perm, idx) => (
                  <Badge key={idx} variant="outline" className="font-mono text-xs">{perm}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

const Settings = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 font-manrope" data-testid="settings-title">Settings</h1>
        <p className="text-slate-600 mt-1 font-inter">Manage system configuration and users</p>
      </div>

      <Tabs defaultValue="users" className="space-y-4">
        <TabsList className="bg-white border border-slate-200">
          <TabsTrigger value="users" className="font-inter" data-testid="tab-users">
            <UsersIcon className="h-4 w-4 mr-2" />
            Users
          </TabsTrigger>
          <TabsTrigger value="roles" className="font-inter" data-testid="tab-roles">
            <Key className="h-4 w-4 mr-2" />
            Roles & Permissions
          </TabsTrigger>
          <TabsTrigger value="company" className="font-inter" data-testid="tab-company">
            <Building2 className="h-4 w-4 mr-2" />
            Company
          </TabsTrigger>
        </TabsList>

        <TabsContent value="users">
          <UserManagement />
        </TabsContent>

        <TabsContent value="roles">
          <RolePermissions />
        </TabsContent>

        <TabsContent value="company">
          <Card className="border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="font-manrope">Company Information</CardTitle>
              <CardDescription className="font-inter">Manage company details and locations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="font-inter">Company Name</Label>
                    <Input defaultValue="Adhesive Tapes Pvt. Ltd." className="mt-1" />
                  </div>
                  <div>
                    <Label className="font-inter">GSTIN</Label>
                    <Input defaultValue="27XXXXX0000X1ZX" className="mt-1" />
                  </div>
                </div>
                <div>
                  <Label className="font-inter">Locations</Label>
                  <div className="mt-2 space-y-2">
                    <Card className="bg-blue-50 border-blue-200">
                      <CardContent className="p-3">
                        <div className="font-semibold text-sm font-inter">BWD - Base Warehouse & Dispatch</div>
                        <div className="text-xs text-slate-600 font-inter mt-1">Main warehouse and distribution center</div>
                      </CardContent>
                    </Card>
                    <Card className="bg-orange-50 border-orange-200">
                      <CardContent className="p-3">
                        <div className="font-semibold text-sm font-inter">SGM - Production Factory</div>
                        <div className="text-xs text-slate-600 font-inter mt-1">Manufacturing and coating facility</div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Settings;