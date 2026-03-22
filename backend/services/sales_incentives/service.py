"""
Sales Incentives Services - Business Logic Layer for Sales Incentives module
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from repositories.sales_incentives import (
    sales_target_repository,
    incentive_slab_repository,
    incentive_payout_repository,
    sales_achievement_repository
)
from repositories.hrms import employee_repository
from core.exceptions import NotFoundError, ValidationError, BusinessRuleError
from core.legacy_db import db


class SalesTargetService:
    """Business logic for Sales Target management"""
    
    def __init__(self):
        self.repo = sales_target_repository
    
    async def get_all_targets(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all targets with optional filters"""
        query = {}
        if filters:
            if filters.get('employee_id'):
                query['employee_id'] = filters['employee_id']
            if filters.get('period'):
                query['period'] = filters['period']
            if filters.get('status'):
                query['status'] = filters['status']
            if filters.get('target_type'):
                query['target_type'] = filters['target_type']
        return await self.repo.get_all(query)
    
    async def get_target(self, target_id: str) -> Dict[str, Any]:
        """Get a single target"""
        return await self.repo.get_by_id_or_raise(target_id, "Sales Target")
    
    async def create_target(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new sales target"""
        # Get employee name
        employee = await employee_repository.get_by_id(data['employee_id'])
        if employee:
            data['employee_name'] = employee.get('name')
        
        # Check for existing target
        existing = await self.repo.get_employee_current_target(
            data['employee_id'],
            data['target_type'],
            data['period']
        )
        if existing:
            raise BusinessRuleError("Target already exists for this employee and period")
        
        data['achieved_amount'] = 0
        data['achieved_quantity'] = 0
        data['achievement_percent'] = 0
        data['status'] = 'active'
        
        return await self.repo.create(data, user_id)
    
    async def update_achievement(self, target_id: str, achieved_amount: float, achieved_quantity: int, user_id: str) -> Dict[str, Any]:
        """Update target achievement"""
        target = await self.get_target(target_id)
        
        target_amount = target.get('target_amount', 0)
        achievement_percent = (achieved_amount / target_amount * 100) if target_amount > 0 else 0
        
        # Determine status
        if achievement_percent >= 100:
            status = 'exceeded' if achievement_percent > 100 else 'achieved'
        else:
            status = 'active'
        
        return await self.repo.update(target_id, {
            'achieved_amount': achieved_amount,
            'achieved_quantity': achieved_quantity,
            'achievement_percent': round(achievement_percent, 2),
            'status': status
        }, user_id)
    
    async def get_employee_targets(self, employee_id: str) -> List[Dict[str, Any]]:
        """Get all targets for an employee"""
        return await self.repo.get_by_employee(employee_id)


class IncentiveSlabService:
    """Business logic for Incentive Slab management"""
    
    def __init__(self):
        self.repo = incentive_slab_repository
    
    async def get_all_slabs(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all incentive slabs"""
        if active_only:
            return await self.repo.get_active_slabs()
        return await self.repo.get_all()
    
    async def create_slab(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Create a new incentive slab"""
        data['is_active'] = True
        return await self.repo.create(data, user_id)
    
    async def update_slab(self, slab_id: str, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Update an incentive slab"""
        return await self.repo.update_or_raise(slab_id, data, user_id, "Incentive Slab")
    
    async def get_applicable_slab(self, achievement_percent: float) -> Optional[Dict[str, Any]]:
        """Get the applicable slab for a given achievement"""
        return await self.repo.get_slab_for_achievement(achievement_percent)


class IncentivePayoutService:
    """Business logic for Incentive Payout management"""
    
    def __init__(self):
        self.repo = incentive_payout_repository
    
    async def get_all_payouts(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get all payouts with optional filters"""
        query = {}
        if filters:
            if filters.get('employee_id'):
                query['employee_id'] = filters['employee_id']
            if filters.get('period'):
                query['period'] = filters['period']
            if filters.get('status'):
                query['status'] = filters['status']
        return await self.repo.get_all(query)
    
    async def calculate_payout(self, target_id: str, user_id: str) -> Dict[str, Any]:
        """Calculate incentive payout for a target"""
        target = await sales_target_service.get_target(target_id)
        
        achievement_percent = target.get('achievement_percent', 0)
        achieved_amount = target.get('achieved_amount', 0)
        target_amount = target.get('target_amount', 0)
        
        # Get applicable slab
        slab = await incentive_slab_service.get_applicable_slab(achievement_percent)
        
        if not slab:
            raise BusinessRuleError("No applicable incentive slab found for this achievement level")
        
        # Calculate incentive
        if slab.get('incentive_type') == 'percentage':
            incentive = achieved_amount * slab.get('incentive_value', 0) / 100
        elif slab.get('incentive_type') == 'fixed':
            incentive = slab.get('incentive_value', 0)
        else:  # per_unit
            incentive = target.get('achieved_quantity', 0) * slab.get('incentive_value', 0)
        
        # Calculate bonus for exceeding target
        bonus = 0
        if achievement_percent > 100:
            excess_amount = achieved_amount - target_amount
            bonus = excess_amount * 0.05  # 5% bonus on excess
        
        payout_data = {
            'employee_id': target.get('employee_id'),
            'employee_name': target.get('employee_name'),
            'period': target.get('period'),
            'target_id': target_id,
            'target_amount': target_amount,
            'achieved_amount': achieved_amount,
            'achievement_percent': achievement_percent,
            'slab_applied': slab.get('slab_name'),
            'calculated_incentive': round(incentive, 2),
            'bonus_amount': round(bonus, 2),
            'total_payout': round(incentive + bonus, 2),
            'status': 'calculated'
        }
        
        return await self.repo.create(payout_data, user_id)
    
    async def approve_payout(self, payout_id: str, user_id: str) -> Dict[str, Any]:
        """Approve a payout"""
        payout = await self.repo.get_by_id_or_raise(payout_id, "Incentive Payout")
        
        if payout.get('status') != 'calculated':
            raise BusinessRuleError(f"Cannot approve payout with status '{payout.get('status')}'")
        
        return await self.repo.update(payout_id, {
            'status': 'approved',
            'approved_by': user_id,
            'approved_at': datetime.now(timezone.utc).isoformat()
        }, user_id)
    
    async def mark_paid(self, payout_id: str, payroll_id: str, user_id: str) -> Dict[str, Any]:
        """Mark payout as paid"""
        payout = await self.repo.get_by_id_or_raise(payout_id, "Incentive Payout")
        
        if payout.get('status') != 'approved':
            raise BusinessRuleError("Cannot mark as paid - payout must be approved first")
        
        return await self.repo.update(payout_id, {
            'status': 'paid',
            'payroll_id': payroll_id,
            'paid_at': datetime.now(timezone.utc).isoformat()
        }, user_id)
    
    async def get_pending_approval(self) -> List[Dict[str, Any]]:
        """Get payouts pending approval"""
        return await self.repo.get_pending_approval()


class SalesLeaderboardService:
    """Business logic for Sales Leaderboard"""
    
    def __init__(self):
        self.repo = sales_achievement_repository
    
    async def get_leaderboard(self, period: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sales leaderboard for a period"""
        return await self.repo.get_leaderboard(period, limit)
    
    async def get_employee_rank(self, employee_id: str, period: str) -> Dict[str, Any]:
        """Get employee's rank in the leaderboard"""
        leaderboard = await self.get_leaderboard(period, limit=100)
        for rank, entry in enumerate(leaderboard, 1):
            if entry.get('employee_id') == employee_id:
                return {
                    'rank': rank,
                    'total_participants': len(leaderboard),
                    **entry
                }
        return {'rank': None, 'total_participants': len(leaderboard)}


# Service instances
sales_target_service = SalesTargetService()
incentive_slab_service = IncentiveSlabService()
incentive_payout_service = IncentivePayoutService()
sales_leaderboard_service = SalesLeaderboardService()
