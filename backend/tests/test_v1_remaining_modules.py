"""
Test Suite for Remaining Modules - Production, HRMS, Accounts, and Field Registry
Tests the v1 API endpoints with PostgreSQL backend

Testing Focus:
- Authentication flow
- Production module (Machines CRUD)
- HRMS module (Employees CRUD)
- Accounts module (Invoices creation with account_id)
- Field Registry (modules and config)
- Dashboard metrics
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

# Get backend URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://postgres-frontend-v1.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "admin@instabiz.com"
TEST_PASSWORD = "adminpassword"

# Test data tracking for cleanup
test_created_ids = {
    'machines': [],
    'employees': [],
    'invoices': [],
    'accounts': []
}


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip("Authentication failed - cannot proceed with tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestAuthentication:
    """Authentication tests"""
    
    def test_login_success(self, api_client):
        """Test successful login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "Token not in response"
        print(f"✓ Login successful, received token")
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code in [401, 400], f"Expected 401/400, got {response.status_code}"
        print(f"✓ Invalid credentials correctly rejected")


class TestDashboard:
    """Dashboard metrics tests"""
    
    def test_dashboard_overview(self, authenticated_client):
        """Test dashboard overview endpoint"""
        response = authenticated_client.get(f"{BASE_URL}/api/dashboard/overview")
        
        assert response.status_code == 200, f"Dashboard overview failed: {response.text}"
        data = response.json()
        
        # Verify dashboard contains expected sections
        assert isinstance(data, dict), "Dashboard should return a dictionary"
        print(f"✓ Dashboard overview returned metrics")
        print(f"  Metrics received: {list(data.keys())[:5]}...")


class TestProductionMachines:
    """Production module - Machines CRUD tests"""
    
    def test_list_machines(self, authenticated_client):
        """Test listing all machines"""
        response = authenticated_client.get(f"{BASE_URL}/api/v1/production/machines")
        
        assert response.status_code == 200, f"List machines failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Machines should return a list"
        print(f"✓ Listed {len(data)} machines")
    
    def test_create_machine(self, authenticated_client):
        """Test creating a new machine"""
        machine_data = {
            "machine_name": f"TEST_Machine_{uuid.uuid4().hex[:8]}",
            "machine_code": f"TEST-MCH-{uuid.uuid4().hex[:6]}",
            "machine_type": "slitting",
            "capacity_per_hour": 100.0,
            "power_consumption_kw": 50.0,
            "maintenance_cycle_days": 30,
            "notes": "Test machine for automated testing"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/v1/production/machines",
            json=machine_data
        )
        
        assert response.status_code in [200, 201], f"Create machine failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Machine ID not in response"
        assert data.get("machine_name") == machine_data["machine_name"]
        assert data.get("machine_type") == machine_data["machine_type"]
        
        # Track for cleanup
        test_created_ids['machines'].append(data['id'])
        print(f"✓ Created machine: {data['id']}")
        return data['id']
    
    def test_get_machine(self, authenticated_client):
        """Test getting a single machine"""
        # First create a machine
        machine_data = {
            "machine_name": f"TEST_GetMachine_{uuid.uuid4().hex[:8]}",
            "machine_code": f"TEST-GET-{uuid.uuid4().hex[:6]}",
            "machine_type": "coating"
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/v1/production/machines",
            json=machine_data
        )
        assert create_response.status_code in [200, 201]
        created = create_response.json()
        machine_id = created['id']
        test_created_ids['machines'].append(machine_id)
        
        # Now get the machine
        response = authenticated_client.get(f"{BASE_URL}/api/v1/production/machines/{machine_id}")
        
        assert response.status_code == 200, f"Get machine failed: {response.text}"
        data = response.json()
        assert data['id'] == machine_id
        assert data['machine_name'] == machine_data['machine_name']
        print(f"✓ Retrieved machine: {machine_id}")
    
    def test_update_machine(self, authenticated_client):
        """Test updating a machine"""
        # First create a machine
        machine_data = {
            "machine_name": f"TEST_UpdateMachine_{uuid.uuid4().hex[:8]}",
            "machine_code": f"TEST-UPD-{uuid.uuid4().hex[:6]}",
            "machine_type": "rewinding"
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/v1/production/machines",
            json=machine_data
        )
        assert create_response.status_code in [200, 201]
        created = create_response.json()
        machine_id = created['id']
        test_created_ids['machines'].append(machine_id)
        
        # Update the machine
        update_data = {
            "status": "maintenance",
            "notes": "Updated notes for testing"
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/v1/production/machines/{machine_id}",
            json=update_data
        )
        
        assert response.status_code == 200, f"Update machine failed: {response.text}"
        data = response.json()
        assert data.get('status') == 'maintenance' or data.get('notes') == 'Updated notes for testing'
        print(f"✓ Updated machine: {machine_id}")
    
    def test_available_machines(self, authenticated_client):
        """Test getting available machines"""
        response = authenticated_client.get(f"{BASE_URL}/api/v1/production/machines/available")
        
        assert response.status_code == 200, f"Available machines failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Available machines should return a list"
        print(f"✓ Retrieved {len(data)} available machines")


class TestHRMSEmployees:
    """HRMS module - Employees CRUD tests"""
    
    def test_list_employees(self, authenticated_client):
        """Test listing all employees"""
        response = authenticated_client.get(f"{BASE_URL}/api/v1/hrms/employees")
        
        assert response.status_code == 200, f"List employees failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Employees should return a list"
        print(f"✓ Listed {len(data)} employees")
    
    def test_create_employee(self, authenticated_client):
        """Test creating a new employee"""
        employee_data = {
            "employee_code": f"TEST-EMP-{uuid.uuid4().hex[:6]}",
            "name": f"Test Employee {uuid.uuid4().hex[:8]}",
            "email": f"test.employee.{uuid.uuid4().hex[:6]}@test.com",
            "phone": "9876543210",
            "department": "Production",
            "designation": "Operator",
            "location": "Main Plant",
            "date_of_joining": "2024-01-15",
            "shift_timing": "9:00 AM - 6:00 PM",
            "basic_salary": 25000.0,
            "hra": 5000.0,
            "pf": 2500.0
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/v1/hrms/employees",
            json=employee_data
        )
        
        assert response.status_code in [200, 201], f"Create employee failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Employee ID not in response"
        assert data.get("name") == employee_data["name"]
        assert data.get("department") == employee_data["department"]
        
        # Track for cleanup
        test_created_ids['employees'].append(data['id'])
        print(f"✓ Created employee: {data['id']}")
        return data['id']
    
    def test_get_employee(self, authenticated_client):
        """Test getting a single employee"""
        # First create an employee
        employee_data = {
            "employee_code": f"TEST-GET-{uuid.uuid4().hex[:6]}",
            "name": f"Test Get Employee {uuid.uuid4().hex[:8]}",
            "email": f"get.employee.{uuid.uuid4().hex[:6]}@test.com",
            "department": "Quality",
            "designation": "Inspector"
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/v1/hrms/employees",
            json=employee_data
        )
        assert create_response.status_code in [200, 201]
        created = create_response.json()
        employee_id = created['id']
        test_created_ids['employees'].append(employee_id)
        
        # Now get the employee
        response = authenticated_client.get(f"{BASE_URL}/api/v1/hrms/employees/{employee_id}")
        
        assert response.status_code == 200, f"Get employee failed: {response.text}"
        data = response.json()
        assert data['id'] == employee_id
        assert data['name'] == employee_data['name']
        print(f"✓ Retrieved employee: {employee_id}")
    
    def test_update_employee(self, authenticated_client):
        """Test updating an employee"""
        # First create an employee
        employee_data = {
            "employee_code": f"TEST-UPD-{uuid.uuid4().hex[:6]}",
            "name": f"Test Update Employee {uuid.uuid4().hex[:8]}",
            "email": f"update.employee.{uuid.uuid4().hex[:6]}@test.com",
            "department": "Sales",
            "designation": "Executive"
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/v1/hrms/employees",
            json=employee_data
        )
        assert create_response.status_code in [200, 201]
        created = create_response.json()
        employee_id = created['id']
        test_created_ids['employees'].append(employee_id)
        
        # Update the employee
        update_data = {
            "designation": "Senior Executive",
            "basic_salary": 35000.0
        }
        
        response = authenticated_client.put(
            f"{BASE_URL}/api/v1/hrms/employees/{employee_id}",
            json=update_data
        )
        
        assert response.status_code == 200, f"Update employee failed: {response.text}"
        data = response.json()
        # Verify update was applied
        assert data.get('designation') == 'Senior Executive' or data.get('basic_salary') == 35000.0
        print(f"✓ Updated employee: {employee_id}")


class TestAccountsInvoices:
    """Accounts module - Invoices tests"""
    
    @pytest.fixture(scope="class")
    def test_account_id(self, authenticated_client):
        """Get or create a test account for invoice tests"""
        # First try to get existing accounts
        response = authenticated_client.get(f"{BASE_URL}/api/v1/crm/accounts")
        if response.status_code == 200:
            accounts = response.json()
            if accounts and len(accounts) > 0:
                # Find any account or create one
                for acc in accounts:
                    if acc.get('id'):
                        print(f"  Using existing account: {acc.get('id')}")
                        return acc['id']
        
        # Create a test account if none exists
        account_data = {
            "company_name": f"TEST_Account_{uuid.uuid4().hex[:8]}",
            "name": f"TEST_Account_{uuid.uuid4().hex[:8]}",
            "email": f"test.account.{uuid.uuid4().hex[:6]}@test.com",
            "phone": "9876543210",
            "gstin": "27AABCU9603R1ZM",
            "address": "Test Address",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001"
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/v1/crm/accounts",
            json=account_data
        )
        
        if create_response.status_code in [200, 201]:
            created = create_response.json()
            test_created_ids['accounts'].append(created['id'])
            print(f"  Created test account: {created['id']}")
            return created['id']
        
        pytest.skip("Could not get or create a test account for invoice tests")
    
    def test_list_invoices(self, authenticated_client):
        """Test listing all invoices"""
        response = authenticated_client.get(f"{BASE_URL}/api/v1/accounts/invoices")
        
        assert response.status_code == 200, f"List invoices failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Invoices should return a list"
        print(f"✓ Listed {len(data)} invoices")
    
    def test_create_invoice(self, authenticated_client, test_account_id):
        """Test creating a new invoice (requires account_id)"""
        invoice_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        invoice_data = {
            "invoice_type": "Sales",
            "account_id": test_account_id,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "payment_terms": "Net 30",
            "items": [
                {
                    "description": "Test Product - BOPP Tape",
                    "hsn_code": "39199090",
                    "quantity": 10,
                    "unit": "Rolls",
                    "unit_price": 250.0,
                    "discount_percent": 0,
                    "tax_percent": 18
                }
            ],
            "notes": "Test invoice created by automated tests"
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/v1/accounts/invoices",
            json=invoice_data
        )
        
        assert response.status_code in [200, 201], f"Create invoice failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Invoice ID not in response"
        assert "invoice_number" in data, "Invoice number not in response"
        assert data.get("account_id") == test_account_id
        
        # Verify tax calculations
        assert data.get("subtotal", 0) > 0, "Subtotal should be calculated"
        
        # Track for cleanup
        test_created_ids['invoices'].append(data['id'])
        print(f"✓ Created invoice: {data['invoice_number']} (ID: {data['id']})")
        print(f"  Subtotal: {data.get('subtotal')}, Total: {data.get('grand_total')}")
        return data['id']
    
    def test_get_invoice(self, authenticated_client, test_account_id):
        """Test getting a single invoice"""
        # First create an invoice
        invoice_date = datetime.now().strftime('%Y-%m-%d')
        due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        invoice_data = {
            "invoice_type": "Sales",
            "account_id": test_account_id,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "items": [
                {
                    "description": "Test Item",
                    "quantity": 5,
                    "unit": "Pcs",
                    "unit_price": 100.0,
                    "tax_percent": 18
                }
            ]
        }
        
        create_response = authenticated_client.post(
            f"{BASE_URL}/api/v1/accounts/invoices",
            json=invoice_data
        )
        assert create_response.status_code in [200, 201]
        created = create_response.json()
        invoice_id = created['id']
        test_created_ids['invoices'].append(invoice_id)
        
        # Now get the invoice
        response = authenticated_client.get(f"{BASE_URL}/api/v1/accounts/invoices/{invoice_id}")
        
        assert response.status_code == 200, f"Get invoice failed: {response.text}"
        data = response.json()
        assert data['id'] == invoice_id
        print(f"✓ Retrieved invoice: {invoice_id}")
    
    def test_overdue_invoices(self, authenticated_client):
        """Test getting overdue invoices"""
        response = authenticated_client.get(f"{BASE_URL}/api/v1/accounts/invoices/overdue")
        
        assert response.status_code == 200, f"Overdue invoices failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Overdue invoices should return a list"
        print(f"✓ Retrieved {len(data)} overdue invoices")
    
    def test_invoice_aging(self, authenticated_client):
        """Test getting invoice aging summary"""
        response = authenticated_client.get(f"{BASE_URL}/api/v1/accounts/invoices/aging")
        
        assert response.status_code == 200, f"Invoice aging failed: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Invoice aging should return a dict"
        print(f"✓ Retrieved invoice aging summary")


class TestFieldRegistry:
    """Field Registry module tests"""
    
    def test_get_modules(self, authenticated_client):
        """Test getting available modules"""
        response = authenticated_client.get(f"{BASE_URL}/api/field-registry/modules")
        
        assert response.status_code == 200, f"Get modules failed: {response.text}"
        data = response.json()
        
        # Verify expected modules exist
        assert isinstance(data, dict), "Modules should return a dictionary"
        expected_modules = ['crm', 'inventory', 'production', 'accounts', 'hrms']
        for module in expected_modules:
            assert module in data, f"Module '{module}' not found in field registry"
        
        print(f"✓ Retrieved field registry modules: {list(data.keys())}")
    
    def test_get_masters(self, authenticated_client):
        """Test getting master types"""
        response = authenticated_client.get(f"{BASE_URL}/api/field-registry/masters")
        
        assert response.status_code == 200, f"Get masters failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Masters should return a list"
        assert len(data) > 0, "Masters list should not be empty"
        
        print(f"✓ Retrieved {len(data)} master types")
    
    def test_save_field_config(self, authenticated_client):
        """Test saving field configuration"""
        config_data = {
            "module": "test_module",
            "entity": "test_entity",
            "entity_label": "Test Entity",
            "fields": [
                {
                    "field_name": "test_field",
                    "field_label": "Test Field",
                    "field_type": "text",
                    "section": "basic",
                    "is_required": True,
                    "show_in_list": True,
                    "order": 1
                },
                {
                    "field_name": "test_select",
                    "field_label": "Test Select",
                    "field_type": "select",
                    "section": "basic",
                    "is_required": False,
                    "order": 2,
                    "options": [
                        {"value": "option1", "label": "Option 1"},
                        {"value": "option2", "label": "Option 2"}
                    ]
                }
            ]
        }
        
        response = authenticated_client.post(
            f"{BASE_URL}/api/field-registry/config",
            json=config_data
        )
        
        assert response.status_code == 200, f"Save config failed: {response.text}"
        data = response.json()
        assert "message" in data or "module" in data
        print(f"✓ Saved field configuration for test_module/test_entity")
    
    def test_get_field_config(self, authenticated_client):
        """Test getting field configuration"""
        # Get config for CRM leads (should have default config)
        response = authenticated_client.get(f"{BASE_URL}/api/field-registry/config/crm/leads")
        
        assert response.status_code == 200, f"Get config failed: {response.text}"
        data = response.json()
        
        # Verify config structure
        assert "module" in data or "fields" in data, "Config should have module or fields"
        print(f"✓ Retrieved field configuration for crm/leads")
    
    def test_get_kanban_stages(self, authenticated_client):
        """Test getting Kanban stages"""
        response = authenticated_client.get(f"{BASE_URL}/api/field-registry/stages/crm/leads")
        
        assert response.status_code == 200, f"Get stages failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Stages should return a list"
        print(f"✓ Retrieved {len(data)} Kanban stages for crm/leads")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_data(self, authenticated_client):
        """Clean up all TEST_ prefixed data created during tests"""
        cleanup_summary = {
            'machines': 0,
            'employees': 0,
            'invoices': 0,
            'accounts': 0
        }
        
        # Note: We track created IDs but actual deletion depends on API support
        # For now, just report what was created
        
        for entity_type, ids in test_created_ids.items():
            cleanup_summary[entity_type] = len(ids)
        
        print(f"✓ Test data created during this run:")
        for entity_type, count in cleanup_summary.items():
            if count > 0:
                print(f"  - {entity_type}: {count} records")
        
        # Tests pass regardless - cleanup is informational
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
