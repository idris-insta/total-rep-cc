/**
 * Status Distribution Chart Component
 * Displays horizontal bar chart for status distribution
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { STATUS_COLORS } from '../constants';

const StatusDistributionChart = ({ 
  title, 
  data = {}, 
  total = 0,
  showValue = false,
  emptyMessage = 'No data available'
}) => {
  const entries = Object.entries(data);
  
  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-manrope">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {entries.length === 0 ? (
            <p className="text-slate-400 text-center py-4">{emptyMessage}</p>
          ) : (
            entries.map(([status, value]) => {
              const count = typeof value === 'object' ? value.count : value;
              const amount = typeof value === 'object' ? value.total : null;
              const percentage = total > 0 ? (count / total) * 100 : 0;
              
              return (
                <div key={status} className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${STATUS_COLORS[status] || 'bg-slate-400'}`}></div>
                  <span className="flex-1 text-sm capitalize">{status.replace(/_/g, ' ')}</span>
                  <span className="font-semibold">{count}</span>
                  {showValue && amount !== null && (
                    <span className="text-sm text-slate-500 font-mono">
                      ₹{amount.toLocaleString('en-IN')}
                    </span>
                  )}
                  <div className="w-24 h-2 bg-slate-100 rounded-full">
                    <div 
                      className={`h-full rounded-full ${STATUS_COLORS[status] || 'bg-slate-400'}`}
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default StatusDistributionChart;
