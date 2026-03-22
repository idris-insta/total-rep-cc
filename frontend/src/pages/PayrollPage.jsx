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
  DollarSign, Users, Calculator, FileText, Download, CheckCircle, 
  Clock, RefreshCw, Calendar, Plus, Eye, Printer
} from 'lucide-react';

const API_URL = import.meta.env.VITE_BACKEND_URL;

const PayrollPage = () => {
  const [payrolls, setPayrolls] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showProcessPayroll, setShowProcessPayroll] = useState(false);
  const [showPayslip, setShowPayslip] = useState(false);
  const [selectedPayroll, setSelectedPayroll] = useState(null);
  const [payslipData, setPayslipData] = useState(null);
  const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().slice(0, 7));

  const token = localStorage.getItem('token');
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const [newPayroll, setNewPayroll] = useState({
    payroll_month: new Date().toISOString().slice(0, 7),
    employee_id: '',
    working_days: 26,
    present_days: 26,
    leaves_taken: 0,
    overtime_hours: 0,
    overtime_rate: 0,
    incentive_amount: 0,
    bonus_amount: 0,
    advance_deduction: 0,
    loan_deduction: 0,
    other_deductions: 0,
    remarks: ''
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [payrollRes, empRes] = await Promise.all([
        fetch(`${API_URL}/api/payroll/?payroll_month=${selectedMonth}`, { headers }),
        fetch(`${API_URL}/api/hrms/employees`, { headers })
      ]);

      if (payrollRes.ok) setPayrolls(await payrollRes.json());
      if (empRes.ok) setEmployees(await empRes.json());
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [selectedMonth]);

  const handleProcessPayroll = async () => {
    try {
      const response = await fetch(`${API_URL}/api/payroll/process`, {
        method: 'POST',
        headers,
        body: JSON.stringify(newPayroll)
      });

      if (response.ok) {
        setShowProcessPayroll(false);
        fetchData();
      } else {
        const error = await response.json();
        alert(error.detail || 'Error processing payroll');
      }
    } catch (error) {
      console.error('Error processing payroll:', error);
    }
  };

  const handleViewPayslip = async (payrollId) => {
    try {
      const response = await fetch(`${API_URL}/api/payroll/${payrollId}/payslip`, { headers });
      if (response.ok) {
        const data = await response.json();
        setPayslipData(data);
        setShowPayslip(true);
      }
    } catch (error) {
      console.error('Error fetching payslip:', error);
    }
  };

  const handleApprove = async (payrollId) => {
    try {
      const response = await fetch(`${API_URL}/api/payroll/${payrollId}/approve`, {
        method: 'PUT',
        headers
      });
      if (response.ok) {
        fetchData();
      } else {
        const error = await response.json();
        alert(error.detail || 'Error approving payroll');
      }
    } catch (error) {
      console.error('Error approving payroll:', error);
    }
  };

  const handleMarkPaid = async (payrollId) => {
    try {
      await fetch(`${API_URL}/api/payroll/${payrollId}/mark-paid`, {
        method: 'PUT',
        headers
      });
      fetchData();
    } catch (error) {
      console.error('Error marking payroll as paid:', error);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount || 0);
  };

  const getStatusBadge = (status) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      pending_approval: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      paid: 'bg-green-100 text-green-800'
    };
    return <Badge className={colors[status] || 'bg-gray-100'}>{status?.replace('_', ' ').toUpperCase()}</Badge>;
  };

  const totalGross = payrolls.reduce((sum, p) => sum + (p.gross_salary || 0), 0);
  const totalNet = payrolls.reduce((sum, p) => sum + (p.net_salary || 0), 0);
  const totalDeductions = payrolls.reduce((sum, p) => sum + (p.total_deductions || 0), 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Payroll Management</h1>
          <p className="text-sm text-gray-500">Process and manage employee payroll</p>
        </div>
        <div className="flex gap-2">
          <Input 
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="w-40"
          />
          <Dialog open={showProcessPayroll} onOpenChange={setShowProcessPayroll}>
            <DialogTrigger asChild>
              <Button><Calculator className="h-4 w-4 mr-2" />Process Payroll</Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Process Payroll</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Payroll Month *</Label>
                  <Input 
                    type="month"
                    value={newPayroll.payroll_month}
                    onChange={(e) => setNewPayroll({...newPayroll, payroll_month: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Employee *</Label>
                  <Select 
                    value={newPayroll.employee_id}
                    onValueChange={(v) => setNewPayroll({...newPayroll, employee_id: v})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select employee" />
                    </SelectTrigger>
                    <SelectContent>
                      {employees.map(emp => (
                        <SelectItem key={emp.id} value={emp.id}>
                          {emp.name} ({emp.employee_code || emp.id.slice(0,8)})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Working Days</Label>
                    <Input 
                      type="number"
                      value={newPayroll.working_days}
                      onChange={(e) => setNewPayroll({...newPayroll, working_days: parseInt(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>Present Days</Label>
                    <Input 
                      type="number"
                      value={newPayroll.present_days}
                      onChange={(e) => setNewPayroll({...newPayroll, present_days: parseFloat(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>Leaves Taken</Label>
                    <Input 
                      type="number"
                      value={newPayroll.leaves_taken}
                      onChange={(e) => setNewPayroll({...newPayroll, leaves_taken: parseFloat(e.target.value)})}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Overtime Hours</Label>
                    <Input 
                      type="number"
                      value={newPayroll.overtime_hours}
                      onChange={(e) => setNewPayroll({...newPayroll, overtime_hours: parseFloat(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>OT Rate (per hour)</Label>
                    <Input 
                      type="number"
                      value={newPayroll.overtime_rate}
                      onChange={(e) => setNewPayroll({...newPayroll, overtime_rate: parseFloat(e.target.value)})}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Incentive</Label>
                    <Input 
                      type="number"
                      value={newPayroll.incentive_amount}
                      onChange={(e) => setNewPayroll({...newPayroll, incentive_amount: parseFloat(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>Bonus</Label>
                    <Input 
                      type="number"
                      value={newPayroll.bonus_amount}
                      onChange={(e) => setNewPayroll({...newPayroll, bonus_amount: parseFloat(e.target.value)})}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Advance Deduction</Label>
                    <Input 
                      type="number"
                      value={newPayroll.advance_deduction}
                      onChange={(e) => setNewPayroll({...newPayroll, advance_deduction: parseFloat(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>Loan Deduction</Label>
                    <Input 
                      type="number"
                      value={newPayroll.loan_deduction}
                      onChange={(e) => setNewPayroll({...newPayroll, loan_deduction: parseFloat(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>Other Deductions</Label>
                    <Input 
                      type="number"
                      value={newPayroll.other_deductions}
                      onChange={(e) => setNewPayroll({...newPayroll, other_deductions: parseFloat(e.target.value)})}
                    />
                  </div>
                </div>
                <div>
                  <Label>Remarks</Label>
                  <Input 
                    value={newPayroll.remarks}
                    onChange={(e) => setNewPayroll({...newPayroll, remarks: e.target.value})}
                  />
                </div>
                <Button onClick={handleProcessPayroll} className="w-full">
                  <Calculator className="h-4 w-4 mr-2" />
                  Calculate & Process
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-full">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Employees</p>
              <p className="text-2xl font-bold">{payrolls.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-full">
              <DollarSign className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Gross</p>
              <p className="text-2xl font-bold">{formatCurrency(totalGross)}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-red-100 rounded-full">
              <Calculator className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Deductions</p>
              <p className="text-2xl font-bold">{formatCurrency(totalDeductions)}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-full">
              <FileText className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Net Payable</p>
              <p className="text-2xl font-bold">{formatCurrency(totalNet)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Payroll List */}
      {loading ? (
        <div className="flex justify-center p-8">
          <RefreshCw className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : payrolls.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Calculator className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">No payroll records for {selectedMonth}</p>
            <Button className="mt-4" onClick={() => setShowProcessPayroll(true)}>
              <Plus className="h-4 w-4 mr-2" /> Process First Payroll
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Payroll for {selectedMonth}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left p-3">Employee</th>
                    <th className="text-left p-3">Days</th>
                    <th className="text-right p-3">Gross</th>
                    <th className="text-right p-3">Deductions</th>
                    <th className="text-right p-3">Net</th>
                    <th className="text-center p-3">Status</th>
                    <th className="text-center p-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {payrolls.map(payroll => (
                    <tr key={payroll.id} className="border-b hover:bg-gray-50">
                      <td className="p-3">
                        <p className="font-medium">{payroll.employee_name || 'Unknown'}</p>
                        <p className="text-sm text-gray-500">{payroll.employee_code}</p>
                      </td>
                      <td className="p-3">
                        <p>{payroll.present_days}/{payroll.working_days}</p>
                        <p className="text-sm text-gray-500">LOP: {payroll.lop_days || 0}</p>
                      </td>
                      <td className="p-3 text-right font-medium">{formatCurrency(payroll.gross_salary)}</td>
                      <td className="p-3 text-right text-red-600">{formatCurrency(payroll.total_deductions)}</td>
                      <td className="p-3 text-right font-bold text-green-600">{formatCurrency(payroll.net_salary)}</td>
                      <td className="p-3 text-center">{getStatusBadge(payroll.status)}</td>
                      <td className="p-3">
                        <div className="flex justify-center gap-2">
                          <Button size="sm" variant="outline" onClick={() => handleViewPayslip(payroll.id)}>
                            <Eye className="h-4 w-4" />
                          </Button>
                          {payroll.status === 'draft' && (
                            <Button size="sm" variant="outline" onClick={() => handleApprove(payroll.id)}>
                              <CheckCircle className="h-4 w-4" />
                            </Button>
                          )}
                          {payroll.status === 'approved' && (
                            <Button size="sm" onClick={() => handleMarkPaid(payroll.id)}>
                              Pay
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-100 font-bold">
                  <tr>
                    <td className="p-3" colSpan="2">Total</td>
                    <td className="p-3 text-right">{formatCurrency(totalGross)}</td>
                    <td className="p-3 text-right text-red-600">{formatCurrency(totalDeductions)}</td>
                    <td className="p-3 text-right text-green-600">{formatCurrency(totalNet)}</td>
                    <td colSpan="2"></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Payslip Modal */}
      <Dialog open={showPayslip} onOpenChange={setShowPayslip}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Payslip - {payslipData?.payroll_month}</DialogTitle>
          </DialogHeader>
          {payslipData && (
            <div className="space-y-4">
              {/* Employee Info */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded">
                <div>
                  <p className="text-sm text-gray-500">Employee Name</p>
                  <p className="font-medium">{payslipData.employee?.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Employee Code</p>
                  <p className="font-medium">{payslipData.employee?.code}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Department</p>
                  <p className="font-medium">{payslipData.employee?.department || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Pay Period</p>
                  <p className="font-medium">{payslipData.payroll_month}</p>
                </div>
              </div>

              {/* Attendance */}
              <div className="grid grid-cols-4 gap-4 p-4 border rounded">
                <div className="text-center">
                  <p className="text-sm text-gray-500">Working Days</p>
                  <p className="font-bold">{payslipData.attendance?.working_days}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500">Present Days</p>
                  <p className="font-bold">{payslipData.attendance?.present_days}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500">Leaves</p>
                  <p className="font-bold">{payslipData.attendance?.leaves_taken}</p>
                </div>
                <div className="text-center">
                  <p className="text-sm text-gray-500">LOP Days</p>
                  <p className="font-bold text-red-600">{payslipData.attendance?.lop_days}</p>
                </div>
              </div>

              {/* Earnings & Deductions */}
              <div className="grid grid-cols-2 gap-4">
                <div className="border rounded p-4">
                  <h4 className="font-bold mb-3 text-green-600">Earnings</h4>
                  <div className="space-y-2">
                    {Object.entries(payslipData.earnings || {}).map(([key, value]) => (
                      value > 0 && (
                        <div key={key} className="flex justify-between">
                          <span className="text-gray-600">{key.replace(/_/g, ' ')}</span>
                          <span>{formatCurrency(value)}</span>
                        </div>
                      )
                    ))}
                    <div className="flex justify-between font-bold border-t pt-2">
                      <span>Gross Salary</span>
                      <span className="text-green-600">{formatCurrency(payslipData.gross_salary)}</span>
                    </div>
                  </div>
                </div>

                <div className="border rounded p-4">
                  <h4 className="font-bold mb-3 text-red-600">Deductions</h4>
                  <div className="space-y-2">
                    {Object.entries(payslipData.deductions || {}).map(([key, value]) => (
                      value > 0 && (
                        <div key={key} className="flex justify-between">
                          <span className="text-gray-600">{key.replace(/_/g, ' ')}</span>
                          <span>{formatCurrency(value)}</span>
                        </div>
                      )
                    ))}
                    <div className="flex justify-between font-bold border-t pt-2">
                      <span>Total Deductions</span>
                      <span className="text-red-600">{formatCurrency(payslipData.total_deductions)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Net Salary */}
              <div className="p-4 bg-green-50 rounded text-center">
                <p className="text-sm text-gray-600">Net Salary Payable</p>
                <p className="text-3xl font-bold text-green-600">{formatCurrency(payslipData.net_salary)}</p>
              </div>

              <Button className="w-full" variant="outline">
                <Printer className="h-4 w-4 mr-2" /> Print Payslip
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PayrollPage;
