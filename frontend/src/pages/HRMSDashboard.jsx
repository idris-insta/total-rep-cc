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
  Clock, Calendar, Users, CheckCircle, XCircle, AlertTriangle,
  Coffee, LogIn, LogOut, RefreshCw, Plus, FileText, Calculator,
  Briefcase, UserCheck, Timer
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const HRMSDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [employees, setEmployees] = useState([]);
  const [attendance, setAttendance] = useState([]);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [leaveApplications, setLeaveApplications] = useState([]);
  const [loans, setLoans] = useState([]);
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));
  const [leaveDialogOpen, setLeaveDialogOpen] = useState(false);
  const [attendanceDialogOpen, setAttendanceDialogOpen] = useState(false);
  const [leaveForm, setLeaveForm] = useState({
    employee_id: '', leave_type_id: '', from_date: '', to_date: '', reason: '', half_day: false
  });
  const [attendanceForm, setAttendanceForm] = useState({
    employee_id: '', date: new Date().toISOString().slice(0, 10), check_in: '09:00', check_out: '18:00', status: 'present'
  });

  useEffect(() => {
    fetchData();
  }, [selectedMonth]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [empRes, attRes, leaveTypesRes, leaveAppsRes, loansRes] = await Promise.all([
        api.get('/hrms/employees').catch(() => ({ data: [] })),
        api.get(`/hrms-enhanced/attendance?from_date=${selectedMonth}-01&to_date=${selectedMonth}-31`).catch(() => ({ data: [] })),
        api.get('/hrms-enhanced/leave-types').catch(() => ({ data: [] })),
        api.get('/hrms-enhanced/leave-applications').catch(() => ({ data: [] })),
        api.get('/hrms-enhanced/loans').catch(() => ({ data: [] }))
      ]);
      setEmployees(empRes.data || []);
      setAttendance(attRes.data || []);
      setLeaveTypes(leaveTypesRes.data || []);
      setLeaveApplications(leaveAppsRes.data || []);
      setLoans(loansRes.data || []);
    } catch (error) {
      toast.error('Failed to load HRMS data');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckIn = async (employeeId) => {
    try {
      const res = await api.post(`/hrms-enhanced/attendance/check-in?employee_id=${employeeId}`);
      toast.success(res.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Check-in failed');
    }
  };

  const handleCheckOut = async (employeeId) => {
    try {
      const res = await api.post(`/hrms-enhanced/attendance/check-out?employee_id=${employeeId}`);
      toast.success(res.data.message);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Check-out failed');
    }
  };

  const handleMarkAttendance = async (e) => {
    e.preventDefault();
    try {
      await api.post('/hrms-enhanced/attendance', attendanceForm);
      toast.success('Attendance marked');
      setAttendanceDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to mark attendance');
    }
  };

  const handleApplyLeave = async (e) => {
    e.preventDefault();
    try {
      await api.post('/hrms-enhanced/leave-applications', leaveForm);
      toast.success('Leave application submitted');
      setLeaveDialogOpen(false);
      setLeaveForm({ employee_id: '', leave_type_id: '', from_date: '', to_date: '', reason: '', half_day: false });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to apply leave');
    }
  };

  const handleApproveLeave = async (appId) => {
    try {
      await api.put(`/hrms-enhanced/leave-applications/${appId}/approve`);
      toast.success('Leave approved');
      fetchData();
    } catch (error) {
      toast.error('Failed to approve leave');
    }
  };

  const handleRejectLeave = async (appId) => {
    try {
      await api.put(`/hrms-enhanced/leave-applications/${appId}/reject?reason=Rejected by admin`);
      toast.success('Leave rejected');
      fetchData();
    } catch (error) {
      toast.error('Failed to reject leave');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      present: 'bg-green-100 text-green-800',
      absent: 'bg-red-100 text-red-800',
      late: 'bg-orange-100 text-orange-800',
      half_day: 'bg-yellow-100 text-yellow-800',
      on_leave: 'bg-blue-100 text-blue-800',
      pending: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800'
    };
    return <Badge className={styles[status] || 'bg-gray-100'}>{status?.replace('_', ' ')}</Badge>;
  };

  // Summary stats
  const todayAttendance = attendance.filter(a => a.date === new Date().toISOString().slice(0, 10));
  const presentToday = todayAttendance.filter(a => a.status === 'present' || a.status === 'late').length;
  const pendingLeaves = leaveApplications.filter(l => l.status === 'pending').length;
  const activeLoans = loans.filter(l => l.status === 'active').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin h-12 w-12 border-4 border-accent border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope">HRMS Dashboard</h1>
          <p className="text-slate-600 mt-1">Attendance, Leave & Payroll Management</p>
        </div>
        <div className="flex items-center gap-3">
          <Input
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="w-40"
          />
          <Button onClick={fetchData} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <UserCheck className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Present Today</p>
                <p className="text-2xl font-bold">{presentToday} / {employees.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-yellow-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Calendar className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Pending Leaves</p>
                <p className="text-2xl font-bold">{pendingLeaves}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Briefcase className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Active Loans</p>
                <p className="text-2xl font-bold">{activeLoans}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Total Employees</p>
                <p className="text-2xl font-bold">{employees.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue="attendance" className="space-y-4">
        <TabsList className="grid grid-cols-4 w-full max-w-2xl">
          <TabsTrigger value="attendance" className="gap-2">
            <Clock className="h-4 w-4" />Attendance
          </TabsTrigger>
          <TabsTrigger value="leave" className="gap-2">
            <Calendar className="h-4 w-4" />Leave
          </TabsTrigger>
          <TabsTrigger value="loans" className="gap-2">
            <Briefcase className="h-4 w-4" />Loans
          </TabsTrigger>
          <TabsTrigger value="statutory" className="gap-2">
            <Calculator className="h-4 w-4" />Statutory
          </TabsTrigger>
        </TabsList>

        {/* Attendance Tab */}
        <TabsContent value="attendance">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Attendance Management</CardTitle>
                <Dialog open={attendanceDialogOpen} onOpenChange={setAttendanceDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="bg-accent hover:bg-accent/90">
                      <Plus className="h-4 w-4 mr-2" />Mark Attendance
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Mark Attendance</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleMarkAttendance} className="space-y-4">
                      <div className="space-y-2">
                        <Label>Employee</Label>
                        <Select value={attendanceForm.employee_id} onValueChange={(v) => setAttendanceForm({...attendanceForm, employee_id: v})}>
                          <SelectTrigger><SelectValue placeholder="Select employee" /></SelectTrigger>
                          <SelectContent>
                            {employees.map(emp => (
                              <SelectItem key={emp.id} value={emp.id}>{emp.first_name} {emp.last_name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Date</Label>
                          <Input type="date" value={attendanceForm.date} onChange={(e) => setAttendanceForm({...attendanceForm, date: e.target.value})} />
                        </div>
                        <div className="space-y-2">
                          <Label>Status</Label>
                          <Select value={attendanceForm.status} onValueChange={(v) => setAttendanceForm({...attendanceForm, status: v})}>
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="present">Present</SelectItem>
                              <SelectItem value="absent">Absent</SelectItem>
                              <SelectItem value="half_day">Half Day</SelectItem>
                              <SelectItem value="late">Late</SelectItem>
                              <SelectItem value="on_leave">On Leave</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Check In</Label>
                          <Input type="time" value={attendanceForm.check_in} onChange={(e) => setAttendanceForm({...attendanceForm, check_in: e.target.value})} />
                        </div>
                        <div className="space-y-2">
                          <Label>Check Out</Label>
                          <Input type="time" value={attendanceForm.check_out} onChange={(e) => setAttendanceForm({...attendanceForm, check_out: e.target.value})} />
                        </div>
                      </div>
                      <DialogFooter>
                        <Button type="submit" className="bg-accent">Save Attendance</Button>
                      </DialogFooter>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {/* Quick Check-in/out */}
              <div className="mb-6 p-4 bg-slate-50 rounded-lg">
                <h4 className="font-semibold mb-3">Quick Actions</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {employees.slice(0, 4).map(emp => {
                    const todayAtt = todayAttendance.find(a => a.employee_id === emp.id);
                    return (
                      <div key={emp.id} className="p-3 bg-white rounded-lg border">
                        <p className="font-medium text-sm">{emp.first_name} {emp.last_name}</p>
                        <div className="flex gap-2 mt-2">
                          {!todayAtt?.check_in ? (
                            <Button size="sm" variant="outline" onClick={() => handleCheckIn(emp.id)} className="flex-1">
                              <LogIn className="h-3 w-3 mr-1" />In
                            </Button>
                          ) : !todayAtt?.check_out ? (
                            <Button size="sm" variant="outline" onClick={() => handleCheckOut(emp.id)} className="flex-1">
                              <LogOut className="h-3 w-3 mr-1" />Out
                            </Button>
                          ) : (
                            <span className="text-xs text-green-600 flex items-center"><CheckCircle className="h-3 w-3 mr-1" />Done</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Attendance List */}
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="px-4 py-3 text-left">Employee</th>
                      <th className="px-4 py-3 text-left">Date</th>
                      <th className="px-4 py-3 text-left">Check In</th>
                      <th className="px-4 py-3 text-left">Check Out</th>
                      <th className="px-4 py-3 text-left">Hours</th>
                      <th className="px-4 py-3 text-left">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attendance.slice(0, 20).map((att, idx) => (
                      <tr key={idx} className="border-t">
                        <td className="px-4 py-3 font-medium">{att.employee_name}</td>
                        <td className="px-4 py-3">{att.date}</td>
                        <td className="px-4 py-3">{att.check_in || '-'}</td>
                        <td className="px-4 py-3">{att.check_out || '-'}</td>
                        <td className="px-4 py-3">{att.working_hours?.toFixed(1) || '-'}</td>
                        <td className="px-4 py-3">{getStatusBadge(att.status)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Leave Tab */}
        <TabsContent value="leave">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Leave Management</CardTitle>
                <Dialog open={leaveDialogOpen} onOpenChange={setLeaveDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="bg-accent hover:bg-accent/90">
                      <Plus className="h-4 w-4 mr-2" />Apply Leave
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Apply for Leave</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleApplyLeave} className="space-y-4">
                      <div className="space-y-2">
                        <Label>Employee</Label>
                        <Select value={leaveForm.employee_id} onValueChange={(v) => setLeaveForm({...leaveForm, employee_id: v})}>
                          <SelectTrigger><SelectValue placeholder="Select employee" /></SelectTrigger>
                          <SelectContent>
                            {employees.map(emp => (
                              <SelectItem key={emp.id} value={emp.id}>{emp.first_name} {emp.last_name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Leave Type</Label>
                        <Select value={leaveForm.leave_type_id} onValueChange={(v) => setLeaveForm({...leaveForm, leave_type_id: v})}>
                          <SelectTrigger><SelectValue placeholder="Select leave type" /></SelectTrigger>
                          <SelectContent>
                            {leaveTypes.map(lt => (
                              <SelectItem key={lt.id} value={lt.id}>{lt.name} ({lt.code})</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>From Date</Label>
                          <Input type="date" value={leaveForm.from_date} onChange={(e) => setLeaveForm({...leaveForm, from_date: e.target.value})} required />
                        </div>
                        <div className="space-y-2">
                          <Label>To Date</Label>
                          <Input type="date" value={leaveForm.to_date} onChange={(e) => setLeaveForm({...leaveForm, to_date: e.target.value})} required />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Reason</Label>
                        <Textarea value={leaveForm.reason} onChange={(e) => setLeaveForm({...leaveForm, reason: e.target.value})} required />
                      </div>
                      <DialogFooter>
                        <Button type="submit" className="bg-accent">Submit Application</Button>
                      </DialogFooter>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {/* Leave Types Summary */}
              <div className="grid grid-cols-3 md:grid-cols-6 gap-3 mb-6">
                {leaveTypes.map(lt => (
                  <div key={lt.id} className="p-3 bg-slate-50 rounded-lg text-center">
                    <p className="text-xs text-slate-500">{lt.code}</p>
                    <p className="font-semibold text-lg">{lt.annual_quota}</p>
                    <p className="text-xs text-slate-600">{lt.name}</p>
                  </div>
                ))}
              </div>

              {/* Leave Applications */}
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="px-4 py-3 text-left">Employee</th>
                      <th className="px-4 py-3 text-left">Type</th>
                      <th className="px-4 py-3 text-left">From</th>
                      <th className="px-4 py-3 text-left">To</th>
                      <th className="px-4 py-3 text-left">Days</th>
                      <th className="px-4 py-3 text-left">Status</th>
                      <th className="px-4 py-3 text-left">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaveApplications.map((app, idx) => (
                      <tr key={idx} className="border-t">
                        <td className="px-4 py-3 font-medium">{app.employee_name}</td>
                        <td className="px-4 py-3">{app.leave_type_name}</td>
                        <td className="px-4 py-3">{app.from_date}</td>
                        <td className="px-4 py-3">{app.to_date}</td>
                        <td className="px-4 py-3">{app.days}</td>
                        <td className="px-4 py-3">{getStatusBadge(app.status)}</td>
                        <td className="px-4 py-3">
                          {app.status === 'pending' && (
                            <div className="flex gap-1">
                              <Button size="sm" variant="ghost" onClick={() => handleApproveLeave(app.id)} className="text-green-600 h-7 px-2">
                                <CheckCircle className="h-4 w-4" />
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => handleRejectLeave(app.id)} className="text-red-600 h-7 px-2">
                                <XCircle className="h-4 w-4" />
                              </Button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Loans Tab */}
        <TabsContent value="loans">
          <Card>
            <CardHeader>
              <CardTitle>Loan & Advance Management</CardTitle>
            </CardHeader>
            <CardContent>
              {loans.length > 0 ? (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-100">
                      <tr>
                        <th className="px-4 py-3 text-left">Employee</th>
                        <th className="px-4 py-3 text-left">Type</th>
                        <th className="px-4 py-3 text-right">Amount</th>
                        <th className="px-4 py-3 text-right">EMI</th>
                        <th className="px-4 py-3 text-right">Outstanding</th>
                        <th className="px-4 py-3 text-left">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loans.map((loan, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-4 py-3 font-medium">{loan.employee_name}</td>
                          <td className="px-4 py-3">{loan.loan_type?.replace('_', ' ')}</td>
                          <td className="px-4 py-3 text-right">₹{loan.amount?.toLocaleString('en-IN')}</td>
                          <td className="px-4 py-3 text-right">₹{loan.emi_amount?.toLocaleString('en-IN')}</td>
                          <td className="px-4 py-3 text-right">₹{loan.outstanding_amount?.toLocaleString('en-IN')}</td>
                          <td className="px-4 py-3">{getStatusBadge(loan.status)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <Briefcase className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No active loans</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Statutory Tab */}
        <TabsContent value="statutory">
          <Card>
            <CardHeader>
              <CardTitle>Statutory Compliance (PF/ESI/PT)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-6">
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-3">Provident Fund (PF)</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span>Employee Contribution:</span><span className="font-semibold">12%</span></div>
                    <div className="flex justify-between"><span>Employer Contribution:</span><span className="font-semibold">12%</span></div>
                    <div className="flex justify-between"><span>Wage Ceiling:</span><span className="font-semibold">₹15,000</span></div>
                  </div>
                </div>
                <div className="p-4 bg-green-50 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-3">ESI</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span>Employee Contribution:</span><span className="font-semibold">0.75%</span></div>
                    <div className="flex justify-between"><span>Employer Contribution:</span><span className="font-semibold">3.25%</span></div>
                    <div className="flex justify-between"><span>Wage Ceiling:</span><span className="font-semibold">₹21,000</span></div>
                  </div>
                </div>
                <div className="p-4 bg-orange-50 rounded-lg">
                  <h4 className="font-semibold text-orange-800 mb-3">Professional Tax (PT)</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span>Up to ₹10,000:</span><span className="font-semibold">₹0</span></div>
                    <div className="flex justify-between"><span>₹10,001 - ₹15,000:</span><span className="font-semibold">₹150</span></div>
                    <div className="flex justify-between"><span>Above ₹15,000:</span><span className="font-semibold">₹200</span></div>
                  </div>
                </div>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <h4 className="font-semibold text-purple-800 mb-3">Labour Welfare Fund (LWF)</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span>Employee Contribution:</span><span className="font-semibold">₹20</span></div>
                    <div className="flex justify-between"><span>Employer Contribution:</span><span className="font-semibold">₹40</span></div>
                    <div className="flex justify-between"><span>Frequency:</span><span className="font-semibold">Half-yearly</span></div>
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

export default HRMSDashboard;
