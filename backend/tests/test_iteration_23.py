"""
Iteration 23 - Comprehensive ERP Testing
Tests for:
- Authentication (Login)
- CRM Module (Leads, Accounts, Quotations, Samples)
- Inventory Module (Items, Warehouses, Stock)
- Production Module (Dashboard, Machines, Order Sheets, Work Orders)
- Field Registry (All 8 modules)
- DPR Reports
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://postgres-frontend-v1.preview.emergentagent.com')


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@instabiz.com",
        "password": "adminpassword"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == "admin@instabiz.com"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"


class TestCRMModule:
    """CRM Module tests - Leads, Accounts, Quotations, Samples"""
    
    def test_crm_leads_list(self, auth_headers):
        """Test CRM Leads list endpoint"""
        response = requests.get(f"{BASE_URL}/api/crm/leads", headers=auth_headers)
        assert response.status_code == 200, f"Leads list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Leads should return list"
    
    def test_crm_leads_kanban(self, auth_headers):
        """Test CRM Leads Kanban view"""
        response = requests.get(f"{BASE_URL}/api/crm/leads/kanban/view", headers=auth_headers)
        assert response.status_code == 200, f"Leads Kanban failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Kanban should return dict"
    
    def test_crm_leads_stats(self, auth_headers):
        """Test CRM Leads stats summary"""
        response = requests.get(f"{BASE_URL}/api/crm/leads/stats/summary", headers=auth_headers)
        assert response.status_code == 200, f"Leads stats failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Stats should return dict"
    
    def test_crm_accounts_list(self, auth_headers):
        """Test CRM Customer Accounts list"""
        response = requests.get(f"{BASE_URL}/api/crm/accounts", headers=auth_headers)
        assert response.status_code == 200, f"Accounts list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Accounts should return list"
    
    def test_crm_quotations_list(self, auth_headers):
        """Test CRM Quotations list"""
        response = requests.get(f"{BASE_URL}/api/crm/quotations", headers=auth_headers)
        assert response.status_code == 200, f"Quotations list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Quotations should return list"
    
    def test_crm_samples_list(self, auth_headers):
        """Test CRM Samples list"""
        response = requests.get(f"{BASE_URL}/api/crm/samples", headers=auth_headers)
        assert response.status_code == 200, f"Samples list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Samples should return list"
    
    def test_crm_followups_list(self, auth_headers):
        """Test CRM Followups list"""
        response = requests.get(f"{BASE_URL}/api/crm/followups", headers=auth_headers)
        assert response.status_code == 200, f"Followups list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Followups should return list"


class TestInventoryModule:
    """Inventory Module tests"""
    
    def test_inventory_items_list(self, auth_headers):
        """Test Inventory Items list"""
        response = requests.get(f"{BASE_URL}/api/inventory/items", headers=auth_headers)
        assert response.status_code == 200, f"Items list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Items should return list"
    
    def test_inventory_warehouses(self, auth_headers):
        """Test Inventory Warehouses list"""
        response = requests.get(f"{BASE_URL}/api/inventory/warehouses", headers=auth_headers)
        assert response.status_code == 200, f"Warehouses list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Warehouses should return list"
    
    def test_inventory_stock_balance(self, auth_headers):
        """Test Inventory Stock Balance"""
        response = requests.get(f"{BASE_URL}/api/inventory/stock/balance", headers=auth_headers)
        assert response.status_code == 200, f"Stock balance failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Stock balance should return list"
    
    def test_inventory_stats_overview(self, auth_headers):
        """Test Inventory Stats Overview"""
        response = requests.get(f"{BASE_URL}/api/inventory/stats/overview", headers=auth_headers)
        assert response.status_code == 200, f"Stats overview failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Stats should return dict"
    
    def test_inventory_transfers(self, auth_headers):
        """Test Inventory Transfers list"""
        response = requests.get(f"{BASE_URL}/api/inventory/transfers", headers=auth_headers)
        assert response.status_code == 200, f"Transfers list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Transfers should return list"


class TestProductionModule:
    """Production Module tests - 7-stage workflow"""
    
    def test_production_dashboard(self, auth_headers):
        """Test Production Control Center Dashboard"""
        response = requests.get(f"{BASE_URL}/api/production-stages/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Production Dashboard failed: {response.text}"
        data = response.json()
        assert "summary" in data, "Dashboard should have summary"
        assert "stages" in data, "Dashboard should have stages"
        # Verify 7 stages exist
        stages = data.get("stages", {})
        expected_stages = ['coating', 'slitting', 'rewinding', 'cutting', 'packing', 'ready_to_deliver', 'delivered']
        for stage in expected_stages:
            assert stage in stages, f"Missing stage: {stage}"
    
    def test_production_machines_list(self, auth_headers):
        """Test Production Machines list"""
        response = requests.get(f"{BASE_URL}/api/production-stages/machines", headers=auth_headers)
        assert response.status_code == 200, f"Machines list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Machines should return list"
    
    def test_production_order_sheets_list(self, auth_headers):
        """Test Production Order Sheets list"""
        response = requests.get(f"{BASE_URL}/api/production-stages/order-sheets", headers=auth_headers)
        assert response.status_code == 200, f"Order sheets list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Order sheets should return list"
    
    def test_production_work_orders_list(self, auth_headers):
        """Test Production Work Orders list"""
        response = requests.get(f"{BASE_URL}/api/production-stages/work-order-stages", headers=auth_headers)
        assert response.status_code == 200, f"Work orders list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Work orders should return list"
    
    def test_production_stage_dashboard_coating(self, auth_headers):
        """Test Coating stage dashboard"""
        response = requests.get(f"{BASE_URL}/api/production-stages/stages/coating/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Coating dashboard failed: {response.text}"
        data = response.json()
        assert data.get("stage") == "coating", "Stage should be coating"
    
    def test_production_stage_dashboard_slitting(self, auth_headers):
        """Test Slitting stage dashboard"""
        response = requests.get(f"{BASE_URL}/api/production-stages/stages/slitting/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Slitting dashboard failed: {response.text}"
        data = response.json()
        assert data.get("stage") == "slitting", "Stage should be slitting"
    
    def test_production_inventory_holds(self, auth_headers):
        """Test Production inventory holds (stock reservation)"""
        response = requests.get(f"{BASE_URL}/api/production-stages/inventory/holds", headers=auth_headers)
        assert response.status_code == 200, f"Inventory holds failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Holds should return list"
    
    def test_production_stock_status(self, auth_headers):
        """Test Production stock status"""
        response = requests.get(f"{BASE_URL}/api/production-stages/inventory/stock-status", headers=auth_headers)
        assert response.status_code == 200, f"Stock status failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Stock status should return list"
    
    def test_production_available_sales_orders(self, auth_headers):
        """Test available sales orders for order sheet creation"""
        response = requests.get(f"{BASE_URL}/api/production-stages/sales-orders/available", headers=auth_headers)
        assert response.status_code == 200, f"Available sales orders failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Sales orders should return list"


class TestFieldRegistry:
    """Field Registry tests - All 8 modules"""
    
    def test_field_registry_modules(self, auth_headers):
        """Test Field Registry modules list"""
        response = requests.get(f"{BASE_URL}/api/field-registry/modules", headers=auth_headers)
        assert response.status_code == 200, f"Modules list failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Modules should return dict"
        # Check for expected modules (accounts instead of finance)
        expected_modules = ['crm', 'inventory', 'production', 'accounts', 'procurement', 'quality', 'hrms', 'settings']
        for module in expected_modules:
            assert module in data, f"Missing module: {module}"
    
    def test_field_registry_crm_leads_config(self, auth_headers):
        """Test Field Registry config for CRM Leads"""
        response = requests.get(f"{BASE_URL}/api/field-registry/config/crm/leads", headers=auth_headers)
        assert response.status_code == 200, f"CRM Leads config failed: {response.text}"
        data = response.json()
        assert data.get("module") == "crm", "Module should be crm"
        assert data.get("entity") == "leads", "Entity should be leads"
        assert "fields" in data, "Config should have fields"
    
    def test_field_registry_crm_accounts_config(self, auth_headers):
        """Test Field Registry config for CRM Accounts"""
        response = requests.get(f"{BASE_URL}/api/field-registry/config/crm/accounts", headers=auth_headers)
        assert response.status_code == 200, f"CRM Accounts config failed: {response.text}"
        data = response.json()
        assert data.get("module") == "crm", "Module should be crm"
        assert data.get("entity") == "accounts", "Entity should be accounts"
    
    def test_field_registry_inventory_items_config(self, auth_headers):
        """Test Field Registry config for Inventory Items"""
        response = requests.get(f"{BASE_URL}/api/field-registry/config/inventory/items", headers=auth_headers)
        assert response.status_code == 200, f"Inventory Items config failed: {response.text}"
        data = response.json()
        assert data.get("module") == "inventory", "Module should be inventory"
    
    def test_field_registry_production_work_orders_config(self, auth_headers):
        """Test Field Registry config for Production Work Orders"""
        response = requests.get(f"{BASE_URL}/api/field-registry/config/production/work_orders", headers=auth_headers)
        assert response.status_code == 200, f"Production Work Orders config failed: {response.text}"
        data = response.json()
        assert data.get("module") == "production", "Module should be production"


class TestDPRReports:
    """DPR Reports tests"""
    
    def test_dpr_stage_wise_report(self, auth_headers):
        """Test DPR Stage-wise report"""
        response = requests.get(f"{BASE_URL}/api/production-stages/reports/stage-wise", headers=auth_headers)
        assert response.status_code == 200, f"Stage-wise report failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Report should return dict"
    
    def test_dpr_machine_wise_report(self, auth_headers):
        """Test DPR Machine-wise report"""
        response = requests.get(f"{BASE_URL}/api/production-stages/reports/machine-wise", headers=auth_headers)
        assert response.status_code == 200, f"Machine-wise report failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Report should return dict"
    
    def test_dpr_daily_report(self, auth_headers):
        """Test DPR Daily report - uses date-based endpoint"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/production-stages/dpr/{today}", headers=auth_headers)
        assert response.status_code == 200, f"Daily report failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Report should return dict"


class TestDashboard:
    """Dashboard tests"""
    
    def test_dashboard_overview(self, auth_headers):
        """Test Dashboard overview"""
        response = requests.get(f"{BASE_URL}/api/dashboard/overview", headers=auth_headers)
        assert response.status_code == 200, f"Dashboard overview failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Dashboard should return dict"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
