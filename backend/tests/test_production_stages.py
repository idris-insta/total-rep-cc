"""
Production Stages Module Tests
Tests for:
- Machine Master CRUD operations
- Production Dashboard API
- Stage-specific dashboards
- Order Sheets API
- Work Order Stages API
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://postgres-frontend-v1.preview.emergentagent.com')

class TestProductionStagesAuth:
    """Authentication and basic connectivity tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@instabiz.com", "password": "adminpassword"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json().get("token")
        assert token, "No token in response"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
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
        print(f"✓ Login successful, user: {data['user'].get('name')}")


class TestProductionDashboard:
    """Production Dashboard API tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@instabiz.com", "password": "adminpassword"}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_dashboard_returns_correct_structure(self, auth_headers):
        """Test /api/production-stages/dashboard returns correct JSON structure"""
        response = requests.get(f"{BASE_URL}/api/production-stages/dashboard", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify summary section
        assert "summary" in data
        summary = data["summary"]
        assert "total_sku" in summary
        assert "sku_in_process" in summary
        assert "total_pcs_in_process" in summary
        assert "total_sqm_in_process" in summary
        assert "overall_progress" in summary
        
        # Verify stages section with all 7 stages
        assert "stages" in data
        stages = data["stages"]
        expected_stages = ["coating", "slitting", "rewinding", "cutting", "packing", "ready_to_deliver", "delivered"]
        for stage in expected_stages:
            assert stage in stages, f"Missing stage: {stage}"
            assert "pending" in stages[stage]
            assert "in_progress" in stages[stage]
            assert "completed" in stages[stage]
            assert "total" in stages[stage]
        
        # Verify other sections
        assert "order_sheets" in data
        assert "work_orders" in data
        assert "priority" in data
        assert "machines" in data
        
        print(f"✓ Dashboard structure verified with {len(expected_stages)} stages")
        print(f"  - Total SKUs: {summary['total_sku']}")
        print(f"  - Machines: {data['machines']['total']}")
    
    def test_dashboard_requires_auth(self):
        """Test dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/production-stages/dashboard")
        assert response.status_code == 401 or response.status_code == 403
        print("✓ Dashboard correctly requires authentication")


class TestMachineMaster:
    """Machine Master CRUD tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@instabiz.com", "password": "adminpassword"}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_get_machines_list(self, auth_headers):
        """Test GET /api/production-stages/machines returns list"""
        response = requests.get(f"{BASE_URL}/api/production-stages/machines", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Machines list returned {len(data)} machines")
        
        # Verify machine structure if any exist
        if len(data) > 0:
            machine = data[0]
            assert "id" in machine
            assert "machine_code" in machine
            assert "machine_name" in machine
            assert "machine_type" in machine
            assert "capacity" in machine
            assert "location" in machine
            assert "wastage_norm_percent" in machine
            assert "status" in machine
            print(f"  - First machine: {machine['machine_code']} - {machine['machine_name']}")
    
    def test_get_machines_filter_by_type(self, auth_headers):
        """Test filtering machines by type"""
        response = requests.get(
            f"{BASE_URL}/api/production-stages/machines?machine_type=coating",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        for machine in data:
            assert machine["machine_type"] == "coating"
        print(f"✓ Type filter works, found {len(data)} coating machines")
    
    def test_get_machines_filter_by_location(self, auth_headers):
        """Test filtering machines by location"""
        response = requests.get(
            f"{BASE_URL}/api/production-stages/machines?location=BWD",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        for machine in data:
            assert machine["location"] == "BWD"
        print(f"✓ Location filter works, found {len(data)} machines at BWD")
    
    def test_create_machine(self, auth_headers):
        """Test creating a new machine"""
        unique_code = f"TEST-{str(uuid.uuid4())[:6].upper()}"
        machine_data = {
            "machine_code": unique_code,
            "machine_name": "Test Machine for Pytest",
            "machine_type": "cutting",
            "capacity": 100,
            "capacity_uom": "pcs/hour",
            "location": "BWD",
            "wastage_norm_percent": 3.5,
            "notes": "Created by pytest"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/production-stages/machines",
            json=machine_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["machine_code"] == unique_code
        assert data["machine_name"] == "Test Machine for Pytest"
        assert data["machine_type"] == "cutting"
        assert data["wastage_norm_percent"] == 3.5
        assert data["status"] == "active"
        assert "id" in data
        
        print(f"✓ Machine created: {unique_code}")
        
        # Cleanup - delete the test machine
        machine_id = data["id"]
        delete_response = requests.delete(
            f"{BASE_URL}/api/production-stages/machines/{machine_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200
        print(f"✓ Test machine cleaned up")
    
    def test_create_machine_duplicate_code_fails(self, auth_headers):
        """Test that duplicate machine code fails"""
        # First, get existing machines
        response = requests.get(f"{BASE_URL}/api/production-stages/machines", headers=auth_headers)
        machines = response.json()
        
        if len(machines) > 0:
            existing_code = machines[0]["machine_code"]
            
            machine_data = {
                "machine_code": existing_code,
                "machine_name": "Duplicate Test",
                "machine_type": "coating",
                "capacity": 100,
                "location": "BWD",
                "wastage_norm_percent": 2.0
            }
            
            response = requests.post(
                f"{BASE_URL}/api/production-stages/machines",
                json=machine_data,
                headers=auth_headers
            )
            assert response.status_code == 400
            assert "already exists" in response.json().get("detail", "").lower()
            print(f"✓ Duplicate machine code correctly rejected")
        else:
            pytest.skip("No existing machines to test duplicate")
    
    def test_update_machine(self, auth_headers):
        """Test updating a machine"""
        # Create a test machine first
        unique_code = f"TEST-UPD-{str(uuid.uuid4())[:4].upper()}"
        create_response = requests.post(
            f"{BASE_URL}/api/production-stages/machines",
            json={
                "machine_code": unique_code,
                "machine_name": "Update Test Machine",
                "machine_type": "packing",
                "capacity": 50,
                "location": "SGM",
                "wastage_norm_percent": 2.0
            },
            headers=auth_headers
        )
        assert create_response.status_code == 200
        machine_id = create_response.json()["id"]
        
        # Update the machine
        update_response = requests.put(
            f"{BASE_URL}/api/production-stages/machines/{machine_id}",
            json={
                "machine_name": "Updated Machine Name",
                "wastage_norm_percent": 4.5
            },
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_response = requests.get(
            f"{BASE_URL}/api/production-stages/machines/{machine_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        updated = get_response.json()
        assert updated["machine_name"] == "Updated Machine Name"
        assert updated["wastage_norm_percent"] == 4.5
        
        print(f"✓ Machine updated successfully")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/production-stages/machines/{machine_id}", headers=auth_headers)


class TestStageDashboards:
    """Stage-specific dashboard tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@instabiz.com", "password": "adminpassword"}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    @pytest.mark.parametrize("stage", [
        "coating", "slitting", "rewinding", "cutting", "packing", "ready_to_deliver", "delivered"
    ])
    def test_stage_dashboard_returns_correct_structure(self, auth_headers, stage):
        """Test each stage dashboard returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/production-stages/stages/{stage}/dashboard",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify structure
        assert data["stage"] == stage
        assert "summary" in data
        assert "quantities" in data
        assert "hourly_production" in data
        assert "stage_metrics" in data
        assert "work_orders" in data
        
        # Verify summary fields
        summary = data["summary"]
        assert "pending" in summary
        assert "in_progress" in summary
        assert "completed" in summary
        assert "total" in summary
        
        # Verify quantities fields
        quantities = data["quantities"]
        assert "total_target" in quantities
        assert "total_completed" in quantities
        assert "total_wastage" in quantities
        assert "completion_percent" in quantities
        assert "wastage_percent" in quantities
        
        print(f"✓ Stage '{stage}' dashboard structure verified")
    
    def test_invalid_stage_returns_400(self, auth_headers):
        """Test invalid stage returns 400 error"""
        response = requests.get(
            f"{BASE_URL}/api/production-stages/stages/invalid_stage/dashboard",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Invalid stage" in response.json().get("detail", "")
        print("✓ Invalid stage correctly returns 400")


class TestOrderSheets:
    """Order Sheets API tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@instabiz.com", "password": "adminpassword"}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_get_order_sheets_list(self, auth_headers):
        """Test GET /api/production-stages/order-sheets returns list"""
        response = requests.get(
            f"{BASE_URL}/api/production-stages/order-sheets",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Order sheets list returned {len(data)} items")


class TestWorkOrderStages:
    """Work Order Stages API tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@instabiz.com", "password": "adminpassword"}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_get_work_order_stages_list(self, auth_headers):
        """Test GET /api/production-stages/work-order-stages returns list"""
        response = requests.get(
            f"{BASE_URL}/api/production-stages/work-order-stages",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Work order stages list returned {len(data)} items")
    
    def test_filter_work_orders_by_stage(self, auth_headers):
        """Test filtering work orders by stage"""
        response = requests.get(
            f"{BASE_URL}/api/production-stages/work-order-stages?stage=coating",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        for wo in data:
            assert wo["stage"] == "coating"
        print(f"✓ Stage filter works, found {len(data)} coating work orders")


class TestReports:
    """Production Reports API tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get headers with auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@instabiz.com", "password": "adminpassword"}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_stage_wise_report(self, auth_headers):
        """Test stage-wise production report"""
        response = requests.get(
            f"{BASE_URL}/api/production-stages/reports/stage-wise",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        print(f"✓ Stage-wise report returned data for {len(data)} stages")
    
    def test_machine_wise_report(self, auth_headers):
        """Test machine-wise production report"""
        response = requests.get(
            f"{BASE_URL}/api/production-stages/reports/machine-wise",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        print(f"✓ Machine-wise report returned data for {len(data)} machines")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
