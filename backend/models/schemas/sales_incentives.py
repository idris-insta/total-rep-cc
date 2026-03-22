"""
Sales Incentives Schemas - Pydantic models for Sales Incentives module
"""
from pydantic import BaseModel
from typing import Optional, List


# ==================== SALES TARGET SCHEMAS ====================
class SalesTargetCreate(BaseModel):
    employee_id: str
    target_type: str  # monthly, quarterly, yearly
    period: str  # YYYY-MM, YYYY-Q1/Q2/Q3/Q4, YYYY
    target_amount: float
    target_quantity: int = 0
    product_category: Optional[str] = None
    branch_id: Optional[str] = None
    notes: Optional[str] = None


class SalesTargetUpdate(BaseModel):
    target_amount: Optional[float] = None
    target_quantity: Optional[int] = None
    notes: Optional[str] = None


class SalesTargetResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    target_type: str
    period: str
    target_amount: float
    target_quantity: int
    achieved_amount: float
    achieved_quantity: int
    achievement_percent: float
    product_category: Optional[str] = None
    branch_id: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: Optional[str] = None


# ==================== INCENTIVE SLAB SCHEMAS ====================
class IncentiveSlabCreate(BaseModel):
    slab_name: str
    min_achievement: float
    max_achievement: float
    incentive_type: str  # percentage, fixed, per_unit
    incentive_value: float
    is_cumulative: bool = False
    applies_to: str = "all"


class IncentiveSlabUpdate(BaseModel):
    slab_name: Optional[str] = None
    min_achievement: Optional[float] = None
    max_achievement: Optional[float] = None
    incentive_type: Optional[str] = None
    incentive_value: Optional[float] = None
    is_cumulative: Optional[bool] = None
    is_active: Optional[bool] = None


class IncentiveSlabResponse(BaseModel):
    id: str
    slab_name: str
    min_achievement: float
    max_achievement: float
    incentive_type: str
    incentive_value: float
    is_cumulative: bool
    applies_to: str
    is_active: bool
    created_at: Optional[str] = None


# ==================== INCENTIVE PAYOUT SCHEMAS ====================
class IncentivePayoutResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: Optional[str] = None
    period: str
    target_id: str
    target_amount: float
    achieved_amount: float
    achievement_percent: float
    slab_applied: str
    calculated_incentive: float
    bonus_amount: float
    total_payout: float
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    paid_at: Optional[str] = None
    payroll_id: Optional[str] = None
    created_at: Optional[str] = None


# ==================== LEADERBOARD SCHEMAS ====================
class LeaderboardEntry(BaseModel):
    rank: int
    employee_id: str
    employee_name: Optional[str] = None
    achieved_amount: float
    achievement_percent: float
