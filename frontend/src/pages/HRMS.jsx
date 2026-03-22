import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { 
  Plus, Search, Edit, Trash2, Eye, Users, Calendar, Clock,
  UserCheck, UserX, FileText, DollarSign, RefreshCw, Download,
  Building, CheckCircle, XCircle, AlertTriangle, BarChart3,
  Briefcase, CalendarDays, Timer, CreditCard
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import api from '../lib/api';
import { toast } from 'sonner';
import useCustomFields from '../hooks/useCustomFields';
import DynamicFormFields from '../components/DynamicFormFields';

// ==================== HRMS DASHBOARD ====================
const HRMSDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total_employees: 0, present_today: 0, on_leave: 0, pending_leaves: 0,
    departments: {}, locations: {}
  });
  const [loading, setLoading] = useState(true);
  const [recentAttendance, setRecentAttendance] = useState([]);

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    try {
      const [employeesRes, attendanceRes, leavesRes] = await Promise.all([
        api.get('/hrms/employees'),
        api.get(`/hrms/attendance?date=${new Date().toISOString().split('T')[0]}`),
        api.get('/hrms/leave-requests?status=pending')
      ]);
      
      const employees = employeesRes.data;
      const todayAttendance = attendanceRes.data;
      const pendingLeaves = leavesRes.data;
      
      // Calculate stats
      const deptCount = {};
      const locCount = {};
      employees.forEach(emp => {
        deptCount[emp.department] = (deptCount[emp.department] || 0) + 1;
        locCount[emp.location] = (locCount[emp.location] || 0) + 1;
      });
      
      const presentCount = todayAttendance.filter(a => a.status === 'present').length;
      const leaveCount = todayAttendance.filter(a => a.status === 'leave').length;
      
      setStats({
        total_employees: employees.length,
        present_today: presentCount,
        on_leave: leaveCount,
        pending_leaves: pendingLeaves.length,
        departments: deptCount,
        locations: locCount
      });
      setRecentAttendance(todayAttendance.slice(0, 10));
    } catch (error) {
      console.error('Failed to load HRMS stats', error);
    } finally {
      setLoading(false);
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
    <div className="space-y-6" data-testid="hrms-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">HRMS Dashboard</h2>
          <p className="text-slate-600 mt-1 font-inter">Employee management, attendance & payroll</p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />Refresh
        </Button>
      </div>

      {/* Main Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/hrms/employees')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-blue-100 flex items-center justify-center">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-blue-600">{stats.total_employees}</div>
                <p className="text-sm text-slate-500">Employees</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/hrms/attendance')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-green-100 flex items-center justify-center">
                <UserCheck className="h-6 w-6 text-green-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-green-600">{stats.present_today}</div>
                <p className="text-sm text-slate-500">Present Today</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/hrms/leave')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-orange-100 flex items-center justify-center">
                <CalendarDays className="h-6 w-6 text-orange-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-orange-600">{stats.on_leave}</div>
                <p className="text-sm text-slate-500">On Leave</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer" onClick={() => navigate('/hrms/leave')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="h-12 w-12 rounded-lg bg-red-100 flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-red-600">{stats.pending_leaves}</div>
                <p className="text-sm text-slate-500">Pending Approvals</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Department & Location Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="font-manrope">By Department</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.departments).map(([dept, count]) => (
                <div key={dept} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Briefcase className="h-5 w-5 text-slate-400" />
                    <span className="font-medium text-slate-900">{dept}</span>
                  </div>
                  <Badge className="bg-blue-100 text-blue-800">{count}</Badge>
                </div>
              ))}
              {Object.keys(stats.departments).length === 0 && (
                <p className="text-center text-slate-500 py-4">No employees yet</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 shadow-sm">
          <CardHeader>
            <CardTitle className="font-manrope">By Location</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.locations).map(([loc, count]) => (
                <div key={loc} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <Building className="h-5 w-5 text-slate-400" />
                    <span className="font-medium text-slate-900">{loc}</span>
                  </div>
                  <Badge className="bg-green-100 text-green-800">{count}</Badge>
                </div>
              ))}
              {Object.keys(stats.locations).length === 0 && (
                <p className="text-center text-slate-500 py-4">No locations yet</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="font-manrope">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/hrms/employees')}>
              <Users className="h-6 w-6" />
              <span>Employees</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/hrms/attendance')}>
              <Clock className="h-6 w-6" />
              <span>Attendance</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/hrms/leave')}>
              <CalendarDays className="h-6 w-6" />
              <span>Leave</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/hrms/payroll')}>
              <CreditCard className="h-6 w-6" />
              <span>Payroll</span>
            </Button>
            <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => navigate('/hrms/reports')}>
              <BarChart3 className="h-6 w-6" />
              <span>Reports</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== EMPLOYEES LIST ====================
const EmployeesList = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({ department: 'all', location: 'all' });
  const [formData, setFormData] = useState({
    employee_code: '', name: '', email: '', phone: '',
    department: 'Production', designation: '', location: 'BWD',
    date_of_joining: '', shift_timing: 'General',
    basic_salary: '', hra: '', pf: '12', esi: '0.75', pt: '200'
  });
  
  // Dynamic fields from Power Settings
  const { fields: customFields } = useCustomFields('hrms_employees');
  const [customFieldValues, setCustomFieldValues] = useState({});

  useEffect(() => { fetchEmployees(); }, [filters]);

  const fetchEmployees = async () => {
    try {
      let url = '/hrms/employees?';
      if (filters.department !== 'all') url += `department=${filters.department}&`;
      if (filters.location !== 'all') url += `location=${filters.location}&`;
      const response = await api.get(url);
      setEmployees(response.data);
    } catch (error) {
      toast.error('Failed to load employees');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        basic_salary: parseFloat(formData.basic_salary) || 0,
        hra: parseFloat(formData.hra) || 0,
        pf: parseFloat(formData.pf) || 12,
        esi: parseFloat(formData.esi) || 0.75,
        pt: parseFloat(formData.pt) || 200,
        custom_fields: customFieldValues
      };

      if (editingEmployee) {
        await api.put(`/hrms/employees/${editingEmployee.id}`, payload);
        toast.success('Employee updated');
      } else {
        await api.post('/hrms/employees', payload);
        toast.success('Employee created');
      }
      setOpen(false);
      setEditingEmployee(null);
      setCustomFieldValues({});
      fetchEmployees();
      resetForm();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save employee');
    }
  };

  const handleEdit = (employee) => {
    setEditingEmployee(employee);
    setFormData({
      employee_code: employee.employee_code || '',
      name: employee.name || '',
      email: employee.email || '',
      phone: employee.phone || '',
      department: employee.department || 'Production',
      designation: employee.designation || '',
      location: employee.location || 'BWD',
      date_of_joining: employee.date_of_joining || '',
      shift_timing: employee.shift_timing || 'General',
      basic_salary: employee.basic_salary?.toString() || '',
      hra: employee.hra?.toString() || '',
      pf: employee.pf?.toString() || '12',
      esi: employee.esi?.toString() || '0.75',
      pt: employee.pt?.toString() || '200'
    });
    setCustomFieldValues(employee.custom_fields || {});
    setOpen(true);
  };

  const resetForm = () => {
    setFormData({
      employee_code: '', name: '', email: '', phone: '',
      department: 'Production', designation: '', location: 'BWD',
      date_of_joining: '', shift_timing: 'General',
      basic_salary: '', hra: '', pf: '12', esi: '0.75', pt: '200'
    });
    setCustomFieldValues({});
  };
  
  const handleCustomFieldChange = (fieldName, value) => {
    setCustomFieldValues(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const filteredEmployees = employees.filter(emp =>
    emp.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.employee_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    emp.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const deptColors = {
    'Production': 'bg-blue-100 text-blue-800',
    'Sales': 'bg-green-100 text-green-800',
    'Purchase': 'bg-purple-100 text-purple-800',
    'HR/Admin': 'bg-orange-100 text-orange-800',
    'Accounts': 'bg-yellow-100 text-yellow-800',
    'Quality': 'bg-red-100 text-red-800'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="employees-list">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Employees</h2>
          <p className="text-slate-600 mt-1 font-inter">{employees.length} employees</p>
        </div>
        <Dialog open={open} onOpenChange={(val) => { setOpen(val); if (!val) { setEditingEmployee(null); resetForm(); } }}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90" data-testid="add-employee-button">
              <Plus className="h-4 w-4 mr-2" />Add Employee
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="font-manrope">{editingEmployee ? 'Edit' : 'Add'} Employee</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <Tabs defaultValue="basic" className="w-full">
                <TabsList className={`grid w-full ${customFields.length > 0 ? 'grid-cols-4' : 'grid-cols-3'}`}>
                  <TabsTrigger value="basic">Basic Info</TabsTrigger>
                  <TabsTrigger value="work">Work Details</TabsTrigger>
                  <TabsTrigger value="salary">Salary & Statutory</TabsTrigger>
                  {customFields.length > 0 && <TabsTrigger value="custom">Custom</TabsTrigger>}
                </TabsList>

                <TabsContent value="basic" className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Employee Code *</Label>
                      <Input value={formData.employee_code} onChange={(e) => setFormData({...formData, employee_code: e.target.value})} placeholder="EMP001" required />
                    </div>
                    <div className="space-y-2">
                      <Label>Full Name *</Label>
                      <Input value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Email *</Label>
                      <Input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone *</Label>
                      <Input value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} required />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="work" className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Department *</Label>
                      <Select value={formData.department} onValueChange={(v) => setFormData({...formData, department: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Production">Production</SelectItem>
                          <SelectItem value="Sales">Sales</SelectItem>
                          <SelectItem value="Purchase">Purchase</SelectItem>
                          <SelectItem value="HR/Admin">HR/Admin</SelectItem>
                          <SelectItem value="Accounts">Accounts</SelectItem>
                          <SelectItem value="Quality">Quality</SelectItem>
                          <SelectItem value="R&D">R&D</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Designation *</Label>
                      <Input value={formData.designation} onChange={(e) => setFormData({...formData, designation: e.target.value})} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Location *</Label>
                      <Select value={formData.location} onValueChange={(v) => setFormData({...formData, location: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="BWD">BWD (Bhiwandi)</SelectItem>
                          <SelectItem value="SGM">SGM (Silvassa)</SelectItem>
                          <SelectItem value="HO">Head Office</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Date of Joining *</Label>
                      <Input type="date" value={formData.date_of_joining} onChange={(e) => setFormData({...formData, date_of_joining: e.target.value})} required />
                    </div>
                    <div className="space-y-2">
                      <Label>Shift Timing</Label>
                      <Select value={formData.shift_timing} onValueChange={(v) => setFormData({...formData, shift_timing: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="General">General (9-6)</SelectItem>
                          <SelectItem value="Morning">Morning (6-2)</SelectItem>
                          <SelectItem value="Evening">Evening (2-10)</SelectItem>
                          <SelectItem value="Night">Night (10-6)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="salary" className="space-y-4 mt-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label>Basic Salary (₹) *</Label>
                      <Input type="number" value={formData.basic_salary} onChange={(e) => setFormData({...formData, basic_salary: e.target.value})} required />
                    </div>
                    <div className="space-y-2">
                      <Label>HRA (₹)</Label>
                      <Input type="number" value={formData.hra} onChange={(e) => setFormData({...formData, hra: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>PF (%)</Label>
                      <Input type="number" step="0.01" value={formData.pf} onChange={(e) => setFormData({...formData, pf: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>ESI (%)</Label>
                      <Input type="number" step="0.01" value={formData.esi} onChange={(e) => setFormData({...formData, esi: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>PT (₹)</Label>
                      <Input type="number" value={formData.pt} onChange={(e) => setFormData({...formData, pt: e.target.value})} />
                    </div>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Gross Salary:</strong> ₹{((parseFloat(formData.basic_salary) || 0) + (parseFloat(formData.hra) || 0)).toLocaleString('en-IN')}
                    </p>
                  </div>
                </TabsContent>
                
                {/* Dynamic Custom Fields Tab */}
                {customFields.length > 0 && (
                  <TabsContent value="custom" className="space-y-4 mt-4">
                    <DynamicFormFields
                      fields={customFields}
                      values={customFieldValues}
                      onChange={handleCustomFieldChange}
                      columns={2}
                      showSections={true}
                    />
                  </TabsContent>
                )}
              </Tabs>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setOpen(false); setEditingEmployee(null); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">{editingEmployee ? 'Update' : 'Create'}</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input placeholder="Search employees..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" />
        </div>
        <Select value={filters.department} onValueChange={(v) => setFilters({...filters, department: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Department" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            <SelectItem value="Production">Production</SelectItem>
            <SelectItem value="Sales">Sales</SelectItem>
            <SelectItem value="Purchase">Purchase</SelectItem>
            <SelectItem value="HR/Admin">HR/Admin</SelectItem>
            <SelectItem value="Accounts">Accounts</SelectItem>
          </SelectContent>
        </Select>
        <Select value={filters.location} onValueChange={(v) => setFilters({...filters, location: v})}>
          <SelectTrigger className="w-[130px]"><SelectValue placeholder="Location" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Locations</SelectItem>
            <SelectItem value="BWD">BWD</SelectItem>
            <SelectItem value="SGM">SGM</SelectItem>
            <SelectItem value="HO">Head Office</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Employees Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Code</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Department</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Designation</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Location</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Contact</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Joining</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredEmployees.length === 0 ? (
                  <tr><td colSpan="8" className="px-4 py-12 text-center text-slate-500">No employees found</td></tr>
                ) : (
                  filteredEmployees.map((emp) => (
                    <tr key={emp.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-sm font-semibold text-slate-900">{emp.employee_code}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-slate-900">{emp.name}</div>
                        <div className="text-sm text-slate-500">{emp.email}</div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge className={deptColors[emp.department] || 'bg-slate-100 text-slate-800'}>{emp.department}</Badge>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-600">{emp.designation}</td>
                      <td className="px-4 py-3"><Badge variant="outline">{emp.location}</Badge></td>
                      <td className="px-4 py-3 text-sm text-slate-600 font-mono">{emp.phone}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{emp.date_of_joining}</td>
                      <td className="px-4 py-3">
                        <Button variant="ghost" size="sm" onClick={() => handleEdit(emp)}>
                          <Edit className="h-4 w-4" />
                        </Button>
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

// ==================== ATTENDANCE ====================
const AttendanceManagement = () => {
  const [attendance, setAttendance] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [formData, setFormData] = useState({
    employee_id: '', date: new Date().toISOString().split('T')[0],
    check_in: '09:00', check_out: '18:00', status: 'present', hours_worked: '9'
  });

  useEffect(() => { fetchData(); }, [selectedDate]);

  const fetchData = async () => {
    try {
      const [attendanceRes, employeesRes] = await Promise.all([
        api.get(`/hrms/attendance?date=${selectedDate}`),
        api.get('/hrms/employees')
      ]);
      setAttendance(attendanceRes.data);
      setEmployees(employeesRes.data);
    } catch (error) {
      toast.error('Failed to load attendance');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/hrms/attendance', {
        ...formData,
        hours_worked: parseFloat(formData.hours_worked) || 0
      });
      toast.success('Attendance marked');
      setOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to mark attendance');
    }
  };

  const getEmployeeName = (empId) => {
    const emp = employees.find(e => e.id === empId);
    return emp ? emp.name : 'Unknown';
  };

  const statusColors = {
    present: 'bg-green-100 text-green-800',
    absent: 'bg-red-100 text-red-800',
    leave: 'bg-yellow-100 text-yellow-800',
    half_day: 'bg-orange-100 text-orange-800'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="attendance-management">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Attendance</h2>
          <p className="text-slate-600 mt-1 font-inter">Daily attendance tracking</p>
        </div>
        <div className="flex gap-2">
          <Input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} className="w-[180px]" />
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button className="bg-accent hover:bg-accent/90">
                <Plus className="h-4 w-4 mr-2" />Mark Attendance
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Mark Attendance</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label>Employee *</Label>
                  <Select value={formData.employee_id} onValueChange={(v) => setFormData({...formData, employee_id: v})}>
                    <SelectTrigger><SelectValue placeholder="Select employee" /></SelectTrigger>
                    <SelectContent>
                      {employees.map(emp => (
                        <SelectItem key={emp.id} value={emp.id}>{emp.employee_code} - {emp.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Date *</Label>
                    <Input type="date" value={formData.date} onChange={(e) => setFormData({...formData, date: e.target.value})} required />
                  </div>
                  <div className="space-y-2">
                    <Label>Status *</Label>
                    <Select value={formData.status} onValueChange={(v) => setFormData({...formData, status: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="present">Present</SelectItem>
                        <SelectItem value="absent">Absent</SelectItem>
                        <SelectItem value="leave">Leave</SelectItem>
                        <SelectItem value="half_day">Half Day</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Check In</Label>
                    <Input type="time" value={formData.check_in} onChange={(e) => setFormData({...formData, check_in: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Check Out</Label>
                    <Input type="time" value={formData.check_out} onChange={(e) => setFormData({...formData, check_out: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Hours Worked</Label>
                    <Input type="number" step="0.5" value={formData.hours_worked} onChange={(e) => setFormData({...formData, hours_worked: e.target.value})} />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                  <Button type="submit" className="bg-accent hover:bg-accent/90">Save</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="border-slate-200">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{attendance.filter(a => a.status === 'present').length}</div>
            <p className="text-sm text-slate-500">Present</p>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-red-600">{attendance.filter(a => a.status === 'absent').length}</div>
            <p className="text-sm text-slate-500">Absent</p>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-yellow-600">{attendance.filter(a => a.status === 'leave').length}</div>
            <p className="text-sm text-slate-500">On Leave</p>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-orange-600">{attendance.filter(a => a.status === 'half_day').length}</div>
            <p className="text-sm text-slate-500">Half Day</p>
          </CardContent>
        </Card>
      </div>

      {/* Attendance Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Employee</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Check In</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Check Out</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Hours</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {attendance.length === 0 ? (
                  <tr><td colSpan="6" className="px-4 py-12 text-center text-slate-500">No attendance records for this date</td></tr>
                ) : (
                  attendance.map((att) => (
                    <tr key={att.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-semibold text-slate-900">{getEmployeeName(att.employee_id)}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{att.date}</td>
                      <td className="px-4 py-3 text-sm font-mono text-slate-600">{att.check_in || '-'}</td>
                      <td className="px-4 py-3 text-sm font-mono text-slate-600">{att.check_out || '-'}</td>
                      <td className="px-4 py-3 text-sm font-mono text-slate-900">{att.hours_worked || 0}h</td>
                      <td className="px-4 py-3">
                        <Badge className={statusColors[att.status]}>{att.status}</Badge>
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

// ==================== LEAVE MANAGEMENT ====================
const LeaveManagement = () => {
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState({ status: 'all' });
  const [formData, setFormData] = useState({
    employee_id: '', leave_type: 'PL', from_date: '', to_date: '', reason: ''
  });

  useEffect(() => { fetchData(); }, [filters]);

  const fetchData = async () => {
    try {
      let url = '/hrms/leave-requests?';
      if (filters.status !== 'all') url += `status=${filters.status}&`;
      
      const [leavesRes, employeesRes] = await Promise.all([
        api.get(url),
        api.get('/hrms/employees')
      ]);
      setLeaveRequests(leavesRes.data);
      setEmployees(employeesRes.data);
    } catch (error) {
      toast.error('Failed to load leave requests');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post('/hrms/leave-requests', formData);
      toast.success('Leave request submitted');
      setOpen(false);
      fetchData();
      setFormData({ employee_id: '', leave_type: 'PL', from_date: '', to_date: '', reason: '' });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit leave request');
    }
  };

  const handleApprove = async (leaveId) => {
    try {
      await api.put(`/hrms/leave-requests/${leaveId}/approve`);
      toast.success('Leave approved');
      fetchData();
    } catch (error) {
      toast.error('Failed to approve leave');
    }
  };

  const handleReject = async (leaveId) => {
    const reason = window.prompt('Enter rejection reason:');
    if (!reason) return;
    try {
      await api.put(`/hrms/leave-requests/${leaveId}/reject?reason=${encodeURIComponent(reason)}`);
      toast.success('Leave rejected');
      fetchData();
    } catch (error) {
      toast.error('Failed to reject leave');
    }
  };

  const getEmployeeName = (empId) => {
    const emp = employees.find(e => e.id === empId);
    return emp ? emp.name : 'Unknown';
  };

  const statusColors = {
    pending: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800'
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="leave-management">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Leave Management</h2>
          <p className="text-slate-600 mt-1 font-inter">{leaveRequests.length} requests</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button className="bg-accent hover:bg-accent/90">
              <Plus className="h-4 w-4 mr-2" />Apply Leave
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Apply for Leave</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label>Employee *</Label>
                <Select value={formData.employee_id} onValueChange={(v) => setFormData({...formData, employee_id: v})}>
                  <SelectTrigger><SelectValue placeholder="Select employee" /></SelectTrigger>
                  <SelectContent>
                    {employees.map(emp => (
                      <SelectItem key={emp.id} value={emp.id}>{emp.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Leave Type *</Label>
                <Select value={formData.leave_type} onValueChange={(v) => setFormData({...formData, leave_type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PL">Privilege Leave (PL)</SelectItem>
                    <SelectItem value="CL">Casual Leave (CL)</SelectItem>
                    <SelectItem value="SL">Sick Leave (SL)</SelectItem>
                    <SelectItem value="LWP">Leave Without Pay</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>From Date *</Label>
                  <Input type="date" value={formData.from_date} onChange={(e) => setFormData({...formData, from_date: e.target.value})} required />
                </div>
                <div className="space-y-2">
                  <Label>To Date *</Label>
                  <Input type="date" value={formData.to_date} onChange={(e) => setFormData({...formData, to_date: e.target.value})} required />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Reason *</Label>
                <Textarea value={formData.reason} onChange={(e) => setFormData({...formData, reason: e.target.value})} required />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                <Button type="submit" className="bg-accent hover:bg-accent/90">Submit</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <Select value={filters.status} onValueChange={(v) => setFilters({...filters, status: v})}>
          <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Leave Requests Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Employee</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">From</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">To</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Days</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Reason</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {leaveRequests.length === 0 ? (
                  <tr><td colSpan="8" className="px-4 py-12 text-center text-slate-500">No leave requests</td></tr>
                ) : (
                  leaveRequests.map((leave) => (
                    <tr key={leave.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-semibold text-slate-900">{getEmployeeName(leave.employee_id)}</td>
                      <td className="px-4 py-3"><Badge variant="outline">{leave.leave_type}</Badge></td>
                      <td className="px-4 py-3 text-sm text-slate-600">{leave.from_date}</td>
                      <td className="px-4 py-3 text-sm text-slate-600">{leave.to_date}</td>
                      <td className="px-4 py-3 text-sm font-semibold text-slate-900">{leave.days}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 max-w-[200px] truncate">{leave.reason}</td>
                      <td className="px-4 py-3"><Badge className={statusColors[leave.status]}>{leave.status}</Badge></td>
                      <td className="px-4 py-3">
                        {leave.status === 'pending' && (
                          <div className="flex gap-1">
                            <Button variant="outline" size="sm" onClick={() => handleApprove(leave.id)} className="text-green-600">
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                            <Button variant="outline" size="sm" onClick={() => handleReject(leave.id)} className="text-red-600">
                              <XCircle className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
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

// ==================== PAYROLL ====================
const PayrollManagement = () => {
  const [payrollRecords, setPayrollRecords] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(String(new Date().getMonth() + 1).padStart(2, '0'));
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [formData, setFormData] = useState({
    employee_id: '', month: '', year: new Date().getFullYear(),
    days_present: '26', days_absent: '0', overtime_hours: '0'
  });

  useEffect(() => { fetchData(); }, [selectedMonth, selectedYear]);

  const fetchData = async () => {
    try {
      const [payrollRes, employeesRes] = await Promise.all([
        api.get(`/hrms/payroll?month=${selectedMonth}&year=${selectedYear}`),
        api.get('/hrms/employees')
      ]);
      setPayrollRecords(payrollRes.data);
      setEmployees(employeesRes.data);
    } catch (error) {
      toast.error('Failed to load payroll data');
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePayroll = async (e) => {
    e.preventDefault();
    try {
      const result = await api.post('/hrms/payroll', {
        ...formData,
        days_present: parseFloat(formData.days_present),
        days_absent: parseFloat(formData.days_absent),
        overtime_hours: parseFloat(formData.overtime_hours)
      });
      toast.success(`Payroll generated. Net Salary: ₹${result.data.net_salary.toLocaleString('en-IN')}`);
      setOpen(false);
      fetchData();
    } catch (error) {
      const msg = error.response?.data?.detail;
      if (msg && msg.includes('Approval required')) {
        toast.error('Approval required. Please approve in Approvals Inbox, then generate again.');
        return;
      }
      toast.error(msg || 'Failed to generate payroll');
    }
  };

  const getEmployeeName = (empId) => {
    const emp = employees.find(e => e.id === empId);
    return emp ? emp.name : 'Unknown';
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="payroll-management">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">Payroll</h2>
          <p className="text-slate-600 mt-1 font-inter">Monthly salary processing</p>
        </div>
        <div className="flex gap-2">
          <Select value={selectedMonth} onValueChange={setSelectedMonth}>
            <SelectTrigger className="w-[120px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              {[...Array(12)].map((_, i) => (
                <SelectItem key={i} value={String(i + 1).padStart(2, '0')}>
                  {new Date(2000, i).toLocaleString('default', { month: 'long' })}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={String(selectedYear)} onValueChange={(v) => setSelectedYear(parseInt(v))}>
            <SelectTrigger className="w-[100px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              {[2024, 2025, 2026].map(y => (
                <SelectItem key={y} value={String(y)}>{y}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button className="bg-accent hover:bg-accent/90">
                <Plus className="h-4 w-4 mr-2" />Generate Payroll
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Generate Payroll</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleGeneratePayroll} className="space-y-4">
                <div className="space-y-2">
                  <Label>Employee *</Label>
                  <Select value={formData.employee_id} onValueChange={(v) => setFormData({...formData, employee_id: v})}>
                    <SelectTrigger><SelectValue placeholder="Select employee" /></SelectTrigger>
                    <SelectContent>
                      {employees.map(emp => (
                        <SelectItem key={emp.id} value={emp.id}>{emp.employee_code} - {emp.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Month *</Label>
                    <Select value={formData.month} onValueChange={(v) => setFormData({...formData, month: v})}>
                      <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                      <SelectContent>
                        {[...Array(12)].map((_, i) => (
                          <SelectItem key={i} value={String(i + 1).padStart(2, '0')}>
                            {new Date(2000, i).toLocaleString('default', { month: 'long' })}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Year *</Label>
                    <Input type="number" value={formData.year} onChange={(e) => setFormData({...formData, year: parseInt(e.target.value)})} />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Days Present</Label>
                    <Input type="number" value={formData.days_present} onChange={(e) => setFormData({...formData, days_present: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Days Absent</Label>
                    <Input type="number" value={formData.days_absent} onChange={(e) => setFormData({...formData, days_absent: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>OT Hours</Label>
                    <Input type="number" value={formData.overtime_hours} onChange={(e) => setFormData({...formData, overtime_hours: e.target.value})} />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
                  <Button type="submit" className="bg-accent hover:bg-accent/90">Generate</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <p className="text-sm text-slate-500">Total Gross</p>
            <p className="text-2xl font-bold text-slate-900 font-mono">
              ₹{payrollRecords.reduce((sum, p) => sum + (p.gross_salary || 0), 0).toLocaleString('en-IN')}
            </p>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <p className="text-sm text-slate-500">Total Deductions</p>
            <p className="text-2xl font-bold text-red-600 font-mono">
              ₹{payrollRecords.reduce((sum, p) => sum + (p.total_deductions || 0), 0).toLocaleString('en-IN')}
            </p>
          </CardContent>
        </Card>
        <Card className="border-slate-200">
          <CardContent className="p-4">
            <p className="text-sm text-slate-500">Total Net Payable</p>
            <p className="text-2xl font-bold text-green-600 font-mono">
              ₹{payrollRecords.reduce((sum, p) => sum + (p.net_salary || 0), 0).toLocaleString('en-IN')}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Payroll Table */}
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Employee</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Days</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Basic</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">HRA</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Gross</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">PF</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">ESI</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">PT</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Net</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {payrollRecords.length === 0 ? (
                  <tr><td colSpan="9" className="px-4 py-12 text-center text-slate-500">No payroll records for this period</td></tr>
                ) : (
                  payrollRecords.map((payroll) => (
                    <tr key={payroll.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-semibold text-slate-900">{getEmployeeName(payroll.employee_id)}</td>
                      <td className="px-4 py-3 text-right font-mono text-slate-600">{payroll.days_present}</td>
                      <td className="px-4 py-3 text-right font-mono text-slate-600">₹{(payroll.earned_basic || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono text-slate-600">₹{(payroll.earned_hra || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono text-slate-900">₹{(payroll.gross_salary || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono text-red-600">₹{(payroll.pf_deduction || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono text-red-600">₹{(payroll.esi_deduction || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono text-red-600">₹{(payroll.pt_deduction || 0).toLocaleString('en-IN')}</td>
                      <td className="px-4 py-3 text-right font-mono font-semibold text-green-600">₹{(payroll.net_salary || 0).toLocaleString('en-IN')}</td>
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

// ==================== REPORTS ====================
const HRMSReports = () => {
  const [reportData, setReportData] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchData(); }, [selectedMonth]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/hrms/reports/attendance-summary?month=${selectedMonth}`);
      setReportData(res.data);
    } catch (error) {
      toast.error('Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div></div>;

  return (
    <div className="space-y-6" data-testid="hrms-reports">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 font-manrope">HR Reports</h2>
          <p className="text-slate-600 mt-1 font-inter">Attendance & payroll analytics</p>
        </div>
        <div className="flex gap-2">
          <Input type="month" value={selectedMonth} onChange={(e) => setSelectedMonth(e.target.value)} className="w-[180px]" />
          <Button variant="outline" size="sm"><Download className="h-4 w-4 mr-2" />Export</Button>
        </div>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle>Attendance Summary - {selectedMonth}</CardTitle>
        </CardHeader>
        <CardContent>
          {reportData && Object.keys(reportData).length > 0 ? (
            <div className="space-y-4">
              {Object.entries(reportData).map(([empId, data]) => (
                <div key={empId} className="p-4 border rounded-lg">
                  <div className="grid grid-cols-4 gap-4 text-center">
                    <div>
                      <p className="text-2xl font-bold text-green-600">{data.present}</p>
                      <p className="text-sm text-slate-500">Present</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-red-600">{data.absent}</p>
                      <p className="text-sm text-slate-500">Absent</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-yellow-600">{data.leave}</p>
                      <p className="text-sm text-slate-500">Leave</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-blue-600">{data.total_hours}h</p>
                      <p className="text-sm text-slate-500">Total Hours</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-slate-500 py-8">No attendance data for this period</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// ==================== MAIN HRMS COMPONENT ====================
const HRMS = () => {
  return (
    <Routes>
      <Route index element={<HRMSDashboard />} />
      <Route path="employees" element={<EmployeesList />} />
      <Route path="attendance" element={<AttendanceManagement />} />
      <Route path="leave" element={<LeaveManagement />} />
      <Route path="payroll" element={<PayrollManagement />} />
      <Route path="reports" element={<HRMSReports />} />
    </Routes>
  );
};

export default HRMS;
