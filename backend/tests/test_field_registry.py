"""
Field Registry API Tests
Tests for the Field Registry feature - metadata-driven field configuration system
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://postgres-frontend-v1.preview.emergentagent.com')


class TestFieldRegistryAuth:
    """Authentication tests for Field Registry endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_modules_endpoint_requires_auth(self):
        """Test that /modules endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/field-registry/modules")
        assert response.status_code == 403 or response.status_code == 401
    
    def test_config_endpoint_requires_auth(self):
        """Test that /config endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/field-registry/config/crm/leads")
        assert response.status_code == 403 or response.status_code == 401


class TestFieldRegistryModules:
    """Tests for /api/field-registry/modules endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_modules_returns_all_modules(self):
        """Test that /modules returns all 6 modules"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/modules")
        assert response.status_code == 200
        
        data = response.json()
        expected_modules = ["crm", "inventory", "accounts", "production", "procurement", "hrms"]
        
        for module in expected_modules:
            assert module in data, f"Module '{module}' not found in response"
    
    def test_crm_module_has_correct_entities(self):
        """Test that CRM module has correct entities"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/modules")
        assert response.status_code == 200
        
        data = response.json()
        crm_entities = data.get("crm", {}).get("entities", {})
        
        expected_entities = ["leads", "accounts", "quotations", "samples"]
        for entity in expected_entities:
            assert entity in crm_entities, f"Entity '{entity}' not found in CRM module"
    
    def test_modules_have_labels(self):
        """Test that all modules have labels"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/modules")
        assert response.status_code == 200
        
        data = response.json()
        for module_key, module_data in data.items():
            assert "label" in module_data, f"Module '{module_key}' missing label"
            assert "entities" in module_data, f"Module '{module_key}' missing entities"


class TestFieldRegistryLeadsConfig:
    """Tests for CRM Leads configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_leads_config_returns_correct_structure(self):
        """Test that leads config has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/leads")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("module") == "crm"
        assert data.get("entity") == "leads"
        assert "fields" in data
        assert "kanban_stages" in data
    
    def test_leads_has_9_kanban_stages(self):
        """Test that leads has exactly 9 Kanban stages"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/leads")
        assert response.status_code == 200
        
        data = response.json()
        stages = data.get("kanban_stages", [])
        assert len(stages) == 9, f"Expected 9 stages, got {len(stages)}"
        
        expected_stages = [
            "Hot Leads", "Cold Leads", "Contacted", "Qualified", 
            "Proposal", "Negotiation", "Converted", "Customer", "Lost"
        ]
        stage_labels = [s.get("label") for s in stages]
        for expected in expected_stages:
            assert expected in stage_labels, f"Stage '{expected}' not found"
    
    def test_leads_has_20_fields(self):
        """Test that leads has exactly 20 fields"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/leads")
        assert response.status_code == 200
        
        data = response.json()
        fields = data.get("fields", [])
        assert len(fields) == 20, f"Expected 20 fields, got {len(fields)}"
    
    def test_leads_fields_have_sections(self):
        """Test that leads fields are organized into sections"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/leads")
        assert response.status_code == 200
        
        data = response.json()
        fields = data.get("fields", [])
        
        sections = set(f.get("section") for f in fields)
        expected_sections = {"basic", "address", "classification", "followup"}
        
        for section in expected_sections:
            assert section in sections, f"Section '{section}' not found"
    
    def test_leads_required_fields(self):
        """Test that leads has correct required fields"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/leads")
        assert response.status_code == 200
        
        data = response.json()
        fields = data.get("fields", [])
        
        required_fields = [f for f in fields if f.get("is_required")]
        required_names = [f.get("field_name") for f in required_fields]
        
        assert "company_name" in required_names, "company_name should be required"
        assert "contact_person" in required_names, "contact_person should be required"
    
    def test_leads_source_field_has_options(self):
        """Test that source field has dropdown options"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/leads")
        assert response.status_code == 200
        
        data = response.json()
        fields = data.get("fields", [])
        
        source_field = next((f for f in fields if f.get("field_name") == "source"), None)
        assert source_field is not None, "Source field not found"
        assert source_field.get("field_type") == "select"
        
        options = source_field.get("options", [])
        assert len(options) >= 5, f"Expected at least 5 source options, got {len(options)}"


class TestFieldRegistryAccountsConfig:
    """Tests for CRM Accounts configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_accounts_config_returns_correct_structure(self):
        """Test that accounts config has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/accounts")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("module") == "crm"
        assert data.get("entity") == "accounts"
        assert "fields" in data
    
    def test_accounts_has_fields(self):
        """Test that accounts has fields configured"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/accounts")
        assert response.status_code == 200
        
        data = response.json()
        fields = data.get("fields", [])
        assert len(fields) > 0, "Accounts should have fields configured"


class TestFieldRegistryQuotationsConfig:
    """Tests for CRM Quotations configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_quotations_config_returns_correct_structure(self):
        """Test that quotations config has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/quotations")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("module") == "crm"
        assert data.get("entity") == "quotations"
        assert "fields" in data


class TestFieldRegistrySamplesConfig:
    """Tests for CRM Samples configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_samples_config_returns_correct_structure(self):
        """Test that samples config has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/samples")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("module") == "crm"
        assert data.get("entity") == "samples"
        assert "fields" in data


class TestFieldRegistryMasters:
    """Tests for /api/field-registry/masters endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_masters_endpoint_returns_list(self):
        """Test that /masters returns list of master types"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/masters")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_masters_have_required_fields(self):
        """Test that masters have type, label, and description"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/masters")
        assert response.status_code == 200
        
        data = response.json()
        for master in data:
            assert "type" in master
            assert "label" in master
            assert "description" in master


class TestFieldRegistrySaveConfig:
    """Tests for saving field configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_save_config_requires_admin_role(self):
        """Test that saving config requires admin role"""
        # First get the current config
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/leads")
        assert response.status_code == 200
        
        config = response.json()
        
        # Try to save (should work for admin)
        save_response = self.session.post(f"{BASE_URL}/api/field-registry/config", json=config)
        # Admin should be able to save
        assert save_response.status_code == 200, f"Save failed: {save_response.text}"
    
    def test_save_config_returns_success_message(self):
        """Test that saving config returns success message"""
        # Get current config
        response = self.session.get(f"{BASE_URL}/api/field-registry/config/crm/leads")
        assert response.status_code == 200
        
        config = response.json()
        
        # Save config
        save_response = self.session.post(f"{BASE_URL}/api/field-registry/config", json=config)
        assert save_response.status_code == 200
        
        data = save_response.json()
        assert "message" in data
        assert data.get("module") == "crm"
        assert data.get("entity") == "leads"


class TestFieldRegistryStages:
    """Tests for Kanban stages endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert login_response.status_code == 200
        self.token = login_response.json().get("token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_stages_for_leads(self):
        """Test getting Kanban stages for leads"""
        response = self.session.get(f"{BASE_URL}/api/field-registry/stages/crm/leads")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 9


class TestFieldRegistryNonAdminAccess:
    """Tests for non-admin access restrictions"""
    
    def test_non_admin_cannot_save_config(self):
        """Test that non-admin users cannot save configuration"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # First register a non-admin user
        register_response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": "TEST_viewer@test.com",
            "password": "testpassword",
            "name": "Test Viewer",
            "role": "viewer"
        })
        
        if register_response.status_code == 400:
            # User already exists, try to login
            login_response = session.post(f"{BASE_URL}/api/auth/login", json={
                "email": "TEST_viewer@test.com",
                "password": "testpassword"
            })
            if login_response.status_code != 200:
                pytest.skip("Could not create or login as non-admin user")
            token = login_response.json().get("token")
        else:
            assert register_response.status_code == 200
            token = register_response.json().get("token")
        
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Try to save config (should fail)
        config = {
            "module": "crm",
            "entity": "leads",
            "entity_label": "Leads",
            "fields": []
        }
        
        save_response = session.post(f"{BASE_URL}/api/field-registry/config", json=config)
        assert save_response.status_code == 403, "Non-admin should not be able to save config"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
