"""
Test Suite for AI BI Dashboard APIs
Features tested:
1. Natural Language Query API - POST /api/ai/nl-query
2. AI Insights Generation API - POST /api/ai/generate-insights
3. AI Predictions API - POST /api/ai/predict
4. AI Smart Alerts API - POST /api/ai/smart-alerts
5. Query History API - GET /api/ai/query-history
6. Alerts History API - GET /api/ai/alerts-history
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@instabiz.com"
TEST_PASSWORD = "adminpassword"


class TestAIBIDashboard:
    """AI Business Intelligence Dashboard API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    # ==================== 1. NATURAL LANGUAGE QUERY TESTS ====================
    def test_nl_query_basic(self):
        """Test basic natural language query"""
        response = self.session.post(f"{BASE_URL}/api/ai/nl-query", json={
            "query": "What is our current sales status?"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "query" in data, "Response should contain 'query' field"
        assert "answer" in data, "Response should contain 'answer' field"
        assert "data_snapshot" in data, "Response should contain 'data_snapshot' field"
        assert data["query"] == "What is our current sales status?"
        assert len(data["answer"]) > 0, "AI answer should not be empty"
        print(f"✓ NL Query successful - Answer length: {len(data['answer'])} chars")
    
    def test_nl_query_top_products(self):
        """Test query about top products"""
        response = self.session.post(f"{BASE_URL}/api/ai/nl-query", json={
            "query": "What were our top 5 products this month?"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
        print(f"✓ Top products query successful")
    
    def test_nl_query_with_context(self):
        """Test NL query with additional context"""
        response = self.session.post(f"{BASE_URL}/api/ai/nl-query", json={
            "query": "How much do customers owe us?",
            "context": "Focus on overdue amounts"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "data_snapshot" in data
        # Verify data snapshot contains AR/AP info
        assert "ar" in data["data_snapshot"] or "mtd_sales" in data["data_snapshot"]
        print(f"✓ NL Query with context successful")
    
    def test_nl_query_empty_query_validation(self):
        """Test that empty query is handled"""
        response = self.session.post(f"{BASE_URL}/api/ai/nl-query", json={
            "query": ""
        })
        # Empty query might still work but return generic response
        # or might return 422 validation error
        assert response.status_code in [200, 422], f"Unexpected status: {response.status_code}"
        print(f"✓ Empty query handled with status {response.status_code}")
    
    # ==================== 2. AI INSIGHTS GENERATION TESTS ====================
    def test_generate_insights_all_areas(self):
        """Test insights generation for all areas"""
        response = self.session.post(f"{BASE_URL}/api/ai/generate-insights", json={
            "focus_area": "all",
            "time_period": "month"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "focus_area" in data
        assert "time_period" in data
        assert "insights" in data
        assert "generated_at" in data
        assert "data_basis" in data
        
        assert data["focus_area"] == "all"
        assert data["time_period"] == "month"
        assert len(data["insights"]) > 0, "Insights should not be empty"
        print(f"✓ All areas insights generated - Length: {len(data['insights'])} chars")
    
    def test_generate_insights_sales(self):
        """Test insights generation for sales focus"""
        response = self.session.post(f"{BASE_URL}/api/ai/generate-insights", json={
            "focus_area": "sales",
            "time_period": "quarter"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["focus_area"] == "sales"
        assert data["time_period"] == "quarter"
        assert len(data["insights"]) > 0
        print(f"✓ Sales insights generated")
    
    def test_generate_insights_inventory(self):
        """Test insights generation for inventory focus"""
        response = self.session.post(f"{BASE_URL}/api/ai/generate-insights", json={
            "focus_area": "inventory",
            "time_period": "week"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["focus_area"] == "inventory"
        assert "data_basis" in data
        assert "low_stock_count" in data["data_basis"]
        print(f"✓ Inventory insights generated")
    
    def test_generate_insights_production(self):
        """Test insights generation for production focus"""
        response = self.session.post(f"{BASE_URL}/api/ai/generate-insights", json={
            "focus_area": "production",
            "time_period": "month"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["focus_area"] == "production"
        assert "scrap_rate" in data["data_basis"]
        print(f"✓ Production insights generated")
    
    def test_generate_insights_finance(self):
        """Test insights generation for finance focus"""
        response = self.session.post(f"{BASE_URL}/api/ai/generate-insights", json={
            "focus_area": "finance",
            "time_period": "year"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["focus_area"] == "finance"
        print(f"✓ Finance insights generated")
    
    # ==================== 3. PREDICTIVE ANALYTICS TESTS ====================
    def test_predict_sales(self):
        """Test sales prediction"""
        response = self.session.post(f"{BASE_URL}/api/ai/predict", json={
            "metric": "sales",
            "horizon_days": 30
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "metric" in data
        assert "horizon_days" in data
        assert "prediction" in data
        assert "historical_data" in data
        assert "current_state" in data
        assert "generated_at" in data
        
        assert data["metric"] == "sales"
        assert data["horizon_days"] == 30
        assert len(data["prediction"]) > 0, "Prediction should not be empty"
        print(f"✓ Sales prediction generated - Length: {len(data['prediction'])} chars")
    
    def test_predict_inventory(self):
        """Test inventory prediction"""
        response = self.session.post(f"{BASE_URL}/api/ai/predict", json={
            "metric": "inventory",
            "horizon_days": 14
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "inventory"
        assert data["horizon_days"] == 14
        assert len(data["prediction"]) > 0
        print(f"✓ Inventory prediction generated")
    
    def test_predict_cash_flow(self):
        """Test cash flow prediction"""
        response = self.session.post(f"{BASE_URL}/api/ai/predict", json={
            "metric": "cash_flow",
            "horizon_days": 60
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["metric"] == "cash_flow"
        assert data["horizon_days"] == 60
        assert "current_state" in data
        assert "ar" in data["current_state"]
        assert "ap" in data["current_state"]
        print(f"✓ Cash flow prediction generated")
    
    def test_predict_different_horizons(self):
        """Test predictions with different time horizons"""
        horizons = [7, 14, 30, 60, 90]
        for horizon in horizons:
            response = self.session.post(f"{BASE_URL}/api/ai/predict", json={
                "metric": "sales",
                "horizon_days": horizon
            })
            assert response.status_code == 200, f"Failed for horizon {horizon}"
            data = response.json()
            assert data["horizon_days"] == horizon
        print(f"✓ All horizon values tested: {horizons}")
    
    # ==================== 4. SMART ALERTS TESTS ====================
    def test_smart_alerts_all(self):
        """Test smart alerts for all areas"""
        response = self.session.post(f"{BASE_URL}/api/ai/smart-alerts", json={
            "check_type": "all"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "check_type" in data
        assert "alerts" in data
        assert "summary" in data
        assert "generated_at" in data
        
        assert data["check_type"] == "all"
        assert len(data["alerts"]) > 0, "Alerts should not be empty"
        
        # Verify summary contains expected fields
        summary = data["summary"]
        assert "overdue_invoices" in summary
        assert "overdue_amount" in summary
        assert "low_stock_items" in summary
        assert "scrap_rate" in summary
        assert "ar_ap_gap" in summary
        print(f"✓ Smart alerts generated - Length: {len(data['alerts'])} chars")
    
    def test_smart_alerts_sales(self):
        """Test smart alerts for sales"""
        response = self.session.post(f"{BASE_URL}/api/ai/smart-alerts", json={
            "check_type": "sales"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["check_type"] == "sales"
        assert "alerts" in data
        print(f"✓ Sales alerts generated")
    
    def test_smart_alerts_inventory(self):
        """Test smart alerts for inventory"""
        response = self.session.post(f"{BASE_URL}/api/ai/smart-alerts", json={
            "check_type": "inventory"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["check_type"] == "inventory"
        print(f"✓ Inventory alerts generated")
    
    def test_smart_alerts_production(self):
        """Test smart alerts for production"""
        response = self.session.post(f"{BASE_URL}/api/ai/smart-alerts", json={
            "check_type": "production"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["check_type"] == "production"
        print(f"✓ Production alerts generated")
    
    def test_smart_alerts_payments(self):
        """Test smart alerts for payments"""
        response = self.session.post(f"{BASE_URL}/api/ai/smart-alerts", json={
            "check_type": "payments"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["check_type"] == "payments"
        print(f"✓ Payments alerts generated")
    
    # ==================== 5. HISTORY ENDPOINTS TESTS ====================
    def test_query_history(self):
        """Test query history retrieval"""
        # First make a query to ensure there's history
        self.session.post(f"{BASE_URL}/api/ai/nl-query", json={
            "query": "Test query for history"
        })
        
        # Wait a moment for the query to be saved
        time.sleep(0.5)
        
        response = self.session.get(f"{BASE_URL}/api/ai/query-history?limit=10")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Query history should be a list"
        print(f"✓ Query history retrieved - {len(data)} items")
    
    def test_alerts_history(self):
        """Test alerts history retrieval"""
        # First generate an alert to ensure there's history
        self.session.post(f"{BASE_URL}/api/ai/smart-alerts", json={
            "check_type": "all"
        })
        
        # Wait a moment for the alert to be saved
        time.sleep(0.5)
        
        response = self.session.get(f"{BASE_URL}/api/ai/alerts-history?limit=10")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Alerts history should be a list"
        print(f"✓ Alerts history retrieved - {len(data)} items")
    
    # ==================== 6. AUTHENTICATION TESTS ====================
    def test_nl_query_without_auth(self):
        """Test that NL query requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/ai/nl-query", json={
            "query": "Test query"
        })
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Authentication required for NL query")
    
    def test_insights_without_auth(self):
        """Test that insights require authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/ai/generate-insights", json={
            "focus_area": "all",
            "time_period": "month"
        })
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Authentication required for insights")
    
    def test_predict_without_auth(self):
        """Test that predictions require authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/ai/predict", json={
            "metric": "sales",
            "horizon_days": 30
        })
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Authentication required for predictions")
    
    def test_alerts_without_auth(self):
        """Test that alerts require authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/ai/smart-alerts", json={
            "check_type": "all"
        })
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Authentication required for alerts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
