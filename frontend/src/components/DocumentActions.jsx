import React, { useState } from 'react';
import { Button } from './ui/button';
import { 
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, 
  DropdownMenuTrigger, DropdownMenuSeparator, DropdownMenuLabel 
} from './ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { 
  Eye, FileDown, Printer, Mail, MessageSquare, MoreVertical,
  Send, Copy, ExternalLink, CheckCircle
} from 'lucide-react';
import api from '../lib/api';
import { toast } from 'sonner';

const backendUrl = import.meta.env.VITE_BACKEND_URL;

/**
 * Universal Document Actions Component
 * Provides PDF preview, download, print, email, and WhatsApp functionality
 * 
 * @param {string} documentType - invoice, quotation, work_order, delivery_challan, purchase_order, sample, payment
 * @param {string} documentId - The document ID
 * @param {string} documentNumber - Display number (e.g., INV-001)
 * @param {object} recipient - { name, email, phone } - Pre-filled recipient info
 * @param {boolean} compact - Show only icons (default: false)
 */
const DocumentActions = ({ 
  documentType, 
  documentId, 
  documentNumber,
  recipient = {},
  compact = false,
  onSendComplete
}) => {
  const [emailDialogOpen, setEmailDialogOpen] = useState(false);
  const [whatsappDialogOpen, setWhatsappDialogOpen] = useState(false);
  const [sending, setSending] = useState(false);
  
  const [emailForm, setEmailForm] = useState({
    recipient_email: recipient.email || '',
    recipient_name: recipient.name || '',
    subject: '',
    message: ''
  });
  
  const [whatsappForm, setWhatsappForm] = useState({
    recipient_phone: recipient.phone || '',
    recipient_name: recipient.name || '',
    message: ''
  });
  
  const [whatsappResult, setWhatsappResult] = useState(null);

  // URL mappings for different document types
  const getPdfUrl = (action) => {
    const typeMap = {
      'invoice': 'invoice',
      'quotation': 'quotation',
      'work_order': 'work-order',
      'delivery_challan': 'delivery-challan',
      'purchase_order': 'purchase-order',
      'sample': 'sample',
      'payment': 'payment'
    };
    const urlType = typeMap[documentType] || documentType;
    return `${backendUrl}/api/pdf/${urlType}/${documentId}/${action}`;
  };

  const handlePreview = () => {
    window.open(getPdfUrl('preview'), '_blank');
  };

  const handleDownload = () => {
    window.open(getPdfUrl('pdf'), '_blank');
  };

  const handlePrint = () => {
    const printWindow = window.open(getPdfUrl('preview'), '_blank');
    if (printWindow) {
      printWindow.onload = () => {
        setTimeout(() => printWindow.print(), 500);
      };
    }
  };

  const handleSendEmail = async () => {
    if (!emailForm.recipient_email) {
      toast.error('Please enter recipient email');
      return;
    }
    
    setSending(true);
    try {
      const response = await api.post('/communicate/email/send', {
        document_type: documentType,
        document_id: documentId,
        ...emailForm
      });
      
      toast.success(`Email sent to ${emailForm.recipient_email}`);
      setEmailDialogOpen(false);
      onSendComplete?.('email', response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send email');
    } finally {
      setSending(false);
    }
  };

  const handleGenerateWhatsApp = async () => {
    if (!whatsappForm.recipient_phone) {
      toast.error('Please enter recipient phone number');
      return;
    }
    
    setSending(true);
    try {
      const response = await api.post('/communicate/whatsapp/send', {
        document_type: documentType,
        document_id: documentId,
        ...whatsappForm
      });
      
      setWhatsappResult(response.data);
      toast.success('WhatsApp message generated');
      onSendComplete?.('whatsapp', response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to generate WhatsApp message');
    } finally {
      setSending(false);
    }
  };

  const openWhatsApp = () => {
    if (whatsappResult?.whatsapp_url) {
      window.open(whatsappResult.whatsapp_url, '_blank');
    }
  };

  const copyWhatsAppMessage = () => {
    if (whatsappResult?.message_text) {
      navigator.clipboard.writeText(whatsappResult.message_text);
      toast.success('Message copied to clipboard');
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" onClick={handlePreview} title="Preview PDF">
          <Eye className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={handleDownload} title="Download PDF" className="text-blue-600">
          <FileDown className="h-4 w-4" />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Send Document</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setEmailDialogOpen(true)}>
              <Mail className="h-4 w-4 mr-2" /> Send Email
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setWhatsappDialogOpen(true)}>
              <MessageSquare className="h-4 w-4 mr-2 text-green-600" /> Send WhatsApp
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handlePrint}>
              <Printer className="h-4 w-4 mr-2" /> Print
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        
        {/* Email Dialog */}
        <Dialog open={emailDialogOpen} onOpenChange={setEmailDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-blue-600" />
                Send {documentNumber} via Email
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Recipient Email *</Label>
                  <Input 
                    type="email"
                    value={emailForm.recipient_email}
                    onChange={(e) => setEmailForm({...emailForm, recipient_email: e.target.value})}
                    placeholder="customer@email.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Recipient Name</Label>
                  <Input 
                    value={emailForm.recipient_name}
                    onChange={(e) => setEmailForm({...emailForm, recipient_name: e.target.value})}
                    placeholder="John Doe"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Subject (optional)</Label>
                <Input 
                  value={emailForm.subject}
                  onChange={(e) => setEmailForm({...emailForm, subject: e.target.value})}
                  placeholder="Leave blank for default subject"
                />
              </div>
              <div className="space-y-2">
                <Label>Message (optional)</Label>
                <Textarea 
                  value={emailForm.message}
                  onChange={(e) => setEmailForm({...emailForm, message: e.target.value})}
                  placeholder="Add a custom message..."
                  rows={3}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEmailDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleSendEmail} disabled={sending} className="bg-blue-600 hover:bg-blue-700">
                {sending ? 'Sending...' : <><Send className="h-4 w-4 mr-2" /> Send Email</>}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* WhatsApp Dialog */}
        <Dialog open={whatsappDialogOpen} onOpenChange={(open) => {
          setWhatsappDialogOpen(open);
          if (!open) setWhatsappResult(null);
        }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-green-600" />
                Send {documentNumber} via WhatsApp
              </DialogTitle>
            </DialogHeader>
            
            {!whatsappResult ? (
              <>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Phone Number *</Label>
                      <Input 
                        value={whatsappForm.recipient_phone}
                        onChange={(e) => setWhatsappForm({...whatsappForm, recipient_phone: e.target.value})}
                        placeholder="9876543210"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Recipient Name</Label>
                      <Input 
                        value={whatsappForm.recipient_name}
                        onChange={(e) => setWhatsappForm({...whatsappForm, recipient_name: e.target.value})}
                        placeholder="John"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Custom Message (optional)</Label>
                    <Textarea 
                      value={whatsappForm.message}
                      onChange={(e) => setWhatsappForm({...whatsappForm, message: e.target.value})}
                      placeholder="Leave blank for default message"
                      rows={3}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setWhatsappDialogOpen(false)}>Cancel</Button>
                  <Button onClick={handleGenerateWhatsApp} disabled={sending} className="bg-green-600 hover:bg-green-700">
                    {sending ? 'Generating...' : 'Generate Message'}
                  </Button>
                </DialogFooter>
              </>
            ) : (
              <>
                <div className="space-y-4">
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <span className="font-semibold text-green-800">Message Ready!</span>
                    </div>
                    <pre className="whitespace-pre-wrap text-sm font-sans text-slate-700">
                      {whatsappResult.message_text}
                    </pre>
                  </div>
                </div>
                <DialogFooter className="flex-col sm:flex-row gap-2">
                  <Button variant="outline" onClick={copyWhatsAppMessage} className="flex-1">
                    <Copy className="h-4 w-4 mr-2" /> Copy Message
                  </Button>
                  <Button onClick={openWhatsApp} className="bg-green-600 hover:bg-green-700 flex-1">
                    <ExternalLink className="h-4 w-4 mr-2" /> Open WhatsApp
                  </Button>
                </DialogFooter>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    );
  }

  // Full buttons view (non-compact)
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <Button variant="outline" size="sm" onClick={handlePreview}>
        <Eye className="h-4 w-4 mr-2" /> Preview
      </Button>
      <Button variant="outline" size="sm" onClick={handleDownload}>
        <FileDown className="h-4 w-4 mr-2" /> Download
      </Button>
      <Button variant="outline" size="sm" onClick={handlePrint}>
        <Printer className="h-4 w-4 mr-2" /> Print
      </Button>
      <Button variant="outline" size="sm" onClick={() => setEmailDialogOpen(true)}>
        <Mail className="h-4 w-4 mr-2" /> Email
      </Button>
      <Button variant="outline" size="sm" onClick={() => setWhatsappDialogOpen(true)} className="text-green-600 border-green-300 hover:bg-green-50">
        <MessageSquare className="h-4 w-4 mr-2" /> WhatsApp
      </Button>
      
      {/* Dialogs same as above */}
      <Dialog open={emailDialogOpen} onOpenChange={setEmailDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-blue-600" />
              Send {documentNumber} via Email
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Recipient Email *</Label>
                <Input 
                  type="email"
                  value={emailForm.recipient_email}
                  onChange={(e) => setEmailForm({...emailForm, recipient_email: e.target.value})}
                  placeholder="customer@email.com"
                />
              </div>
              <div className="space-y-2">
                <Label>Recipient Name</Label>
                <Input 
                  value={emailForm.recipient_name}
                  onChange={(e) => setEmailForm({...emailForm, recipient_name: e.target.value})}
                  placeholder="John Doe"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Subject (optional)</Label>
              <Input 
                value={emailForm.subject}
                onChange={(e) => setEmailForm({...emailForm, subject: e.target.value})}
                placeholder="Leave blank for default subject"
              />
            </div>
            <div className="space-y-2">
              <Label>Message (optional)</Label>
              <Textarea 
                value={emailForm.message}
                onChange={(e) => setEmailForm({...emailForm, message: e.target.value})}
                placeholder="Add a custom message..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEmailDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleSendEmail} disabled={sending} className="bg-blue-600 hover:bg-blue-700">
              {sending ? 'Sending...' : <><Send className="h-4 w-4 mr-2" /> Send Email</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={whatsappDialogOpen} onOpenChange={(open) => {
        setWhatsappDialogOpen(open);
        if (!open) setWhatsappResult(null);
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-green-600" />
              Send {documentNumber} via WhatsApp
            </DialogTitle>
          </DialogHeader>
          
          {!whatsappResult ? (
            <>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Phone Number *</Label>
                    <Input 
                      value={whatsappForm.recipient_phone}
                      onChange={(e) => setWhatsappForm({...whatsappForm, recipient_phone: e.target.value})}
                      placeholder="9876543210"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Recipient Name</Label>
                    <Input 
                      value={whatsappForm.recipient_name}
                      onChange={(e) => setWhatsappForm({...whatsappForm, recipient_name: e.target.value})}
                      placeholder="John"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Custom Message (optional)</Label>
                  <Textarea 
                    value={whatsappForm.message}
                    onChange={(e) => setWhatsappForm({...whatsappForm, message: e.target.value})}
                    placeholder="Leave blank for default message"
                    rows={3}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setWhatsappDialogOpen(false)}>Cancel</Button>
                <Button onClick={handleGenerateWhatsApp} disabled={sending} className="bg-green-600 hover:bg-green-700">
                  {sending ? 'Generating...' : 'Generate Message'}
                </Button>
              </DialogFooter>
            </>
          ) : (
            <>
              <div className="space-y-4">
                <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <span className="font-semibold text-green-800">Message Ready!</span>
                  </div>
                  <pre className="whitespace-pre-wrap text-sm font-sans text-slate-700">
                    {whatsappResult.message_text}
                  </pre>
                </div>
              </div>
              <DialogFooter className="flex-col sm:flex-row gap-2">
                <Button variant="outline" onClick={copyWhatsAppMessage} className="flex-1">
                  <Copy className="h-4 w-4 mr-2" /> Copy Message
                </Button>
                <Button onClick={openWhatsApp} className="bg-green-600 hover:bg-green-700 flex-1">
                  <ExternalLink className="h-4 w-4 mr-2" /> Open WhatsApp
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DocumentActions;
