"""
Customer Health Score API Tests
Tests for /api/customer-health/widget and /api/customer-health/scores endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('VITE_BACKEND_URL', '').rstrip('/')

class TestCustomerHealthAPI:
    """Customer Health Score endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed - skipping tests")
    
    def test_customer_health_widget_endpoint(self):
        """Test GET /api/customer-health/widget returns widget data"""
        response = self.session.get(f"{BASE_URL}/api/customer-health/widget")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "summary" in data, "Response should contain 'summary'"
        assert "attention_needed" in data, "Response should contain 'attention_needed'"
        assert "health_distribution" in data, "Response should contain 'health_distribution'"
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_customers" in summary, "Summary should contain 'total_customers'"
        assert "critical" in summary, "Summary should contain 'critical'"
        assert "at_risk" in summary, "Summary should contain 'at_risk'"
        assert "healthy" in summary, "Summary should contain 'healthy'"
        assert "excellent" in summary, "Summary should contain 'excellent'"
        assert "avg_health_score" in summary, "Summary should contain 'avg_health_score'"
        
        # Verify health_distribution structure
        health_dist = data["health_distribution"]
        assert "CRITICAL" in health_dist, "health_distribution should contain 'CRITICAL'"
        assert "AT_RISK" in health_dist, "health_distribution should contain 'AT_RISK'"
        assert "HEALTHY" in health_dist, "health_distribution should contain 'HEALTHY'"
        assert "EXCELLENT" in health_dist, "health_distribution should contain 'EXCELLENT'"
        
        # Verify attention_needed is a list
        assert isinstance(data["attention_needed"], list), "attention_needed should be a list"
        
        print(f"Widget data: total_customers={summary['total_customers']}, avg_score={summary['avg_health_score']}")
        print(f"Distribution: CRITICAL={health_dist['CRITICAL']}, AT_RISK={health_dist['AT_RISK']}, HEALTHY={health_dist['HEALTHY']}, EXCELLENT={health_dist['EXCELLENT']}")
    
    def test_customer_health_scores_endpoint(self):
        """Test GET /api/customer-health/scores returns health scores"""
        response = self.session.get(f"{BASE_URL}/api/customer-health/scores")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "scores" in data, "Response should contain 'scores'"
        assert "summary" in data, "Response should contain 'summary'"
        
        # Verify scores is a list
        assert isinstance(data["scores"], list), "scores should be a list"
        
        # Verify summary structure
        summary = data["summary"]
        assert "total_customers" in summary
        assert "critical" in summary
        assert "at_risk" in summary
        assert "healthy" in summary
        assert "excellent" in summary
        assert "avg_health_score" in summary
        assert "total_at_risk_outstanding" in summary
        
        print(f"Scores endpoint: {len(data['scores'])} customers returned")
        print(f"Summary: total={summary['total_customers']}, avg_score={summary['avg_health_score']}")
    
    def test_customer_health_scores_with_limit(self):
        """Test GET /api/customer-health/scores with limit parameter"""
        response = self.session.get(f"{BASE_URL}/api/customer-health/scores?limit=5")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert len(data["scores"]) <= 5, "Should return at most 5 scores"
        
        print(f"With limit=5: returned {len(data['scores'])} scores")
    
    def test_customer_health_scores_with_filter(self):
        """Test GET /api/customer-health/scores with filter_status parameter"""
        # Test filtering by CRITICAL status
        response = self.session.get(f"{BASE_URL}/api/customer-health/scores?filter_status=CRITICAL")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # All returned scores should be CRITICAL
        for score in data["scores"]:
            assert score["health_status"] == "CRITICAL", f"Expected CRITICAL status, got {score['health_status']}"
        
        print(f"Filter CRITICAL: returned {len(data['scores'])} critical customers")
    
    def test_customer_health_score_structure(self):
        """Test that individual health scores have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/customer-health/scores?limit=10")
        
        assert response.status_code == 200
        
        data = response.json()
        
        if len(data["scores"]) > 0:
            score = data["scores"][0]
            
            # Verify required fields
            required_fields = [
                "account_id", "account_name", "health_score", "health_status",
                "buying_status", "is_order_overdue",
                "debtor_segment", "payment_score", "total_outstanding",
                "overdue_amount", "invoices_overdue",
                "risk_factors", "recommended_actions", "priority_rank"
            ]
            
            for field in required_fields:
                assert field in score, f"Score should contain '{field}'"
            
            # Verify health_score is 0-100
            assert 0 <= score["health_score"] <= 100, f"health_score should be 0-100, got {score['health_score']}"
            
            # Verify health_status is valid
            valid_statuses = ["CRITICAL", "AT_RISK", "HEALTHY", "EXCELLENT"]
            assert score["health_status"] in valid_statuses, f"Invalid health_status: {score['health_status']}"
            
            # Verify buying_status is valid
            valid_buying = ["URGENT_FOLLOWUP", "GENTLE_REMINDER", "PRE_EMPTIVE_CHECK", "NO_ACTION", "NO_DATA"]
            assert score["buying_status"] in valid_buying, f"Invalid buying_status: {score['buying_status']}"
            
            # Verify debtor_segment is valid
            valid_segments = ["GOLD", "SILVER", "BRONZE", "BLOCKED", "NEW"]
            assert score["debtor_segment"] in valid_segments, f"Invalid debtor_segment: {score['debtor_segment']}"
            
            # Verify risk_factors and recommended_actions are lists
            assert isinstance(score["risk_factors"], list), "risk_factors should be a list"
            assert isinstance(score["recommended_actions"], list), "recommended_actions should be a list"
            
            print(f"Sample score: {score['account_name']} - Score: {score['health_score']}, Status: {score['health_status']}")
            print(f"  Buying: {score['buying_status']}, Debtor: {score['debtor_segment']}")
            print(f"  Risk factors: {score['risk_factors'][:2]}")
        else:
            print("No customer scores available (may need accounts with data)")
    
    def test_customer_health_widget_unauthorized(self):
        """Test that widget endpoint requires authentication"""
        # Create new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.get(f"{BASE_URL}/api/customer-health/widget")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthorized, got {response.status_code}"
        
        print("Unauthorized access correctly rejected")
    
    def test_customer_health_scores_unauthorized(self):
        """Test that scores endpoint requires authentication"""
        # Create new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.get(f"{BASE_URL}/api/customer-health/scores")
        
        # Should return 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthorized, got {response.status_code}"
        
        print("Unauthorized access correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
