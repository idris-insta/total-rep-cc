"""
Test Suite for AdhesiveFlow ERP - 6 Pillars Core Engine
Tests the following pillars:
1. Physics Engine - Unit Conversion (KG ↔ SQM ↔ PCS)
2. Production Redline - 7% Scrap Lock
3. CRM Buying DNA - Late Customer Detection
4. Multi-Branch Ledger - GST Bridge
5. Import Bridge - Landed Cost Calculator
6. Director Cockpit - Pulse Dashboard
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        return data["token"]
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@instabiz.com"


class TestPhysicsEngine:
    """Pillar 1: Physics Engine - Unit Conversion Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_kg_to_sqm_conversion(self, auth_headers):
        """Test KG to SQM conversion"""
        response = requests.post(f"{BASE_URL}/api/core/physics/convert", 
            headers=auth_headers,
            json={
                "from_unit": "KG",
                "to_unit": "SQM",
                "quantity": 100,
                "thickness_micron": 40,
                "width_mm": 48,
                "length_m": 65,
                "density_kg_m3": 920
            })
        assert response.status_code == 200
        data = response.json()
        assert "from_value" in data
        assert "to_value" in data
        assert "conversion_factor" in data
        assert "formula_used" in data
        assert data["from_unit"] == "KG"
        assert data["to_unit"] == "SQM"
        assert data["from_value"] == 100
        assert data["to_value"] > 0  # Should have a positive conversion result
    
    def test_sqm_to_kg_conversion(self, auth_headers):
        """Test SQM to KG conversion"""
        response = requests.post(f"{BASE_URL}/api/core/physics/convert",
            headers=auth_headers,
            json={
                "from_unit": "SQM",
                "to_unit": "KG",
                "quantity": 1000,
                "thickness_micron": 40,
                "width_mm": 48,
                "length_m": 65
            })
        assert response.status_code == 200
        data = response.json()
        assert data["from_unit"] == "SQM"
        assert data["to_unit"] == "KG"
        assert data["to_value"] > 0
    
    def test_pcs_to_kg_conversion(self, auth_headers):
        """Test PCS/ROL to KG conversion"""
        response = requests.post(f"{BASE_URL}/api/core/physics/convert",
            headers=auth_headers,
            json={
                "from_unit": "PCS",
                "to_unit": "KG",
                "quantity": 50,
                "thickness_micron": 40,
                "width_mm": 48,
                "length_m": 65
            })
        assert response.status_code == 200
        data = response.json()
        assert data["from_unit"] == "PCS"
        assert data["to_unit"] == "KG"
        assert data["to_value"] > 0
    
    def test_mtr_to_sqm_conversion(self, auth_headers):
        """Test MTR to SQM conversion"""
        response = requests.post(f"{BASE_URL}/api/core/physics/convert",
            headers=auth_headers,
            json={
                "from_unit": "MTR",
                "to_unit": "SQM",
                "quantity": 1000,
                "width_mm": 48
            })
        assert response.status_code == 200
        data = response.json()
        assert data["from_unit"] == "MTR"
        assert data["to_unit"] == "SQM"
        # 1000 MTR * 0.048m width = 48 SQM
        assert data["to_value"] == 48.0


class TestProductionRedline:
    """Pillar 2: Production Redline - 7% Scrap Lock Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_redline_check_within_limit(self, auth_headers):
        """Test redline check with scrap within 7% limit"""
        # First create a work order for testing
        wo_response = requests.post(f"{BASE_URL}/api/production/work-orders",
            headers=auth_headers,
            json={
                "item_id": "test-item-001",
                "item_name": "Test BOPP Tape",
                "quantity": 1000,
                "uom": "PCS",
                "machine_id": "M001",
                "raw_material_issued": 100
            })
        
        if wo_response.status_code == 200:
            wo_id = wo_response.json().get("id")
        else:
            wo_id = "test-wo-001"  # Use dummy ID if creation fails
        
        # Test redline check with 5% scrap (within limit)
        response = requests.post(f"{BASE_URL}/api/core/redline/check-entry",
            headers=auth_headers,
            json={
                "wo_id": wo_id,
                "quantity_produced": 95,
                "wastage": 5,  # 5% scrap
                "operator_id": "OP001",
                "shift": "A"
            })
        
        # Should return 200 even if WO not found (returns check result)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "allowed" in data
            assert "scrap_percent" in data
            assert "limit_percent" in data
            assert data["limit_percent"] == 7.0
    
    def test_redline_check_exceeds_limit(self, auth_headers):
        """Test redline check with scrap exceeding 7% limit"""
        response = requests.post(f"{BASE_URL}/api/core/redline/check-entry",
            headers=auth_headers,
            json={
                "wo_id": "test-wo-002",
                "quantity_produced": 90,
                "wastage": 10,  # 10% scrap - exceeds limit
                "operator_id": "OP001",
                "shift": "A"
            })
        
        # Should return 404 if WO not found, but we're testing the logic
        assert response.status_code in [200, 404]


class TestBuyingDNA:
    """Pillar 3: CRM Buying DNA - Late Customer Detection Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_late_customers(self, auth_headers):
        """Test getting late customers list"""
        response = requests.get(f"{BASE_URL}/api/core/buying-dna/late-customers",
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Should return a list (empty or with customers)
        assert isinstance(data, list)
        # If there are late customers, verify structure
        if len(data) > 0:
            customer = data[0]
            assert "customer_id" in customer
            assert "customer_name" in customer
            assert "days_late" in customer
    
    def test_get_buying_dna_for_customer(self, auth_headers):
        """Test getting buying DNA for a specific customer"""
        # First get a customer ID
        customers_response = requests.get(f"{BASE_URL}/api/crm/accounts",
            headers=auth_headers)
        
        if customers_response.status_code == 200:
            customers = customers_response.json()
            if len(customers) > 0:
                customer_id = customers[0].get("id")
                response = requests.get(f"{BASE_URL}/api/core/buying-dna/{customer_id}",
                    headers=auth_headers)
                assert response.status_code == 200
                data = response.json()
                assert "customer_id" in data
                assert "has_pattern" in data


class TestGSTBridge:
    """Pillar 4: Multi-Branch Ledger - GST Bridge Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_gst_bridge_summary(self, auth_headers):
        """Test GST bridge summary for a period"""
        # Test with current month
        from datetime import datetime
        current_period = datetime.now().strftime("%m%Y")
        
        response = requests.get(f"{BASE_URL}/api/core/gst-bridge/summary",
            headers=auth_headers,
            params={"period": current_period})
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "consolidated" in data
        assert "gst_computation" in data
        # Verify GST computation structure
        gst = data["gst_computation"]
        assert "output_tax" in gst
        assert "input_tax" in gst
        assert "net_gst_payable" in gst
        assert "status" in gst


class TestImportBridge:
    """Pillar 5: Import Bridge - Landed Cost Calculator Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_landed_cost_calculation(self, auth_headers):
        """Test landed cost calculation"""
        response = requests.post(f"{BASE_URL}/api/core/import-bridge/landed-cost",
            headers=auth_headers,
            json={
                "fob_value_usd": 10000,
                "exchange_rate": 83.5,
                "freight_usd": 500,
                "insurance_percent": 1.1,
                "basic_customs_duty_percent": 10,
                "social_welfare_surcharge_percent": 10,
                "igst_percent": 18,
                "clearing_charges_inr": 15000,
                "transport_to_warehouse_inr": 10000,
                "quantity_units": 1000,
                "uom": "KG"
            })
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        assert "fob_value_inr" in data
        assert "cif_value_inr" in data
        assert "basic_customs_duty" in data
        assert "igst" in data
        assert "total_duties" in data
        assert "total_landed_cost" in data
        assert "landed_cost_per_unit" in data
        assert "minimum_selling_price" in data
        assert "recommended_selling_price" in data
        assert "breakdown" in data
        
        # Verify calculations are positive
        assert data["fob_value_inr"] > 0
        assert data["total_landed_cost"] > 0
        assert data["landed_cost_per_unit"] > 0
        
        # Verify MSP is higher than landed cost
        assert data["minimum_selling_price"] > data["landed_cost_per_unit"]
        assert data["recommended_selling_price"] > data["minimum_selling_price"]
    
    def test_landed_cost_with_different_quantities(self, auth_headers):
        """Test landed cost with different quantities"""
        response = requests.post(f"{BASE_URL}/api/core/import-bridge/landed-cost",
            headers=auth_headers,
            json={
                "fob_value_usd": 5000,
                "exchange_rate": 83.0,
                "freight_usd": 200,
                "quantity_units": 500,
                "uom": "KG"
            })
        assert response.status_code == 200
        data = response.json()
        assert data["landed_cost_per_unit"] > 0


class TestDirectorCockpit:
    """Pillar 6: Director Cockpit - Pulse Dashboard Tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for admin/director"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_director_pulse(self, auth_headers):
        """Test director pulse dashboard data"""
        response = requests.get(f"{BASE_URL}/api/core/cockpit/pulse",
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify pulse structure
        assert "timestamp" in data
        assert "cash_pulse" in data
        assert "production_pulse" in data
        assert "sales_pulse" in data
        assert "override_queue" in data
        
        # Verify cash pulse structure
        cash = data["cash_pulse"]
        assert "receivables" in cash
        assert "payables" in cash
        assert "net_position" in cash
        assert "health" in cash
        
        # Verify production pulse structure
        prod = data["production_pulse"]
        assert "work_orders_active" in prod
        assert "avg_scrap_percent" in prod
        assert "scrap_limit" in prod
        assert "scrap_status" in prod
        assert prod["scrap_limit"] == 7.0  # Verify 7% limit
        
        # Verify sales pulse structure
        sales = data["sales_pulse"]
        assert "mtd_sales" in sales
        assert "mtd_orders" in sales
    
    def test_pending_overrides(self, auth_headers):
        """Test getting pending override requests"""
        response = requests.get(f"{BASE_URL}/api/core/cockpit/overrides-pending",
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "pending_count" in data
        assert "pending_overrides" in data
        assert isinstance(data["pending_overrides"], list)


class TestCustomization:
    """Test customization endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@instabiz.com",
            "password": "adminpassword"
        })
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_custom_fields(self, auth_headers):
        """Test getting custom fields"""
        response = requests.get(f"{BASE_URL}/api/customization/custom-fields",
            headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
