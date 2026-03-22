/**
 * Data Table Component
 * Reusable table with search, filters, and actions
 */
import React from 'react';
import { Card, CardContent } from '../../../components/ui/card';
import { Input } from '../../../components/ui/input';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Search, Edit, Trash2 } from 'lucide-react';
import { getBadgeColor } from '../constants';

const DataTable = ({
  columns,
  data = [],
  searchTerm = '',
  onSearchChange,
  emptyMessage = 'No data found',
  emptyFilterMessage = 'No items match your filters',
  onEdit,
  onDelete,
  renderActions,
  testIdPrefix = 'row'
}) => {
  const hasFilters = searchTerm.length > 0;

  return (
    <Card className="border-slate-200 shadow-sm">
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                {columns.map((col) => (
                  <th 
                    key={col.key} 
                    className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter"
                  >
                    {col.label}
                  </th>
                ))}
                {(onEdit || onDelete || renderActions) && (
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600 uppercase font-inter">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.length === 0 ? (
                <tr>
                  <td 
                    colSpan={columns.length + (onEdit || onDelete || renderActions ? 1 : 0)} 
                    className="px-4 py-12 text-center text-slate-500 font-inter"
                  >
                    {hasFilters ? emptyFilterMessage : emptyMessage}
                  </td>
                </tr>
              ) : (
                data.map((row, index) => (
                  <tr 
                    key={row.id || index} 
                    className="hover:bg-slate-50 transition-colors"
                    data-testid={`${testIdPrefix}-${row.id || index}`}
                  >
                    {columns.map((col) => (
                      <td key={col.key} className="px-4 py-3">
                        {col.render ? col.render(row[col.key], row) : (
                          <span className="text-sm text-slate-900 font-inter">
                            {row[col.key] || '-'}
                          </span>
                        )}
                      </td>
                    ))}
                    {(onEdit || onDelete || renderActions) && (
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          {renderActions ? renderActions(row) : (
                            <>
                              {onEdit && (
                                <Button 
                                  variant="ghost" 
                                  size="sm" 
                                  onClick={() => onEdit(row)}
                                  data-testid={`edit-${testIdPrefix}-${row.id}`}
                                >
                                  <Edit className="h-4 w-4" />
                                </Button>
                              )}
                              {onDelete && (
                                <Button 
                                  variant="ghost" 
                                  size="sm" 
                                  onClick={() => onDelete(row.id)}
                                  className="text-destructive"
                                  data-testid={`delete-${testIdPrefix}-${row.id}`}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              )}
                            </>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};

export default DataTable;
