/**
 * Recent Activity List Component
 * Displays a list of recent items with status badges
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { getBadgeColor, formatCurrency } from '../constants';

const RecentActivityList = ({
  title,
  items = [],
  emptyMessage = 'No items yet',
  onViewAll,
  renderItem,
  keyField = 'id'
}) => {
  return (
    <Card className="border-slate-200 shadow-sm">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-manrope">{title}</CardTitle>
          {onViewAll && (
            <Button variant="ghost" size="sm" onClick={onViewAll}>
              View All
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-slate-400 text-center py-4">{emptyMessage}</p>
        ) : (
          <div className="space-y-2">
            {items.map((item) => (
              <div key={item[keyField]} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                {renderItem ? renderItem(item) : (
                  <>
                    <div>
                      <p className="font-semibold text-sm">{item.name || item.company_name}</p>
                      <p className="text-xs text-slate-500">{item.subtitle || item.contact_person}</p>
                    </div>
                    <Badge className={`text-xs ${getBadgeColor(item.status)}`}>
                      {item.status}
                    </Badge>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Pre-configured variants
export const RecentLeadsList = ({ leads, onViewAll }) => (
  <RecentActivityList
    title="Recent Leads"
    items={leads}
    emptyMessage="No leads yet"
    onViewAll={onViewAll}
    renderItem={(lead) => (
      <>
        <div>
          <p className="font-semibold text-sm">{lead.company_name}</p>
          <p className="text-xs text-slate-500">{lead.contact_person}</p>
        </div>
        <Badge className={`text-xs ${getBadgeColor(lead.status)}`}>
          {lead.status}
        </Badge>
      </>
    )}
  />
);

export const RecentQuotesList = ({ quotes, onViewAll }) => (
  <RecentActivityList
    title="Recent Quotations"
    items={quotes}
    emptyMessage="No quotations yet"
    onViewAll={onViewAll}
    renderItem={(quote) => (
      <>
        <div>
          <p className="font-semibold text-sm font-mono">{quote.quote_number}</p>
          <p className="text-xs text-slate-500">{quote.account_name}</p>
        </div>
        <div className="text-right">
          <p className="font-semibold text-sm font-mono">{formatCurrency(quote.grand_total)}</p>
          <Badge className={`text-xs ${getBadgeColor(quote.status)}`}>
            {quote.status}
          </Badge>
        </div>
      </>
    )}
  />
);

export default RecentActivityList;
