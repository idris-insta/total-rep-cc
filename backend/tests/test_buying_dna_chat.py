"""
Test Suite for Buying DNA Sales Hunter and Real-time Chat APIs
Tests P2 Sidebar Search & Favorites, P3 Buying DNA, P3 Real-time Chat
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://postgres-frontend-v1.preview.emergentagent.com').rstrip('/')


class TestAuth:
    """Authentication tests"""
    
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
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}


class TestBuyingDNAPatterns(TestAuth):
    """Buying DNA Sales Hunter - Pattern Analysis Tests"""
    
    def test_get_buying_patterns(self, auth_headers):
        """Test GET /api/buying-dna/patterns - returns patterns and summary"""
        response = requests.get(f"{BASE_URL}/api/buying-dna/patterns", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "patterns" in data, "Response should have 'patterns' key"
        assert "summary" in data, "Response should have 'summary' key"
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_tracked" in summary
        assert "urgent_followup" in summary
        assert "gentle_reminder" in summary
        assert "preemptive_check" in summary
        assert "no_action" in summary
        
        # Verify patterns is a list
        assert isinstance(data["patterns"], list)
        
        # If patterns exist, verify structure
        if data["patterns"]:
            pattern = data["patterns"][0]
            required_fields = [
                "account_id", "account_name", "avg_order_interval_days",
                "days_since_last_order", "is_overdue", "suggested_action"
            ]
            for field in required_fields:
                assert field in pattern, f"Pattern missing field: {field}"
    
    def test_get_buying_dna_dashboard(self, auth_headers):
        """Test GET /api/buying-dna/dashboard - returns dashboard summary"""
        response = requests.get(f"{BASE_URL}/api/buying-dna/dashboard", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "summary" in data
        assert "top_urgent" in data
        assert "recent_followups" in data
        assert "metrics" in data
    
    def test_log_followup(self, auth_headers):
        """Test POST /api/buying-dna/followup-log - logs a follow-up action"""
        response = requests.post(
            f"{BASE_URL}/api/buying-dna/followup-log",
            params={
                "account_id": "test-account-123",
                "action_type": "whatsapp_sent",
                "notes": "Test follow-up log"
            },
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "log_id" in data
        assert data["message"] == "Follow-up logged successfully"


class TestRealtimeChat(TestAuth):
    """Real-time Chat Module Tests"""
    
    def test_get_chat_rooms(self, auth_headers):
        """Test GET /api/realtime-chat/rooms - returns user's chat rooms"""
        response = requests.get(f"{BASE_URL}/api/realtime-chat/rooms", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of rooms"
    
    def test_create_chat_room(self, auth_headers, auth_token):
        """Test POST /api/realtime-chat/rooms - creates a new chat room"""
        # Get current user ID from token
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert me_response.status_code == 200
        user_id = me_response.json()["id"]
        
        room_data = {
            "name": "TEST_Chat_Room",
            "room_type": "group",
            "members": [user_id],
            "description": "Test room for automated testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/realtime-chat/rooms",
            json=room_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["name"] == "TEST_Chat_Room"
        assert data["room_type"] == "group"
        
        return data["id"]
    
    def test_get_online_users(self, auth_headers):
        """Test GET /api/realtime-chat/online-users - returns online users"""
        response = requests.get(f"{BASE_URL}/api/realtime-chat/online-users", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of users"
    
    def test_send_message_rest_fallback(self, auth_headers):
        """Test POST /api/realtime-chat/rooms/{room_id}/messages - REST fallback for sending messages"""
        # First create a room
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        user_id = me_response.json()["id"]
        
        room_data = {
            "name": "TEST_Message_Room",
            "room_type": "group",
            "members": [user_id],
            "description": "Test room for message testing"
        }
        
        room_response = requests.post(
            f"{BASE_URL}/api/realtime-chat/rooms",
            json=room_data,
            headers=auth_headers
        )
        room_id = room_response.json()["id"]
        
        # Send a message
        message_data = {
            "room_id": room_id,
            "content": "TEST_Hello from automated test!",
            "message_type": "text"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/realtime-chat/rooms/{room_id}/messages",
            json=message_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert data["content"] == "TEST_Hello from automated test!"
        assert data["message_type"] == "text"
        
        return room_id
    
    def test_get_room_messages(self, auth_headers):
        """Test GET /api/realtime-chat/rooms/{room_id}/messages - get messages for a room"""
        # First create a room and send a message
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        user_id = me_response.json()["id"]
        
        room_data = {
            "name": "TEST_Get_Messages_Room",
            "room_type": "group",
            "members": [user_id]
        }
        
        room_response = requests.post(
            f"{BASE_URL}/api/realtime-chat/rooms",
            json=room_data,
            headers=auth_headers
        )
        room_id = room_response.json()["id"]
        
        # Send a message first
        message_data = {
            "room_id": room_id,
            "content": "TEST_Message for retrieval test",
            "message_type": "text"
        }
        requests.post(
            f"{BASE_URL}/api/realtime-chat/rooms/{room_id}/messages",
            json=message_data,
            headers=auth_headers
        )
        
        # Get messages
        response = requests.get(
            f"{BASE_URL}/api/realtime-chat/rooms/{room_id}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list of messages"
        assert len(data) > 0, "Should have at least one message"
        
        # Verify message structure
        msg = data[-1]  # Last message
        assert "id" in msg
        assert "content" in msg
        assert "sender_id" in msg


class TestBuyingDNAAccountPattern(TestAuth):
    """Test account-specific buying pattern endpoint"""
    
    def test_get_account_pattern_not_found(self, auth_headers):
        """Test GET /api/buying-dna/patterns/{account_id} - returns 404 for non-existent account"""
        response = requests.get(
            f"{BASE_URL}/api/buying-dna/patterns/non-existent-account-id",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
