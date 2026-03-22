"""
Test Suite for v1 Layered Architecture APIs
Tests CRM, Inventory, and Production modules with Repository -> Service -> API layers

Test Categories:
- CRM Module: Leads, Accounts, Quotations, Samples
- Inventory Module: Items, Warehouses, Transfers, Adjustments
- Production Module: Machines, Order Sheets, Work Orders
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('VITE_BACKEND_URL', '').rstrip('/')
AUTH_TOKEN = None


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for all tests"""
    global AUTH_TOKEN
    if AUTH_TOKEN:
        return AUTH_TOKEN
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@instabiz.com", "password": "adminpassword"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    AUTH_TOKEN = response.json()['token']
    return AUTH_TOKEN


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@instabiz.com", "password": "adminpassword"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@instabiz.com"
        print("✓ Login success test passed")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print("✓ Login invalid credentials test passed")


class TestCRMLeadsV1:
    """Tests for v1 CRM Leads API"""
    
    def test_get_leads(self, api_client):
        """GET /api/v1/crm/leads - returns list of leads"""
        response = api_client.get(f"{BASE_URL}/api/v1/crm/leads")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/crm/leads returned {len(data)} leads")
    
    def test_get_leads_kanban_view(self, api_client):
        """GET /api/v1/crm/leads/kanban/view - returns kanban stages and leads"""
        response = api_client.get(f"{BASE_URL}/api/v1/crm/leads/kanban/view")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "stages" in data, "Expected 'stages' key in response"
        assert "leads" in data, "Expected 'leads' key in response"
        assert isinstance(data["stages"], list), "Expected stages to be a list"
        print(f"✓ GET /api/v1/crm/leads/kanban/view returned {len(data['stages'])} stages")
    
    def test_get_leads_with_filter(self, api_client):
        """GET /api/v1/crm/leads with status filter"""
        response = api_client.get(f"{BASE_URL}/api/v1/crm/leads?status=new")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/crm/leads with filter returned {len(data)} leads")


class TestCRMAccountsV1:
    """Tests for v1 CRM Accounts API"""
    
    def test_get_accounts(self, api_client):
        """GET /api/v1/crm/accounts - returns list of accounts"""
        response = api_client.get(f"{BASE_URL}/api/v1/crm/accounts")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/crm/accounts returned {len(data)} accounts")
    
    def test_get_accounts_with_type_filter(self, api_client):
        """GET /api/v1/crm/accounts with account_type filter"""
        response = api_client.get(f"{BASE_URL}/api/v1/crm/accounts?account_type=customer")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/crm/accounts with type filter returned {len(data)} accounts")


class TestCRMQuotationsV1:
    """Tests for v1 CRM Quotations API"""
    
    def test_get_quotations(self, api_client):
        """GET /api/v1/crm/quotations - returns list of quotations"""
        response = api_client.get(f"{BASE_URL}/api/v1/crm/quotations")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/crm/quotations returned {len(data)} quotations")


class TestCRMSamplesV1:
    """Tests for v1 CRM Samples API"""
    
    def test_get_samples(self, api_client):
        """GET /api/v1/crm/samples - returns list of samples"""
        response = api_client.get(f"{BASE_URL}/api/v1/crm/samples")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/crm/samples returned {len(data)} samples")


class TestInventoryItemsV1:
    """Tests for v1 Inventory Items API"""
    
    def test_get_items(self, api_client):
        """GET /api/v1/inventory/items - returns list of items"""
        response = api_client.get(f"{BASE_URL}/api/v1/inventory/items")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/inventory/items returned {len(data)} items")
    
    def test_get_low_stock_items(self, api_client):
        """GET /api/v1/inventory/items/low-stock"""
        response = api_client.get(f"{BASE_URL}/api/v1/inventory/items/low-stock")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/inventory/items/low-stock returned {len(data)} items")


class TestInventoryWarehousesV1:
    """Tests for v1 Inventory Warehouses API"""
    
    def test_get_warehouses(self, api_client):
        """GET /api/v1/inventory/warehouses - returns list of warehouses"""
        response = api_client.get(f"{BASE_URL}/api/v1/inventory/warehouses")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/inventory/warehouses returned {len(data)} warehouses")


class TestInventoryTransfersV1:
    """Tests for v1 Inventory Transfers API"""
    
    def test_get_transfers(self, api_client):
        """GET /api/v1/inventory/transfers - returns list of transfers"""
        response = api_client.get(f"{BASE_URL}/api/v1/inventory/transfers")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/inventory/transfers returned {len(data)} transfers")


class TestInventoryAdjustmentsV1:
    """Tests for v1 Inventory Adjustments API"""
    
    def test_get_adjustments(self, api_client):
        """GET /api/v1/inventory/adjustments - returns list of adjustments"""
        response = api_client.get(f"{BASE_URL}/api/v1/inventory/adjustments")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/inventory/adjustments returned {len(data)} adjustments")
    
    def test_get_pending_adjustments(self, api_client):
        """GET /api/v1/inventory/adjustments/pending"""
        response = api_client.get(f"{BASE_URL}/api/v1/inventory/adjustments/pending")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/inventory/adjustments/pending returned {len(data)} adjustments")


class TestProductionMachinesV1:
    """Tests for v1 Production Machines API"""
    
    def test_get_machines(self, api_client):
        """GET /api/v1/production/machines - returns list of machines"""
        response = api_client.get(f"{BASE_URL}/api/v1/production/machines")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/production/machines returned {len(data)} machines")
    
    def test_get_available_machines(self, api_client):
        """GET /api/v1/production/machines/available"""
        response = api_client.get(f"{BASE_URL}/api/v1/production/machines/available")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/production/machines/available returned {len(data)} machines")


class TestProductionOrderSheetsV1:
    """Tests for v1 Production Order Sheets API"""
    
    def test_get_order_sheets(self, api_client):
        """GET /api/v1/production/order-sheets - returns list of order sheets"""
        response = api_client.get(f"{BASE_URL}/api/v1/production/order-sheets")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/production/order-sheets returned {len(data)} order sheets")
    
    def test_get_pending_order_sheets(self, api_client):
        """GET /api/v1/production/order-sheets/pending"""
        response = api_client.get(f"{BASE_URL}/api/v1/production/order-sheets/pending")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/production/order-sheets/pending returned {len(data)} order sheets")


class TestProductionWorkOrdersV1:
    """Tests for v1 Production Work Orders API"""
    
    def test_get_work_orders(self, api_client):
        """GET /api/v1/production/work-orders - returns list of work orders"""
        response = api_client.get(f"{BASE_URL}/api/v1/production/work-orders")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        print(f"✓ GET /api/v1/production/work-orders returned {len(data)} work orders")
    
    def test_get_in_progress_work_orders(self, api_client):
        """GET /api/v1/production/work-orders/in-progress"""
        response = api_client.get(f"{BASE_URL}/api/v1/production/work-orders/in-progress")
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/v1/production/work-orders/in-progress returned {len(data)} work orders")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
