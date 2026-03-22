#!/usr/bin/env python3
"""
Backend API Testing Script for Adhesive ERP System
Tests all backend endpoints as per review request
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "https://postgres-frontend-v1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@instabiz.com"
ADMIN_PASSWORD = "adminpassword"

class APITester:
    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ERP-Test-Client/1.0'})
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def make_request(self, method, endpoint, data=None, params=None):
        """Make authenticated API request"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
            
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.Timeout:
            print(f"Request timeout for {method} {endpoint}")
            return None
        except requests.exceptions.ConnectionError:
            print(f"Connection error for {method} {endpoint}")
            return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None
    
    def test_auth_login(self):
        """Test 1: POST /api/auth/login"""
        print("\n=== Testing Authentication ===")
        
        response = self.make_request("POST", "/auth/login", {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response and response.status_code == 200:
            data = response.json()
            if "token" in data:
                self.token = data["token"]
                self.log_test("Auth Login", True, f"Token received for {data.get('user', {}).get('email')}")
                return True
            else:
                self.log_test("Auth Login", False, "No token in response")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Auth Login", False, f"Status: {status}, Error: {error}")
        return False
    
    def test_auth_me(self):
        """Test 2: GET /api/auth/me"""
        response = self.make_request("GET", "/auth/me")
        
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Auth Me", True, f"User: {data.get('name')} ({data.get('role')})")
            return True
        else:
            status = response.status_code if response else "No response"
            self.log_test("Auth Me", False, f"Status: {status}")
        return False
    
    def test_hrms_employees(self):
        """Test 3-4: HRMS Employee CRUD"""
        print("\n=== Testing HRMS ===")
        
        # Create employee
        employee_data = {
            "employee_code": f"EMP{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": "Rajesh Kumar",
            "email": f"rajesh.kumar.{uuid.uuid4().hex[:8]}@instabiz.com",
            "phone": "9876543210",
            "department": "Production",
            "designation": "Machine Operator",
            "location": "Mumbai Plant",
            "date_of_joining": "2024-01-15",
            "shift_timing": "08:00-17:00",
            "basic_salary": 25000.0,
            "hra": 5000.0,
            "pf": 12.0,
            "esi": 1.75,
            "pt": 200.0
        }
        
        response = self.make_request("POST", "/hrms/employees", employee_data)
        
        if response and response.status_code == 200:
            emp_data = response.json()
            employee_id = emp_data.get("id")
            self.log_test("Create Employee", True, f"Employee ID: {employee_id}")
            
            # List employees
            response = self.make_request("GET", "/hrms/employees")
            if response and response.status_code == 200:
                employees = response.json()
                found = any(emp.get("id") == employee_id for emp in employees)
                self.log_test("List Employees", found, f"Found {len(employees)} employees, created employee present: {found}")
                return employee_id
            else:
                self.log_test("List Employees", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Create Employee", False, f"Status: {status}, Error: {error}")
        return None
    
    def test_hrms_attendance(self, employee_id):
        """Test 5: HRMS Attendance"""
        if not employee_id:
            self.log_test("Mark Attendance", False, "No employee ID available")
            return
            
        today = datetime.now().strftime("%Y-%m-%d")
        attendance_data = {
            "employee_id": employee_id,
            "date": today,
            "check_in": "08:30:00",
            "check_out": "17:15:00",
            "status": "present",
            "hours_worked": 8.75
        }
        
        response = self.make_request("POST", "/hrms/attendance", attendance_data)
        
        if response and response.status_code == 200:
            self.log_test("Mark Attendance", True, f"Attendance marked for {today}")
            
            # Get attendance
            response = self.make_request("GET", "/hrms/attendance", params={"date": today})
            if response and response.status_code == 200:
                attendance_list = response.json()
                found = any(att.get("employee_id") == employee_id for att in attendance_list)
                self.log_test("Get Attendance", found, f"Found {len(attendance_list)} attendance records")
            else:
                self.log_test("Get Attendance", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Mark Attendance", False, f"Status: {status}, Error: {error}")
    
    def test_hrms_leave_requests(self, employee_id):
        """Test 6: HRMS Leave Requests"""
        if not employee_id:
            self.log_test("Create Leave Request", False, "No employee ID available")
            return
            
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        leave_data = {
            "employee_id": employee_id,
            "leave_type": "Sick Leave",
            "from_date": tomorrow,
            "to_date": day_after,
            "reason": "Medical checkup and recovery"
        }
        
        response = self.make_request("POST", "/hrms/leave-requests", leave_data)
        
        if response and response.status_code == 200:
            leave_data = response.json()
            leave_id = leave_data.get("id")
            self.log_test("Create Leave Request", True, f"Leave ID: {leave_id}")
            
            # Approve leave
            response = self.make_request("PUT", f"/hrms/leave-requests/{leave_id}/approve")
            if response and response.status_code == 200:
                self.log_test("Approve Leave Request", True, "Leave approved successfully")
            else:
                self.log_test("Approve Leave Request", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Create Leave Request", False, f"Status: {status}, Error: {error}")
    
    def test_quality_inspections(self):
        """Test 7: Quality Inspections"""
        print("\n=== Testing Quality ===")
        
        inspection_data = {
            "inspection_type": "Incoming Material",
            "reference_type": "Purchase Order",
            "reference_id": f"PO-{uuid.uuid4().hex[:8]}",
            "item_id": f"ITEM-{uuid.uuid4().hex[:8]}",
            "batch_number": f"BATCH-{datetime.now().strftime('%Y%m%d')}-001",
            "test_parameters": [
                {"parameter": "Thickness", "expected": "0.5mm", "actual": "0.52mm", "result": "pass"},
                {"parameter": "Adhesion Strength", "expected": ">2N/cm", "actual": "2.3N/cm", "result": "pass"},
                {"parameter": "Color Match", "expected": "Blue", "actual": "Blue", "result": "pass"}
            ],
            "inspector": "Quality Team",
            "notes": "All parameters within acceptable limits"
        }
        
        response = self.make_request("POST", "/quality/inspections", inspection_data)
        
        if response and response.status_code == 200:
            insp_data = response.json()
            self.log_test("Create QC Inspection", True, f"Inspection: {insp_data.get('inspection_number')}")
            
            # List inspections
            response = self.make_request("GET", "/quality/inspections")
            if response and response.status_code == 200:
                inspections = response.json()
                self.log_test("List QC Inspections", True, f"Found {len(inspections)} inspections")
            else:
                self.log_test("List QC Inspections", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Create QC Inspection", False, f"Status: {status}, Error: {error}")
    
    def test_quality_complaints(self):
        """Test 8: Quality Complaints"""
        complaint_data = {
            "account_id": f"ACC-{uuid.uuid4().hex[:8]}",
            "invoice_id": f"INV-{uuid.uuid4().hex[:8]}",
            "batch_number": f"BATCH-{datetime.now().strftime('%Y%m%d')}-002",
            "complaint_type": "Adhesion Failure",
            "description": "Customer reported that tape is not sticking properly to cardboard surfaces",
            "severity": "high"
        }
        
        response = self.make_request("POST", "/quality/complaints", complaint_data)
        
        if response and response.status_code == 200:
            complaint_data = response.json()
            self.log_test("Create Complaint", True, f"Complaint: {complaint_data.get('complaint_number')}")
            
            # List complaints
            response = self.make_request("GET", "/quality/complaints")
            if response and response.status_code == 200:
                complaints = response.json()
                self.log_test("List Complaints", True, f"Found {len(complaints)} complaints")
            else:
                self.log_test("List Complaints", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Create Complaint", False, f"Status: {status}, Error: {error}")
    
    def test_quality_tds(self):
        """Test 9: Quality TDS Documents"""
        tds_data = {
            "item_id": f"ITEM-{uuid.uuid4().hex[:8]}",
            "document_type": "Technical Data Sheet",
            "document_url": "https://example.com/tds/adhesive-tape-001.pdf",
            "version": "v2.1",
            "notes": "Updated specifications for improved adhesion"
        }
        
        response = self.make_request("POST", "/quality/tds", tds_data)
        
        if response and response.status_code == 200:
            tds_data = response.json()
            self.log_test("Create TDS Document", True, f"TDS ID: {tds_data.get('id')}")
            
            # List TDS
            response = self.make_request("GET", "/quality/tds")
            if response and response.status_code == 200:
                tds_list = response.json()
                self.log_test("List TDS Documents", True, f"Found {len(tds_list)} TDS documents")
            else:
                self.log_test("List TDS Documents", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Create TDS Document", False, f"Status: {status}, Error: {error}")
    
    def test_inventory_setup(self):
        """Test 10: Ensure warehouse and item exist"""
        print("\n=== Testing Inventory Setup ===")
        
        # Check warehouses
        response = self.make_request("GET", "/inventory/warehouses")
        warehouse_id = None
        
        if response and response.status_code == 200:
            warehouses = response.json()
            if warehouses:
                warehouse_id = warehouses[0]["id"]
                self.log_test("Check Warehouses", True, f"Found {len(warehouses)} warehouses")
            else:
                # Create warehouse
                warehouse_data = {
                    "warehouse_code": "WH-MAIN",
                    "warehouse_name": "Main Warehouse",
                    "warehouse_type": "Main",
                    "address": "Industrial Area, Mumbai",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "pincode": "400001",
                    "is_active": True
                }
                
                response = self.make_request("POST", "/inventory/warehouses", warehouse_data)
                if response and response.status_code == 200:
                    wh_data = response.json()
                    warehouse_id = wh_data.get("id")
                    self.log_test("Create Warehouse", True, f"Warehouse ID: {warehouse_id}")
                else:
                    self.log_test("Create Warehouse", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Check Warehouses", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Check items
        response = self.make_request("GET", "/inventory/items")
        item_id = None
        
        if response and response.status_code == 200:
            items = response.json()
            if items:
                item_id = items[0]["id"]
                self.log_test("Check Items", True, f"Found {len(items)} items")
            else:
                # Create item
                item_data = {
                    "item_code": f"TAPE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "item_name": "Double Sided Adhesive Tape",
                    "category": "Adhesive Tapes",
                    "item_type": "Finished Goods",
                    "hsn_code": "39191090",
                    "uom": "Rolls",
                    "thickness": 0.5,
                    "width": 25.0,
                    "length": 50.0,
                    "color": "Clear",
                    "adhesive_type": "Acrylic",
                    "base_material": "PET Film",
                    "grade": "Industrial",
                    "standard_cost": 150.0,
                    "selling_price": 200.0,
                    "min_order_qty": 10,
                    "reorder_level": 50,
                    "safety_stock": 20,
                    "lead_time_days": 7,
                    "is_active": True
                }
                
                response = self.make_request("POST", "/inventory/items", item_data)
                if response and response.status_code == 200:
                    item_data = response.json()
                    item_id = item_data.get("id")
                    self.log_test("Create Item", True, f"Item ID: {item_id}")
                else:
                    self.log_test("Create Item", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Check Items", False, f"Status: {response.status_code if response else 'No response'}")
        
        return warehouse_id, item_id
    
    def test_production_setup(self):
        """Test 11: Ensure machine exists"""
        print("\n=== Testing Production Setup ===")
        
        response = self.make_request("GET", "/production/machines")
        machine_id = None
        
        if response and response.status_code == 200:
            machines = response.json()
            if machines:
                machine_id = machines[0]["id"]
                self.log_test("Check Machines", True, f"Found {len(machines)} machines")
            else:
                # Create machine
                machine_data = {
                    "machine_code": f"MC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "machine_name": "Tape Coating Machine #1",
                    "machine_type": "Coating",
                    "capacity": 1000.0,
                    "location": "Production Floor A",
                    "status": "active"
                }
                
                response = self.make_request("POST", "/production/machines", machine_data)
                if response and response.status_code == 200:
                    machine_data = response.json()
                    machine_id = machine_data.get("id")
                    self.log_test("Create Machine", True, f"Machine ID: {machine_id}")
                else:
                    self.log_test("Create Machine", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Check Machines", False, f"Status: {response.status_code if response else 'No response'}")
        
        return machine_id
    
    def test_production_workflow(self, item_id, machine_id):
        """Test 12-15: Production + Inventory Integration"""
        print("\n=== Testing Production Workflow ===")
        
        if not item_id or not machine_id:
            self.log_test("Production Workflow", False, "Missing item_id or machine_id")
            return
        
        # Create work order
        wo_data = {
            "item_id": item_id,
            "quantity_to_make": 100.0,
            "machine_id": machine_id,
            "thickness": 0.5,
            "color": "Clear",
            "width": 25.0,
            "length": 50.0,
            "brand": "InstaBiz",
            "priority": "high"
        }
        
        response = self.make_request("POST", "/production/work-orders", wo_data)
        
        if response and response.status_code == 200:
            wo_data = response.json()
            wo_id = wo_data.get("id")
            self.log_test("Create Work Order", True, f"WO: {wo_data.get('wo_number')}")
            
            # Start work order
            response = self.make_request("PUT", f"/production/work-orders/{wo_id}/start")
            if response and response.status_code == 200:
                self.log_test("Start Work Order", True, "Work order started")
                
                # Create production entry
                production_data = {
                    "wo_id": wo_id,
                    "quantity_produced": 95.0,
                    "wastage": 5.0,
                    "start_time": "08:00:00",
                    "end_time": "16:00:00",
                    "operator": "Rajesh Kumar",
                    "notes": "Production completed successfully with minimal wastage"
                }
                
                response = self.make_request("POST", "/production/production-entries", production_data)
                if response and response.status_code == 200:
                    prod_data = response.json()
                    self.log_test("Create Production Entry", True, f"Batch: {prod_data.get('batch_number')}")
                    
                    # Verify production entries list
                    response = self.make_request("GET", "/production/production-entries")
                    if response and response.status_code == 200:
                        entries = response.json()
                        found = any(entry.get("wo_id") == wo_id for entry in entries)
                        self.log_test("List Production Entries", found, f"Found {len(entries)} entries")
                        
                        # Verify inventory stock balance
                        response = self.make_request("GET", "/inventory/stock/balance", params={"item_id": item_id})
                        if response and response.status_code == 200:
                            balances = response.json()
                            total_qty = sum(bal.get("quantity", 0) for bal in balances)
                            self.log_test("Check Stock Balance", total_qty >= 95, f"Total stock: {total_qty}")
                            
                            # Verify item current_stock
                            response = self.make_request("GET", f"/inventory/items/{item_id}")
                            if response and response.status_code == 200:
                                item_data = response.json()
                                current_stock = item_data.get("current_stock", 0)
                                self.log_test("Check Item Current Stock", current_stock >= 95, f"Current stock: {current_stock}")
                            else:
                                self.log_test("Check Item Current Stock", False, f"Status: {response.status_code if response else 'No response'}")
                        else:
                            self.log_test("Check Stock Balance", False, f"Status: {response.status_code if response else 'No response'}")
                    else:
                        self.log_test("List Production Entries", False, f"Status: {response.status_code if response else 'No response'}")
                else:
                    self.log_test("Create Production Entry", False, f"Status: {response.status_code if response else 'No response'}")
            else:
                self.log_test("Start Work Order", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Create Work Order", False, f"Status: {status}, Error: {error}")
    
    def test_stock_transfer_approval(self, warehouse_id, item_id):
        """Test 1: Stock Transfer Approval Enforcement"""
        print("\n=== Testing Stock Transfer Approval Enforcement ===")
        
        if not warehouse_id or not item_id:
            self.log_test("Stock Transfer Approval", False, "Missing warehouse_id or item_id")
            return None
            
        # Get warehouses to create transfer between two
        response = self.make_request("GET", "/inventory/warehouses")
        if not response or response.status_code != 200:
            self.log_test("Get Warehouses for Transfer", False, f"Status: {response.status_code if response else 'No response'}")
            return None
            
        warehouses = response.json()
        if len(warehouses) < 2:
            # Create second warehouse
            wh2_data = {
                "warehouse_code": "WH-BRANCH",
                "warehouse_name": "Branch Warehouse",
                "warehouse_type": "Branch",
                "address": "Branch Location, Mumbai",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400002",
                "is_active": True
            }
            response = self.make_request("POST", "/inventory/warehouses", wh2_data)
            if response and response.status_code == 200:
                wh2_data = response.json()
                to_warehouse = wh2_data.get("id")
                self.log_test("Create Second Warehouse", True, f"Warehouse ID: {to_warehouse}")
            else:
                self.log_test("Create Second Warehouse", False, f"Status: {response.status_code if response else 'No response'}")
                return None
        else:
            to_warehouse = warehouses[1]["id"]
            
        # Create stock transfer
        transfer_data = {
            "from_warehouse": warehouse_id,
            "to_warehouse": to_warehouse,
            "items": [
                {
                    "item_id": item_id,
                    "quantity": 10.0,
                    "batch_no": f"BATCH-{datetime.now().strftime('%Y%m%d')}-001"
                }
            ],
            "scheduled_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "truck_no": "MH01AB1234",
            "driver_name": "Suresh Patil",
            "driver_phone": "9876543210",
            "notes": "Test transfer for approval enforcement"
        }
        
        response = self.make_request("POST", "/inventory/transfers", transfer_data)
        if response and response.status_code == 200:
            transfer = response.json()
            transfer_id = transfer.get("id")
            self.log_test("Create Stock Transfer", True, f"Transfer: {transfer.get('transfer_number')}")
            
            # Verify approval request was auto-created
            response = self.make_request("GET", "/approvals/requests", params={"status": "pending", "module": "Inventory"})
            if response and response.status_code == 200:
                approvals = response.json()
                transfer_approval = next((a for a in approvals if a.get("entity_id") == transfer_id and a.get("entity_type") == "StockTransfer"), None)
                if transfer_approval:
                    self.log_test("Auto-create Approval Request", True, f"Approval ID: {transfer_approval.get('id')}")
                    
                    # Try to issue transfer without approval - should return 409
                    response = self.make_request("PUT", f"/inventory/transfers/{transfer_id}/issue")
                    if response and response.status_code == 409:
                        self.log_test("Block Issue Without Approval", True, "409 Approval required returned")
                        
                        # Approve the request
                        approval_id = transfer_approval.get("id")
                        response = self.make_request("PUT", f"/approvals/requests/{approval_id}/approve", {"notes": "Test approval"})
                        if response and response.status_code == 200:
                            self.log_test("Approve Transfer Request", True, "Approval successful")
                            
                            # Retry issue - should succeed now
                            response = self.make_request("PUT", f"/inventory/transfers/{transfer_id}/issue")
                            if response and response.status_code == 200:
                                self.log_test("Issue After Approval", True, "Transfer issued successfully")
                                return transfer_id
                            else:
                                self.log_test("Issue After Approval", False, f"Status: {response.status_code if response else 'No response'}")
                        else:
                            self.log_test("Approve Transfer Request", False, f"Status: {response.status_code if response else 'No response'}")
                    else:
                        self.log_test("Block Issue Without Approval", False, f"Expected 409, got {response.status_code if response else 'No response'}")
                else:
                    self.log_test("Auto-create Approval Request", False, "No approval request found for transfer")
            else:
                self.log_test("List Approval Requests", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Create Stock Transfer", False, f"Status: {status}, Error: {error}")
        
        return None
    
    def test_hrms_payroll_approval(self, employee_id):
        """Test 2: HRMS Payroll Approval Enforcement"""
        print("\n=== Testing HRMS Payroll Approval Enforcement ===")
        
        if not employee_id:
            self.log_test("HRMS Payroll Approval", False, "No employee ID available")
            return
            
        payroll_data = {
            "employee_id": employee_id,
            "month": "December",
            "year": 2024,
            "days_present": 22.0,
            "days_absent": 8.0,
            "overtime_hours": 5.0
        }
        
        # First call should return 409 and auto-create approval request
        response = self.make_request("POST", "/hrms/payroll", payroll_data)
        if response and response.status_code == 409:
            self.log_test("Block Payroll Without Approval", True, "409 Approval required returned")
            
            # Verify approval request was auto-created
            response = self.make_request("GET", "/approvals/requests", params={"status": "pending", "module": "HRMS"})
            if response and response.status_code == 200:
                approvals = response.json()
                payroll_approval = next((a for a in approvals if a.get("entity_type") == "Payroll" and a.get("action") == "Payroll Run"), None)
                if payroll_approval:
                    self.log_test("Auto-create Payroll Approval", True, f"Approval ID: {payroll_approval.get('id')}")
                    
                    # Approve the request
                    approval_id = payroll_approval.get("id")
                    response = self.make_request("PUT", f"/approvals/requests/{approval_id}/approve", {"notes": "Test payroll approval"})
                    if response and response.status_code == 200:
                        self.log_test("Approve Payroll Request", True, "Approval successful")
                        
                        # Retry payroll - should succeed now
                        response = self.make_request("POST", "/hrms/payroll", payroll_data)
                        if response and response.status_code == 200:
                            payroll_result = response.json()
                            self.log_test("Generate Payroll After Approval", True, f"Net salary: {payroll_result.get('net_salary')}")
                        else:
                            self.log_test("Generate Payroll After Approval", False, f"Status: {response.status_code if response else 'No response'}")
                    else:
                        self.log_test("Approve Payroll Request", False, f"Status: {response.status_code if response else 'No response'}")
                else:
                    self.log_test("Auto-create Payroll Approval", False, "No payroll approval request found")
            else:
                self.log_test("List Payroll Approvals", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Block Payroll Without Approval", False, f"Expected 409, got {response.status_code if response else 'No response'}")
    
    def test_production_scrap_approval(self, item_id, machine_id):
        """Test 3: Production Scrap >7% Approval Enforcement"""
        print("\n=== Testing Production Scrap >7% Approval Enforcement ===")
        
        if not item_id or not machine_id:
            self.log_test("Production Scrap Approval", False, "Missing item_id or machine_id")
            return None
            
        # Create work order
        wo_data = {
            "item_id": item_id,
            "quantity_to_make": 100.0,
            "machine_id": machine_id,
            "thickness": 0.5,
            "color": "Clear",
            "width": 25.0,
            "length": 50.0,
            "brand": "InstaBiz",
            "priority": "high"
        }
        
        response = self.make_request("POST", "/production/work-orders", wo_data)
        if response and response.status_code == 200:
            wo = response.json()
            wo_id = wo.get("id")
            self.log_test("Create Work Order for Scrap Test", True, f"WO: {wo.get('wo_number')}")
            
            # Start work order
            response = self.make_request("PUT", f"/production/work-orders/{wo_id}/start")
            if response and response.status_code == 200:
                self.log_test("Start Work Order for Scrap Test", True, "Work order started")
                
                # Create production entry with >7% wastage (8 wastage out of 92 produced = 8.7%)
                production_data = {
                    "wo_id": wo_id,
                    "quantity_produced": 92.0,
                    "wastage": 8.0,  # 8.7% wastage
                    "start_time": "08:00:00",
                    "end_time": "16:00:00",
                    "operator": "Rajesh Kumar",
                    "notes": "Test production with high wastage for approval enforcement"
                }
                
                # First call should return 409 and auto-create approval request
                response = self.make_request("POST", "/production/production-entries", production_data)
                if response and response.status_code == 409:
                    self.log_test("Block High Scrap Without Approval", True, "409 Approval required returned")
                    
                    # Verify approval request was auto-created
                    response = self.make_request("GET", "/approvals/requests", params={"status": "pending", "module": "Production"})
                    if response and response.status_code == 200:
                        approvals = response.json()
                        scrap_approval = next((a for a in approvals if a.get("entity_id") == wo_id and a.get("action") == "Production Scrap"), None)
                        if scrap_approval:
                            self.log_test("Auto-create Scrap Approval", True, f"Approval ID: {scrap_approval.get('id')}")
                            
                            # Approve the request
                            approval_id = scrap_approval.get("id")
                            response = self.make_request("PUT", f"/approvals/requests/{approval_id}/approve", {"notes": "Test scrap approval"})
                            if response and response.status_code == 200:
                                self.log_test("Approve Scrap Request", True, "Approval successful")
                                
                                # Retry production entry - should succeed now and update inventory
                                response = self.make_request("POST", "/production/production-entries", production_data)
                                if response and response.status_code == 200:
                                    prod_result = response.json()
                                    self.log_test("Create Production Entry After Approval", True, f"Batch: {prod_result.get('batch_number')}")
                                    
                                    # Verify inventory stock was updated
                                    response = self.make_request("GET", "/inventory/stock/balance", params={"item_id": item_id})
                                    if response and response.status_code == 200:
                                        balances = response.json()
                                        total_qty = sum(bal.get("quantity", 0) for bal in balances)
                                        self.log_test("Verify Stock Update After Production", total_qty >= 92, f"Total stock: {total_qty}")
                                        return wo_id
                                    else:
                                        self.log_test("Verify Stock Update After Production", False, f"Status: {response.status_code if response else 'No response'}")
                                else:
                                    self.log_test("Create Production Entry After Approval", False, f"Status: {response.status_code if response else 'No response'}")
                            else:
                                self.log_test("Approve Scrap Request", False, f"Status: {response.status_code if response else 'No response'}")
                        else:
                            self.log_test("Auto-create Scrap Approval", False, "No scrap approval request found")
                    else:
                        self.log_test("List Scrap Approvals", False, f"Status: {response.status_code if response else 'No response'}")
                else:
                    self.log_test("Block High Scrap Without Approval", False, f"Expected 409, got {response.status_code if response else 'No response'}")
            else:
                self.log_test("Start Work Order for Scrap Test", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Create Work Order for Scrap Test", False, f"Status: {response.status_code if response else 'No response'}")
        
        return None
    
    def test_production_cancel_approval(self, item_id, machine_id):
        """Test 4: Production Cancel Work Order Approval Enforcement"""
        print("\n=== Testing Production Cancel Work Order Approval Enforcement ===")
        
        if not item_id or not machine_id:
            self.log_test("Production Cancel Approval", False, "Missing item_id or machine_id")
            return
            
        # Create work order for cancellation test
        wo_data = {
            "item_id": item_id,
            "quantity_to_make": 50.0,
            "machine_id": machine_id,
            "thickness": 0.5,
            "color": "Blue",
            "width": 20.0,
            "length": 30.0,
            "brand": "InstaBiz",
            "priority": "normal"
        }
        
        response = self.make_request("POST", "/production/work-orders", wo_data)
        if response and response.status_code == 200:
            wo = response.json()
            wo_id = wo.get("id")
            self.log_test("Create Work Order for Cancel Test", True, f"WO: {wo.get('wo_number')}")
            
            # First call to cancel should return 409 and auto-create approval request
            response = self.make_request("PUT", f"/production/work-orders/{wo_id}/cancel")
            if response and response.status_code == 409:
                self.log_test("Block Cancel Without Approval", True, "409 Approval required returned")
                
                # Verify approval request was auto-created
                response = self.make_request("GET", "/approvals/requests", params={"status": "pending", "module": "Production"})
                if response and response.status_code == 200:
                    approvals = response.json()
                    cancel_approval = next((a for a in approvals if a.get("entity_id") == wo_id and a.get("action") == "Cancel Production Order"), None)
                    if cancel_approval:
                        self.log_test("Auto-create Cancel Approval", True, f"Approval ID: {cancel_approval.get('id')}")
                        
                        # Approve the request
                        approval_id = cancel_approval.get("id")
                        response = self.make_request("PUT", f"/approvals/requests/{approval_id}/approve", {"notes": "Test cancel approval"})
                        if response and response.status_code == 200:
                            self.log_test("Approve Cancel Request", True, "Approval successful")
                            
                            # Retry cancel - should succeed now and set status to cancelled
                            response = self.make_request("PUT", f"/production/work-orders/{wo_id}/cancel")
                            if response and response.status_code == 200:
                                self.log_test("Cancel Work Order After Approval", True, "Work order cancelled successfully")
                                
                                # Verify work order status is cancelled
                                response = self.make_request("GET", f"/production/work-orders/{wo_id}")
                                if response and response.status_code == 200:
                                    wo_status = response.json()
                                    if wo_status.get("status") == "cancelled":
                                        self.log_test("Verify Cancelled Status", True, "Status set to cancelled")
                                    else:
                                        self.log_test("Verify Cancelled Status", False, f"Status: {wo_status.get('status')}")
                                else:
                                    self.log_test("Verify Cancelled Status", False, f"Status: {response.status_code if response else 'No response'}")
                            else:
                                self.log_test("Cancel Work Order After Approval", False, f"Status: {response.status_code if response else 'No response'}")
                        else:
                            self.log_test("Approve Cancel Request", False, f"Status: {response.status_code if response else 'No response'}")
                    else:
                        self.log_test("Auto-create Cancel Approval", False, "No cancel approval request found")
                else:
                    self.log_test("List Cancel Approvals", False, f"Status: {response.status_code if response else 'No response'}")
            else:
                self.log_test("Block Cancel Without Approval", False, f"Expected 409, got {response.status_code if response else 'No response'}")
        else:
            self.log_test("Create Work Order for Cancel Test", False, f"Status: {response.status_code if response else 'No response'}")

    def test_procurement_enhancements(self):
        """Test ERP Procurement Enhancements as per review request"""
        print("\n=== Testing ERP Procurement Enhancements ===")
        
        # Test 1: Procurement - Pincode Auto-Fill API
        print("\n--- Testing Pincode Auto-Fill API ---")
        
        # Test with valid pincode 400001 (Mumbai)
        response = self.make_request("GET", "/procurement/geo/pincode/400001")
        if response and response.status_code == 200:
            data = response.json()
            expected_fields = ["city", "state", "district", "country"]
            has_all_fields = all(field in data for field in expected_fields)
            is_mumbai = "mumbai" in data.get("city", "").lower() and "maharashtra" in data.get("state", "").lower()
            self.log_test("Pincode Auto-Fill - Valid 400001", has_all_fields and is_mumbai, 
                         f"City: {data.get('city')}, State: {data.get('state')}, District: {data.get('district')}")
        else:
            self.log_test("Pincode Auto-Fill - Valid 400001", False, 
                         f"Status: {response.status_code if response else 'No response'}")
        
        # Test with valid pincode 110001 (Delhi)
        response = self.make_request("GET", "/procurement/geo/pincode/110001")
        if response and response.status_code == 200:
            data = response.json()
            expected_fields = ["city", "state", "district", "country"]
            has_all_fields = all(field in data for field in expected_fields)
            is_delhi = "delhi" in data.get("state", "").lower()
            self.log_test("Pincode Auto-Fill - Valid 110001", has_all_fields and is_delhi,
                         f"City: {data.get('city')}, State: {data.get('state')}, District: {data.get('district')}")
        else:
            self.log_test("Pincode Auto-Fill - Valid 110001", False,
                         f"Status: {response.status_code if response else 'No response'}")
        
        # Test with invalid pincode
        response = self.make_request("GET", "/procurement/geo/pincode/12345")
        if response and response.status_code == 404:
            self.log_test("Pincode Auto-Fill - Invalid 12345", True, "404 error returned as expected")
        else:
            self.log_test("Pincode Auto-Fill - Invalid 12345", False,
                         f"Expected 404, got {response.status_code if response else 'No response'}")
        
        # Test 2: Procurement - GSTIN Validation API
        print("\n--- Testing GSTIN Validation API ---")
        
        # Test with valid GSTIN 27AAACR4849M1Z7 (Maharashtra)
        response = self.make_request("GET", "/procurement/gstin/validate/27AAACR4849M1Z7")
        if response and response.status_code == 200:
            data = response.json()
            is_valid = data.get("valid") == True
            has_state = "maharashtra" in data.get("state", "").lower()
            has_pan = data.get("pan") == "AAACR4849M"
            self.log_test("GSTIN Validation - Valid 27AAACR4849M1Z7", is_valid and has_state and has_pan,
                         f"Valid: {data.get('valid')}, State: {data.get('state')}, PAN: {data.get('pan')}")
        else:
            self.log_test("GSTIN Validation - Valid 27AAACR4849M1Z7", False,
                         f"Status: {response.status_code if response else 'No response'}")
        
        # Test with valid GSTIN 07AAACR4849M1ZK (Delhi)
        response = self.make_request("GET", "/procurement/gstin/validate/07AAACR4849M1ZK")
        if response and response.status_code == 200:
            data = response.json()
            is_valid = data.get("valid") == True
            has_state = "delhi" in data.get("state", "").lower()
            has_pan = data.get("pan") == "AAACR4849M"
            self.log_test("GSTIN Validation - Valid 07AAACR4849M1ZK", is_valid and has_state and has_pan,
                         f"Valid: {data.get('valid')}, State: {data.get('state')}, PAN: {data.get('pan')}")
        else:
            self.log_test("GSTIN Validation - Valid 07AAACR4849M1ZK", False,
                         f"Status: {response.status_code if response else 'No response'}")
        
        # Test with invalid GSTIN
        response = self.make_request("GET", "/procurement/gstin/validate/12345678901234X")
        if response and response.status_code == 400:
            self.log_test("GSTIN Validation - Invalid 12345678901234X", True, "400 error returned as expected")
        else:
            self.log_test("GSTIN Validation - Invalid 12345678901234X", False,
                         f"Expected 400, got {response.status_code if response else 'No response'}")
        
        # Test 3: Get suppliers for TDS info test
        print("\n--- Testing Supplier TDS/TCS Info API ---")
        
        response = self.make_request("GET", "/procurement/suppliers")
        supplier_id = None
        if response and response.status_code == 200:
            suppliers = response.json()
            if suppliers:
                supplier_id = suppliers[0].get("id")
                self.log_test("Get Suppliers List", True, f"Found {len(suppliers)} suppliers")
            else:
                # Create a test supplier if none exist
                supplier_data = {
                    "supplier_name": "Test Supplier for TDS",
                    "contact_person": "John Doe",
                    "email": "john@testsupplier.com",
                    "phone": "9876543210",
                    "address": "Test Address",
                    "pincode": "400001",
                    "gstin": "27AAACR4849M1Z7",
                    "payment_terms": "30 days"
                }
                
                response = self.make_request("POST", "/procurement/suppliers", supplier_data)
                if response and response.status_code == 200:
                    supplier = response.json()
                    supplier_id = supplier.get("id")
                    self.log_test("Create Test Supplier", True, f"Supplier ID: {supplier_id}")
                else:
                    self.log_test("Create Test Supplier", False, f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Get Suppliers List", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test TDS/TCS Info API
        if supplier_id:
            response = self.make_request("GET", f"/procurement/suppliers/{supplier_id}/tds-info")
            if response and response.status_code == 200:
                data = response.json()
                required_fields = ["cumulative_purchase_value", "threshold", "threshold_exceeded", "tds_rate", "tds_applicable", "message"]
                has_all_fields = all(field in data for field in required_fields)
                self.log_test("Supplier TDS/TCS Info", has_all_fields,
                             f"Cumulative: ₹{data.get('cumulative_purchase_value', 0)}, Threshold: ₹{data.get('threshold', 0)}, TDS Rate: {data.get('tds_rate', 0)}%")
            else:
                self.log_test("Supplier TDS/TCS Info", False,
                             f"Status: {response.status_code if response else 'No response'}")
        
        # Test 4: Purchase Order Edit API
        print("\n--- Testing Purchase Order Edit API ---")
        
        # First get warehouses and items for PO creation
        warehouse_id, item_id = self.test_inventory_setup()
        
        if warehouse_id and item_id and supplier_id:
            # Create a draft PO
            po_data = {
                "supplier_id": supplier_id,
                "warehouse_id": warehouse_id,
                "items": [
                    {
                        "item_id": item_id,
                        "quantity": 100.0,
                        "unit_price": 50.0,
                        "tax_percent": 18.0
                    }
                ],
                "notes": "Original PO notes",
                "expected_date": "2024-12-31"
            }
            
            response = self.make_request("POST", "/procurement/purchase-orders", po_data)
            if response and response.status_code == 200:
                po = response.json()
                po_id = po.get("id")
                self.log_test("Create Draft PO for Edit Test", True, f"PO: {po.get('po_number')}")
                
                # Edit the PO (update notes and expected_date)
                edit_data = {
                    "notes": "Updated PO notes for testing",
                    "expected_date": "2025-01-15"
                }
                
                response = self.make_request("PUT", f"/procurement/purchase-orders/{po_id}", edit_data)
                if response and response.status_code == 200:
                    updated_po = response.json()
                    notes_updated = updated_po.get("notes") == "Updated PO notes for testing"
                    date_updated = updated_po.get("expected_date") == "2025-01-15"
                    self.log_test("Edit Draft PO", notes_updated and date_updated,
                                 f"Notes: {updated_po.get('notes')}, Expected Date: {updated_po.get('expected_date')}")
                    
                    # Change status to received and try to edit (should fail)
                    response = self.make_request("PUT", f"/procurement/purchase-orders/{po_id}", {"status": "received"})
                    if response and response.status_code == 200:
                        # Now try to edit received PO (should return 400)
                        response = self.make_request("PUT", f"/procurement/purchase-orders/{po_id}", {"notes": "Should not work"})
                        if response and response.status_code == 400:
                            self.log_test("Block Edit of Received PO", True, "400 error returned as expected")
                        else:
                            self.log_test("Block Edit of Received PO", False,
                                         f"Expected 400, got {response.status_code if response else 'No response'}")
                    else:
                        self.log_test("Change PO Status to Received", False,
                                     f"Status: {response.status_code if response else 'No response'}")
                else:
                    self.log_test("Edit Draft PO", False,
                                 f"Status: {response.status_code if response else 'No response'}")
            else:
                self.log_test("Create Draft PO for Edit Test", False,
                             f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("PO Edit Test Setup", False, "Missing warehouse_id, item_id, or supplier_id")

    def test_accounts_credit_note(self):
        """Test Accounts - Credit Note Creation"""
        print("\n=== Testing Accounts Credit Note Creation ===")
        
        # First get or create an account
        response = self.make_request("GET", "/crm/accounts")
        account_id = None
        
        if response and response.status_code == 200:
            accounts = response.json()
            if accounts:
                account_id = accounts[0].get("id")
                self.log_test("Get Accounts for Credit Note", True, f"Found {len(accounts)} accounts")
            else:
                # Create test account
                account_data = {
                    "customer_name": "Test Customer for Credit Note",
                    "account_type": "Customer",
                    "gstin": "27AAACR4849M1Z7",
                    "billing_address": "Test Address",
                    "billing_pincode": "400001",
                    "credit_limit": 50000.0,
                    "credit_days": 30,
                    "payment_terms": "30 days"
                }
                
                response = self.make_request("POST", "/crm/accounts", account_data)
                if response and response.status_code == 200:
                    account = response.json()
                    account_id = account.get("id")
                    self.log_test("Create Test Account for Credit Note", True, f"Account ID: {account_id}")
                else:
                    self.log_test("Create Test Account for Credit Note", False,
                                 f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Get Accounts for Credit Note", False,
                         f"Status: {response.status_code if response else 'No response'}")
        
        # Create Credit Note
        if account_id:
            credit_note_data = {
                "invoice_type": "Credit Note",
                "account_id": account_id,
                "items": [
                    {
                        "description": "Product Return - Defective Item",
                        "hsn_code": "39191090",
                        "quantity": 5.0,
                        "unit": "Pcs",
                        "unit_price": 100.0,
                        "tax_percent": 18.0
                    }
                ],
                "invoice_date": "2024-12-20",
                "due_date": "2024-12-20",
                "notes": "Credit note for defective product return"
            }
            
            response = self.make_request("POST", "/accounts/invoices", credit_note_data)
            if response and response.status_code == 200:
                credit_note = response.json()
                invoice_number = credit_note.get("invoice_number", "")
                starts_with_cn = invoice_number.startswith("CN-")
                is_credit_note_type = credit_note.get("invoice_type") == "Credit Note"
                
                self.log_test("Create Credit Note", starts_with_cn and is_credit_note_type,
                             f"Invoice Number: {invoice_number}, Type: {credit_note.get('invoice_type')}")
            else:
                self.log_test("Create Credit Note", False,
                             f"Status: {response.status_code if response else 'No response'}")
        else:
            self.log_test("Create Credit Note", False, "No account_id available")

    def test_crm_account_address_autofill(self):
        """Test CRM Account creation/update with pincode auto-fill"""
        print("\n=== Testing CRM Account Address Auto-fill ===")
        
        # Create account with billing_pincode=110001
        account_data = {
            "customer_name": "Test Customer for Address Auto-fill",
            "account_type": "Customer",
            "gstin": "07AABCU9603R1ZX",  # Valid Delhi GSTIN
            "billing_address": "Test Address, Connaught Place",
            "billing_pincode": "110001",  # New Delhi pincode
            "credit_limit": 50000.0,
            "credit_days": 30,
            "credit_control": "Warn",
            "payment_terms": "30 days"
        }
        
        response = self.make_request("POST", "/crm/accounts", account_data)
        
        if response and response.status_code == 200:
            account = response.json()
            account_id = account.get("id")
            
            # Check if geo fields were auto-filled
            billing_city = account.get("billing_city")
            billing_state = account.get("billing_state")
            billing_district = account.get("billing_district")
            
            auto_fill_success = (
                billing_city and billing_state and billing_district and
                "delhi" in billing_state.lower()
            )
            
            self.log_test("Create Account with Pincode Auto-fill", auto_fill_success, 
                         f"City: {billing_city}, State: {billing_state}, District: {billing_district}")
            
            if account_id:
                # Test update with different pincode
                update_data = {
                    "billing_pincode": "400001"  # Mumbai pincode
                }
                
                response = self.make_request("PUT", f"/crm/accounts/{account_id}", update_data)
                
                if response and response.status_code == 200:
                    updated_account = response.json()
                    updated_city = updated_account.get("billing_city")
                    updated_state = updated_account.get("billing_state")
                    updated_district = updated_account.get("billing_district")
                    
                    update_success = (
                        updated_city and updated_state and updated_district and
                        "maharashtra" in updated_state.lower()
                    )
                    
                    self.log_test("Update Account Pincode Auto-fill", update_success,
                                 f"Updated - City: {updated_city}, State: {updated_state}, District: {updated_district}")
                    return account_id
                else:
                    self.log_test("Update Account Pincode Auto-fill", False, 
                                 f"Status: {response.status_code if response else 'No response'}")
            else:
                self.log_test("Create Account with Pincode Auto-fill", False, "No account ID returned")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Create Account with Pincode Auto-fill", False, f"Status: {status}, Error: {error}")
        
        return None
    
    def test_crm_samples_multi_item(self):
        """Test CRM Samples with multi-item functionality"""
        print("\n=== Testing CRM Samples Multi-Item ===")
        
        # First create an account for the sample
        account_data = {
            "customer_name": "Sample Test Customer",
            "account_type": "Customer", 
            "gstin": "27AABCU9603R1ZX",  # Valid Maharashtra GSTIN
            "billing_address": "Sample Test Address",
            "billing_pincode": "400001",
            "credit_limit": 25000.0,
            "credit_days": 30,
            "credit_control": "Warn",
            "payment_terms": "30 days"
        }
        
        response = self.make_request("POST", "/crm/accounts", account_data)
        
        if not response or response.status_code != 200:
            self.log_test("Create Account for Sample Test", False, "Failed to create test account")
            return
            
        account = response.json()
        account_id = account.get("id")
        self.log_test("Create Account for Sample Test", True, f"Account ID: {account_id}")
        
        # Create sample with 2 items
        sample_data = {
            "account_id": account_id,
            "contact_person": "John Doe",
            "items": [
                {
                    "product_name": "Double Sided Tape",
                    "product_specs": "25mm x 50m, Clear, Acrylic adhesive",
                    "quantity": 5.0,
                    "unit": "Rolls"
                },
                {
                    "product_name": "Foam Tape",
                    "product_specs": "12mm x 25m, Black, PE foam base",
                    "quantity": 10.0,
                    "unit": "Rolls"
                }
            ],
            "from_location": "Mumbai Warehouse",
            "feedback_due_date": "2024-12-31",
            "purpose": "Product evaluation and testing",
            "notes": "Customer wants to test adhesion on cardboard packaging"
        }
        
        response = self.make_request("POST", "/crm/samples", sample_data)
        
        if response and response.status_code == 200:
            sample = response.json()
            sample_id = sample.get("id")
            items = sample.get("items", [])
            
            # Verify 2 items were created
            items_count_correct = len(items) == 2
            self.log_test("Create Sample with 2 Items", items_count_correct, 
                         f"Sample ID: {sample_id}, Items count: {len(items)}")
            
            if sample_id:
                # Fetch samples list and confirm the sample has 2 items
                response = self.make_request("GET", "/crm/samples")
                
                if response and response.status_code == 200:
                    samples_list = response.json()
                    created_sample = next((s for s in samples_list if s.get("id") == sample_id), None)
                    
                    if created_sample:
                        fetched_items = created_sample.get("items", [])
                        fetch_success = len(fetched_items) == 2
                        self.log_test("Fetch Sample List - Verify 2 Items", fetch_success,
                                     f"Fetched items count: {len(fetched_items)}")
                        
                        # Update sample - change second item quantity
                        if len(fetched_items) >= 2:
                            updated_items = fetched_items.copy()
                            updated_items[1]["quantity"] = 15.0  # Change from 10.0 to 15.0
                            
                            update_data = {
                                "items": updated_items,
                                "notes": "Updated second item quantity for testing"
                            }
                            
                            response = self.make_request("PUT", f"/crm/samples/{sample_id}", update_data)
                            
                            if response and response.status_code == 200:
                                updated_sample = response.json()
                                updated_items = updated_sample.get("items", [])
                                
                                # Verify the update persisted
                                if len(updated_items) >= 2:
                                    second_item_qty = updated_items[1].get("quantity")
                                    update_success = second_item_qty == 15.0
                                    self.log_test("Update Sample Second Item Quantity", update_success,
                                                 f"Second item quantity: {second_item_qty} (expected: 15.0)")
                                else:
                                    self.log_test("Update Sample Second Item Quantity", False, 
                                                 "Updated sample doesn't have 2 items")
                            else:
                                self.log_test("Update Sample Second Item Quantity", False,
                                             f"Status: {response.status_code if response else 'No response'}")
                        else:
                            self.log_test("Update Sample Second Item Quantity", False, 
                                         "Sample doesn't have 2 items to update")
                    else:
                        self.log_test("Fetch Sample List - Verify 2 Items", False, 
                                     "Created sample not found in list")
                else:
                    self.log_test("Fetch Sample List - Verify 2 Items", False,
                                 f"Status: {response.status_code if response else 'No response'}")
            else:
                self.log_test("Create Sample with 2 Items", False, "No sample ID returned")
        else:
            status = response.status_code if response else "No response"
            error = response.text if response else "Connection failed"
            self.log_test("Create Sample with 2 Items", False, f"Status: {status}, Error: {error}")

    def test_director_dashboard(self):
        """Test Director Command Center endpoints"""
        print("\n=== Testing Director Command Center ===")
        
        # Test cash pulse
        response = self.make_request("GET", "/director/cash-pulse")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Director Cash Pulse", True, f"AR: {data.get('total_receivables', 0)}, AP: {data.get('total_payables', 0)}")
        else:
            self.log_test("Director Cash Pulse", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test production pulse
        response = self.make_request("GET", "/director/production-pulse")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Director Production Pulse", True, f"WO in progress: {data.get('work_orders_in_progress', 0)}")
        else:
            self.log_test("Director Production Pulse", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test sales pulse
        response = self.make_request("GET", "/director/sales-pulse")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Director Sales Pulse", True, f"MTD Sales: {data.get('mtd_sales', 0)}")
        else:
            self.log_test("Director Sales Pulse", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test alerts
        response = self.make_request("GET", "/director/alerts")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Director Alerts", True, f"Pending approvals: {data.get('pending_approvals', {}).get('count', 0)}")
        else:
            self.log_test("Director Alerts", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test summary
        response = self.make_request("GET", "/director/summary")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Director Summary", True, "Complete dashboard summary received")
        else:
            self.log_test("Director Summary", False, f"Status: {response.status_code if response else 'No response'}")

    def test_branches(self):
        """Test Branches module"""
        print("\n=== Testing Branches ===")
        
        # Create branch
        branch_data = {
            "branch_code": "MH",
            "branch_name": "Maharashtra",
            "state": "Maharashtra",
            "gstin": "27AABCU9603R1ZM",
            "address": "Mumbai",
            "city": "Mumbai",
            "pincode": "400001"
        }
        
        response = self.make_request("POST", "/branches/", branch_data)
        branch_id = None
        
        if response and response.status_code == 200:
            branch = response.json()
            branch_id = branch.get("id")
            self.log_test("Create Branch", True, f"Branch: {branch.get('branch_name')} ({branch.get('branch_code')})")
        else:
            self.log_test("Create Branch", False, f"Status: {response.status_code if response else 'No response'}")
        
        # List branches
        response = self.make_request("GET", "/branches/")
        if response and response.status_code == 200:
            branches = response.json()
            self.log_test("List Branches", True, f"Found {len(branches)} branches")
        else:
            self.log_test("List Branches", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Get branch dashboard
        if branch_id:
            response = self.make_request("GET", f"/branches/{branch_id}/dashboard")
            if response and response.status_code == 200:
                dashboard = response.json()
                self.log_test("Branch Dashboard", True, f"Sales: {dashboard.get('sales', {}).get('total', 0)}")
            else:
                self.log_test("Branch Dashboard", False, f"Status: {response.status_code if response else 'No response'}")
        
        return branch_id

    def test_gatepass(self):
        """Test Gatepass module"""
        print("\n=== Testing Gatepass ===")
        
        # Create transporter
        transporter_data = {
            "transporter_name": "Reliable Transport Co.",
            "contact_person": "Suresh Patil",
            "phone": "9876543210",
            "gstin": "27AABCU9603R1ZX",
            "address": "Transport Nagar, Mumbai",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        response = self.make_request("POST", "/gatepass/transporters", transporter_data)
        transporter_id = None
        
        if response and response.status_code == 200:
            transporter = response.json()
            transporter_id = transporter.get("id")
            self.log_test("Create Transporter", True, f"Transporter: {transporter.get('transporter_name')}")
        else:
            self.log_test("Create Transporter", False, f"Status: {response.status_code if response else 'No response'}")
        
        # List transporters
        response = self.make_request("GET", "/gatepass/transporters")
        if response and response.status_code == 200:
            transporters = response.json()
            self.log_test("List Transporters", True, f"Found {len(transporters)} transporters")
        else:
            self.log_test("List Transporters", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Create inward gatepass (need warehouse_id)
        warehouse_id, item_id = self.test_inventory_setup()
        
        if warehouse_id and item_id:
            gatepass_data = {
                "gatepass_type": "inward",
                "reference_type": "GRN",
                "transporter_id": transporter_id,
                "vehicle_no": "MH01AB1234",
                "driver_name": "Ramesh Kumar",
                "driver_phone": "9876543211",
                "party_name": "ABC Suppliers",
                "party_address": "Supplier Address",
                "warehouse_id": warehouse_id,
                "items": [
                    {
                        "item_id": item_id,
                        "item_name": "Test Item",
                        "quantity": 100.0,
                        "uom": "Rolls",
                        "batch_no": "BATCH001"
                    }
                ],
                "purpose": "Raw material delivery"
            }
            
            response = self.make_request("POST", "/gatepass/", gatepass_data)
            gatepass_id = None
            
            if response and response.status_code == 200:
                gatepass = response.json()
                gatepass_id = gatepass.get("id")
                self.log_test("Create Inward Gatepass", True, f"Gatepass: {gatepass.get('gatepass_no')}")
            else:
                self.log_test("Create Inward Gatepass", False, f"Status: {response.status_code if response else 'No response'}")
            
            # List gatepasses
            response = self.make_request("GET", "/gatepass/")
            if response and response.status_code == 200:
                gatepasses = response.json()
                self.log_test("List Gatepasses", True, f"Found {len(gatepasses)} gatepasses")
            else:
                self.log_test("List Gatepasses", False, f"Status: {response.status_code if response else 'No response'}")
            
            # Get vehicle log
            response = self.make_request("GET", "/gatepass/vehicle-log")
            if response and response.status_code == 200:
                log = response.json()
                self.log_test("Vehicle Log", True, f"Found {len(log)} vehicle entries")
            else:
                self.log_test("Vehicle Log", False, f"Status: {response.status_code if response else 'No response'}")

    def test_expenses(self):
        """Test Expenses module"""
        print("\n=== Testing Expenses ===")
        
        # Bootstrap expense buckets
        response = self.make_request("POST", "/expenses/buckets/bootstrap")
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Bootstrap Expense Buckets", True, data.get('message', ''))
        else:
            self.log_test("Bootstrap Expense Buckets", False, f"Status: {response.status_code if response else 'No response'}")
        
        # List expense buckets
        response = self.make_request("GET", "/expenses/buckets")
        bucket_id = None
        
        if response and response.status_code == 200:
            buckets = response.json()
            self.log_test("List Expense Buckets", True, f"Found {len(buckets)} buckets")
            if buckets:
                bucket_id = buckets[0].get("id")
        else:
            self.log_test("List Expense Buckets", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Create expense entry
        if bucket_id:
            expense_data = {
                "bucket_id": bucket_id,
                "expense_date": "2024-12-20",
                "amount": 5000.0,
                "payment_mode": "bank",
                "vendor_name": "Office Supplies Co.",
                "description": "Office stationery and supplies",
                "department": "Admin"
            }
            
            response = self.make_request("POST", "/expenses/entries", expense_data)
            if response and response.status_code == 200:
                entry = response.json()
                self.log_test("Create Expense Entry", True, f"Entry: {entry.get('expense_no')}")
            else:
                self.log_test("Create Expense Entry", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Get expense analytics
        response = self.make_request("GET", "/expenses/analytics/by-bucket")
        if response and response.status_code == 200:
            analytics = response.json()
            self.log_test("Expense Analytics", True, f"Found {len(analytics)} bucket analytics")
        else:
            self.log_test("Expense Analytics", False, f"Status: {response.status_code if response else 'No response'}")

    def test_payroll(self):
        """Test Payroll module"""
        print("\n=== Testing Payroll ===")
        
        # List payrolls
        response = self.make_request("GET", "/payroll/")
        if response and response.status_code == 200:
            payrolls = response.json()
            self.log_test("List Payrolls", True, f"Found {len(payrolls)} payroll records")
        else:
            self.log_test("List Payrolls", False, f"Status: {response.status_code if response else 'No response'}")

    def test_employee_vault(self):
        """Test Employee Vault module"""
        print("\n=== Testing Employee Vault ===")
        
        # Get document types
        response = self.make_request("GET", "/employee-vault/document-types")
        if response and response.status_code == 200:
            doc_types = response.json()
            self.log_test("Employee Document Types", True, f"Found {len(doc_types)} document types")
        else:
            self.log_test("Employee Document Types", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Get employees first for asset assignment
        response = self.make_request("GET", "/hrms/employees")
        employee_id = None
        
        if response and response.status_code == 200:
            employees = response.json()
            if employees:
                employee_id = employees[0].get("id")
        
        # Assign asset to employee
        if employee_id:
            asset_data = {
                "employee_id": employee_id,
                "asset_type": "Laptop",
                "asset_name": "Dell Latitude 5520",
                "asset_code": "LAP001",
                "serial_number": "DL123456789",
                "assigned_date": "2024-12-20",
                "condition": "New",
                "value": 65000.0
            }
            
            response = self.make_request("POST", "/employee-vault/assets", asset_data)
            if response and response.status_code == 200:
                asset = response.json()
                self.log_test("Assign Employee Asset", True, f"Asset: {asset.get('asset_name')}")
            else:
                self.log_test("Assign Employee Asset", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Get expiring documents
        response = self.make_request("GET", "/employee-vault/documents/expiring")
        if response and response.status_code == 200:
            docs = response.json()
            self.log_test("Expiring Documents", True, f"Found {len(docs)} expiring documents")
        else:
            self.log_test("Expiring Documents", False, f"Status: {response.status_code if response else 'No response'}")

    def test_sales_incentives(self):
        """Test Sales Incentives module"""
        print("\n=== Testing Sales Incentives ===")
        
        # Get incentive slabs
        response = self.make_request("GET", "/sales-incentives/slabs")
        if response and response.status_code == 200:
            slabs = response.json()
            self.log_test("Incentive Slabs", True, f"Found {len(slabs)} incentive slabs")
        else:
            self.log_test("Incentive Slabs", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Get employees for target creation
        response = self.make_request("GET", "/hrms/employees")
        employee_id = None
        
        if response and response.status_code == 200:
            employees = response.json()
            if employees:
                employee_id = employees[0].get("id")
        
        # Create sales target
        if employee_id:
            target_data = {
                "employee_id": employee_id,
                "target_type": "monthly",
                "period": "2025-01",
                "target_amount": 500000.0,
                "target_quantity": 100,
                "product_category": "all"
            }
            
            response = self.make_request("POST", "/sales-incentives/targets", target_data)
            if response and response.status_code == 200:
                target = response.json()
                self.log_test("Create Sales Target", True, f"Target: {target.get('target_amount')}")
            else:
                self.log_test("Create Sales Target", False, f"Status: {response.status_code if response else 'No response'}")
        
        # List targets
        response = self.make_request("GET", "/sales-incentives/targets")
        if response and response.status_code == 200:
            targets = response.json()
            self.log_test("List Sales Targets", True, f"Found {len(targets)} targets")
        else:
            self.log_test("List Sales Targets", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Get leaderboard
        response = self.make_request("GET", "/sales-incentives/leaderboard", params={"period": "2025-01"})
        if response and response.status_code == 200:
            leaderboard = response.json()
            self.log_test("Sales Leaderboard", True, f"Found {len(leaderboard)} entries")
        else:
            self.log_test("Sales Leaderboard", False, f"Status: {response.status_code if response else 'No response'}")

    def test_import_bridge(self):
        """Test Import Bridge module"""
        print("\n=== Testing Import Bridge ===")
        
        # Get exchange rates
        response = self.make_request("GET", "/imports/exchange-rates")
        if response and response.status_code == 200:
            rates = response.json()
            self.log_test("Exchange Rates", True, f"Base: {rates.get('base', 'N/A')}")
        else:
            self.log_test("Exchange Rates", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Create import PO (need supplier first)
        supplier_data = {
            "supplier_name": "Global Materials Inc.",
            "supplier_type": "International",
            "contact_person": "John Smith",
            "email": "john@globalmaterials.com",
            "phone": "+1-555-0123",
            "address": "123 Industrial Ave, New York, USA",
            "payment_terms": "LC 90 days",
            "currency": "USD"
        }
        
        # Create supplier first
        supplier_response = self.make_request("POST", "/procurement/suppliers", supplier_data)
        supplier_id = None
        
        if supplier_response and supplier_response.status_code == 200:
            supplier = supplier_response.json()
            supplier_id = supplier.get("id")
        
        # Get item for import PO
        item_response = self.make_request("GET", "/inventory/items")
        item_id = None
        
        if item_response and item_response.status_code == 200:
            items = item_response.json()
            if items:
                item_id = items[0].get("id")
        
        # Create import PO
        if supplier_id and item_id:
            import_po_data = {
                "supplier_id": supplier_id,
                "po_date": "2024-12-20",
                "expected_arrival": "2025-01-20",
                "items": [
                    {
                        "item_id": item_id,
                        "item_name": "Adhesive Raw Material",
                        "quantity": 1000.0,
                        "uom": "KG",
                        "foreign_unit_price": 5.50,
                        "foreign_currency": "USD"
                    }
                ],
                "foreign_currency": "USD",
                "exchange_rate": 83.50,
                "port_of_loading": "New York",
                "port_of_discharge": "JNPT Mumbai",
                "shipping_terms": "FOB",
                "container_type": "20ft",
                "payment_terms": "LC 90 days"
            }
            
            response = self.make_request("POST", "/imports/purchase-orders", import_po_data)
            import_po_id = None
            
            if response and response.status_code == 200:
                po = response.json()
                import_po_id = po.get("id")
                self.log_test("Create Import PO", True, f"PO: {po.get('po_number')}")
            else:
                self.log_test("Create Import PO", False, f"Status: {response.status_code if response else 'No response'}")
            
            # List import POs
            response = self.make_request("GET", "/imports/purchase-orders")
            if response and response.status_code == 200:
                pos = response.json()
                self.log_test("List Import POs", True, f"Found {len(pos)} import POs")
            else:
                self.log_test("List Import POs", False, f"Status: {response.status_code if response else 'No response'}")
            
            # Calculate landing cost
            if import_po_id:
                landing_cost_data = {
                    "import_po_id": import_po_id,
                    "basic_customs_duty": 10000.0,
                    "igst": 15000.0,
                    "ocean_freight": 25000.0,
                    "insurance": 5000.0,
                    "cha_charges": 8000.0,
                    "port_charges": 3000.0,
                    "settlement_exchange_rate": 84.0
                }
                
                response = self.make_request("POST", "/imports/landing-cost", landing_cost_data)
                if response and response.status_code == 200:
                    cost = response.json()
                    self.log_test("Calculate Landing Cost", True, f"Landed value: {cost.get('landed_inr_value')}")
                else:
                    self.log_test("Calculate Landing Cost", False, f"Status: {response.status_code if response else 'No response'}")

    def test_production_v2(self):
        """Test Production V2 module"""
        print("\n=== Testing Production V2 ===")
        
        # Get coating batches
        response = self.make_request("GET", "/production-v2/coating-batches")
        if response and response.status_code == 200:
            batches = response.json()
            self.log_test("Coating Batches", True, f"Found {len(batches)} coating batches")
        else:
            self.log_test("Coating Batches", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Get converting jobs
        response = self.make_request("GET", "/production-v2/converting-jobs")
        if response and response.status_code == 200:
            jobs = response.json()
            self.log_test("Converting Jobs", True, f"Found {len(jobs)} converting jobs")
        else:
            self.log_test("Converting Jobs", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Get RM requisitions
        response = self.make_request("GET", "/production-v2/rm-requisitions")
        if response and response.status_code == 200:
            requisitions = response.json()
            self.log_test("RM Requisitions", True, f"Found {len(requisitions)} RM requisitions")
        else:
            self.log_test("RM Requisitions", False, f"Status: {response.status_code if response else 'No response'}")

    def test_inventory_uom_conversion(self):
        """Test Inventory UOM Conversion if items have dimensions"""
        print("\n=== Testing Inventory UOM Conversion ===")
        
        # Get items to check for dimensions
        response = self.make_request("GET", "/inventory/items")
        if response and response.status_code == 200:
            items = response.json()
            items_with_dimensions = [item for item in items if item.get('width') and item.get('length')]
            
            if items_with_dimensions:
                item = items_with_dimensions[0]
                # Test UOM conversion endpoint if it exists
                conversion_data = {
                    "item_id": item.get("id"),
                    "from_uom": "Rolls",
                    "to_uom": "SqM",
                    "quantity": 10.0
                }
                
                response = self.make_request("POST", "/inventory/uom-convert", conversion_data)
                if response and response.status_code == 200:
                    result = response.json()
                    self.log_test("UOM Conversion", True, f"Converted: {result.get('converted_quantity', 0)}")
                else:
                    self.log_test("UOM Conversion", False, f"Status: {response.status_code if response else 'No response'}")
            else:
                self.log_test("UOM Conversion", True, "No items with dimensions found - skipping UOM conversion test")
        else:
            self.log_test("Check Items for UOM Conversion", False, f"Status: {response.status_code if response else 'No response'}")

    def test_procurement_enhancements(self):
        """Test Procurement Module Enhancements as per review request"""
        print("\n=== Testing Procurement Module Enhancements ===")
        
        # Test 1: Pincode Auto-Fill API
        print("\n--- Testing Pincode Auto-Fill API ---")
        
        # Test valid pincode: 400001 (Mumbai)
        response = self.make_request("GET", "/procurement/geo/pincode/400001")
        if response and response.status_code == 200:
            data = response.json()
            mumbai_success = (
                data.get("city") and data.get("state") and data.get("district") and 
                data.get("country") == "India" and "mumbai" in data.get("city", "").lower()
            )
            self.log_test("Pincode 400001 (Mumbai)", mumbai_success, 
                         f"City: {data.get('city')}, State: {data.get('state')}, District: {data.get('district')}")
        else:
            self.log_test("Pincode 400001 (Mumbai)", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test valid pincode: 110001 (Delhi)
        response = self.make_request("GET", "/procurement/geo/pincode/110001")
        if response and response.status_code == 200:
            data = response.json()
            delhi_success = (
                data.get("city") and data.get("state") and data.get("district") and 
                data.get("country") == "India" and "delhi" in data.get("state", "").lower()
            )
            self.log_test("Pincode 110001 (Delhi)", delhi_success, 
                         f"City: {data.get('city')}, State: {data.get('state')}, District: {data.get('district')}")
        else:
            self.log_test("Pincode 110001 (Delhi)", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test invalid pincode: 12345
        response = self.make_request("GET", "/procurement/geo/pincode/12345")
        if response and response.status_code == 404:
            self.log_test("Invalid Pincode 12345", True, "Correctly returned 404 for invalid pincode")
        else:
            self.log_test("Invalid Pincode 12345", False, f"Expected 404, got {response.status_code if response else 'No response'}")
        
        # Test 2: GSTIN Validation API
        print("\n--- Testing GSTIN Validation API ---")
        
        # Test valid GSTIN: 27AAACR4849M1Z7 (Maharashtra)
        response = self.make_request("GET", "/procurement/gstin/validate/27AAACR4849M1Z7")
        if response and response.status_code == 200:
            data = response.json()
            mh_gstin_success = (
                data.get("valid") == True and 
                "maharashtra" in data.get("state", "").lower() and
                data.get("pan") == "AAACR4849M"
            )
            self.log_test("Valid GSTIN 27AAACR4849M1Z7 (Maharashtra)", mh_gstin_success, 
                         f"Valid: {data.get('valid')}, State: {data.get('state')}, PAN: {data.get('pan')}")
        else:
            self.log_test("Valid GSTIN 27AAACR4849M1Z7 (Maharashtra)", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test valid GSTIN: 07AAACR4849M1ZK (Delhi)
        response = self.make_request("GET", "/procurement/gstin/validate/07AAACR4849M1ZK")
        if response and response.status_code == 200:
            data = response.json()
            delhi_gstin_success = (
                data.get("valid") == True and 
                "delhi" in data.get("state", "").lower() and
                data.get("pan") == "AAACR4849M"
            )
            self.log_test("Valid GSTIN 07AAACR4849M1ZK (Delhi)", delhi_gstin_success, 
                         f"Valid: {data.get('valid')}, State: {data.get('state')}, PAN: {data.get('pan')}")
        else:
            self.log_test("Valid GSTIN 07AAACR4849M1ZK (Delhi)", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test invalid GSTIN: 12345678901234X
        response = self.make_request("GET", "/procurement/gstin/validate/12345678901234X")
        if response and response.status_code == 400:
            self.log_test("Invalid GSTIN 12345678901234X", True, "Correctly returned 400 for invalid GSTIN")
        else:
            self.log_test("Invalid GSTIN 12345678901234X", False, f"Expected 400, got {response.status_code if response else 'No response'}")
        
        # Test 3: Supplier Create with Auto-Fill
        print("\n--- Testing Supplier Create with Auto-Fill ---")
        
        supplier_data = {
            "supplier_name": "Test Auto-Fill Supplier",
            "supplier_type": "Raw Material",
            "contact_person": "Rajesh Sharma",
            "email": f"rajesh.{uuid.uuid4().hex[:8]}@testautofill.com",
            "phone": "9876543210",
            "address": "Test Address, Industrial Area",
            "pincode": "400001",  # Mumbai pincode for auto-fill
            "gstin": "27AAACR4849M1Z7",  # Valid Maharashtra GSTIN for auto-fill
            "payment_terms": "30 days",
            "credit_limit": 100000.0
        }
        
        response = self.make_request("POST", "/procurement/suppliers", supplier_data)
        if response and response.status_code == 200:
            supplier = response.json()
            supplier_id = supplier.get("id")
            
            # Check auto-fill from pincode and GSTIN
            city_filled = supplier.get("city") and "mumbai" in supplier.get("city", "").lower()
            state_filled = supplier.get("state") and "maharashtra" in supplier.get("state", "").lower()
            pan_filled = supplier.get("pan") == "AAACR4849M"
            
            autofill_success = city_filled and state_filled and pan_filled
            
            self.log_test("Supplier Create with Auto-Fill", autofill_success, 
                         f"ID: {supplier_id}, City: {supplier.get('city')}, State: {supplier.get('state')}, PAN: {supplier.get('pan')}")
            
            # Test 4: PO Edit API
            print("\n--- Testing PO Edit API ---")
            
            if supplier_id:
                # First, ensure we have a warehouse and item
                warehouse_id, item_id = self.test_inventory_setup()
                
                if warehouse_id and item_id:
                    # Create a draft PO
                    po_data = {
                        "supplier_id": supplier_id,
                        "po_type": "Standard",
                        "warehouse_id": warehouse_id,
                        "items": [
                            {
                                "item_id": item_id,
                                "quantity": 100.0,
                                "unit_price": 50.0,
                                "tax_percent": 18.0,
                                "discount_percent": 0.0,
                                "delivery_date": "2025-01-15",
                                "notes": "Test item for PO edit"
                            }
                        ],
                        "currency": "INR",
                        "payment_terms": "30 days",
                        "delivery_terms": "FOB",
                        "notes": "Original PO notes",
                        "expected_date": "2025-01-15"
                    }
                    
                    response = self.make_request("POST", "/procurement/purchase-orders", po_data)
                    if response and response.status_code == 200:
                        po = response.json()
                        po_id = po.get("id")
                        self.log_test("Create Draft PO for Edit Test", True, f"PO: {po.get('po_number')}, Status: {po.get('status')}")
                        
                        # Test editing draft PO (should succeed)
                        edit_data = {
                            "notes": "Updated PO notes for testing",
                            "expected_date": "2025-01-20"
                        }
                        
                        response = self.make_request("PUT", f"/procurement/purchase-orders/{po_id}", edit_data)
                        if response and response.status_code == 200:
                            updated_po = response.json()
                            edit_success = (
                                updated_po.get("notes") == "Updated PO notes for testing" and
                                updated_po.get("expected_date") == "2025-01-20"
                            )
                            self.log_test("Edit Draft PO", edit_success, 
                                         f"Notes: {updated_po.get('notes')}, Expected Date: {updated_po.get('expected_date')}")
                            
                            # Change PO status to "received" to test edit restriction
                            response = self.make_request("PUT", f"/procurement/purchase-orders/{po_id}/status?status=received")
                            if response and response.status_code == 200:
                                self.log_test("Change PO Status to Received", True, "Status changed successfully")
                                
                                # Try to edit received PO (should fail with 400)
                                edit_data_2 = {
                                    "notes": "This edit should fail"
                                }
                                
                                response = self.make_request("PUT", f"/procurement/purchase-orders/{po_id}", edit_data_2)
                                if response and response.status_code == 400:
                                    self.log_test("Edit Received PO (Should Fail)", True, "Correctly returned 400 for editing received PO")
                                else:
                                    self.log_test("Edit Received PO (Should Fail)", False, f"Expected 400, got {response.status_code if response else 'No response'}")
                            else:
                                self.log_test("Change PO Status to Received", False, f"Status: {response.status_code if response else 'No response'}")
                        else:
                            self.log_test("Edit Draft PO", False, f"Status: {response.status_code if response else 'No response'}")
                    else:
                        self.log_test("Create Draft PO for Edit Test", False, f"Status: {response.status_code if response else 'No response'}")
                else:
                    self.log_test("PO Edit Test Setup", False, "Missing warehouse_id or item_id")
            else:
                self.log_test("PO Edit Test Setup", False, "No supplier_id from auto-fill test")
        else:
            self.log_test("Supplier Create with Auto-Fill", False, f"Status: {response.status_code if response else 'No response'}")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Backend API Tests for InstaBiz Industrial ERP - Procurement Module Enhancements")
        print(f"Base URL: {BASE_URL}")
        print("=" * 80)
        
        # Authentication tests
        if not self.test_auth_login():
            print("❌ Authentication failed - stopping tests")
            return
        
        self.test_auth_me()
        
        # Test procurement module enhancements as per review request
        self.test_procurement_enhancements()
        
        # Test accounts credit note creation
        self.test_accounts_credit_note()
        
        # Test other modules if needed
        # self.test_director_dashboard()
        # self.test_branches()
        # self.test_gatepass()
        # self.test_expenses()
        # self.test_payroll()
        # self.test_employee_vault()
        # self.test_sales_incentives()
        # self.test_import_bridge()
        # self.test_production_v2()
        # self.test_inventory_uom_conversion()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed == total

if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)