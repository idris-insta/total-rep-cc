"""
PDF Generator API Tests
Tests for Invoice and Quotation PDF generation endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('VITE_BACKEND_URL', 'https://postgres-frontend-v1.preview.emergentagent.com')


class TestPDFGenerator:
    """PDF Generator endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get an invoice ID for testing
        invoices_response = self.session.get(f"{BASE_URL}/api/accounts/invoices?limit=1")
        if invoices_response.status_code == 200 and invoices_response.json():
            self.invoice_id = invoices_response.json()[0].get("id")
        else:
            self.invoice_id = None
            
        # Get a quotation ID for testing
        quotations_response = self.session.get(f"{BASE_URL}/api/crm/quotations?limit=1")
        if quotations_response.status_code == 200 and quotations_response.json():
            self.quotation_id = quotations_response.json()[0].get("id")
        else:
            self.quotation_id = None
    
    # ==================== Invoice PDF Tests ====================
    
    def test_invoice_pdf_download_success(self):
        """Test invoice PDF download endpoint returns valid PDF"""
        if not self.invoice_id:
            pytest.skip("No invoice available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pdf/invoice/{self.invoice_id}/pdf")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Content-Type assertion
        assert "application/pdf" in response.headers.get("Content-Type", ""), \
            f"Expected application/pdf, got {response.headers.get('Content-Type')}"
        
        # Content-Disposition should be attachment for download
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition, \
            f"Expected attachment disposition, got {content_disposition}"
        
        # PDF should have content
        assert len(response.content) > 0, "PDF content is empty"
        
        # PDF should start with %PDF header
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF"
        
        print(f"Invoice PDF download successful: {len(response.content)} bytes")
    
    def test_invoice_pdf_preview_success(self):
        """Test invoice PDF preview endpoint returns valid PDF with inline disposition"""
        if not self.invoice_id:
            pytest.skip("No invoice available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pdf/invoice/{self.invoice_id}/preview")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Content-Type assertion
        assert "application/pdf" in response.headers.get("Content-Type", ""), \
            f"Expected application/pdf, got {response.headers.get('Content-Type')}"
        
        # Content-Disposition should be inline for preview
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "inline" in content_disposition, \
            f"Expected inline disposition, got {content_disposition}"
        
        # PDF should have content
        assert len(response.content) > 0, "PDF content is empty"
        
        # PDF should start with %PDF header
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF"
        
        print(f"Invoice PDF preview successful: {len(response.content)} bytes")
    
    def test_invoice_pdf_not_found(self):
        """Test invoice PDF endpoint returns 404 for non-existent invoice"""
        response = self.session.get(f"{BASE_URL}/api/pdf/invoice/non-existent-id/pdf")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Expected error detail in response"
        print(f"Invoice not found handled correctly: {data}")
    
    def test_invoice_pdf_unauthorized(self):
        """Test invoice PDF endpoint requires authentication"""
        # Create new session without auth
        unauth_session = requests.Session()
        response = unauth_session.get(f"{BASE_URL}/api/pdf/invoice/{self.invoice_id}/pdf")
        
        assert response.status_code in [401, 403], \
            f"Expected 401/403 for unauthorized, got {response.status_code}"
        print("Invoice PDF unauthorized access handled correctly")
    
    # ==================== Quotation PDF Tests ====================
    
    def test_quotation_pdf_download_success(self):
        """Test quotation PDF download endpoint returns valid PDF"""
        if not self.quotation_id:
            pytest.skip("No quotation available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pdf/quotation/{self.quotation_id}/pdf")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Content-Type assertion
        assert "application/pdf" in response.headers.get("Content-Type", ""), \
            f"Expected application/pdf, got {response.headers.get('Content-Type')}"
        
        # Content-Disposition should be attachment for download
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disposition, \
            f"Expected attachment disposition, got {content_disposition}"
        
        # PDF should have content
        assert len(response.content) > 0, "PDF content is empty"
        
        # PDF should start with %PDF header
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF"
        
        print(f"Quotation PDF download successful: {len(response.content)} bytes")
    
    def test_quotation_pdf_preview_success(self):
        """Test quotation PDF preview endpoint returns valid PDF with inline disposition"""
        if not self.quotation_id:
            pytest.skip("No quotation available for testing")
        
        response = self.session.get(f"{BASE_URL}/api/pdf/quotation/{self.quotation_id}/preview")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Content-Type assertion
        assert "application/pdf" in response.headers.get("Content-Type", ""), \
            f"Expected application/pdf, got {response.headers.get('Content-Type')}"
        
        # Content-Disposition should be inline for preview
        content_disposition = response.headers.get("Content-Disposition", "")
        assert "inline" in content_disposition, \
            f"Expected inline disposition, got {content_disposition}"
        
        # PDF should have content
        assert len(response.content) > 0, "PDF content is empty"
        
        # PDF should start with %PDF header
        assert response.content[:4] == b'%PDF', "Response is not a valid PDF"
        
        print(f"Quotation PDF preview successful: {len(response.content)} bytes")
    
    def test_quotation_pdf_not_found(self):
        """Test quotation PDF endpoint returns 404 for non-existent quotation"""
        response = self.session.get(f"{BASE_URL}/api/pdf/quotation/non-existent-id/pdf")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data, "Expected error detail in response"
        print(f"Quotation not found handled correctly: {data}")
    
    def test_quotation_pdf_unauthorized(self):
        """Test quotation PDF endpoint requires authentication"""
        # Create new session without auth
        unauth_session = requests.Session()
        response = unauth_session.get(f"{BASE_URL}/api/pdf/quotation/{self.quotation_id}/pdf")
        
        assert response.status_code in [401, 403], \
            f"Expected 401/403 for unauthorized, got {response.status_code}"
        print("Quotation PDF unauthorized access handled correctly")
