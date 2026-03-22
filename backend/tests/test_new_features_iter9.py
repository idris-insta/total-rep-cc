"""
Test Suite for Iteration 9 - New Features Testing
Features: Chat System, Drive System, Bulk Import, E-Invoice & E-Way Bill
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://postgres-frontend-v1.preview.emergentagent.com').rstrip('/')

class TestAuthentication:
    """Test authentication for all subsequent tests"""
    
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
    
    def test_login_success(self, auth_token):
        """Test login with valid credentials"""
        assert auth_token is not None
        assert len(auth_token) > 0


class TestChatSystem:
    """Test Chat System APIs"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_conversations(self, auth_headers):
        """Test GET /api/chat/conversations - returns conversation list"""
        response = requests.get(f"{BASE_URL}/api/chat/conversations", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_get_chat_users(self, auth_headers):
        """Test GET /api/chat/users - returns list of users for chat"""
        response = requests.get(f"{BASE_URL}/api/chat/users", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_get_tasks(self, auth_headers):
        """Test GET /api/chat/tasks - returns task list"""
        response = requests.get(f"{BASE_URL}/api/chat/tasks", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_create_task(self, auth_headers):
        """Test POST /api/chat/tasks - create a new task"""
        # First get a user to assign to
        users_response = requests.get(f"{BASE_URL}/api/chat/users", headers=auth_headers)
        users = users_response.json()
        
        if len(users) > 0:
            task_data = {
                "title": "TEST_Task from iteration 9",
                "description": "Test task description",
                "assigned_to": users[0]["id"],
                "priority": "medium"
            }
            response = requests.post(f"{BASE_URL}/api/chat/tasks", json=task_data, headers=auth_headers)
            assert response.status_code == 200, f"Failed: {response.text}"
            data = response.json()
            assert "id" in data
            assert data["title"] == task_data["title"]
        else:
            pytest.skip("No users available to assign task")


class TestDriveSystem:
    """Test Drive System APIs"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_storage_stats(self, auth_headers):
        """Test GET /api/drive/storage - returns storage statistics"""
        response = requests.get(f"{BASE_URL}/api/drive/storage", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_size" in data
        assert "file_count" in data
        assert "folder_count" in data
        assert "storage_limit" in data
    
    def test_get_folders(self, auth_headers):
        """Test GET /api/drive/folders - returns folder list"""
        response = requests.get(f"{BASE_URL}/api/drive/folders", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_get_files(self, auth_headers):
        """Test GET /api/drive/files - returns file list"""
        response = requests.get(f"{BASE_URL}/api/drive/files", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_create_folder(self, auth_headers):
        """Test POST /api/drive/folders - create a new folder"""
        folder_data = {
            "name": "TEST_Folder_Iter9",
            "color": "#3b82f6"
        }
        response = requests.post(f"{BASE_URL}/api/drive/folders", json=folder_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"] == folder_data["name"]


class TestBulkImport:
    """Test Bulk Import APIs"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_download_customers_template(self, auth_headers):
        """Test GET /api/bulk-import/templates/customers - downloads Excel template"""
        response = requests.get(f"{BASE_URL}/api/bulk-import/templates/customers", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")
    
    def test_download_items_template(self, auth_headers):
        """Test GET /api/bulk-import/templates/items - downloads Excel template"""
        response = requests.get(f"{BASE_URL}/api/bulk-import/templates/items", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")
    
    def test_download_opening_balance_template(self, auth_headers):
        """Test GET /api/bulk-import/templates/opening_balance - downloads Excel template"""
        response = requests.get(f"{BASE_URL}/api/bulk-import/templates/opening_balance", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")
    
    def test_download_opening_stock_template(self, auth_headers):
        """Test GET /api/bulk-import/templates/opening_stock - downloads Excel template"""
        response = requests.get(f"{BASE_URL}/api/bulk-import/templates/opening_stock", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers.get("content-type", "")


class TestEInvoice:
    """Test E-Invoice & E-Way Bill APIs"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_einvoice_summary(self, auth_headers):
        """Test GET /api/einvoice/summary - returns e-invoice summary statistics"""
        response = requests.get(f"{BASE_URL}/api/einvoice/summary", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_invoices" in data
        assert "irn_generated" in data
        assert "irn_pending" in data
        assert "eway_generated" in data
    
    def test_get_pending_invoices(self, auth_headers):
        """Test GET /api/einvoice/pending-invoices - returns pending invoices"""
        response = requests.get(f"{BASE_URL}/api/einvoice/pending-invoices", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_get_einvoice_logs(self, auth_headers):
        """Test GET /api/einvoice/logs - returns activity logs"""
        response = requests.get(f"{BASE_URL}/api/einvoice/logs", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
    
    def test_get_credentials_admin_only(self, auth_headers):
        """Test GET /api/einvoice/credentials - admin only endpoint"""
        response = requests.get(f"{BASE_URL}/api/einvoice/credentials", headers=auth_headers)
        # Should return 200 for admin user
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"


class TestNavigationLinks:
    """Test that navigation links exist in sidebar"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_chat_route_accessible(self, auth_headers):
        """Verify /chat route is accessible"""
        # This tests that the backend doesn't block the route
        # Frontend routing is handled by React Router
        response = requests.get(f"{BASE_URL}/api/chat/conversations", headers=auth_headers)
        assert response.status_code == 200
    
    def test_drive_route_accessible(self, auth_headers):
        """Verify /drive route is accessible"""
        response = requests.get(f"{BASE_URL}/api/drive/storage", headers=auth_headers)
        assert response.status_code == 200
    
    def test_bulk_import_route_accessible(self, auth_headers):
        """Verify /bulk-import route is accessible"""
        response = requests.get(f"{BASE_URL}/api/bulk-import/templates/customers", headers=auth_headers)
        assert response.status_code == 200
    
    def test_einvoice_route_accessible(self, auth_headers):
        """Verify /einvoice route is accessible"""
        response = requests.get(f"{BASE_URL}/api/einvoice/summary", headers=auth_headers)
        assert response.status_code == 200
