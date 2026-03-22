import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Package, Factory, ShoppingCart, Calculator, Users, Shield, Settings, Menu, X, LogOut, TrendingUp, Boxes, Wand2, ClipboardCheck, BarChart3, Gauge, Truck, Banknote, Ship, FolderLock, Trophy, Receipt, PieChart, Clock, Layers, FileEdit, Sliders, Brain, ChevronDown, ChevronRight, MessageSquare, HardDrive, Upload, FileText, Zap, Dna, Search, Star, StarOff, Heart, Warehouse, ClipboardList, ArrowRightLeft } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { cn } from '../../lib/utils';
import NotificationCenter from '../NotificationCenter';

const NavGroup = ({ group, location, setIsOpen }) => {
  const [expanded, setExpanded] = useState(
    group.children.some(child => location.pathname.startsWith(child.href))
  );

  const isGroupActive = group.children.some(child => location.pathname.startsWith(child.href));

  return (
    <div className="space-y-1">
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn(
          "w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all",
          isGroupActive
            ? "bg-gradient-to-r from-accent/10 to-transparent border-l-2 border-accent text-white"
            : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
        )}
      >
        <div className="flex items-center gap-3">
          <group.icon className="h-5 w-5" strokeWidth={1.5} />
          <span className="font-inter">{group.name}</span>
        </div>
        {expanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
      </button>
      
      {expanded && (
        <div className="ml-4 pl-4 border-l border-slate-700 space-y-1">
          {group.children.map((item) => {
            const isActive = location.pathname.startsWith(item.href);
            return (
              <Link
                key={item.name}
                to={item.href}
                data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all",
                  isActive
                    ? "bg-accent/20 text-white font-medium"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
                )}
                onClick={() => setIsOpen(false)}
              >
                <item.icon className="h-4 w-4" strokeWidth={1.5} />
                <span className="font-inter">{item.name}</span>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
};

const Sidebar = ({ isOpen, setIsOpen }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [favorites, setFavorites] = useState(() => {
    const saved = localStorage.getItem('sidebar_favorites');
    return saved ? JSON.parse(saved) : [];
  });

  // Flatten navigation for search
  const flattenNav = (items) => {
    let flat = [];
    items.forEach(item => {
      if (item.type === 'group' && item.children) {
        flat = flat.concat(item.children.map(c => ({ ...c, parent: item.name })));
      } else if (item.type === 'link') {
        flat.push(item);
      }
    });
    return flat;
  };

  const toggleFavorite = (href) => {
    const newFavorites = favorites.includes(href) 
      ? favorites.filter(f => f !== href)
      : [...favorites, href];
    setFavorites(newFavorites);
    localStorage.setItem('sidebar_favorites', JSON.stringify(newFavorites));
  };

  // Grouped navigation structure
  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, type: 'link' },
    { name: 'Director Center', href: '/director', icon: Gauge, type: 'link' },
    { name: 'CRM', href: '/crm', icon: TrendingUp, type: 'link' },
    { 
      name: 'Inventory', 
      icon: Boxes, 
      type: 'group',
      children: [
        { name: 'Stock & Items', href: '/inventory', icon: Package },
        { name: 'Warehouses', href: '/inventory/warehouses', icon: Warehouse },
        { name: 'Stock Register', href: '/inventory/stock-register', icon: ClipboardList },
        { name: 'Stock Transfers', href: '/inventory/stock-transfers', icon: ArrowRightLeft },
        { name: 'Adjustments', href: '/inventory/stock-adjustments', icon: ClipboardCheck },
        { name: 'Advanced', href: '/advanced-inventory', icon: Layers },
      ]
    },
    { 
      name: 'Production', 
      icon: Factory, 
      type: 'group',
      children: [
        { name: 'Overview', href: '/production', icon: Factory },
        { name: 'Work Orders', href: '/production-stages', icon: ClipboardList },
        { name: 'Machines', href: '/production-stages/machines', icon: Layers },
        { name: 'Order Sheets', href: '/production-stages/order-sheets', icon: Package },
        { name: 'DPR Reports', href: '/production-stages/reports', icon: BarChart3 },
      ]
    },
    { 
      name: 'Procurement', 
      icon: ShoppingCart, 
      type: 'group',
      children: [
        { name: 'Purchase Orders', href: '/procurement', icon: ShoppingCart },
        { name: 'Gatepass', href: '/gatepass', icon: Truck },
        { name: 'Import Bridge', href: '/import-bridge', icon: Ship },
      ]
    },
    { name: 'Accounts', href: '/accounts', icon: Calculator, type: 'link' },
    { name: 'Collector', href: '/collector', icon: Zap, type: 'link' },
    { 
      name: 'HRMS', 
      icon: Users, 
      type: 'group',
      children: [
        { name: 'Employees', href: '/hrms', icon: Users },
        { name: 'HR Dashboard', href: '/hrms-dashboard', icon: Clock },
        { name: 'Payroll', href: '/payroll', icon: Banknote },
        { name: 'Employee Vault', href: '/employee-vault', icon: FolderLock },
      ]
    },
    { name: 'Sales Incentives', href: '/sales-incentives', icon: Trophy, type: 'link' },
    { name: 'GST Compliance', href: '/gst-compliance', icon: Receipt, type: 'link' },
    { name: 'E-Invoice', href: '/einvoice', icon: FileText, type: 'link' },
    { name: 'Buying DNA', href: '/buying-dna', icon: Dna, type: 'link' },
    { name: 'Customer Health', href: '/customer-health', icon: Heart, type: 'link' },
    { name: 'Analytics', href: '/analytics', icon: PieChart, type: 'link' },
    { name: 'AI Dashboard', href: '/ai-dashboard', icon: Brain, type: 'link' },
    { name: 'Quality', href: '/quality', icon: Shield, type: 'link' },
    { name: 'Approvals', href: '/approvals', icon: ClipboardCheck, type: 'link' },
    { name: 'Reports', href: '/reports', icon: BarChart3, type: 'link' },
    { name: 'Chat', href: '/chat', icon: MessageSquare, type: 'link' },
    { name: 'Drive', href: '/drive', icon: HardDrive, type: 'link' },
    { name: 'Bulk Import', href: '/bulk-import', icon: Upload, type: 'link' },
    { name: 'Field Registry', href: '/field-registry', icon: Layers, type: 'link' },
    { name: 'Customization', href: '/customization', icon: Wand2, type: 'link' },
    { name: 'Power Settings', href: '/power-settings', icon: Sliders, type: 'link' },
    { name: 'Doc Editor', href: '/document-editor', icon: FileEdit, type: 'link' },
    { name: 'Settings', href: '/settings', icon: Settings, type: 'link' },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <>
      <div
        className={cn(
          "fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity",
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={() => setIsOpen(false)}
      />
      
      <aside
        className={cn(
          "fixed md:sticky top-0 left-0 z-50 h-screen w-64 bg-primary border-r border-slate-800 transition-transform duration-300 flex flex-col",
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        <div className="p-6 border-b border-slate-800">
          <h1 className="text-xl font-manrope font-bold text-primary-foreground">AdhesiveFlow ERP</h1>
          <p className="text-xs text-slate-400 mt-1 font-inter">Industrial Management</p>
        </div>

        {/* Search Bar */}
        <div className="px-4 py-3 border-b border-slate-800">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
            <Input
              placeholder="Search menu..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 h-9"
              data-testid="sidebar-search"
            />
          </div>
        </div>

        {/* Favorites Section */}
        {favorites.length > 0 && !searchTerm && (
          <div className="px-4 py-2 border-b border-slate-800">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2 px-2">Favorites</p>
            {flattenNav(navigation).filter(item => favorites.includes(item.href)).map(item => (
              <Link
                key={`fav-${item.href}`}
                to={item.href}
                className="flex items-center gap-2 px-2 py-1.5 rounded text-sm text-amber-400 hover:bg-slate-800/50"
                onClick={() => setIsOpen(false)}
              >
                <Star className="h-3 w-3 fill-amber-400" />
                <span className="font-inter">{item.name}</span>
              </Link>
            ))}
          </div>
        )}

        <nav className="flex-1 overflow-y-auto p-4 space-y-1">
          {/* Search Results */}
          {searchTerm ? (
            <div className="space-y-1">
              {flattenNav(navigation)
                .filter(item => item.name.toLowerCase().includes(searchTerm.toLowerCase()))
                .map(item => {
                  const isActive = location.pathname.startsWith(item.href);
                  return (
                    <div key={item.href} className="flex items-center gap-1">
                      <Link
                        to={item.href}
                        className={cn(
                          "flex-1 flex items-center gap-3 px-4 py-2 rounded-lg text-sm transition-all",
                          isActive ? "bg-accent/20 text-white" : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
                        )}
                        onClick={() => { setIsOpen(false); setSearchTerm(''); }}
                      >
                        <item.icon className="h-4 w-4" />
                        <span>{item.name}</span>
                        {item.parent && <Badge variant="outline" className="text-xs ml-auto">{item.parent}</Badge>}
                      </Link>
                      <button
                        onClick={() => toggleFavorite(item.href)}
                        className="p-1 text-slate-500 hover:text-amber-400"
                      >
                        {favorites.includes(item.href) ? <Star className="h-4 w-4 fill-amber-400 text-amber-400" /> : <StarOff className="h-4 w-4" />}
                      </button>
                    </div>
                  );
                })}
              {flattenNav(navigation).filter(item => item.name.toLowerCase().includes(searchTerm.toLowerCase())).length === 0 && (
                <p className="text-slate-500 text-sm text-center py-4">No results found</p>
              )}
            </div>
          ) : (
            /* Regular Navigation */
            navigation.map((item) => {
            if (item.type === 'group') {
              return (
                <NavGroup 
                  key={item.name} 
                  group={item} 
                  location={location} 
                  setIsOpen={setIsOpen}
                />
              );
            }
            
            const isActive = location.pathname.startsWith(item.href);
            return (
              <Link
                key={item.name}
                to={item.href}
                data-testid={`nav-${item.name.toLowerCase().replace(/\s+/g, '-')}`}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all",
                  isActive
                    ? "bg-gradient-to-r from-accent/10 to-transparent border-l-2 border-accent text-white"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-white"
                )}
                onClick={() => setIsOpen(false)}
              >
                <item.icon className="h-5 w-5" strokeWidth={1.5} />
                <span className="font-inter">{item.name}</span>
              </Link>
            );
          })
          )}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-4 py-3 mb-2">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-accent to-orange-600 flex items-center justify-center text-white font-bold text-sm">
              {user?.name?.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate font-inter">{user?.name}</p>
              <p className="text-xs text-slate-400 truncate font-inter">{user?.role}</p>
            </div>
          </div>
          <Button
            onClick={handleLogout}
            variant="ghost"
            className="w-full justify-start text-slate-400 hover:text-white hover:bg-slate-800/50"
            data-testid="logout-button"
          >
            <LogOut className="h-4 w-4 mr-2" />
            <span className="font-inter">Logout</span>
          </Button>
        </div>
      </aside>
    </>
  );
};

const MainLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 flex">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 border-b border-slate-200 bg-white/80 backdrop-blur-md flex items-center px-6 justify-between sticky top-0 z-30">
          <button
            className="md:hidden p-2 rounded-lg hover:bg-slate-100"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            data-testid="mobile-menu-button"
          >
            {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <NotificationCenter />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
