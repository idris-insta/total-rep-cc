"""
Test P1/P2 Features: Dynamic Form Rendering, Document Editor, PDF/Excel Exports
Tests custom fields API, document templates, and analytics export endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('VITE_BACKEND_URL', 'https://postgres-frontend-v1.preview.emergentagent.com')

class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@instabiz.com"


class TestCustomFields:
    """Custom Fields API tests for Dynamic Form Rendering"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_get_custom_fields_crm_leads(self, auth_token):
        """Test fetching custom fields for crm_leads module"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/custom-fields/fields/crm_leads", headers=headers)
        
        assert response.status_code == 200
        fields = response.json()
        assert isinstance(fields, list)
        
        # Check for expected custom fields
        field_names = [f.get("field_name") for f in fields]
        
        # Verify Industry field exists
        assert "industry" in field_names, "Industry custom field should exist"
        
        # Verify Annual Revenue field exists
        assert "annual_revenue" in field_names, "Annual Revenue custom field should exist"
        
        # Verify No. of Employees field exists
        assert "employee_count" in field_names, "Employee Count custom field should exist"
        
        # Verify field structure
        industry_field = next((f for f in fields if f.get("field_name") == "industry"), None)
        assert industry_field is not None
        assert industry_field.get("field_type") == "select"
        assert industry_field.get("field_label") == "Industry"
        assert "options" in industry_field
        assert len(industry_field["options"]) > 0
    
    def test_custom_fields_have_correct_types(self, auth_token):
        """Test that custom fields have correct field types"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/custom-fields/fields/crm_leads", headers=headers)
        
        assert response.status_code == 200
        fields = response.json()
        
        # Check field types
        for field in fields:
            if field.get("field_name") == "industry":
                assert field.get("field_type") == "select"
            elif field.get("field_name") == "annual_revenue":
                assert field.get("field_type") == "number"
            elif field.get("field_name") == "employee_count":
                assert field.get("field_type") == "select"
    
    def test_custom_fields_have_sections(self, auth_token):
        """Test that custom fields have section grouping"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/custom-fields/fields/crm_leads", headers=headers)
        
        assert response.status_code == 200
        fields = response.json()
        
        # Check that Business Info section exists
        sections = set(f.get("section") for f in fields if f.get("section"))
        assert "Business Info" in sections, "Business Info section should exist"


class TestDocumentTemplates:
    """Document Editor API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_get_document_templates(self, auth_token):
        """Test fetching document templates"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/documents/templates", headers=headers)
        
        # API may return empty list if no templates saved yet
        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)


class TestAnalyticsExports:
    """PDF and Excel Export API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_export_sales_pdf(self, auth_token):
        """Test PDF export for sales report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/export/pdf/sales?period=month",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
        assert len(response.content) > 0, "PDF content should not be empty"
    
    def test_export_sales_excel(self, auth_token):
        """Test Excel export for sales report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/export/excel/sales?period=month",
            headers=headers
        )
        
        assert response.status_code == 200
        assert "spreadsheet" in response.headers.get("content-type", "")
        assert len(response.content) > 0, "Excel content should not be empty"
    
    def test_export_inventory_pdf(self, auth_token):
        """Test PDF export for inventory report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/export/pdf/inventory?period=month",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
    
    def test_export_inventory_excel(self, auth_token):
        """Test Excel export for inventory report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/export/excel/inventory?period=month",
            headers=headers
        )
        
        assert response.status_code == 200
        assert "spreadsheet" in response.headers.get("content-type", "")
    
    def test_export_customers_pdf(self, auth_token):
        """Test PDF export for customers report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/export/pdf/customers?period=month",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"
    
    def test_export_customers_excel(self, auth_token):
        """Test Excel export for customers report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/export/excel/customers?period=month",
            headers=headers
        )
        
        assert response.status_code == 200
        assert "spreadsheet" in response.headers.get("content-type", "")
    
    def test_export_invalid_report_type(self, auth_token):
        """Test export with invalid report type returns 400"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/analytics/export/pdf/invalid_type",
            headers=headers
        )
        
        assert response.status_code == 400


class TestAnalyticsDashboard:
    """Analytics Dashboard API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_get_dashboard_kpis(self, auth_token):
        """Test fetching dashboard KPIs"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/dashboard/kpis", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify KPI fields exist
        assert "today_sales" in data
        assert "today_orders" in data
        assert "month_sales" in data
        assert "month_orders" in data
        assert "pending_pos" in data
        assert "low_stock_items" in data
    
    def test_get_sales_summary(self, auth_token):
        """Test fetching sales summary"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/sales/summary?period=month", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period" in data
        assert "current_period" in data
        assert "previous_period" in data
        assert "growth" in data
    
    def test_get_inventory_summary(self, auth_token):
        """Test fetching inventory summary"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/analytics/inventory/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_items" in data
        assert "total_stock_value" in data
        assert "low_stock_items" in data
        assert "out_of_stock_items" in data


class TestCRMLeads:
    """CRM Leads API tests with custom fields"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_get_leads_kanban(self, auth_token):
        """Test fetching leads in kanban view"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/crm/leads/kanban/view", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_get_leads_list(self, auth_token):
        """Test fetching leads list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/crm/leads", headers=headers)
        
        assert response.status_code == 200
        leads = response.json()
        assert isinstance(leads, list)
