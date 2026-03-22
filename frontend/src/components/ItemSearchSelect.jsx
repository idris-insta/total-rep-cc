import React, { useState, useEffect, useRef } from 'react';
import { Input } from './ui/input';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from './ui/command';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Button } from './ui/button';
import { Check, ChevronsUpDown, Package } from 'lucide-react';
import { cn } from '../lib/utils';
import api from '../lib/api';

/**
 * Searchable Item Dropdown with Auto-populate
 * Searches inventory items by name or code and auto-populates related fields
 */
const ItemSearchSelect = ({ 
  value, 
  onChange, 
  onItemSelect,  // Callback with full item details for auto-populate
  placeholder = "Search items...",
  disabled = false,
  className = ""
}) => {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch items on mount
  useEffect(() => {
    fetchItems();
  }, []);

  const fetchItems = async (search = '') => {
    setLoading(true);
    try {
      const url = search 
        ? `/inventory/items?search=${encodeURIComponent(search)}`
        : '/inventory/items';
      const res = await api.get(url);
      setItems(res.data || []);
    } catch (error) {
      console.error('Failed to fetch items:', error);
    } finally {
      setLoading(false);
    }
  };

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchTerm) {
        fetchItems(searchTerm);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const handleSelect = (itemId) => {
    const selectedItem = items.find(i => i.id === itemId);
    if (selectedItem) {
      onChange(itemId);
      // Call onItemSelect with full item details for auto-populate
      if (onItemSelect) {
        onItemSelect({
          item_id: selectedItem.id,
          item_code: selectedItem.item_code,
          item_name: selectedItem.item_name,
          hsn_code: selectedItem.hsn_code || '',
          uom: selectedItem.uom || 'Pcs',
          unit: selectedItem.uom || 'Pcs',
          unit_price: selectedItem.selling_price || 0,
          tax_percent: 18, // Default GST
          standard_cost: selectedItem.standard_cost || 0,
          min_sale_price: selectedItem.min_sale_price || 0,
          category: selectedItem.category || '',
          thickness: selectedItem.thickness,
          width: selectedItem.width,
          length: selectedItem.length
        });
      }
    }
    setOpen(false);
  };

  const selectedItem = items.find(i => i.id === value);

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
          {selectedItem ? (
            <span className="truncate">{selectedItem.item_code} - {selectedItem.item_name}</span>
          ) : (
            <span className="text-slate-500">{placeholder}</span>
          )}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput 
            placeholder="Search by name or code..." 
            value={searchTerm}
            onValueChange={setSearchTerm}
          />
          <CommandList>
            {loading ? (
              <div className="py-6 text-center text-sm text-slate-500">Loading...</div>
            ) : items.length === 0 ? (
              <CommandEmpty>No items found.</CommandEmpty>
            ) : (
              <CommandGroup>
                {items.slice(0, 50).map((item) => (
                  <CommandItem
                    key={item.id}
                    value={item.id}
                    onSelect={() => handleSelect(item.id)}
                    className="flex items-center gap-2 py-2"
                  >
                    <Package className="h-4 w-4 text-slate-400" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs bg-slate-100 px-1 rounded">{item.item_code}</span>
                        <span className="truncate font-medium">{item.item_name}</span>
                      </div>
                      <div className="text-xs text-slate-500 flex gap-2">
                        <span>₹{item.selling_price?.toLocaleString('en-IN') || 0}</span>
                        <span>•</span>
                        <span>{item.uom}</span>
                        {item.hsn_code && <><span>•</span><span>HSN: {item.hsn_code}</span></>}
                      </div>
                    </div>
                    <Check
                      className={cn(
                        "h-4 w-4",
                        value === item.id ? "opacity-100" : "opacity-0"
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

export default ItemSearchSelect;
