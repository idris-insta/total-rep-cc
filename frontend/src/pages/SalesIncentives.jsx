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
  Trophy, Target, TrendingUp, DollarSign, Users, Calculator,
  Plus, RefreshCw, Award, Medal, Crown, Star
} from 'lucide-react';

const API_URL = import.meta.env.VITE_BACKEND_URL;

const SalesIncentives = () => {
  const [targets, setTargets] = useState([]);
  const [slabs, setSlabs] = useState([]);
  const [payouts, setPayouts] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewTarget, setShowNewTarget] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState(new Date().toISOString().slice(0, 7));

  const token = localStorage.getItem('token');
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const [newTarget, setNewTarget] = useState({
    employee_id: '',
    target_type: 'monthly',
    period: new Date().toISOString().slice(0, 7),
    target_amount: 0,
    target_quantity: 0,
    product_category: 'all',
    notes: ''
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [targetsRes, slabsRes, payoutsRes, leaderboardRes, empRes] = await Promise.all([
        fetch(`${API_URL}/api/sales-incentives/targets?period=${selectedPeriod}`, { headers }),
        fetch(`${API_URL}/api/sales-incentives/slabs`, { headers }),
        fetch(`${API_URL}/api/sales-incentives/payouts?period=${selectedPeriod}`, { headers }),
        fetch(`${API_URL}/api/sales-incentives/leaderboard?period=${selectedPeriod}`, { headers }),
        fetch(`${API_URL}/api/hrms/employees`, { headers })
      ]);

      if (targetsRes.ok) setTargets(await targetsRes.json());
      if (slabsRes.ok) setSlabs(await slabsRes.json());
      if (payoutsRes.ok) setPayouts(await payoutsRes.json());
      if (leaderboardRes.ok) setLeaderboard(await leaderboardRes.json());
      if (empRes.ok) setEmployees(await empRes.json());
    } catch (error) {
      console.error('Error fetching data:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [selectedPeriod]);

  const handleCreateTarget = async () => {
    try {
      const response = await fetch(`${API_URL}/api/sales-incentives/targets`, {
        method: 'POST',
        headers,
        body: JSON.stringify(newTarget)
      });

      if (response.ok) {
        setShowNewTarget(false);
        fetchData();
      }
    } catch (error) {
      console.error('Error creating target:', error);
    }
  };

  const handleCalculateIncentive = async (targetId) => {
    try {
      const response = await fetch(`${API_URL}/api/sales-incentives/calculate/${targetId}`, {
        method: 'POST',
        headers
      });

      if (response.ok) {
        fetchData();
      }
    } catch (error) {
      console.error('Error calculating incentive:', error);
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
      active: 'bg-blue-100 text-blue-800',
      achieved: 'bg-green-100 text-green-800',
      exceeded: 'bg-purple-100 text-purple-800',
      not_achieved: 'bg-red-100 text-red-800'
    };
    return <Badge className={colors[status] || 'bg-gray-100'}>{status?.replace('_', ' ').toUpperCase()}</Badge>;
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return <Crown className="h-6 w-6 text-yellow-500" />;
    if (rank === 2) return <Medal className="h-6 w-6 text-gray-400" />;
    if (rank === 3) return <Medal className="h-6 w-6 text-amber-600" />;
    return <span className="w-6 h-6 flex items-center justify-center font-bold text-gray-500">{rank}</span>;
  };

  const totalTargetAmount = targets.reduce((sum, t) => sum + (t.target_amount || 0), 0);
  const totalAchieved = targets.reduce((sum, t) => sum + (t.achieved_amount || 0), 0);
  const avgAchievement = targets.length > 0 
    ? targets.reduce((sum, t) => sum + (t.achievement_percent || 0), 0) / targets.length 
    : 0;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Sales Incentives</h1>
          <p className="text-sm text-gray-500">Track targets, achievements, and incentive payouts</p>
        </div>
        <div className="flex gap-2">
          <Input 
            type="month"
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="w-40"
          />
          <Dialog open={showNewTarget} onOpenChange={setShowNewTarget}>
            <DialogTrigger asChild>
              <Button><Plus className="h-4 w-4 mr-2" />Set Target</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Set Sales Target</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Employee *</Label>
                  <Select 
                    value={newTarget.employee_id}
                    onValueChange={(v) => setNewTarget({...newTarget, employee_id: v})}
                  >
                    <SelectTrigger><SelectValue placeholder="Select employee" /></SelectTrigger>
                    <SelectContent>
                      {employees.map(emp => (
                        <SelectItem key={emp.id} value={emp.id}>{emp.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Target Type</Label>
                    <Select 
                      value={newTarget.target_type}
                      onValueChange={(v) => setNewTarget({...newTarget, target_type: v})}
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="monthly">Monthly</SelectItem>
                        <SelectItem value="quarterly">Quarterly</SelectItem>
                        <SelectItem value="yearly">Yearly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Period</Label>
                    <Input 
                      type="month"
                      value={newTarget.period}
                      onChange={(e) => setNewTarget({...newTarget, period: e.target.value})}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Target Amount (₹) *</Label>
                    <Input 
                      type="number"
                      value={newTarget.target_amount}
                      onChange={(e) => setNewTarget({...newTarget, target_amount: parseFloat(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>Target Quantity (Units)</Label>
                    <Input 
                      type="number"
                      value={newTarget.target_quantity}
                      onChange={(e) => setNewTarget({...newTarget, target_quantity: parseInt(e.target.value)})}
                    />
                  </div>
                </div>
                <div>
                  <Label>Notes</Label>
                  <Input 
                    value={newTarget.notes}
                    onChange={(e) => setNewTarget({...newTarget, notes: e.target.value})}
                  />
                </div>
                <Button onClick={handleCreateTarget} className="w-full">
                  <Target className="h-4 w-4 mr-2" /> Create Target
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
              <Target className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Target</p>
              <p className="text-2xl font-bold">{formatCurrency(totalTargetAmount)}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-full">
              <TrendingUp className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Achieved</p>
              <p className="text-2xl font-bold">{formatCurrency(totalAchieved)}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-full">
              <Award className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Avg Achievement</p>
              <p className="text-2xl font-bold">{avgAchievement.toFixed(1)}%</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-full">
              <Users className="h-6 w-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Active Targets</p>
              <p className="text-2xl font-bold">{targets.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Leaderboard */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-yellow-500" />
              Leaderboard - {selectedPeriod}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {leaderboard.length > 0 ? (
              <div className="space-y-3">
                {leaderboard.map((entry, idx) => (
                  <div 
                    key={idx} 
                    className={`flex items-center justify-between p-3 rounded-lg ${
                      idx === 0 ? 'bg-yellow-50 border border-yellow-200' :
                      idx === 1 ? 'bg-gray-50 border border-gray-200' :
                      idx === 2 ? 'bg-amber-50 border border-amber-200' :
                      'bg-white border'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {getRankIcon(entry.rank)}
                      <div>
                        <p className="font-medium">{entry.employee_name || 'Unknown'}</p>
                        <p className="text-sm text-gray-500">{entry.achievement_percent?.toFixed(1)}% achieved</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-green-600">{formatCurrency(entry.achieved_amount)}</p>
                      <p className="text-xs text-gray-400">of {formatCurrency(entry.target_amount)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-gray-500 py-4">No data for this period</p>
            )}
          </CardContent>
        </Card>

        {/* Targets List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Sales Targets</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center p-8">
                <RefreshCw className="h-8 w-8 animate-spin text-primary" />
              </div>
            ) : targets.length > 0 ? (
              <div className="space-y-4">
                {targets.map(target => (
                  <div key={target.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-bold">{target.employee_name || 'Unknown'}</p>
                          {getStatusBadge(target.status)}
                          <Badge variant="outline">{target.target_type}</Badge>
                        </div>
                        <div className="mt-2">
                          <div className="flex items-center gap-4 text-sm">
                            <span className="text-gray-500">Target: {formatCurrency(target.target_amount)}</span>
                            <span className="text-green-600">Achieved: {formatCurrency(target.achieved_amount)}</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                            <div 
                              className={`h-2 rounded-full ${
                                target.achievement_percent >= 100 ? 'bg-green-500' :
                                target.achievement_percent >= 80 ? 'bg-blue-500' :
                                target.achievement_percent >= 50 ? 'bg-yellow-500' :
                                'bg-red-500'
                              }`}
                              style={{ width: `${Math.min(target.achievement_percent || 0, 100)}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            {(target.achievement_percent || 0).toFixed(1)}% achieved
                          </p>
                        </div>
                      </div>
                      <Button size="sm" onClick={() => handleCalculateIncentive(target.id)}>
                        <Calculator className="h-4 w-4 mr-1" /> Calculate
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Target className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">No targets set for this period</p>
                <Button className="mt-4" onClick={() => setShowNewTarget(true)}>
                  <Plus className="h-4 w-4 mr-2" /> Set First Target
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Incentive Slabs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Star className="h-5 w-5 text-yellow-500" />
            Incentive Slabs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {slabs.map((slab, idx) => (
              <div 
                key={idx} 
                className={`p-4 rounded-lg border text-center ${
                  idx === slabs.length - 1 ? 'bg-purple-50 border-purple-200' :
                  idx === 0 ? 'bg-gray-50' :
                  'bg-blue-50 border-blue-200'
                }`}
              >
                <p className="font-medium text-sm">{slab.slab_name}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {slab.min_achievement}% - {slab.max_achievement}%
                </p>
                <p className="text-2xl font-bold mt-2 text-green-600">
                  {slab.incentive_value}%
                </p>
                <p className="text-xs text-gray-400">of achieved</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Payouts */}
      {payouts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Incentive Payouts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="text-left p-3">Employee</th>
                    <th className="text-right p-3">Target</th>
                    <th className="text-right p-3">Achieved</th>
                    <th className="text-center p-3">Achievement</th>
                    <th className="text-center p-3">Slab</th>
                    <th className="text-right p-3">Incentive</th>
                    <th className="text-right p-3">Bonus</th>
                    <th className="text-right p-3">Total</th>
                    <th className="text-center p-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {payouts.map(payout => (
                    <tr key={payout.id} className="border-b">
                      <td className="p-3 font-medium">{payout.employee_name}</td>
                      <td className="p-3 text-right">{formatCurrency(payout.target_amount)}</td>
                      <td className="p-3 text-right">{formatCurrency(payout.achieved_amount)}</td>
                      <td className="p-3 text-center">{payout.achievement_percent?.toFixed(1)}%</td>
                      <td className="p-3 text-center"><Badge variant="outline">{payout.slab_applied}</Badge></td>
                      <td className="p-3 text-right">{formatCurrency(payout.calculated_incentive)}</td>
                      <td className="p-3 text-right text-green-600">{formatCurrency(payout.bonus_amount)}</td>
                      <td className="p-3 text-right font-bold">{formatCurrency(payout.total_payout)}</td>
                      <td className="p-3 text-center">
                        <Badge className={payout.status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}>
                          {payout.status?.toUpperCase()}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SalesIncentives;
