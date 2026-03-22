import React, { useState, useEffect, useRef } from 'react';
import { Bell, X, Check, CheckCheck, AlertTriangle, CreditCard, Package, Calendar, Clock, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import api from '../lib/api';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

const NotificationCenter = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const res = await api.get('/notifications/notifications/count');
      setUnreadCount(res.data.unread_count || 0);
    } catch (error) {
      console.error('Failed to fetch notification count');
    }
  };

  const fetchNotifications = async () => {
    setLoading(true);
    try {
      const res = await api.get('/notifications/notifications?limit=20');
      setNotifications(res.data || []);
    } catch (error) {
      console.error('Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  };

  const generateAlerts = async () => {
    try {
      const res = await api.post('/notifications/alerts/generate');
      toast.success(res.data.message);
      fetchNotifications();
      fetchUnreadCount();
    } catch (error) {
      toast.error('Failed to generate alerts');
    }
  };

  const markAsRead = async (notifId) => {
    try {
      await api.put(`/notifications/notifications/${notifId}/read`);
      setNotifications(prev => 
        prev.map(n => n.id === notifId ? {...n, is_read: true} : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark as read');
    }
  };

  const markAllRead = async () => {
    try {
      await api.put('/notifications/notifications/read-all');
      setNotifications(prev => prev.map(n => ({...n, is_read: true})));
      setUnreadCount(0);
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark all as read');
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'payment': return <CreditCard className="h-4 w-4" />;
      case 'stock': return <Package className="h-4 w-4" />;
      case 'approval': return <Calendar className="h-4 w-4" />;
      case 'reminder': return <Clock className="h-4 w-4" />;
      default: return <Bell className="h-4 w-4" />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'normal': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'payment': return 'text-red-500 bg-red-50';
      case 'stock': return 'text-orange-500 bg-orange-50';
      case 'approval': return 'text-blue-500 bg-blue-50';
      default: return 'text-slate-500 bg-slate-50';
    }
  };

  const formatTime = (dateStr) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Notification Bell */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-slate-100 transition-colors"
        data-testid="notification-bell"
      >
        <Bell className="h-5 w-5 text-slate-600" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden z-50">
          {/* Header */}
          <div className="px-4 py-3 bg-gradient-to-r from-slate-900 to-slate-800 text-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              <span className="font-semibold">Notifications</span>
              {unreadCount > 0 && (
                <Badge variant="secondary" className="bg-red-500 text-white text-xs">
                  {unreadCount} new
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-1">
              <Button
                size="sm"
                variant="ghost"
                onClick={generateAlerts}
                className="h-7 px-2 text-white hover:bg-white/20"
                title="Generate system alerts"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
              {unreadCount > 0 && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={markAllRead}
                  className="h-7 px-2 text-white hover:bg-white/20"
                  title="Mark all as read"
                >
                  <CheckCheck className="h-3.5 w-3.5" />
                </Button>
              )}
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setIsOpen(false)}
                className="h-7 px-2 text-white hover:bg-white/20"
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin h-6 w-6 border-2 border-accent border-t-transparent rounded-full"></div>
              </div>
            ) : notifications.length > 0 ? (
              <div className="divide-y divide-slate-100">
                {notifications.map((notif) => (
                  <div
                    key={notif.id}
                    className={cn(
                      "px-4 py-3 hover:bg-slate-50 cursor-pointer transition-colors",
                      !notif.is_read && "bg-blue-50/50"
                    )}
                    onClick={() => !notif.is_read && markAsRead(notif.id)}
                  >
                    <div className="flex items-start gap-3">
                      <div className={cn("p-2 rounded-lg", getTypeColor(notif.type))}>
                        {getIcon(notif.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className={cn("text-sm font-medium", !notif.is_read ? "text-slate-900" : "text-slate-600")}>
                            {notif.title}
                          </p>
                          <Badge className={cn("text-[10px] px-1.5 py-0", getPriorityColor(notif.priority))}>
                            {notif.priority}
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-500 line-clamp-2">{notif.message}</p>
                        <p className="text-[10px] text-slate-400 mt-1">{formatTime(notif.created_at)}</p>
                      </div>
                      {!notif.is_read && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-12 text-center">
                <Bell className="h-12 w-12 text-slate-200 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">No notifications yet</p>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={generateAlerts}
                  className="mt-3"
                >
                  <RefreshCw className="h-3.5 w-3.5 mr-2" />
                  Generate Alerts
                </Button>
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-2 bg-slate-50 border-t">
              <Button
                variant="ghost"
                className="w-full text-xs text-slate-600 hover:text-slate-900"
                onClick={() => {
                  setIsOpen(false);
                  // Navigate to full notifications page if needed
                }}
              >
                View All Notifications
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;
