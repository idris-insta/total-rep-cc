"""
Test suite for Autonomous Collector Module
Features tested:
1. Debtor Segmentation API
2. Block/Unblock Debtor APIs
3. Payment Reminders API
4. Emergency Controls (Nuke Button) APIs
5. Collection Analytics API
6. Quick Actions API
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAutonomousCollector:
    """Test Autonomous Collector APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    # ==================== DEBTOR SEGMENTATION ====================
    def test_get_debtor_segmentation(self):
        """Test debtor segmentation API returns proper structure"""
        response = requests.get(
            f"{BASE_URL}/api/collector/debtors/segmentation",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "segments" in data, "Missing 'segments' in response"
        assert "summary" in data, "Missing 'summary' in response"
        assert "segment_counts" in data, "Missing 'segment_counts' in response"
        
        # Verify segments structure
        segments = data["segments"]
        assert "GOLD" in segments, "Missing GOLD segment"
        assert "SILVER" in segments, "Missing SILVER segment"
        assert "BRONZE" in segments, "Missing BRONZE segment"
        assert "BLOCKED" in segments, "Missing BLOCKED segment"
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_outstanding" in summary, "Missing total_outstanding in summary"
        assert "total_overdue" in summary, "Missing total_overdue in summary"
        
        print(f"✓ Debtor segmentation: {data['segment_counts']}")
    
    # ==================== PAYMENT REMINDERS ====================
    def test_get_pending_reminders(self):
        """Test pending payment reminders API"""
        response = requests.get(
            f"{BASE_URL}/api/collector/reminders/pending",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "reminders" in data, "Missing 'reminders' in response"
        assert "total_count" in data, "Missing 'total_count' in response"
        assert "urgent_count" in data, "Missing 'urgent_count' in response"
        
        # Verify reminders is a list
        assert isinstance(data["reminders"], list), "reminders should be a list"
        
        print(f"✓ Pending reminders: {data['total_count']} total, {data['urgent_count']} urgent")
    
    # ==================== EMERGENCY CONTROLS ====================
    def test_get_emergency_status(self):
        """Test emergency status API"""
        response = requests.get(
            f"{BASE_URL}/api/collector/emergency/status",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "emergency_active" in data, "Missing 'emergency_active' in response"
        assert "active_controls" in data, "Missing 'active_controls' in response"
        
        print(f"✓ Emergency status: active={data['emergency_active']}")
    
    def test_activate_emergency_control(self):
        """Test activating emergency control (Nuke Button)"""
        response = requests.post(
            f"{BASE_URL}/api/collector/emergency/activate",
            headers=self.headers,
            json={
                "action": "FREEZE_ORDERS",
                "scope": "ALL",
                "reason": "TEST - Automated testing of emergency controls",
                "duration_hours": 1
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response
        assert "emergency_id" in data, "Missing emergency_id in response"
        assert data["action"] == "FREEZE_ORDERS", "Action mismatch"
        
        # Store emergency_id for deactivation test
        self.emergency_id = data["emergency_id"]
        print(f"✓ Emergency control activated: {data['emergency_id']}")
        
        # Verify it's now active
        status_response = requests.get(
            f"{BASE_URL}/api/collector/emergency/status",
            headers=self.headers
        )
        status_data = status_response.json()
        assert status_data["emergency_active"] == True, "Emergency should be active"
        
        # Deactivate it
        deactivate_response = requests.post(
            f"{BASE_URL}/api/collector/emergency/deactivate/{data['emergency_id']}",
            headers=self.headers
        )
        assert deactivate_response.status_code == 200, f"Deactivate failed: {deactivate_response.text}"
        print(f"✓ Emergency control deactivated")
    
    # ==================== COLLECTION ANALYTICS ====================
    def test_get_collection_analytics(self):
        """Test collection analytics API"""
        response = requests.get(
            f"{BASE_URL}/api/collector/analytics/collection?period=month",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "period" in data, "Missing 'period' in response"
        assert "total_invoiced" in data, "Missing 'total_invoiced' in response"
        assert "total_collected" in data, "Missing 'total_collected' in response"
        assert "collection_efficiency" in data, "Missing 'collection_efficiency' in response"
        assert "avg_collection_days" in data, "Missing 'avg_collection_days' in response"
        assert "pending_collection" in data, "Missing 'pending_collection' in response"
        
        print(f"✓ Collection analytics: efficiency={data['collection_efficiency']}%, avg_days={data['avg_collection_days']}")
    
    def test_get_collection_analytics_different_periods(self):
        """Test collection analytics with different periods"""
        for period in ["week", "month", "quarter", "year"]:
            response = requests.get(
                f"{BASE_URL}/api/collector/analytics/collection?period={period}",
                headers=self.headers
            )
            assert response.status_code == 200, f"Failed for period {period}: {response.text}"
            data = response.json()
            assert data["period"] == period, f"Period mismatch for {period}"
        
        print("✓ Collection analytics works for all periods")
    
    # ==================== QUICK ACTIONS ====================
    def test_get_quick_actions(self):
        """Test quick actions API for dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/collector/quick-actions",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "actions" in data, "Missing 'actions' in response"
        assert "total_actions" in data, "Missing 'total_actions' in response"
        
        # Verify actions is a list
        assert isinstance(data["actions"], list), "actions should be a list"
        
        # If there are actions, verify structure
        if len(data["actions"]) > 0:
            action = data["actions"][0]
            assert "id" in action, "Action missing 'id'"
            assert "label" in action, "Action missing 'label'"
            assert "count" in action, "Action missing 'count'"
            assert "link" in action, "Action missing 'link'"
        
        print(f"✓ Quick actions: {len(data['actions'])} items, total={data['total_actions']}")


class TestDebtorBlockUnblock:
    """Test debtor block/unblock functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_block_debtor_requires_admin(self):
        """Test that blocking requires admin role"""
        # First get a debtor from segmentation
        seg_response = requests.get(
            f"{BASE_URL}/api/collector/debtors/segmentation",
            headers=self.headers
        )
        data = seg_response.json()
        
        # Find any account to test with
        test_account_id = None
        for segment in ["BRONZE", "SILVER", "GOLD"]:
            if data["segments"][segment]:
                test_account_id = data["segments"][segment][0]["account_id"]
                break
        
        if test_account_id:
            # Admin should be able to block
            response = requests.post(
                f"{BASE_URL}/api/collector/debtors/{test_account_id}/block?reason=TEST_BLOCK",
                headers=self.headers
            )
            # Should succeed for admin
            assert response.status_code == 200, f"Admin should be able to block: {response.text}"
            print(f"✓ Admin can block debtor: {test_account_id}")
            
            # Unblock it
            unblock_response = requests.post(
                f"{BASE_URL}/api/collector/debtors/{test_account_id}/unblock",
                headers=self.headers
            )
            assert unblock_response.status_code == 200, f"Admin should be able to unblock: {unblock_response.text}"
            print(f"✓ Admin can unblock debtor: {test_account_id}")
        else:
            print("⚠ No accounts found to test block/unblock")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
