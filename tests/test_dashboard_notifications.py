"""
Test Dashboard Overview and Notification endpoints
Tests: /api/dashboard/overview, /api/dashboard/revenue-analytics, /api/dashboard/ai-insights
Tests: Notification endpoints for bell functionality
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDashboardOverview:
    """Dashboard overview endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_overview(self):
        """Test /api/dashboard/overview returns data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/overview", headers=self.headers)
        assert response.status_code == 200, f"Dashboard overview failed: {response.text}"
        data = response.json()
        # Verify expected fields from routes/dashboard.py
        assert "crm" in data
        assert "revenue" in data
        assert "inventory" in data
        assert "production" in data
        print(f"Dashboard overview: {data}")
    
    def test_dashboard_revenue_analytics(self):
        """Test /api/dashboard/revenue-analytics returns chart data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/revenue-analytics", headers=self.headers)
        assert response.status_code == 200, f"Revenue analytics failed: {response.text}"
        data = response.json()
        assert "period" in data
        assert "total_revenue" in data
        assert "daily_revenue" in data
        print(f"Revenue analytics: {data}")
    
    def test_dashboard_ai_insights(self):
        """Test /api/dashboard/ai-insights returns insights"""
        response = requests.get(f"{BASE_URL}/api/dashboard/ai-insights", headers=self.headers)
        assert response.status_code == 200, f"AI insights failed: {response.text}"
        data = response.json()
        assert "insights" in data
        print(f"AI insights: {data}")


class TestNotificationBell:
    """Notification endpoints for bell functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_notification_count(self):
        """Test /api/notifications/notifications/count"""
        response = requests.get(f"{BASE_URL}/api/notifications/notifications/count", headers=self.headers)
        assert response.status_code == 200, f"Notification count failed: {response.text}"
        data = response.json()
        assert "unread_count" in data
        print(f"Notification count: {data}")
    
    def test_get_notifications(self):
        """Test /api/notifications/notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications/notifications?limit=20", headers=self.headers)
        assert response.status_code == 200, f"Get notifications failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Notifications: {len(data)} items")
    
    def test_generate_alerts(self):
        """Test /api/notifications/alerts/generate"""
        response = requests.post(f"{BASE_URL}/api/notifications/alerts/generate", headers=self.headers)
        assert response.status_code == 200, f"Generate alerts failed: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"Generate alerts: {data}")
    
    def test_mark_all_read(self):
        """Test /api/notifications/notifications/read-all"""
        response = requests.put(f"{BASE_URL}/api/notifications/notifications/read-all", headers=self.headers)
        assert response.status_code == 200, f"Mark all read failed: {response.text}"
        data = response.json()
        print(f"Mark all read: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
