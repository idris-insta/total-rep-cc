import React, { useEffect, useState } from 'react';
import { Download } from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';

const Reports = () => {
  const [kpis, setKpis] = useState([]);

  const load = async () => {
    try {
      const res = await api.get('/reports/kpis');
      setKpis(res.data?.kpis || []);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load KPIs');
    }
  };

  useEffect(() => {
    const t = setTimeout(() => load(), 0);
    return () => clearTimeout(t);
  }, []);

  const download = async (format) => {
    try {
      const res = await api.get(`/reports/export?format=${format}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      const ext = format === 'pdf' ? 'pdf' : 'xlsx';
      link.setAttribute('download', `kpis.${ext}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success(`Downloaded ${format.toUpperCase()}`);
    } catch (e) {
      toast.error('Download failed');
    }
  };

  return (
    <div className="space-y-6" data-testid="reports-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope">Reports / KPIs</h1>
          <p className="text-slate-600 font-inter mt-1">Workbook KPIs (download as XLSX/PDF)</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => download('xlsx')}>
            <Download className="h-4 w-4 mr-2" /> XLSX
          </Button>
          <Button variant="outline" onClick={() => download('pdf')}>
            <Download className="h-4 w-4 mr-2" /> PDF
          </Button>
        </div>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="font-manrope">KPI List</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Module</TableHead>
                <TableHead>Report/KPI</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Frequency</TableHead>
                <TableHead>Audience</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {kpis.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-center text-slate-500">No KPIs</TableCell>
                </TableRow>
              ) : (
                kpis.map((k) => (
                  <TableRow key={`${k.module}-${k.name}`}>
                    <TableCell className="font-medium">{k.module}</TableCell>
                    <TableCell>{k.name}</TableCell>
                    <TableCell>{k.description}</TableCell>
                    <TableCell>{k.frequency}</TableCell>
                    <TableCell>{k.audience}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default Reports;
