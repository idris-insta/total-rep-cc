"""
Seed data script for PostgreSQL
Seeds initial demo data for the ERP system
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Setup path for imports
sys.path.insert(0, str(ROOT_DIR))

from core.database import init_db, close_db, async_session_factory
from core.legacy_db import db


async def seed_admin_user():
    """Seed admin user"""
    existing = await db.users.find_one({'email': 'admin@adhesiveflow.com'})
    if not existing:
        hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        await db.users.insert_one({
            'id': str(uuid.uuid4()),
            'email': 'admin@adhesiveflow.com',
            'password': hashed,
            'name': 'Admin User',
            'role': 'admin',
            'location': 'Head Office',
            'department': 'Management',
            'is_active': True,
        })
        print("  ✓ Admin user created (admin@adhesiveflow.com / admin123)")
    else:
        print("  ✓ Admin user already exists")


async def seed_machines():
    """Seed initial machine data"""
    machines = [
        {'id': str(uuid.uuid4()), 'machine_code': 'SLIT-001', 'machine_name': 'Slitting Machine 1', 'machine_type': 'slitting', 'capacity_per_hour': 120, 'location': 'SGM', 'status': 'active'},
        {'id': str(uuid.uuid4()), 'machine_code': 'SLIT-002', 'machine_name': 'Slitting Machine 2', 'machine_type': 'slitting', 'capacity_per_hour': 120, 'location': 'SGM', 'status': 'active'},
        {'id': str(uuid.uuid4()), 'machine_code': 'CL1', 'machine_name': 'BOPP Coating Line 1', 'machine_type': 'coating', 'capacity_per_hour': 500, 'location': 'SGM', 'status': 'active'},
        {'id': str(uuid.uuid4()), 'machine_code': 'CL2', 'machine_name': 'Hotmelt Coating Line 2', 'machine_type': 'coating', 'capacity_per_hour': 400, 'location': 'SGM', 'status': 'active'},
        {'id': str(uuid.uuid4()), 'machine_code': 'RW-001', 'machine_name': 'Rewinding Machine 1', 'machine_type': 'rewinding', 'capacity_per_hour': 200, 'location': 'SGM', 'status': 'active'},
    ]
    existing = await db.machines.count_documents({})
    if existing == 0:
        await db.machines.insert_many(machines)
        print(f"  ✓ Seeded {len(machines)} machines")
    else:
        print(f"  ✓ Machines already exist ({existing} records)")


async def seed_warehouses():
    """Seed warehouses"""
    warehouses = [
        {'id': str(uuid.uuid4()), 'code': 'WH-BWD', 'name': 'Bhiwandi Warehouse', 'address': 'Bhiwandi', 'city': 'Bhiwandi', 'state': 'Maharashtra', 'warehouse_type': 'storage', 'is_active': True},
        {'id': str(uuid.uuid4()), 'code': 'WH-SGM', 'name': 'Sangamner Factory', 'address': 'Sangamner', 'city': 'Sangamner', 'state': 'Maharashtra', 'warehouse_type': 'production', 'is_active': True},
    ]
    existing = await db.warehouses.count_documents({})
    if existing == 0:
        await db.warehouses.insert_many(warehouses)
        print(f"  ✓ Seeded {len(warehouses)} warehouses")
    else:
        print(f"  ✓ Warehouses already exist ({existing} records)")


async def seed_items():
    """Seed inventory items"""
    items = [
        {'id': str(uuid.uuid4()), 'item_code': 'BOPP-CLR-48', 'item_name': 'BOPP Clear Tape 48mm', 'category': 'FG', 'item_type': 'BOPP', 'uom': 'Rolls', 'thickness': 40, 'width': 48, 'length': 65, 'color': 'Clear', 'adhesive_type': 'Acrylic', 'reorder_level': 500, 'safety_stock': 200, 'selling_price': 35.0, 'purchase_price': 22.0},
        {'id': str(uuid.uuid4()), 'item_code': 'BOPP-BRN-48', 'item_name': 'BOPP Brown Tape 48mm', 'category': 'FG', 'item_type': 'BOPP', 'uom': 'Rolls', 'thickness': 40, 'width': 48, 'length': 65, 'color': 'Brown', 'adhesive_type': 'Acrylic', 'reorder_level': 300, 'safety_stock': 100, 'selling_price': 38.0, 'purchase_price': 24.0},
        {'id': str(uuid.uuid4()), 'item_code': 'MASK-YLW-24', 'item_name': 'Masking Tape Yellow 24mm', 'category': 'FG', 'item_type': 'Masking', 'uom': 'Rolls', 'thickness': 80, 'width': 24, 'length': 20, 'color': 'Yellow', 'adhesive_type': 'Rubber', 'reorder_level': 200, 'safety_stock': 50, 'selling_price': 45.0, 'purchase_price': 28.0},
        {'id': str(uuid.uuid4()), 'item_code': 'BOPP-FILM-23', 'item_name': 'BOPP Film 23 Micron', 'category': 'RM', 'item_type': 'BOPP', 'uom': 'KG', 'thickness': 23, 'width': 1280, 'reorder_level': 5000, 'safety_stock': 2000, 'purchase_price': 135.0},
        {'id': str(uuid.uuid4()), 'item_code': 'ADH-ACR-01', 'item_name': 'Acrylic Adhesive Grade A', 'category': 'RM', 'item_type': 'Core', 'uom': 'KG', 'adhesive_type': 'Acrylic', 'reorder_level': 2000, 'safety_stock': 500, 'purchase_price': 180.0},
    ]
    existing = await db.items.count_documents({})
    if existing == 0:
        await db.items.insert_many(items)
        print(f"  ✓ Seeded {len(items)} inventory items")
    else:
        print(f"  ✓ Items already exist ({existing} records)")


async def seed_leads():
    """Seed CRM leads"""
    leads = [
        {'id': str(uuid.uuid4()), 'company_name': 'ABC Packaging Ltd', 'contact_person': 'Rajesh Kumar', 'email': 'rajesh@abcpack.com', 'phone': '+91-9876543210', 'source': 'IndiaMART', 'status': 'qualified', 'city': 'Mumbai', 'state': 'Maharashtra', 'country': 'India', 'expected_value': 250000, 'probability': 70},
        {'id': str(uuid.uuid4()), 'company_name': 'XYZ Industries', 'contact_person': 'Priya Sharma', 'email': 'priya@xyzind.com', 'phone': '+91-9898765432', 'source': 'Google', 'status': 'contacted', 'city': 'Delhi', 'state': 'Delhi', 'country': 'India', 'expected_value': 180000, 'probability': 40},
        {'id': str(uuid.uuid4()), 'company_name': 'Global Exports', 'contact_person': 'Ahmed Khan', 'email': 'ahmed@globalexp.com', 'phone': '+91-8765432109', 'source': 'Exhibition', 'status': 'new', 'city': 'Chennai', 'state': 'Tamil Nadu', 'country': 'India', 'expected_value': 500000, 'probability': 25},
        {'id': str(uuid.uuid4()), 'company_name': 'Star Electronics', 'contact_person': 'Vikram Patel', 'email': 'vikram@starel.com', 'phone': '+91-7654321098', 'source': 'TradeIndia', 'status': 'won', 'city': 'Ahmedabad', 'state': 'Gujarat', 'country': 'India', 'expected_value': 320000, 'probability': 95},
    ]
    existing = await db.leads.count_documents({})
    if existing == 0:
        await db.leads.insert_many(leads)
        print(f"  ✓ Seeded {len(leads)} CRM leads")
    else:
        print(f"  ✓ Leads already exist ({existing} records)")


async def seed_accounts():
    """Seed customer accounts"""
    accounts = [
        {'id': str(uuid.uuid4()), 'customer_name': 'Star Electronics Pvt Ltd', 'account_type': 'customer', 'gstin': '24AABCS1234F1Z5', 'email': 'accounts@starel.com', 'phone': '+91-7654321098', 'billing_city': 'Ahmedabad', 'billing_state': 'Gujarat', 'billing_country': 'India', 'credit_limit': 500000, 'credit_days': 30, 'payment_terms': 'Net 30', 'is_active': True},
        {'id': str(uuid.uuid4()), 'customer_name': 'Reliable Packaging Co', 'account_type': 'customer', 'gstin': '27AABCR5678G1Z3', 'email': 'purchase@reliable.com', 'phone': '+91-9988776655', 'billing_city': 'Pune', 'billing_state': 'Maharashtra', 'billing_country': 'India', 'credit_limit': 300000, 'credit_days': 45, 'payment_terms': 'Net 45', 'is_active': True},
        {'id': str(uuid.uuid4()), 'customer_name': 'Cosmo Adhesives Supplier', 'account_type': 'supplier', 'gstin': '27AABCC9012H1Z1', 'email': 'sales@cosmo.com', 'phone': '+91-8877665544', 'billing_city': 'Mumbai', 'billing_state': 'Maharashtra', 'billing_country': 'India', 'credit_limit': 1000000, 'credit_days': 60, 'payment_terms': 'Net 60', 'is_active': True},
    ]
    existing = await db.accounts.count_documents({})
    if existing == 0:
        await db.accounts.insert_many(accounts)
        print(f"  ✓ Seeded {len(accounts)} customer/supplier accounts")
    else:
        print(f"  ✓ Accounts already exist ({existing} records)")


async def seed_suppliers():
    """Seed suppliers"""
    suppliers = [
        {'id': str(uuid.uuid4()), 'supplier_code': 'SUP-001', 'supplier_name': 'Cosmo Films Ltd', 'email': 'sales@cosmofilms.com', 'phone': '+91-1234567890', 'gstin': '27AABCC9012H1Z1', 'city': 'Mumbai', 'state': 'Maharashtra', 'country': 'India', 'payment_terms': 'Net 60', 'supplier_type': 'raw_material', 'is_active': True},
        {'id': str(uuid.uuid4()), 'supplier_code': 'SUP-002', 'supplier_name': 'Henkel India', 'email': 'india@henkel.com', 'phone': '+91-2345678901', 'city': 'Pune', 'state': 'Maharashtra', 'country': 'India', 'payment_terms': 'Net 45', 'supplier_type': 'raw_material', 'is_active': True},
    ]
    existing = await db.suppliers.count_documents({})
    if existing == 0:
        await db.suppliers.insert_many(suppliers)
        print(f"  ✓ Seeded {len(suppliers)} suppliers")
    else:
        print(f"  ✓ Suppliers already exist ({existing} records)")


async def seed_employees():
    """Seed employees"""
    employees = [
        {'id': str(uuid.uuid4()), 'employee_code': 'EMP-001', 'name': 'Amit Deshmukh', 'email': 'amit@adhesiveflow.com', 'phone': '+91-9876543210', 'department': 'Production', 'designation': 'Production Manager', 'employment_type': 'permanent', 'status': 'active', 'location': 'SGM'},
        {'id': str(uuid.uuid4()), 'employee_code': 'EMP-002', 'name': 'Neha Singh', 'email': 'neha@adhesiveflow.com', 'phone': '+91-8765432109', 'department': 'Sales', 'designation': 'Sales Manager', 'employment_type': 'permanent', 'status': 'active', 'location': 'BWD'},
        {'id': str(uuid.uuid4()), 'employee_code': 'EMP-003', 'name': 'Rahul Patil', 'email': 'rahul@adhesiveflow.com', 'phone': '+91-7654321098', 'department': 'Quality', 'designation': 'QC Engineer', 'employment_type': 'permanent', 'status': 'active', 'location': 'SGM'},
    ]
    existing = await db.employees.count_documents({})
    if existing == 0:
        await db.employees.insert_many(employees)
        print(f"  ✓ Seeded {len(employees)} employees")
    else:
        print(f"  ✓ Employees already exist ({existing} records)")


async def seed_branches():
    """Seed branch data"""
    branches = [
        {'id': str(uuid.uuid4()), 'branch_code': 'HO', 'branch_name': 'Head Office', 'branch_type': 'head_office', 'city': 'Mumbai', 'state': 'Maharashtra'},
        {'id': str(uuid.uuid4()), 'branch_code': 'SGM', 'branch_name': 'Sangamner Factory', 'branch_type': 'factory', 'city': 'Sangamner', 'state': 'Maharashtra'},
        {'id': str(uuid.uuid4()), 'branch_code': 'BWD', 'branch_name': 'Bhiwandi Warehouse', 'branch_type': 'warehouse', 'city': 'Bhiwandi', 'state': 'Maharashtra'},
    ]
    existing = await db.branches.count_documents({})
    if existing == 0:
        await db.branches.insert_many(branches)
        print(f"  ✓ Seeded {len(branches)} branches")
    else:
        print(f"  ✓ Branches already exist ({existing} records)")


async def main():
    print("=" * 50)
    print("  AdhesiveFlow ERP - PostgreSQL Data Seeding")
    print("=" * 50)
    print()

    # Initialize database tables
    print("Initializing database tables...")
    await init_db()
    print("  ✓ Database tables created/verified\n")

    print("Seeding data...")
    try:
        await seed_admin_user()
        await seed_machines()
        await seed_warehouses()
        await seed_items()
        await seed_leads()
        await seed_accounts()
        await seed_suppliers()
        await seed_employees()
        await seed_branches()
        print("\n✓ All data seeded successfully!")
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
