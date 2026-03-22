import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { 
  Heart, AlertTriangle, AlertCircle, CheckCircle, Star,
  Phone, MessageSquare, TrendingDown, TrendingUp, ArrowRight,
  RefreshCw
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const CustomerHealthWidget = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealthData();
  }, []);

  const fetchHealthData = async () => {
    try {
      const response = await api.get('/customer-health/widget');
      setData(response.data);
    } catch (error) {
      console.error('Failed to load customer health data');
    } finally {
      setLoading(false);
    }
  };

  const statusConfig = {
    CRITICAL: { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-100', border: 'border-red-300' },
    AT_RISK: { icon: AlertCircle, color: 'text-amber-600', bg: 'bg-amber-100', border: 'border-amber-300' },
    HEALTHY: { icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-100', border: 'border-green-300' },
    EXCELLENT: { icon: Star, color: 'text-blue-600', bg: 'bg-blue-100', border: 'border-blue-300' }
  };

  if (loading) {
    return (
      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-6">
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin h-8 w-8 border-4 border-accent border-t-transparent rounded-full"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  const { summary, attention_needed, health_distribution } = data;

  return (
    <Card className="border-slate-200 shadow-sm" data-testid="customer-health-widget">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Heart className="h-5 w-5 text-red-500" />
            <CardTitle className="text-lg font-manrope">Customer Health Score</CardTitle>
          </div>
          <Button variant="ghost" size="sm" onClick={fetchHealthData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Average Health Score */}
        <div className="text-center p-4 bg-gradient-to-br from-slate-50 to-slate-100 rounded-lg">
          <div className="text-4xl font-bold text-slate-900">{summary.avg_health_score}</div>
          <p className="text-sm text-slate-500">Average Health Score</p>
          <div className="mt-2">
            <Progress value={summary.avg_health_score} className="h-2" />
          </div>
        </div>

        {/* Health Distribution */}
        <div className="grid grid-cols-4 gap-2">
          {Object.entries(health_distribution).map(([status, count]) => {
            const config = statusConfig[status];
            const Icon = config.icon;
            return (
              <div 
                key={status} 
                className={`p-2 rounded-lg text-center ${config.bg} border ${config.border}`}
              >
                <Icon className={`h-4 w-4 mx-auto ${config.color}`} />
                <div className={`text-xl font-bold ${config.color}`}>{count}</div>
                <p className="text-xs text-slate-600">{status.replace('_', ' ')}</p>
              </div>
            );
          })}
        </div>

        {/* At Risk Outstanding */}
        {summary.total_at_risk_outstanding > 0 && (
          <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5 text-red-500" />
              <span className="text-sm text-red-700">At-Risk Outstanding</span>
            </div>
            <span className="font-bold text-red-700 font-mono">
              ₹{summary.total_at_risk_outstanding.toLocaleString('en-IN')}
            </span>
          </div>
        )}

        {/* Attention Needed List */}
        {attention_needed.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Needs Attention</p>
            {attention_needed.slice(0, 3).map((customer) => (
              <div 
                key={customer.account_id} 
                className={`p-3 rounded-lg border ${statusConfig[customer.health_status].border} ${statusConfig[customer.health_status].bg}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">{customer.account_name}</span>
                      <Badge variant="outline" className="text-xs">
                        Score: {customer.health_score}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-600 mt-1">
                      {customer.risk_factors[0]}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    {customer.contact_phone && (
                      <Button 
                        variant="ghost" 
                        size="sm"
                        className="h-7 w-7 p-0"
                        onClick={() => window.open(`tel:${customer.contact_phone}`)}
                      >
                        <Phone className="h-3 w-3" />
                      </Button>
                    )}
                    {customer.contact_phone && (
                      <Button 
                        variant="ghost" 
                        size="sm"
                        className="h-7 w-7 p-0 text-green-600"
                        onClick={() => {
                          const phone = customer.contact_phone.replace(/\D/g, '');
                          window.open(`https://wa.me/${phone.startsWith('91') ? phone : '91' + phone}`);
                        }}
                      >
                        <MessageSquare className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                </div>
                <div className="mt-2 text-xs text-slate-500">
                  <span className="font-medium">Action:</span> {customer.recommended_actions[0]}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* View All Button */}
        <Button 
          variant="outline" 
          className="w-full"
          onClick={() => navigate('/customer-health')}
        >
          View All Customer Health Scores
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </CardContent>
    </Card>
  );
};

export default CustomerHealthWidget;
