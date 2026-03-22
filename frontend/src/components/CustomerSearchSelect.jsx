import React, { useState, useEffect } from 'react';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from './ui/command';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Button } from './ui/button';
import { Check, ChevronsUpDown, User, Building2 } from 'lucide-react';
import { cn } from '../lib/utils';
import api from '../lib/api';

/**
 * Searchable Customer/Account Dropdown with Auto-populate
 * Searches accounts by name, code, GSTIN and auto-populates related fields
 */
const CustomerSearchSelect = ({ 
  value, 
  onChange, 
  onCustomerSelect,  // Callback with full customer details for auto-populate
  placeholder = "Search customer...",
  disabled = false,
  className = "",
  accountType = null  // 'Customer' or 'Supplier' or null for all
}) => {
  const [open, setOpen] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch accounts on mount
  useEffect(() => {
    fetchAccounts();
  }, [accountType]);

  const fetchAccounts = async (search = '') => {
    setLoading(true);
    try {
      let url = '/crm/accounts?';
      if (accountType) url += `account_type=${accountType}&`;
      if (search) url += `search=${encodeURIComponent(search)}&`;
      const res = await api.get(url);
      setAccounts(res.data || []);
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchTerm) {
        fetchAccounts(searchTerm);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleSelect = (accountId) => {
    const selectedAccount = accounts.find(a => a.id === accountId);
    if (selectedAccount) {
      onChange(accountId);
      // Call onCustomerSelect with full details for auto-populate
      if (onCustomerSelect) {
        onCustomerSelect({
          account_id: selectedAccount.id,
          customer_code: selectedAccount.customer_code,
          customer_name: selectedAccount.customer_name,
          contact_person: selectedAccount.contact_person || '',
          email: selectedAccount.email || '',
          phone: selectedAccount.phone || '',
          mobile: selectedAccount.mobile || '',
          gstin: selectedAccount.gstin || '',
          pan: selectedAccount.pan || '',
          billing_address: selectedAccount.address || '',
          billing_city: selectedAccount.city || '',
          billing_state: selectedAccount.state || '',
          billing_pincode: selectedAccount.pincode || '',
          shipping_address: selectedAccount.shipping_address || selectedAccount.address || '',
          shipping_city: selectedAccount.shipping_city || selectedAccount.city || '',
          shipping_state: selectedAccount.shipping_state || selectedAccount.state || '',
          shipping_pincode: selectedAccount.shipping_pincode || selectedAccount.pincode || '',
          payment_terms: selectedAccount.payment_terms || '30 days',
          credit_limit: selectedAccount.credit_limit || 0,
          credit_days: selectedAccount.credit_days || 30,
          account_type: selectedAccount.account_type || 'Customer'
        });
      }
    }
    setOpen(false);
  };

  const selectedAccount = accounts.find(a => a.id === value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn("w-full justify-between h-9 font-normal", className)}
        >
          {selectedAccount ? (
            <span className="truncate">{selectedAccount.customer_name}</span>
          ) : (
            <span className="text-slate-500">{placeholder}</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput 
            placeholder="Search by name, code, GSTIN..." 
            value={searchTerm}
            onValueChange={setSearchTerm}
          />
          <CommandList>
            {loading ? (
              <div className="py-6 text-center text-sm text-slate-500">Loading...</div>
            ) : accounts.length === 0 ? (
              <CommandEmpty>No customers found.</CommandEmpty>
            ) : (
              <CommandGroup>
                {accounts.slice(0, 50).map((account) => (
                  <CommandItem
                    key={account.id}
                    value={account.id}
                    onSelect={() => handleSelect(account.id)}
                    className="flex items-center gap-2 py-2"
                  >
                    {account.account_type === 'Customer' ? (
                      <User className="h-4 w-4 text-blue-500" />
                    ) : (
                      <Building2 className="h-4 w-4 text-green-500" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        {account.customer_code && (
                          <span className="font-mono text-xs bg-slate-100 px-1 rounded">{account.customer_code}</span>
                        )}
                        <span className="truncate font-medium">{account.customer_name}</span>
                      </div>
                      <div className="text-xs text-slate-500 flex gap-2">
                        <span>{account.city || 'No city'}</span>
                        {account.gstin && <><span>•</span><span>{account.gstin}</span></>}
                        {account.phone && <><span>•</span><span>{account.phone}</span></>}
                      </div>
                    </div>
                    <Check
                      className={cn(
                        "h-4 w-4",
                        value === account.id ? "opacity-100" : "opacity-0"
                      )}
                    />
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
};

export default CustomerSearchSelect;
