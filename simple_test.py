#!/usr/bin/env python3
"""
Simple test to debug approval enforcement
"""

import requests
import json

BASE_URL = "https://postgres-frontend-v1.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@instabiz.com"
ADMIN_PASSWORD = "adminpassword"

def test_approval_enforcement():
    session = requests.Session()
    
    # Login
    print("1. Testing login...")
    response = session.post(f"{BASE_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }, timeout=30)
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        return
        
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("✅ Login successful")
    
    # Test stock transfer approval
    print("\n2. Testing stock transfer approval...")
    
    # Get warehouses and items
    wh_response = session.get(f"{BASE_URL}/inventory/warehouses", headers=headers, timeout=30)
    item_response = session.get(f"{BASE_URL}/inventory/items", headers=headers, timeout=30)
    
    if wh_response.status_code != 200 or item_response.status_code != 200:
        print("Failed to get warehouses or items")
        return
        
    warehouses = wh_response.json()
    items = item_response.json()
    
    if len(warehouses) < 2 or len(items) < 1:
        print("Need at least 2 warehouses and 1 item")
        return
    
    # Create transfer
    transfer_data = {
        "from_warehouse": warehouses[0]["id"],
        "to_warehouse": warehouses[1]["id"],
        "items": [{"item_id": items[0]["id"], "quantity": 5.0}]
    }
    
    transfer_response = session.post(f"{BASE_URL}/inventory/transfers", json=transfer_data, headers=headers, timeout=30)
    
    if transfer_response.status_code != 200:
        print(f"Transfer creation failed: {transfer_response.status_code}")
        print(transfer_response.text)
        return
        
    transfer_id = transfer_response.json()["id"]
    print(f"✅ Transfer created: {transfer_id}")
    
    # Try to issue without approval
    print("3. Testing issue without approval...")
    issue_response = session.put(f"{BASE_URL}/inventory/transfers/{transfer_id}/issue", headers=headers, timeout=30)
    
    print(f"Issue response status: {issue_response.status_code}")
    print(f"Issue response text: {issue_response.text}")
    
    if issue_response.status_code == 409:
        print("✅ Correctly blocked with 409")
    else:
        print(f"❌ Expected 409, got {issue_response.status_code}")

if __name__ == "__main__":
    test_approval_enforcement()