"""
Test PDF Generation for All Modules and Document Communication
Tests:
- PDF endpoints for work_order, delivery_challan, purchase_order, sample, payment
- Email send endpoint
- WhatsApp send endpoint
- Communication history endpoint
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('VITE_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@instabiz.com"
TEST_PASSWORD = "adminpassword"


class TestAuth:
    """Get authentication token for subsequent tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns 'token' not 'access_token'
        assert "token" in data, f"Expected 'token' in response: {data}"
        return data["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Return headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}


class TestPDFAllModules(TestAuth):
    """Test PDF generation for all document types"""
    
    # ==================== WORK ORDER PDF ====================
    def test_work_order_pdf_not_found(self, auth_headers):
        """Test work order PDF returns 404 for non-existent ID"""
        response = requests.get(
            f"{BASE_URL}/api/pdf/work-order/nonexistent-id/pdf",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Work Order PDF returns 404 for non-existent ID")
    
    def test_work_order_preview_not_found(self, auth_headers):
        """Test work order preview returns 404 for non-existent ID"""
        response = requests.get(
            f"{BASE_URL}/api/pdf/work-order/nonexistent-id/preview",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Work Order Preview returns 404 for non-existent ID")
    
    def test_work_order_pdf_unauthorized(self):
        """Test work order PDF requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pdf/work-order/test-id/pdf")
        assert response.status_code in [401, 403]
        print("PASS: Work Order PDF requires authentication")
    
    # ==================== DELIVERY CHALLAN PDF ====================
    def test_delivery_challan_pdf_not_found(self, auth_headers):
        """Test delivery challan PDF returns 404 for non-existent ID"""
        response = requests.get(
            f"{BASE_URL}/api/pdf/delivery-challan/nonexistent-id/pdf",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Delivery Challan PDF returns 404 for non-existent ID")
    
    def test_delivery_challan_preview_not_found(self, auth_headers):
        """Test delivery challan preview returns 404 for non-existent ID"""
        response = requests.get(
            f"{BASE_URL}/api/pdf/delivery-challan/nonexistent-id/preview",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Delivery Challan Preview returns 404 for non-existent ID")
    
    def test_delivery_challan_pdf_unauthorized(self):
        """Test delivery challan PDF requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pdf/delivery-challan/test-id/pdf")
        assert response.status_code in [401, 403]
        print("PASS: Delivery Challan PDF requires authentication")
    
    # ==================== PURCHASE ORDER PDF ====================
    def test_purchase_order_pdf_not_found(self, auth_headers):
        """Test purchase order PDF returns 404 for non-existent ID"""
        response = requests.get(
            f"{BASE_URL}/api/pdf/purchase-order/nonexistent-id/pdf",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Purchase Order PDF returns 404 for non-existent ID")
    
    def test_purchase_order_preview_not_found(self, auth_headers):
        """Test purchase order preview returns 404 for non-existent ID"""
        response = requests.get(
            f"{BASE_URL}/api/pdf/purchase-order/nonexistent-id/preview",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Purchase Order Preview returns 404 for non-existent ID")
    
    def test_purchase_order_pdf_unauthorized(self):
        """Test purchase order PDF requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pdf/purchase-order/test-id/pdf")
        assert response.status_code in [401, 403]
        print("PASS: Purchase Order PDF requires authentication")
    
    # ==================== SAMPLE PDF ====================
    def test_sample_pdf_not_found(self, auth_headers):
        """Test sample PDF returns 404 for non-existent ID"""
        response = requests.get(
            f"{BASE_URL}/api/pdf/sample/nonexistent-id/pdf",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Sample PDF returns 404 for non-existent ID")
    
    def test_sample_preview_not_found(self, auth_headers):
        """Test sample preview returns 404 for non-existent ID"""
        response = requests.get(
            f"{BASE_URL}/api/pdf/sample/nonexistent-id/preview",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Sample Preview returns 404 for non-existent ID")
    
    def test_sample_pdf_unauthorized(self):
        """Test sample PDF requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pdf/sample/test-id/pdf")
        assert response.status_code in [401, 403]
        print("PASS: Sample PDF requires authentication")
    
    # ==================== PAYMENT PDF ====================
    def test_payment_pdf_not_found(self, auth_headers):
        """Test payment PDF returns 404 for non-existent ID"""
        response = requests.get(
            f"{BASE_URL}/api/pdf/payment/nonexistent-id/pdf",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Payment PDF returns 404 for non-existent ID")
    
    def test_payment_preview_not_found(self, auth_headers):
        """Test payment preview returns 404 for non-existent ID"""
        response = requests.get(
            f"{BASE_URL}/api/pdf/payment/nonexistent-id/preview",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("PASS: Payment Preview returns 404 for non-existent ID")
    
    def test_payment_pdf_unauthorized(self):
        """Test payment PDF requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pdf/payment/test-id/pdf")
        assert response.status_code in [401, 403]
        print("PASS: Payment PDF requires authentication")


class TestDocumentCommunication(TestAuth):
    """Test Document Communication endpoints (Email & WhatsApp)"""
    
    # ==================== EMAIL ENDPOINTS ====================
    def test_email_send_invalid_document_type(self, auth_headers):
        """Test email send with invalid document type"""
        response = requests.post(
            f"{BASE_URL}/api/communicate/email/send",
            headers=auth_headers,
            json={
                "document_type": "invalid_type",
                "document_id": "test-id",
                "recipient_email": "test@example.com"
            }
        )
        assert response.status_code == 400
        print("PASS: Email send returns 400 for invalid document type")
    
    def test_email_send_document_not_found(self, auth_headers):
        """Test email send with non-existent document"""
        response = requests.post(
            f"{BASE_URL}/api/communicate/email/send",
            headers=auth_headers,
            json={
                "document_type": "invoice",
                "document_id": "nonexistent-id",
                "recipient_email": "test@example.com"
            }
        )
        assert response.status_code == 404
        print("PASS: Email send returns 404 for non-existent document")
    
    def test_email_send_unauthorized(self):
        """Test email send requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/communicate/email/send",
            json={
                "document_type": "invoice",
                "document_id": "test-id",
                "recipient_email": "test@example.com"
            }
        )
        assert response.status_code in [401, 403]
        print("PASS: Email send requires authentication")
    
    def test_email_preview_invalid_document_type(self, auth_headers):
        """Test email preview with invalid document type"""
        response = requests.post(
            f"{BASE_URL}/api/communicate/email/preview",
            headers=auth_headers,
            json={
                "document_type": "invalid_type",
                "document_id": "test-id",
                "recipient_email": "test@example.com"
            }
        )
        assert response.status_code == 400
        print("PASS: Email preview returns 400 for invalid document type")
    
    # ==================== WHATSAPP ENDPOINTS ====================
    def test_whatsapp_send_invalid_document_type(self, auth_headers):
        """Test WhatsApp send with invalid document type"""
        response = requests.post(
            f"{BASE_URL}/api/communicate/whatsapp/send",
            headers=auth_headers,
            json={
                "document_type": "invalid_type",
                "document_id": "test-id",
                "recipient_phone": "9876543210"
            }
        )
        assert response.status_code == 400
        print("PASS: WhatsApp send returns 400 for invalid document type")
    
    def test_whatsapp_send_document_not_found(self, auth_headers):
        """Test WhatsApp send with non-existent document"""
        response = requests.post(
            f"{BASE_URL}/api/communicate/whatsapp/send",
            headers=auth_headers,
            json={
                "document_type": "invoice",
                "document_id": "nonexistent-id",
                "recipient_phone": "9876543210"
            }
        )
        assert response.status_code == 404
        print("PASS: WhatsApp send returns 404 for non-existent document")
    
    def test_whatsapp_send_unauthorized(self):
        """Test WhatsApp send requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/communicate/whatsapp/send",
            json={
                "document_type": "invoice",
                "document_id": "test-id",
                "recipient_phone": "9876543210"
            }
        )
        assert response.status_code in [401, 403]
        print("PASS: WhatsApp send requires authentication")
    
    def test_whatsapp_preview_invalid_document_type(self, auth_headers):
        """Test WhatsApp preview with invalid document type"""
        response = requests.post(
            f"{BASE_URL}/api/communicate/whatsapp/preview",
            headers=auth_headers,
            json={
                "document_type": "invalid_type",
                "document_id": "test-id",
                "recipient_phone": "9876543210"
            }
        )
        assert response.status_code == 400
        print("PASS: WhatsApp preview returns 400 for invalid document type")
    
    # ==================== COMMUNICATION HISTORY ====================
    def test_communication_history_list(self, auth_headers):
        """Test communication history endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/communicate/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Communication history returns list with {len(data)} items")
    
    def test_communication_history_with_filters(self, auth_headers):
        """Test communication history with filters"""
        response = requests.get(
            f"{BASE_URL}/api/communicate/history?document_type=invoice&channel=email&limit=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Communication history with filters returns list")
    
    def test_communication_history_unauthorized(self):
        """Test communication history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/communicate/history")
        assert response.status_code in [401, 403]
        print("PASS: Communication history requires authentication")
    
    def test_document_communication_history(self, auth_headers):
        """Test document-specific communication history"""
        response = requests.get(
            f"{BASE_URL}/api/communicate/history/invoice/test-id",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "document_type" in data
        assert "document_id" in data
        assert "communications" in data
        print("PASS: Document communication history returns correct structure")


class TestPDFWithExistingData(TestAuth):
    """Test PDF generation with existing data from database"""
    
    def test_get_existing_invoice_for_pdf(self, auth_headers):
        """Get an existing invoice to test PDF generation"""
        # First get list of invoices
        response = requests.get(
            f"{BASE_URL}/api/accounts/invoices?limit=1",
            headers=auth_headers
        )
        assert response.status_code == 200
        invoices = response.json()
        
        if invoices and len(invoices) > 0:
            invoice_id = invoices[0].get("id")
            # Test PDF download
            pdf_response = requests.get(
                f"{BASE_URL}/api/pdf/invoice/{invoice_id}/pdf",
                headers=auth_headers
            )
            assert pdf_response.status_code == 200
            assert pdf_response.headers.get("content-type") == "application/pdf"
            assert b"%PDF" in pdf_response.content[:10]
            print(f"PASS: Invoice PDF generated successfully for {invoice_id}")
        else:
            pytest.skip("No invoices found in database")
    
    def test_get_existing_quotation_for_pdf(self, auth_headers):
        """Get an existing quotation to test PDF generation"""
        response = requests.get(
            f"{BASE_URL}/api/crm/quotations?limit=1",
            headers=auth_headers
        )
        assert response.status_code == 200
        quotations = response.json()
        
        if quotations and len(quotations) > 0:
            quote_id = quotations[0].get("id")
            pdf_response = requests.get(
                f"{BASE_URL}/api/pdf/quotation/{quote_id}/pdf",
                headers=auth_headers
            )
            assert pdf_response.status_code == 200
            assert pdf_response.headers.get("content-type") == "application/pdf"
            assert b"%PDF" in pdf_response.content[:10]
            print(f"PASS: Quotation PDF generated successfully for {quote_id}")
        else:
            pytest.skip("No quotations found in database")
    
    def test_get_existing_work_order_for_pdf(self, auth_headers):
        """Get an existing work order to test PDF generation"""
        response = requests.get(
            f"{BASE_URL}/api/production/work-orders?limit=1",
            headers=auth_headers
        )
        assert response.status_code == 200
        work_orders = response.json()
        
        if work_orders and len(work_orders) > 0:
            wo_id = work_orders[0].get("id")
            pdf_response = requests.get(
                f"{BASE_URL}/api/pdf/work-order/{wo_id}/pdf",
                headers=auth_headers
            )
            assert pdf_response.status_code == 200
            assert pdf_response.headers.get("content-type") == "application/pdf"
            assert b"%PDF" in pdf_response.content[:10]
            print(f"PASS: Work Order PDF generated successfully for {wo_id}")
        else:
            pytest.skip("No work orders found in database")
    
    def test_get_existing_purchase_order_for_pdf(self, auth_headers):
        """Get an existing purchase order to test PDF generation"""
        response = requests.get(
            f"{BASE_URL}/api/procurement/purchase-orders?limit=1",
            headers=auth_headers
        )
        assert response.status_code == 200
        pos = response.json()
        
        if pos and len(pos) > 0:
            po_id = pos[0].get("id")
            pdf_response = requests.get(
                f"{BASE_URL}/api/pdf/purchase-order/{po_id}/pdf",
                headers=auth_headers
            )
            assert pdf_response.status_code == 200
            assert pdf_response.headers.get("content-type") == "application/pdf"
            assert b"%PDF" in pdf_response.content[:10]
            print(f"PASS: Purchase Order PDF generated successfully for {po_id}")
        else:
            pytest.skip("No purchase orders found in database")
    
    def test_get_existing_payment_for_pdf(self, auth_headers):
        """Get an existing payment to test PDF generation"""
        response = requests.get(
            f"{BASE_URL}/api/accounts/payments?limit=1",
            headers=auth_headers
        )
        assert response.status_code == 200
        payments = response.json()
        
        if payments and len(payments) > 0:
            payment_id = payments[0].get("id")
            pdf_response = requests.get(
                f"{BASE_URL}/api/pdf/payment/{payment_id}/pdf",
                headers=auth_headers
            )
            assert pdf_response.status_code == 200
            assert pdf_response.headers.get("content-type") == "application/pdf"
            assert b"%PDF" in pdf_response.content[:10]
            print(f"PASS: Payment PDF generated successfully for {payment_id}")
        else:
            pytest.skip("No payments found in database")


class TestEmailSendWithExistingData(TestAuth):
    """Test email send with existing documents"""
    
    def test_email_send_existing_invoice(self, auth_headers):
        """Test email send with existing invoice"""
        # Get an invoice
        response = requests.get(
            f"{BASE_URL}/api/accounts/invoices?limit=1",
            headers=auth_headers
        )
        invoices = response.json()
        
        if invoices and len(invoices) > 0:
            invoice_id = invoices[0].get("id")
            email_response = requests.post(
                f"{BASE_URL}/api/communicate/email/send",
                headers=auth_headers,
                json={
                    "document_type": "invoice",
                    "document_id": invoice_id,
                    "recipient_email": "test@example.com",
                    "recipient_name": "Test Customer"
                }
            )
            assert email_response.status_code == 200
            data = email_response.json()
            assert data.get("success") == True
            assert "log_id" in data
            print(f"PASS: Email sent for invoice {invoice_id}")
        else:
            pytest.skip("No invoices found")
    
    def test_email_send_existing_quotation(self, auth_headers):
        """Test email send with existing quotation"""
        response = requests.get(
            f"{BASE_URL}/api/crm/quotations?limit=1",
            headers=auth_headers
        )
        quotations = response.json()
        
        if quotations and len(quotations) > 0:
            quote_id = quotations[0].get("id")
            email_response = requests.post(
                f"{BASE_URL}/api/communicate/email/send",
                headers=auth_headers,
                json={
                    "document_type": "quotation",
                    "document_id": quote_id,
                    "recipient_email": "test@example.com",
                    "recipient_name": "Test Customer"
                }
            )
            assert email_response.status_code == 200
            data = email_response.json()
            assert data.get("success") == True
            print(f"PASS: Email sent for quotation {quote_id}")
        else:
            pytest.skip("No quotations found")


class TestWhatsAppSendWithExistingData(TestAuth):
    """Test WhatsApp send with existing documents"""
    
    def test_whatsapp_send_existing_invoice(self, auth_headers):
        """Test WhatsApp send with existing invoice"""
        response = requests.get(
            f"{BASE_URL}/api/accounts/invoices?limit=1",
            headers=auth_headers
        )
        invoices = response.json()
        
        if invoices and len(invoices) > 0:
            invoice_id = invoices[0].get("id")
            wa_response = requests.post(
                f"{BASE_URL}/api/communicate/whatsapp/send",
                headers=auth_headers,
                json={
                    "document_type": "invoice",
                    "document_id": invoice_id,
                    "recipient_phone": "9876543210",
                    "recipient_name": "Test Customer"
                }
            )
            assert wa_response.status_code == 200
            data = wa_response.json()
            assert data.get("success") == True
            assert "whatsapp_url" in data
            assert "wa.me" in data["whatsapp_url"]
            print(f"PASS: WhatsApp message generated for invoice {invoice_id}")
        else:
            pytest.skip("No invoices found")
    
    def test_whatsapp_send_existing_quotation(self, auth_headers):
        """Test WhatsApp send with existing quotation"""
        response = requests.get(
            f"{BASE_URL}/api/crm/quotations?limit=1",
            headers=auth_headers
        )
        quotations = response.json()
        
        if quotations and len(quotations) > 0:
            quote_id = quotations[0].get("id")
            wa_response = requests.post(
                f"{BASE_URL}/api/communicate/whatsapp/send",
                headers=auth_headers,
                json={
                    "document_type": "quotation",
                    "document_id": quote_id,
                    "recipient_phone": "9876543210",
                    "recipient_name": "Test Customer"
                }
            )
            assert wa_response.status_code == 200
            data = wa_response.json()
            assert data.get("success") == True
            assert "whatsapp_url" in data
            print(f"PASS: WhatsApp message generated for quotation {quote_id}")
        else:
            pytest.skip("No quotations found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
