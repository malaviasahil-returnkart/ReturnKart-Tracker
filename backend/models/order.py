"""
RETURNKART.IN — PYDANTIC DATA CONTRACTS
Shared models used by: DB layer, AI service, API layer.
Define the shape ONCE here. Import everywhere else.
"""
from datetime import date, datetime
from typing import Optional, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class DPDPFields(BaseModel):
    """DPDP Act 2023 compliance fields. Required on all models touching user data."""
    consent_timestamp: Optional[datetime] = None
    purpose_id: Optional[str] = None
    data_expiry_date: Optional[date] = None
    anonymization_status: bool = False


class ReturnPolicy(BaseModel):
    """Return policy looked up from knowledge_base.json."""
    brand: str
    category: str
    return_window_days: int
    return_type: Literal["refund", "replacement", "exchange", "refund_or_exchange"]
    is_replacement_only: bool = False
    conditions: list[str] = []
    non_returnable: list[str] = []


class OrderBase(BaseModel):
    """Core order fields shared between create and read."""
    order_id: str = Field(..., description="Platform order ID e.g. 402-1234567-8901234")
    brand: str = Field(..., description="Amazon, Myntra, Flipkart, Meesho, Ajio")
    item_name: str
    price: float
    order_date: date
    return_deadline: Optional[date] = None
    category: Optional[str] = None
    courier_partner: Optional[str] = None
    delivery_pincode: Optional[str] = None
    is_replacement_only: bool = False
    status: Literal["active", "kept", "returned", "expired", "want_to_return"] = "active"
    source: Optional[str] = None


class OrderCreate(OrderBase, DPDPFields):
    """Used when inserting a new order into Supabase."""
    user_id: str


class Order(OrderBase, DPDPFields):
    """Full order as returned from DB."""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIOrderContext(BaseModel):
    """Structured output Gemini must return when parsing an invoice email."""
    order_id: Optional[str] = None
    brand: Optional[str] = None
    item_name: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "INR"
    order_date: Optional[str] = None
    category: Optional[str] = None
    courier_partner: Optional[str] = None
    delivery_pincode: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    raw_extraction_notes: Optional[str] = None
