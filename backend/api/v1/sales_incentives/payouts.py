"""
Sales Incentives API Routes - Payouts
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from core.security import get_current_user, require_manager
from services.sales_incentives.service import incentive_payout_service, sales_leaderboard_service

router = APIRouter(prefix="/payouts", tags=["Sales Incentives - Payouts"])


@router.get("")
async def get_payouts(
    employee_id: Optional[str] = None,
    period: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all payouts with optional filters"""
    filters = {}
    if employee_id:
        filters['employee_id'] = employee_id
    if period:
        filters['period'] = period
    if status:
        filters['status'] = status
    return await incentive_payout_service.get_all_payouts(filters)


@router.get("/pending-approval")
async def get_pending_approval(
    current_user: dict = Depends(get_current_user)
):
    """Get payouts pending approval"""
    return await incentive_payout_service.get_pending_approval()


@router.post("/calculate/{target_id}")
async def calculate_payout(
    target_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Calculate incentive payout for a target"""
    return await incentive_payout_service.calculate_payout(target_id, current_user['id'])


@router.put("/{payout_id}/approve")
async def approve_payout(
    payout_id: str,
    current_user: dict = Depends(require_manager)
):
    """Approve a payout (Manager only)"""
    return await incentive_payout_service.approve_payout(payout_id, current_user['id'])


@router.put("/{payout_id}/mark-paid")
async def mark_paid(
    payout_id: str,
    payroll_id: str,
    current_user: dict = Depends(require_manager)
):
    """Mark payout as paid (Manager only)"""
    return await incentive_payout_service.mark_paid(payout_id, payroll_id, current_user['id'])


@router.get("/leaderboard/{period}")
async def get_leaderboard(
    period: str,
    limit: int = Query(10, description="Number of top performers to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get sales leaderboard for a period"""
    return await sales_leaderboard_service.get_leaderboard(period, limit)
