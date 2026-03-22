#!/usr/bin/env python3
"""
Focused Approval Enforcement Test
"""

import requests
import json
import uuid
from datetime import datetime, timedelta

BASE_URL = "https://postgres-frontend-v1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@instabiz.com"
ADMIN_PASSWORD = "adminpassword"

class ApprovalTester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ERP-Approval-Test/1.0'})
        
    def login(self):
        response = self.session.post(f"{BASE_URL}/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=30)
        
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        return False
    
    def test_stock_transfer_approval(self):
        print("=== Stock Transfer Approval Test ===")
        
        # Get data
        wh_resp = self.session.get(f"{BASE_URL}/inventory/warehouses", timeout=30)
        item_resp = self.session.get(f"{BASE_URL}/inventory/items", timeout=30)
        
        warehouses = wh_resp.json()
        items = item_resp.json()
        
        # Create transfer
        transfer_data = {
            "from_warehouse": warehouses[0]["id"],
            "to_warehouse": warehouses[1]["id"],
            "items": [{"item_id": items[0]["id"], "quantity": 5.0}]
        }
        
        transfer_resp = self.session.post(f"{BASE_URL}/inventory/transfers", json=transfer_data, timeout=30)
        transfer_id = transfer_resp.json()["id"]
        print(f"✅ Transfer created: {transfer_id}")
        
        # Test issue without approval
        issue_resp = self.session.put(f"{BASE_URL}/inventory/transfers/{transfer_id}/issue", timeout=30)
        print(f"Issue without approval: {issue_resp.status_code} - {issue_resp.text}")
        
        if issue_resp.status_code == 409:
            print("✅ Stock transfer approval enforcement working")
            
            # Get approval and approve it
            approvals_resp = self.session.get(f"{BASE_URL}/approvals/requests?status=pending&module=Inventory", timeout=30)
            approvals = approvals_resp.json()
            approval = next((a for a in approvals if a["entity_id"] == transfer_id), None)
            
            if approval:
                approve_resp = self.session.put(f"{BASE_URL}/approvals/requests/{approval['id']}/approve", timeout=30)
                print(f"Approval: {approve_resp.status_code}")
                
                # Retry issue
                retry_resp = self.session.put(f"{BASE_URL}/inventory/transfers/{transfer_id}/issue", timeout=30)
                print(f"Issue after approval: {retry_resp.status_code}")
                
                if retry_resp.status_code == 200:
                    print("✅ Issue successful after approval")
                else:
                    print(f"❌ Issue failed after approval: {retry_resp.status_code}")
        else:
            print(f"❌ Expected 409, got {issue_resp.status_code}")
    
    def test_hrms_payroll_approval(self):
        print("\n=== HRMS Payroll Approval Test ===")
        
        # Get employee
        emp_resp = self.session.get(f"{BASE_URL}/hrms/employees", timeout=30)
        employees = emp_resp.json()
        
        if not employees:
            print("❌ No employees found")
            return
            
        employee_id = employees[0]["id"]
        
        payroll_data = {
            "employee_id": employee_id,
            "month": "December",
            "year": 2024,
            "days_present": 22.0,
            "days_absent": 8.0
        }
        
        # Test payroll without approval
        payroll_resp = self.session.post(f"{BASE_URL}/hrms/payroll", json=payroll_data, timeout=30)
        print(f"Payroll without approval: {payroll_resp.status_code} - {payroll_resp.text}")
        
        if payroll_resp.status_code == 409:
            print("✅ HRMS payroll approval enforcement working")
            
            # Get and approve
            approvals_resp = self.session.get(f"{BASE_URL}/approvals/requests?status=pending&module=HRMS", timeout=30)
            approvals = approvals_resp.json()
            approval = next((a for a in approvals if a["action"] == "Payroll Run"), None)
            
            if approval:
                approve_resp = self.session.put(f"{BASE_URL}/approvals/requests/{approval['id']}/approve", timeout=30)
                print(f"Approval: {approve_resp.status_code}")
                
                # Retry payroll
                retry_resp = self.session.post(f"{BASE_URL}/hrms/payroll", json=payroll_data, timeout=30)
                print(f"Payroll after approval: {retry_resp.status_code}")
                
                if retry_resp.status_code == 200:
                    print("✅ Payroll successful after approval")
                else:
                    print(f"❌ Payroll failed after approval: {retry_resp.status_code}")
        else:
            print(f"❌ Expected 409, got {payroll_resp.status_code}")
    
    def test_production_scrap_approval(self):
        print("\n=== Production Scrap Approval Test ===")
        
        # Get data
        machine_resp = self.session.get(f"{BASE_URL}/production/machines", timeout=30)
        item_resp = self.session.get(f"{BASE_URL}/inventory/items", timeout=30)
        
        machines = machine_resp.json()
        items = item_resp.json()
        
        # Create work order
        wo_data = {
            "item_id": items[0]["id"],
            "quantity_to_make": 100.0,
            "machine_id": machines[0]["id"],
            "priority": "high"
        }
        
        wo_resp = self.session.post(f"{BASE_URL}/production/work-orders", json=wo_data, timeout=30)
        wo_id = wo_resp.json()["id"]
        print(f"✅ Work order created: {wo_id}")
        
        # Start work order
        start_resp = self.session.put(f"{BASE_URL}/production/work-orders/{wo_id}/start", timeout=30)
        print(f"Work order started: {start_resp.status_code}")
        
        # Production entry with >7% scrap
        prod_data = {
            "wo_id": wo_id,
            "quantity_produced": 92.0,
            "wastage": 8.0,  # 8.7% scrap
            "start_time": "08:00:00",
            "end_time": "16:00:00",
            "operator": "Test Operator"
        }
        
        prod_resp = self.session.post(f"{BASE_URL}/production/production-entries", json=prod_data, timeout=30)
        print(f"Production with high scrap: {prod_resp.status_code} - {prod_resp.text}")
        
        if prod_resp.status_code == 409:
            print("✅ Production scrap approval enforcement working")
            
            # Get and approve
            approvals_resp = self.session.get(f"{BASE_URL}/approvals/requests?status=pending&module=Production", timeout=30)
            approvals = approvals_resp.json()
            approval = next((a for a in approvals if a["action"] == "Production Scrap"), None)
            
            if approval:
                approve_resp = self.session.put(f"{BASE_URL}/approvals/requests/{approval['id']}/approve", timeout=30)
                print(f"Approval: {approve_resp.status_code}")
                
                # Retry production
                retry_resp = self.session.post(f"{BASE_URL}/production/production-entries", json=prod_data, timeout=30)
                print(f"Production after approval: {retry_resp.status_code}")
                
                if retry_resp.status_code == 200:
                    print("✅ Production successful after approval")
                else:
                    print(f"❌ Production failed after approval: {retry_resp.status_code}")
        else:
            print(f"❌ Expected 409, got {prod_resp.status_code}")
    
    def test_production_cancel_approval(self):
        print("\n=== Production Cancel Approval Test ===")
        
        # Get data
        machine_resp = self.session.get(f"{BASE_URL}/production/machines", timeout=30)
        item_resp = self.session.get(f"{BASE_URL}/inventory/items", timeout=30)
        
        machines = machine_resp.json()
        items = item_resp.json()
        
        # Create work order
        wo_data = {
            "item_id": items[0]["id"],
            "quantity_to_make": 50.0,
            "machine_id": machines[0]["id"],
            "priority": "normal"
        }
        
        wo_resp = self.session.post(f"{BASE_URL}/production/work-orders", json=wo_data, timeout=30)
        wo_id = wo_resp.json()["id"]
        print(f"✅ Work order created: {wo_id}")
        
        # Try to cancel
        cancel_resp = self.session.put(f"{BASE_URL}/production/work-orders/{wo_id}/cancel", timeout=30)
        print(f"Cancel without approval: {cancel_resp.status_code} - {cancel_resp.text}")
        
        if cancel_resp.status_code == 409:
            print("✅ Production cancel approval enforcement working")
            
            # Get and approve
            approvals_resp = self.session.get(f"{BASE_URL}/approvals/requests?status=pending&module=Production", timeout=30)
            approvals = approvals_resp.json()
            approval = next((a for a in approvals if a["action"] == "Cancel Production Order"), None)
            
            if approval:
                approve_resp = self.session.put(f"{BASE_URL}/approvals/requests/{approval['id']}/approve", timeout=30)
                print(f"Approval: {approve_resp.status_code}")
                
                # Retry cancel
                retry_resp = self.session.put(f"{BASE_URL}/production/work-orders/{wo_id}/cancel", timeout=30)
                print(f"Cancel after approval: {retry_resp.status_code}")
                
                if retry_resp.status_code == 200:
                    print("✅ Cancel successful after approval")
                else:
                    print(f"❌ Cancel failed after approval: {retry_resp.status_code}")
        else:
            print(f"❌ Expected 409, got {cancel_resp.status_code}")
    
    def run_tests(self):
        print("🚀 Starting Approval Enforcement Tests")
        print("=" * 50)
        
        if not self.login():
            print("❌ Login failed")
            return
            
        print("✅ Login successful")
        
        self.test_stock_transfer_approval()
        self.test_hrms_payroll_approval()
        self.test_production_scrap_approval()
        self.test_production_cancel_approval()
        
        print("\n" + "=" * 50)
        print("✅ All approval enforcement tests completed")

if __name__ == "__main__":
    tester = ApprovalTester()
    tester.run_tests()