"""
Backend API Tests for Iteration 4 - Power Settings, Document Editor, Advanced Inventory
Tests: Custom Fields API, Document Templates API, Notification API, Dashboard API
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["token"]
    
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


class TestCustomFieldsAPI:
    """Custom Fields API tests for Power Settings"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_get_modules_returns_12(self, auth_token):
        """Test /api/custom-fields/modules returns 12 modules"""
        response = requests.get(
            f"{BASE_URL}/api/custom-fields/modules",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        modules = response.json()
        assert len(modules) == 12, f"Expected 12 modules, got {len(modules)}"
        
        # Verify expected modules exist
        module_ids = [m["id"] for m in modules]
        expected_modules = [
            "crm_leads", "crm_accounts", "crm_quotations",
            "inventory_items", "inventory_warehouses",
            "production_work_orders", "production_machines",
            "accounts_invoices", "accounts_payments",
            "hrms_employees", "procurement_suppliers", "procurement_purchase_orders"
        ]
        for expected in expected_modules:
            assert expected in module_ids, f"Missing module: {expected}"
    
    def test_get_fields_for_module(self, auth_token):
        """Test /api/custom-fields/fields/{module} returns fields"""
        response = requests.get(
            f"{BASE_URL}/api/custom-fields/fields/crm_leads",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        fields = response.json()
        assert isinstance(fields, list)
    
    def test_create_custom_field(self, auth_token):
        """Test creating a custom field"""
        response = requests.post(
            f"{BASE_URL}/api/custom-fields/fields",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "module": "crm_leads",
                "field_name": "test_field_iter4",
                "field_label": "Test Field Iter4",
                "field_type": "text",
                "is_required": False,
                "display_order": 99
            }
        )
        # May return 400 if field already exists, which is fine
        assert response.status_code in [200, 201, 400]
    
    def test_seed_defaults(self, auth_token):
        """Test seeding default fields"""
        response = requests.post(
            f"{BASE_URL}/api/custom-fields/seed-defaults",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestDocumentTemplatesAPI:
    """Document Templates API tests for Document Editor"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_get_templates(self, auth_token):
        """Test /api/documents/templates returns list"""
        response = requests.get(
            f"{BASE_URL}/api/documents/templates",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        templates = response.json()
        assert isinstance(templates, list)
    
    def test_save_template(self, auth_token):
        """Test saving a document template"""
        response = requests.post(
            f"{BASE_URL}/api/documents/templates",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Test Quotation Template",
                "type": "quotation",
                "elements": [
                    {"id": "1", "type": "text", "x": 50, "y": 30, "content": "QUOTATION"}
                ],
                "page_size": "A4",
                "orientation": "portrait"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "template_id" in data


class TestNotificationsAPI:
    """Notifications API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_get_notification_count(self, auth_token):
        """Test /api/notifications/notifications/count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/notifications/count",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "unread_count" in data
    
    def test_get_notifications(self, auth_token):
        """Test /api/notifications/notifications"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/notifications?limit=20",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        notifications = response.json()
        assert isinstance(notifications, list)
    
    def test_generate_alerts(self, auth_token):
        """Test /api/notifications/alerts/generate"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/alerts/generate",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestDashboardAPI:
    """Dashboard API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_dashboard_overview(self, auth_token):
        """Test /api/dashboard/overview"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/overview",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Check expected keys
        expected_keys = ["crm", "revenue", "inventory", "production", "hrms", "quality"]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"
    
    def test_revenue_analytics(self, auth_token):
        """Test /api/dashboard/revenue-analytics"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/revenue-analytics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # Response has period, total_revenue, daily_revenue, by_location
        assert "period" in data or "chart_data" in data
    
    def test_ai_insights(self, auth_token):
        """Test /api/dashboard/ai-insights"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/ai-insights",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "insights" in data


class TestAdvancedInventoryAPI:
    """Advanced Inventory API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_get_batches(self, auth_token):
        """Test /api/inventory-advanced/batches"""
        response = requests.get(
            f"{BASE_URL}/api/inventory-advanced/batches",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        batches = response.json()
        assert isinstance(batches, list)
    
    def test_get_bin_locations(self, auth_token):
        """Test /api/inventory-advanced/bin-locations"""
        response = requests.get(
            f"{BASE_URL}/api/inventory-advanced/bin-locations",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        bins = response.json()
        assert isinstance(bins, list)
    
    def test_get_reorder_alerts(self, auth_token):
        """Test /api/inventory-advanced/reorder-alerts"""
        response = requests.get(
            f"{BASE_URL}/api/inventory-advanced/reorder-alerts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
    
    def test_get_stock_aging(self, auth_token):
        """Test /api/inventory-advanced/stock-aging"""
        response = requests.get(
            f"{BASE_URL}/api/inventory-advanced/stock-aging",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_get_stock_valuation(self, auth_token):
        """Test /api/inventory-advanced/stock-valuation"""
        response = requests.get(
            f"{BASE_URL}/api/inventory-advanced/stock-valuation",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200


class TestCoreModulesAPI:
    """Core modules smoke tests - CRM, Inventory, Production, Accounts, HRMS"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        return response.json()["token"]
    
    def test_crm_leads(self, auth_token):
        """Test CRM leads endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/crm/leads",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_crm_accounts(self, auth_token):
        """Test CRM accounts (customers) endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/crm/accounts",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_inventory_items(self, auth_token):
        """Test inventory items endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/items",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_inventory_warehouses(self, auth_token):
        """Test inventory warehouses endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/inventory/warehouses",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_production_work_orders(self, auth_token):
        """Test production work orders endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/production/work-orders",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_accounts_invoices(self, auth_token):
        """Test accounts invoices endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/accounts/invoices",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_hrms_employees(self, auth_token):
        """Test HRMS employees endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/hrms/employees",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
    
    def test_procurement_suppliers(self, auth_token):
        """Test procurement suppliers endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/procurement/suppliers",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
