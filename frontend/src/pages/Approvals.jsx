import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

const statusBadge = (status) => {
  const s = status || 'pending';
  if (s === 'approved') return <Badge className="bg-emerald-100 text-emerald-800">Approved</Badge>;
  if (s === 'rejected') return <Badge className="bg-red-100 text-red-800">Rejected</Badge>;
  return <Badge className="bg-amber-100 text-amber-800">Pending</Badge>;
};

const Approvals = () => {
  const [loading, setLoading] = useState(false);
  const [requests, setRequests] = useState([]);
  const [status, setStatus] = useState('pending');

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/approvals/requests?status=${status}`);
      setRequests(res.data || []);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to load approvals');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  const approve = async (id) => {
    try {
      await api.put(`/approvals/requests/${id}/approve`);
      toast.success('Approved');
      fetchRequests();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to approve');
    }
  };

  const reject = async (id) => {
    try {
      await api.put(`/approvals/requests/${id}/reject`);
      toast.success('Rejected');
      fetchRequests();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to reject');
    }
  };

  return (
    <div className="space-y-6" data-testid="approvals-inbox">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 font-manrope">Approvals Inbox</h1>
          <p className="text-slate-600 font-inter mt-1">Approve or reject pending requests (Inventory / Production / HRMS)</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-[160px]"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={fetchRequests} disabled={loading}>
            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
          </Button>
        </div>
      </div>

      <Card className="border-slate-200 shadow-sm">
        <CardHeader>
          <CardTitle className="font-manrope">Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Status</TableHead>
                <TableHead>Module</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Condition</TableHead>
                <TableHead>Requested At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {requests.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-slate-500">No requests</TableCell>
                </TableRow>
              ) : (
                requests.map((r) => (
                  <TableRow key={r.id}>
                    <TableCell>{statusBadge(r.status)}</TableCell>
                    <TableCell className="font-medium">{r.module}</TableCell>
                    <TableCell>{r.entity_type}</TableCell>
                    <TableCell>{r.action}</TableCell>
                    <TableCell>{r.condition || '-'}</TableCell>
                    <TableCell>{r.requested_at ? new Date(r.requested_at).toLocaleString() : '-'}</TableCell>
                    <TableCell className="text-right">
                      {r.status === 'pending' ? (
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="outline" onClick={() => reject(r.id)}>
                            <XCircle className="h-4 w-4 mr-2" /> Reject
                          </Button>
                          <Button size="sm" onClick={() => approve(r.id)}>
                            <CheckCircle className="h-4 w-4 mr-2" /> Approve
                          </Button>
                        </div>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </TableCell>
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

export default Approvals;
