"""
Test v1 Layered Architecture APIs - Quality, Sales Incentives, and Settings Modules
Tests for remaining refactored modules: Quality, Sales Incentives, Settings
This completes the v1 API architecture testing for all 9 modules.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('VITE_BACKEND_URL', 'https://postgres-frontend-v1.preview.emergentagent.com').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@instabiz.com"
TEST_PASSWORD = "adminpassword"


class TestAuthentication:
    """Authentication tests for getting bearer token"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for all tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_login_successful(self, auth_token):
        """Verify login returns valid token"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✅ Login successful, token obtained")


# =================== QUALITY MODULE TESTS ===================

class TestQualityInspectionsV1:
    """Test v1 Quality - Inspections API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_inspections(self, auth_headers):
        """GET /api/v1/quality/inspections - returns list of QC inspections"""
        response = requests.get(
            f"{BASE_URL}/api/v1/quality/inspections",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/quality/inspections returned {len(data)} inspections")
    
    def test_get_failed_inspections(self, auth_headers):
        """GET /api/v1/quality/inspections/failed - returns failed inspections"""
        response = requests.get(
            f"{BASE_URL}/api/v1/quality/inspections/failed",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # All returned inspections should have result='fail'
        for inspection in data:
            if 'result' in inspection:
                assert inspection['result'] == 'fail', "All inspections should be failed"
        print(f"✅ GET /api/v1/quality/inspections/failed returned {len(data)} failed inspections")
    
    def test_get_inspection_stats(self, auth_headers):
        """GET /api/v1/quality/inspections/stats - returns inspection statistics"""
        response = requests.get(
            f"{BASE_URL}/api/v1/quality/inspections/stats",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        # Verify expected stats fields
        assert 'total_inspections' in data, "Missing total_inspections field"
        assert 'passed' in data, "Missing passed field"
        assert 'failed' in data, "Missing failed field"
        assert 'pass_rate' in data, "Missing pass_rate field"
        print(f"✅ GET /api/v1/quality/inspections/stats - Total: {data.get('total_inspections')}, Pass Rate: {data.get('pass_rate')}%")


class TestQualityComplaintsV1:
    """Test v1 Quality - Complaints API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_complaints(self, auth_headers):
        """GET /api/v1/quality/complaints - returns list of complaints"""
        response = requests.get(
            f"{BASE_URL}/api/v1/quality/complaints",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/quality/complaints returned {len(data)} complaints")
    
    def test_get_open_complaints(self, auth_headers):
        """GET /api/v1/quality/complaints/open - returns open complaints"""
        response = requests.get(
            f"{BASE_URL}/api/v1/quality/complaints/open",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # All returned complaints should be open or in_progress
        for complaint in data:
            if 'status' in complaint:
                assert complaint['status'] in ['open', 'in_progress'], f"Unexpected status: {complaint.get('status')}"
        print(f"✅ GET /api/v1/quality/complaints/open returned {len(data)} open complaints")
    
    def test_get_complaint_stats(self, auth_headers):
        """GET /api/v1/quality/complaints/stats - returns complaint statistics"""
        response = requests.get(
            f"{BASE_URL}/api/v1/quality/complaints/stats",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dictionary"
        # Verify expected stats fields
        assert 'total' in data, "Missing total field"
        assert 'open' in data, "Missing open field"
        assert 'resolved' in data, "Missing resolved field"
        print(f"✅ GET /api/v1/quality/complaints/stats - Total: {data.get('total')}, Open: {data.get('open')}, Resolved: {data.get('resolved')}")


# =================== SALES INCENTIVES MODULE TESTS ===================

class TestSalesIncentivesTargetsV1:
    """Test v1 Sales Incentives - Targets API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_targets(self, auth_headers):
        """GET /api/v1/sales-incentives/targets - returns list of sales targets"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sales-incentives/targets",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/sales-incentives/targets returned {len(data)} targets")
    
    def test_get_active_targets(self, auth_headers):
        """GET /api/v1/sales-incentives/targets/active - returns active targets"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sales-incentives/targets/active",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # All returned targets should be active
        for target in data:
            if 'status' in target:
                assert target['status'] == 'active', f"Unexpected status: {target.get('status')}"
        print(f"✅ GET /api/v1/sales-incentives/targets/active returned {len(data)} active targets")


class TestSalesIncentivesSlabsV1:
    """Test v1 Sales Incentives - Slabs API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_slabs(self, auth_headers):
        """GET /api/v1/sales-incentives/slabs - returns incentive slabs"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sales-incentives/slabs",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/sales-incentives/slabs returned {len(data)} slabs")


class TestSalesIncentivesPayoutsV1:
    """Test v1 Sales Incentives - Payouts API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_payouts(self, auth_headers):
        """GET /api/v1/sales-incentives/payouts - returns list of payouts"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sales-incentives/payouts",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/sales-incentives/payouts returned {len(data)} payouts")
    
    def test_get_pending_approval_payouts(self, auth_headers):
        """GET /api/v1/sales-incentives/payouts/pending-approval - returns payouts pending approval"""
        response = requests.get(
            f"{BASE_URL}/api/v1/sales-incentives/payouts/pending-approval",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # All returned payouts should have status='calculated' (pending approval)
        for payout in data:
            if 'status' in payout:
                assert payout['status'] == 'calculated', f"Unexpected status: {payout.get('status')}"
        print(f"✅ GET /api/v1/sales-incentives/payouts/pending-approval returned {len(data)} pending payouts")


# =================== SETTINGS MODULE TESTS ===================

class TestSettingsFieldRegistryV1:
    """Test v1 Settings - Field Registry API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_field_configurations(self, auth_headers):
        """GET /api/v1/settings/field-registry - returns field configurations"""
        response = requests.get(
            f"{BASE_URL}/api/v1/settings/field-registry",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/settings/field-registry returned {len(data)} configurations")
    
    def test_get_available_modules(self, auth_headers):
        """GET /api/v1/settings/field-registry/modules - returns available modules"""
        response = requests.get(
            f"{BASE_URL}/api/v1/settings/field-registry/modules",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list of modules"
        print(f"✅ GET /api/v1/settings/field-registry/modules returned {len(data)} modules: {data}")


class TestSettingsBranchesV1:
    """Test v1 Settings - Branches API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_branches(self, auth_headers):
        """GET /api/v1/settings/branches - returns list of branches"""
        response = requests.get(
            f"{BASE_URL}/api/v1/settings/branches",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/settings/branches returned {len(data)} branches")


class TestSettingsUsersV1:
    """Test v1 Settings - Users API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_users(self, auth_headers):
        """GET /api/v1/settings/users - returns list of users"""
        response = requests.get(
            f"{BASE_URL}/api/v1/settings/users",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # Verify sensitive fields are removed
        for user in data:
            assert 'hashed_password' not in user, "Password should not be exposed"
        print(f"✅ GET /api/v1/settings/users returned {len(data)} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
