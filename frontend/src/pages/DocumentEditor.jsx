import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { 
  FileText, Download, Printer, Save, Eye, Plus, Trash2, Move, 
  Type, Hash, Image, Table, AlignLeft, AlignCenter, AlignRight,
  Bold, Italic, Underline, Undo, Redo, ZoomIn, ZoomOut, Grid,
  Square, Circle, Minus, Edit3
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';
import { cn } from '../lib/utils';

const ELEMENT_TYPES = [
  { id: 'text', label: 'Text', icon: Type },
  { id: 'field', label: 'Data Field', icon: Hash },
  { id: 'image', label: 'Image/Logo', icon: Image },
  { id: 'table', label: 'Table', icon: Table },
  { id: 'line', label: 'Line', icon: Minus },
  { id: 'rectangle', label: 'Rectangle', icon: Square },
];

const TEMPLATES = [
  { id: 'invoice', name: 'Sales Invoice', description: 'Standard GST invoice template' },
  { id: 'quotation', name: 'Quotation', description: 'Customer quotation template' },
  { id: 'purchase_order', name: 'Purchase Order', description: 'Supplier PO template' },
  { id: 'delivery_challan', name: 'Delivery Challan', description: 'DC for goods dispatch' },
  { id: 'work_order', name: 'Work Order', description: 'Production work order' },
];

const DATA_FIELDS = [
  { category: 'Company', fields: ['company_name', 'company_address', 'company_gstin', 'company_phone', 'company_email', 'company_logo'] },
  { category: 'Customer', fields: ['customer_name', 'customer_address', 'customer_gstin', 'customer_phone', 'billing_address', 'shipping_address'] },
  { category: 'Document', fields: ['doc_number', 'doc_date', 'due_date', 'reference', 'terms', 'notes'] },
  { category: 'Items', fields: ['item_table', 'item_code', 'item_name', 'quantity', 'rate', 'amount', 'hsn_code'] },
  { category: 'Totals', fields: ['subtotal', 'cgst', 'sgst', 'igst', 'total_tax', 'grand_total', 'amount_in_words'] },
  { category: 'Bank', fields: ['bank_name', 'account_number', 'ifsc_code', 'upi_id', 'qr_code'] },
];

const DocumentEditor = () => {
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [elements, setElements] = useState([]);
  const [selectedElement, setSelectedElement] = useState(null);
  const [zoom, setZoom] = useState(100);
  const [showGrid, setShowGrid] = useState(true);
  const [savedTemplates, setSavedTemplates] = useState([]);
  const canvasRef = useRef(null);
  const [dragStart, setDragStart] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    fetchSavedTemplates();
  }, []);

  const fetchSavedTemplates = async () => {
    try {
      const res = await api.get('/documents/templates');
      setSavedTemplates(res.data || []);
    } catch (error) {
      console.error('Failed to fetch templates');
    }
  };

  const handleSelectTemplate = (template) => {
    setSelectedTemplate(template);
    // Load default elements for the template
    const defaultElements = getDefaultElements(template.id);
    setElements(defaultElements);
  };

  const getDefaultElements = (templateId) => {
    // Default invoice layout
    return [
      { id: '1', type: 'image', x: 50, y: 30, width: 120, height: 60, content: 'company_logo', label: 'Company Logo' },
      { id: '2', type: 'text', x: 400, y: 30, width: 200, height: 40, content: 'TAX INVOICE', fontSize: 24, fontWeight: 'bold', align: 'right' },
      { id: '3', type: 'field', x: 50, y: 100, width: 250, height: 80, content: 'company_name', label: 'Company Name & Address' },
      { id: '4', type: 'field', x: 400, y: 100, width: 200, height: 30, content: 'doc_number', label: 'Invoice #' },
      { id: '5', type: 'field', x: 400, y: 130, width: 200, height: 30, content: 'doc_date', label: 'Date' },
      { id: '6', type: 'line', x: 50, y: 190, width: 550, height: 2, color: '#334155' },
      { id: '7', type: 'text', x: 50, y: 200, width: 100, height: 20, content: 'Bill To:', fontSize: 12, fontWeight: 'bold' },
      { id: '8', type: 'field', x: 50, y: 220, width: 250, height: 80, content: 'customer_name', label: 'Customer Details' },
      { id: '9', type: 'text', x: 350, y: 200, width: 100, height: 20, content: 'Ship To:', fontSize: 12, fontWeight: 'bold' },
      { id: '10', type: 'field', x: 350, y: 220, width: 250, height: 80, content: 'shipping_address', label: 'Shipping Address' },
      { id: '11', type: 'table', x: 50, y: 320, width: 550, height: 200, content: 'item_table', label: 'Items Table' },
      { id: '12', type: 'field', x: 400, y: 540, width: 200, height: 30, content: 'subtotal', label: 'Subtotal' },
      { id: '13', type: 'field', x: 400, y: 570, width: 200, height: 30, content: 'total_tax', label: 'Tax' },
      { id: '14', type: 'field', x: 400, y: 600, width: 200, height: 40, content: 'grand_total', label: 'Grand Total', fontSize: 16, fontWeight: 'bold' },
      { id: '15', type: 'field', x: 50, y: 650, width: 350, height: 30, content: 'amount_in_words', label: 'Amount in Words' },
      { id: '16', type: 'rectangle', x: 50, y: 700, width: 250, height: 80, content: '', label: 'Bank Details Box', borderColor: '#e2e8f0' },
      { id: '17', type: 'field', x: 55, y: 705, width: 240, height: 70, content: 'bank_details', label: 'Bank Details' },
      { id: '18', type: 'image', x: 450, y: 700, width: 80, height: 80, content: 'qr_code', label: 'Payment QR' },
    ];
  };

  const addElement = (type) => {
    const newElement = {
      id: Date.now().toString(),
      type,
      x: 100,
      y: 100,
      width: type === 'line' ? 200 : 150,
      height: type === 'line' ? 2 : type === 'table' ? 150 : 50,
      content: '',
      label: `New ${type}`,
      fontSize: 12,
      fontWeight: 'normal',
      align: 'left',
      color: '#1e293b',
      borderColor: '#e2e8f0',
    };
    setElements([...elements, newElement]);
    setSelectedElement(newElement);
  };

  const updateElement = (id, updates) => {
    setElements(elements.map(el => el.id === id ? { ...el, ...updates } : el));
    if (selectedElement?.id === id) {
      setSelectedElement({ ...selectedElement, ...updates });
    }
  };

  const deleteElement = (id) => {
    setElements(elements.filter(el => el.id !== id));
    if (selectedElement?.id === id) {
      setSelectedElement(null);
    }
  };

  const handleMouseDown = (e, element) => {
    if (element) {
      setSelectedElement(element);
      setDragStart({ x: e.clientX - element.x, y: e.clientY - element.y });
      setIsDragging(true);
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging && selectedElement && dragStart) {
      const newX = Math.max(0, e.clientX - dragStart.x);
      const newY = Math.max(0, e.clientY - dragStart.y);
      updateElement(selectedElement.id, { x: newX, y: newY });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDragStart(null);
  };

  const handleSaveTemplate = async () => {
    if (!selectedTemplate) return;
    try {
      await api.post('/documents/templates', {
        name: selectedTemplate.name,
        type: selectedTemplate.id,
        elements: elements,
        page_size: 'A4',
        orientation: 'portrait'
      });
      toast.success('Template saved successfully');
      fetchSavedTemplates();
    } catch (error) {
      toast.error('Failed to save template');
    }
  };

  const handlePreview = () => {
    toast.info('Preview functionality - would open print preview');
  };

  const handleExport = () => {
    toast.info('Export as PDF - would generate downloadable PDF');
  };

  const renderElement = (element) => {
    const isSelected = selectedElement?.id === element.id;
    const baseStyle = {
      position: 'absolute',
      left: element.x,
      top: element.y,
      width: element.width,
      height: element.height,
      cursor: 'move',
      border: isSelected ? '2px solid #f97316' : '1px dashed #cbd5e1',
      borderRadius: 4,
      padding: 4,
      fontSize: element.fontSize || 12,
      fontWeight: element.fontWeight || 'normal',
      textAlign: element.align || 'left',
      color: element.color || '#1e293b',
      backgroundColor: element.type === 'rectangle' ? 'transparent' : 'white',
    };

    switch (element.type) {
      case 'text':
        return (
          <div
            key={element.id}
            style={baseStyle}
            onMouseDown={(e) => handleMouseDown(e, element)}
            className="overflow-hidden"
          >
            {element.content || 'Text'}
          </div>
        );
      case 'field':
        return (
          <div
            key={element.id}
            style={{ ...baseStyle, backgroundColor: '#f8fafc' }}
            onMouseDown={(e) => handleMouseDown(e, element)}
            className="flex items-center justify-center text-slate-400"
          >
            <Hash className="h-3 w-3 mr-1" />
            {element.label || element.content}
          </div>
        );
      case 'image':
        return (
          <div
            key={element.id}
            style={{ ...baseStyle, backgroundColor: '#f1f5f9' }}
            onMouseDown={(e) => handleMouseDown(e, element)}
            className="flex items-center justify-center"
          >
            <Image className="h-6 w-6 text-slate-400" />
          </div>
        );
      case 'table':
        return (
          <div
            key={element.id}
            style={{ ...baseStyle, backgroundColor: '#fafafa' }}
            onMouseDown={(e) => handleMouseDown(e, element)}
            className="flex items-center justify-center"
          >
            <Table className="h-6 w-6 text-slate-400 mr-2" />
            <span className="text-slate-400">Items Table</span>
          </div>
        );
      case 'line':
        return (
          <div
            key={element.id}
            style={{ ...baseStyle, backgroundColor: element.color || '#334155', border: 'none' }}
            onMouseDown={(e) => handleMouseDown(e, element)}
          />
        );
      case 'rectangle':
        return (
          <div
            key={element.id}
            style={{ ...baseStyle, border: `1px solid ${element.borderColor || '#e2e8f0'}` }}
            onMouseDown={(e) => handleMouseDown(e, element)}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col" data-testid="document-editor">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-white">
        <div className="flex items-center gap-3">
          <FileText className="h-6 w-6 text-accent" />
          <div>
            <h1 className="text-xl font-bold text-slate-900">Document Editor</h1>
            <p className="text-sm text-slate-500">
              {selectedTemplate ? `Editing: ${selectedTemplate.name}` : 'Select a template to start'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setZoom(Math.max(50, zoom - 10))}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="text-sm text-slate-600 w-16 text-center">{zoom}%</span>
          <Button variant="outline" size="sm" onClick={() => setZoom(Math.min(150, zoom + 10))}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <div className="w-px h-6 bg-slate-200 mx-2" />
          <Button variant="outline" size="sm" onClick={() => setShowGrid(!showGrid)}>
            <Grid className={cn("h-4 w-4", showGrid && "text-accent")} />
          </Button>
          <div className="w-px h-6 bg-slate-200 mx-2" />
          <Button variant="outline" size="sm" onClick={handlePreview}>
            <Eye className="h-4 w-4 mr-2" />Preview
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />Export PDF
          </Button>
          <Button className="bg-accent" size="sm" onClick={handleSaveTemplate}>
            <Save className="h-4 w-4 mr-2" />Save
          </Button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Templates & Elements */}
        <div className="w-64 border-r bg-slate-50 overflow-y-auto">
          <Tabs defaultValue="templates" className="h-full">
            <TabsList className="w-full justify-start px-2 pt-2">
              <TabsTrigger value="templates" className="text-xs">Templates</TabsTrigger>
              <TabsTrigger value="elements" className="text-xs">Elements</TabsTrigger>
              <TabsTrigger value="fields" className="text-xs">Fields</TabsTrigger>
            </TabsList>

            <TabsContent value="templates" className="p-3 space-y-2">
              {TEMPLATES.map(template => (
                <div
                  key={template.id}
                  onClick={() => handleSelectTemplate(template)}
                  className={cn(
                    "p-3 rounded-lg border cursor-pointer transition-all",
                    selectedTemplate?.id === template.id 
                      ? "border-accent bg-accent/10" 
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  )}
                >
                  <p className="font-medium text-sm">{template.name}</p>
                  <p className="text-xs text-slate-500">{template.description}</p>
                </div>
              ))}
            </TabsContent>

            <TabsContent value="elements" className="p-3 space-y-2">
              {ELEMENT_TYPES.map(el => (
                <Button
                  key={el.id}
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => addElement(el.id)}
                  disabled={!selectedTemplate}
                >
                  <el.icon className="h-4 w-4 mr-2" />
                  {el.label}
                </Button>
              ))}
            </TabsContent>

            <TabsContent value="fields" className="p-3 space-y-3">
              {DATA_FIELDS.map(category => (
                <div key={category.category}>
                  <p className="text-xs font-semibold text-slate-500 uppercase mb-2">{category.category}</p>
                  <div className="space-y-1">
                    {category.fields.map(field => (
                      <div
                        key={field}
                        draggable
                        className="px-2 py-1.5 text-xs bg-white rounded border hover:border-accent cursor-move"
                      >
                        {field.replace(/_/g, ' ')}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </TabsContent>
          </Tabs>
        </div>

        {/* Canvas Area */}
        <div 
          className="flex-1 overflow-auto p-8 bg-slate-100"
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          {selectedTemplate ? (
            <div
              ref={canvasRef}
              className="mx-auto bg-white shadow-lg relative"
              style={{
                width: 650 * (zoom / 100),
                height: 920 * (zoom / 100),
                transform: `scale(${zoom / 100})`,
                transformOrigin: 'top left',
                backgroundImage: showGrid ? 'radial-gradient(circle, #e2e8f0 1px, transparent 1px)' : 'none',
                backgroundSize: '20px 20px'
              }}
              onClick={() => setSelectedElement(null)}
            >
              {elements.map(renderElement)}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <FileText className="h-16 w-16 text-slate-200 mx-auto mb-4" />
                <p className="text-slate-500">Select a template from the left panel to start editing</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar - Properties */}
        <div className="w-72 border-l bg-white overflow-y-auto">
          <div className="p-4 border-b">
            <h3 className="font-semibold text-sm">Properties</h3>
          </div>
          {selectedElement ? (
            <div className="p-4 space-y-4">
              <div className="space-y-2">
                <Label className="text-xs">Label</Label>
                <Input
                  value={selectedElement.label || ''}
                  onChange={(e) => updateElement(selectedElement.id, { label: e.target.value })}
                  className="h-8 text-sm"
                />
              </div>
              
              {selectedElement.type === 'text' && (
                <div className="space-y-2">
                  <Label className="text-xs">Text Content</Label>
                  <Textarea
                    value={selectedElement.content || ''}
                    onChange={(e) => updateElement(selectedElement.id, { content: e.target.value })}
                    rows={2}
                  />
                </div>
              )}

              {selectedElement.type === 'field' && (
                <div className="space-y-2">
                  <Label className="text-xs">Data Field</Label>
                  <Select
                    value={selectedElement.content}
                    onValueChange={(v) => updateElement(selectedElement.id, { content: v })}
                  >
                    <SelectTrigger className="h-8"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {DATA_FIELDS.flatMap(c => c.fields).map(f => (
                        <SelectItem key={f} value={f}>{f.replace(/_/g, ' ')}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label className="text-xs">X Position</Label>
                  <Input
                    type="number"
                    value={selectedElement.x}
                    onChange={(e) => updateElement(selectedElement.id, { x: parseInt(e.target.value) || 0 })}
                    className="h-8 text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Y Position</Label>
                  <Input
                    type="number"
                    value={selectedElement.y}
                    onChange={(e) => updateElement(selectedElement.id, { y: parseInt(e.target.value) || 0 })}
                    className="h-8 text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Width</Label>
                  <Input
                    type="number"
                    value={selectedElement.width}
                    onChange={(e) => updateElement(selectedElement.id, { width: parseInt(e.target.value) || 50 })}
                    className="h-8 text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Height</Label>
                  <Input
                    type="number"
                    value={selectedElement.height}
                    onChange={(e) => updateElement(selectedElement.id, { height: parseInt(e.target.value) || 20 })}
                    className="h-8 text-sm"
                  />
                </div>
              </div>

              {(selectedElement.type === 'text' || selectedElement.type === 'field') && (
                <>
                  <div className="space-y-2">
                    <Label className="text-xs">Font Size</Label>
                    <Input
                      type="number"
                      value={selectedElement.fontSize || 12}
                      onChange={(e) => updateElement(selectedElement.id, { fontSize: parseInt(e.target.value) || 12 })}
                      className="h-8 text-sm"
                    />
                  </div>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant={selectedElement.fontWeight === 'bold' ? 'default' : 'outline'}
                      onClick={() => updateElement(selectedElement.id, { fontWeight: selectedElement.fontWeight === 'bold' ? 'normal' : 'bold' })}
                    >
                      <Bold className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant={selectedElement.align === 'left' ? 'default' : 'outline'}
                      onClick={() => updateElement(selectedElement.id, { align: 'left' })}
                    >
                      <AlignLeft className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant={selectedElement.align === 'center' ? 'default' : 'outline'}
                      onClick={() => updateElement(selectedElement.id, { align: 'center' })}
                    >
                      <AlignCenter className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant={selectedElement.align === 'right' ? 'default' : 'outline'}
                      onClick={() => updateElement(selectedElement.id, { align: 'right' })}
                    >
                      <AlignRight className="h-3 w-3" />
                    </Button>
                  </div>
                </>
              )}

              <Button
                variant="destructive"
                size="sm"
                className="w-full"
                onClick={() => deleteElement(selectedElement.id)}
              >
                <Trash2 className="h-3.5 w-3.5 mr-2" />Delete Element
              </Button>
            </div>
          ) : (
            <div className="p-4 text-center text-slate-400 text-sm">
              <Edit3 className="h-8 w-8 mx-auto mb-2 text-slate-200" />
              Select an element to edit its properties
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentEditor;
