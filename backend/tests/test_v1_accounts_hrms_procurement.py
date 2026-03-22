"""
Test v1 Layered Architecture APIs - Accounts, HRMS, and Procurement Modules
Tests for newly refactored modules: Accounts, HRMS, Procurement
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


# =================== ACCOUNTS MODULE TESTS ===================

class TestAccountsInvoicesV1:
    """Test v1 Accounts - Invoices API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_invoices(self, auth_headers):
        """GET /api/v1/accounts/invoices - returns list of invoices"""
        response = requests.get(
            f"{BASE_URL}/api/v1/accounts/invoices",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/accounts/invoices - returned {len(data)} invoices")
    
    def test_get_overdue_invoices(self, auth_headers):
        """GET /api/v1/accounts/invoices/overdue - returns overdue invoices"""
        response = requests.get(
            f"{BASE_URL}/api/v1/accounts/invoices/overdue",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/accounts/invoices/overdue - returned {len(data)} overdue invoices")
    
    def test_get_invoice_aging(self, auth_headers):
        """GET /api/v1/accounts/invoices/aging - returns aging summary"""
        response = requests.get(
            f"{BASE_URL}/api/v1/accounts/invoices/aging",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"
        # Check aging buckets
        expected_keys = ['current', '1_30_days', '31_60_days', '61_90_days', 'over_90_days']
        for key in expected_keys:
            assert key in data, f"Missing aging bucket: {key}"
        print(f"✅ GET /api/v1/accounts/invoices/aging - aging summary: {data}")


class TestAccountsPaymentsV1:
    """Test v1 Accounts - Payments API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_payments(self, auth_headers):
        """GET /api/v1/accounts/payments - returns list of payments"""
        response = requests.get(
            f"{BASE_URL}/api/v1/accounts/payments",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/accounts/payments - returned {len(data)} payments")


# =================== HRMS MODULE TESTS ===================

class TestHRMSEmployeesV1:
    """Test v1 HRMS - Employees API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_employees(self, auth_headers):
        """GET /api/v1/hrms/employees - returns list of employees"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hrms/employees",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/hrms/employees - returned {len(data)} employees")
    
    def test_get_employees_with_filter(self, auth_headers):
        """GET /api/v1/hrms/employees with department filter"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hrms/employees",
            headers=auth_headers,
            params={"status": "active"}
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/hrms/employees?status=active - returned {len(data)} employees")


class TestHRMSAttendanceV1:
    """Test v1 HRMS - Attendance API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_attendance(self, auth_headers):
        """GET /api/v1/hrms/attendance - returns attendance records"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hrms/attendance",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/hrms/attendance - returned {len(data)} attendance records")


class TestHRMSLeaveRequestsV1:
    """Test v1 HRMS - Leave Requests API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_leave_requests(self, auth_headers):
        """GET /api/v1/hrms/leave-requests - returns leave requests"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hrms/leave-requests",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/hrms/leave-requests - returned {len(data)} leave requests")
    
    def test_get_pending_leave_requests(self, auth_headers):
        """GET /api/v1/hrms/leave-requests/pending - returns pending leave requests"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hrms/leave-requests/pending",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/hrms/leave-requests/pending - returned {len(data)} pending requests")


class TestHRMSPayrollV1:
    """Test v1 HRMS - Payroll API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_payroll(self, auth_headers):
        """GET /api/v1/hrms/payroll - returns payroll records"""
        response = requests.get(
            f"{BASE_URL}/api/v1/hrms/payroll",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/hrms/payroll - returned {len(data)} payroll records")


# =================== PROCUREMENT MODULE TESTS ===================

class TestProcurementSuppliersV1:
    """Test v1 Procurement - Suppliers API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_suppliers(self, auth_headers):
        """GET /api/v1/procurement/suppliers - returns list of suppliers"""
        response = requests.get(
            f"{BASE_URL}/api/v1/procurement/suppliers",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/procurement/suppliers - returned {len(data)} suppliers")


class TestProcurementPurchaseOrdersV1:
    """Test v1 Procurement - Purchase Orders API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_purchase_orders(self, auth_headers):
        """GET /api/v1/procurement/purchase-orders - returns list of POs"""
        response = requests.get(
            f"{BASE_URL}/api/v1/procurement/purchase-orders",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/procurement/purchase-orders - returned {len(data)} purchase orders")
    
    def test_get_pending_purchase_orders(self, auth_headers):
        """GET /api/v1/procurement/purchase-orders/pending - returns pending POs"""
        response = requests.get(
            f"{BASE_URL}/api/v1/procurement/purchase-orders/pending",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/procurement/purchase-orders/pending - returned {len(data)} pending POs")


class TestProcurementGRNV1:
    """Test v1 Procurement - GRN API"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        token = response.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_grns(self, auth_headers):
        """GET /api/v1/procurement/grn - returns list of GRNs"""
        response = requests.get(
            f"{BASE_URL}/api/v1/procurement/grn",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ GET /api/v1/procurement/grn - returned {len(data)} GRNs")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
