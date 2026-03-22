/**
 * CRM Stats Card Component
 * Reusable card for displaying CRM statistics
 */
import React from 'react';
import { Card, CardContent } from '../../../components/ui/card';

const StatsCard = ({ 
  title, 
  value, 
  icon: Icon, 
  iconBgColor = 'bg-blue-100', 
  iconColor = 'text-blue-600',
  valueColor = 'text-blue-600',
  onClick,
  subtitle
}) => {
  return (
    <Card 
      className={`border-slate-200 shadow-sm hover:shadow-md transition-all ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className={`h-12 w-12 rounded-lg ${iconBgColor} flex items-center justify-center`}>
            <Icon className={`h-6 w-6 ${iconColor}`} />
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold ${valueColor}`}>{value}</div>
            <p className="text-sm text-slate-500">{title}</p>
            {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default StatsCard;
