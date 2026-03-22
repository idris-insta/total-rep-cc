"""
PostgreSQL Migration Backend Tests
Tests for verifying MongoDB to PostgreSQL migration is working correctly
Tests: Authentication, Dashboard, CRM Leads, Inventory Items, Legacy Routes
"""
import pytest
import requests
import os
import uuid

# Backend URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://postgres-frontend-v1.preview.emergentagent.com')
if BASE_URL.endswith('/'):
    BASE_URL = BASE_URL.rstrip('/')

# Test credentials
TEST_EMAIL = "admin@instabiz.com"
TEST_PASSWORD = "adminpassword"


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["email"] == TEST_EMAIL
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401


@pytest.fixture(scope="class")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="class") 
def auth_headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDashboard:
    """Test dashboard endpoints - verifies PostgreSQL connection and data retrieval"""
    
    def test_dashboard_overview(self, auth_headers):
        """Test /api/dashboard/overview returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/overview", headers=auth_headers)
        
        assert response.status_code == 200, f"Dashboard overview failed: {response.text}"
        data = response.json()
        
        # Verify response structure (actual structure from routes/dashboard.py)
        expected_sections = ["crm", "revenue", "inventory", "production", "hrms", "quality"]
        for section in expected_sections:
            assert section in data, f"Missing section '{section}' in dashboard response"
            
        # Verify CRM section
        assert "leads" in data["crm"]
        assert "quotations" in data["crm"]
        
        # Verify revenue section
        assert "total_billed" in data["revenue"]
        
        # Verify values are numbers
        assert isinstance(data["crm"]["leads"], (int, float))
        assert isinstance(data["revenue"]["total_billed"], (int, float))


class TestCRMLeadsV1:
    """Test CRM Leads v1 API - PostgreSQL layered architecture"""
    
    def test_get_leads_list(self, auth_headers):
        """Test GET /api/v1/crm/leads returns list of leads"""
        response = requests.get(f"{BASE_URL}/api/v1/crm/leads", headers=auth_headers)
        
        assert response.status_code == 200, f"Get leads failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
    def test_create_lead(self, auth_headers):
        """Test POST /api/v1/crm/leads creates a new lead"""
        unique_id = str(uuid.uuid4())[:8]
        lead_data = {
            "company_name": f"TEST_Company_{unique_id}",
            "contact_person": "Test Contact",
            "email": f"test_{unique_id}@example.com",
            "phone": "1234567890",
            "source": "website",
            "status": "new"
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/crm/leads", json=lead_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Create lead failed: {response.text}"
        data = response.json()
        
        # Verify created lead
        assert "id" in data, "No id in created lead"
        assert data["company_name"] == lead_data["company_name"]
        assert data["email"] == lead_data["email"]
        
    def test_get_lead_by_id(self, auth_headers):
        """Test GET /api/v1/crm/leads/{id} returns lead details"""
        # First create a lead
        unique_id = str(uuid.uuid4())[:8]
        lead_data = {
            "company_name": f"TEST_GetById_{unique_id}",
            "contact_person": "Test Person",
            "email": f"getbyid_{unique_id}@test.com",
            "phone": "9876543210",
            "source": "referral",
            "status": "new"
        }
        
        create_resp = requests.post(f"{BASE_URL}/api/v1/crm/leads", json=lead_data, headers=auth_headers)
        assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
        lead_id = create_resp.json()["id"]
        
        # Get the lead by ID
        get_resp = requests.get(f"{BASE_URL}/api/v1/crm/leads/{lead_id}", headers=auth_headers)
        assert get_resp.status_code == 200, f"Get lead by id failed: {get_resp.text}"
        
        data = get_resp.json()
        assert data["id"] == lead_id
        assert data["company_name"] == lead_data["company_name"]
        
    def test_update_lead(self, auth_headers):
        """Test PUT /api/v1/crm/leads/{id} updates lead"""
        # Create a lead
        unique_id = str(uuid.uuid4())[:8]
        lead_data = {
            "company_name": f"TEST_Update_{unique_id}",
            "contact_person": "Original Contact",
            "email": f"update_{unique_id}@test.com",
            "phone": "1111111111",
            "source": "email",
            "status": "new"
        }
        
        create_resp = requests.post(f"{BASE_URL}/api/v1/crm/leads", json=lead_data, headers=auth_headers)
        assert create_resp.status_code == 200
        lead_id = create_resp.json()["id"]
        
        # Update the lead
        update_data = {
            "contact_person": "Updated Contact",
            "status": "contacted"
        }
        
        update_resp = requests.put(f"{BASE_URL}/api/v1/crm/leads/{lead_id}", json=update_data, headers=auth_headers)
        assert update_resp.status_code == 200, f"Update failed: {update_resp.text}"
        
        updated_lead = update_resp.json()
        assert updated_lead["contact_person"] == "Updated Contact"
        assert updated_lead["status"] == "contacted"
        
    def test_delete_lead(self, auth_headers):
        """Test DELETE /api/v1/crm/leads/{id} deletes lead"""
        # Create a lead to delete
        unique_id = str(uuid.uuid4())[:8]
        lead_data = {
            "company_name": f"TEST_Delete_{unique_id}",
            "contact_person": "To Be Deleted",
            "email": f"delete_{unique_id}@test.com",
            "phone": "2222222222",
            "source": "website",
            "status": "new"
        }
        
        create_resp = requests.post(f"{BASE_URL}/api/v1/crm/leads", json=lead_data, headers=auth_headers)
        assert create_resp.status_code == 200
        lead_id = create_resp.json()["id"]
        
        # Delete the lead
        delete_resp = requests.delete(f"{BASE_URL}/api/v1/crm/leads/{lead_id}", headers=auth_headers)
        assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.text}"
        
        # Verify lead is deleted
        get_resp = requests.get(f"{BASE_URL}/api/v1/crm/leads/{lead_id}", headers=auth_headers)
        assert get_resp.status_code == 404, "Lead should be deleted"


class TestInventoryItemsV1:
    """Test Inventory Items v1 API - PostgreSQL layered architecture"""
    
    def test_get_items_list(self, auth_headers):
        """Test GET /api/v1/inventory/items returns list of items"""
        response = requests.get(f"{BASE_URL}/api/v1/inventory/items", headers=auth_headers)
        
        assert response.status_code == 200, f"Get items failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
    def test_create_item(self, auth_headers):
        """Test POST /api/v1/inventory/items creates a new item"""
        unique_id = str(uuid.uuid4())[:8]
        item_data = {
            "item_name": f"TEST_Item_{unique_id}",
            "item_code": f"ITM-{unique_id}",
            "category": "finished_goods",
            "item_type": "BOPP",
            "hsn_code": "3919",
            "primary_uom": "Pcs",
            "cost_price": 100.00,
            "reorder_level": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/inventory/items", json=item_data, headers=auth_headers)
        
        assert response.status_code == 200, f"Create item failed: {response.text}"
        data = response.json()
        
        # Verify created item
        assert "id" in data, "No id in created item"
        assert data["item_name"] == item_data["item_name"]
        assert data["item_code"] == item_data["item_code"]
        
    def test_get_item_by_id(self, auth_headers):
        """Test GET /api/v1/inventory/items/{id} returns item details"""
        # First create an item
        unique_id = str(uuid.uuid4())[:8]
        item_data = {
            "item_name": f"TEST_GetById_{unique_id}",
            "item_code": f"GET-{unique_id}",
            "category": "raw_material",
            "primary_uom": "Kg"
        }
        
        create_resp = requests.post(f"{BASE_URL}/api/v1/inventory/items", json=item_data, headers=auth_headers)
        assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
        item_id = create_resp.json()["id"]
        
        # Get the item by ID
        get_resp = requests.get(f"{BASE_URL}/api/v1/inventory/items/{item_id}", headers=auth_headers)
        assert get_resp.status_code == 200, f"Get item by id failed: {get_resp.text}"
        
        data = get_resp.json()
        assert data["id"] == item_id
        assert data["item_name"] == item_data["item_name"]


class TestLegacyCRMRoutes:
    """Test legacy CRM routes with PostgreSQL compatibility layer"""
    
    def test_legacy_get_leads(self, auth_headers):
        """Test GET /api/crm/leads (legacy route) works with PostgreSQL"""
        response = requests.get(f"{BASE_URL}/api/crm/leads", headers=auth_headers)
        
        assert response.status_code == 200, f"Legacy get leads failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
    def test_legacy_leads_kanban(self, auth_headers):
        """Test GET /api/crm/leads/kanban/view (legacy route) works"""
        response = requests.get(f"{BASE_URL}/api/crm/leads/kanban/view", headers=auth_headers)
        
        assert response.status_code == 200, f"Kanban view failed: {response.text}"
        data = response.json()
        
        # Verify kanban structure
        assert "columns" in data or "statuses" in data, "Missing kanban columns/statuses"


class TestDatabasePersistence:
    """Test that data is correctly persisted in PostgreSQL"""
    
    def test_lead_persistence_create_and_read(self, auth_headers):
        """Verify lead created via API is persisted and retrievable"""
        unique_id = str(uuid.uuid4())[:8]
        lead_data = {
            "company_name": f"TEST_Persistence_{unique_id}",
            "contact_person": "Persistence Test",
            "email": f"persist_{unique_id}@test.com",
            "phone": "3333333333",
            "source": "api_test",
            "status": "new",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        # Create lead
        create_resp = requests.post(f"{BASE_URL}/api/v1/crm/leads", json=lead_data, headers=auth_headers)
        assert create_resp.status_code == 200
        created = create_resp.json()
        lead_id = created["id"]
        
        # Read lead back to verify persistence
        get_resp = requests.get(f"{BASE_URL}/api/v1/crm/leads/{lead_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        
        fetched = get_resp.json()
        assert fetched["id"] == lead_id
        assert fetched["company_name"] == lead_data["company_name"]
        assert fetched["email"] == lead_data["email"]
        assert fetched["city"] == lead_data["city"]
        assert fetched["state"] == lead_data["state"]
        
    def test_lead_update_persistence(self, auth_headers):
        """Verify lead update is persisted"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create lead
        create_resp = requests.post(f"{BASE_URL}/api/v1/crm/leads", json={
            "company_name": f"TEST_UpdatePersist_{unique_id}",
            "email": f"updatepersist_{unique_id}@test.com",
            "phone": "4444444444",
            "source": "test",
            "status": "new"
        }, headers=auth_headers)
        assert create_resp.status_code == 200
        lead_id = create_resp.json()["id"]
        
        # Update lead
        update_resp = requests.put(f"{BASE_URL}/api/v1/crm/leads/{lead_id}", json={
            "status": "qualified",
            "estimated_value": 50000
        }, headers=auth_headers)
        assert update_resp.status_code == 200
        
        # Read back to verify persistence
        get_resp = requests.get(f"{BASE_URL}/api/v1/crm/leads/{lead_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        
        fetched = get_resp.json()
        assert fetched["status"] == "qualified"
        assert fetched.get("estimated_value") == 50000


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_leads(self, auth_headers):
        """Remove TEST_ prefixed leads created during testing"""
        # Get all leads
        response = requests.get(f"{BASE_URL}/api/v1/crm/leads", headers=auth_headers)
        if response.status_code == 200:
            leads = response.json()
            for lead in leads:
                if lead.get("company_name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/v1/crm/leads/{lead['id']}", headers=auth_headers)
        
        # Just pass - cleanup is best effort
        assert True
