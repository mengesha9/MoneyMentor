from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from datetime import datetime

from app.models.schemas import CalculationRequest, CalculationResult
from app.services.calculation_service import CalculationService

logger = logging.getLogger(__name__)
router = APIRouter()

def get_calculation_service() -> CalculationService:
    """Get CalculationService instance"""
    return CalculationService()

@router.post("/credit-card-payoff", response_model=CalculationResult)
async def calculate_credit_card_payoff(
    request: CalculationRequest,
    calculation_service: CalculationService = Depends(get_calculation_service)
):
    """Calculate credit card payoff timeline - matches client requirements exactly"""
    try:
        # Extract parameters for credit card payoff
        params = {
            "balance": request.principal,
            "apr": request.interest_rate,
            "monthly_payment": request.monthly_payment,
            "target_months": request.target_months
        }
        
        # Perform calculation
        result = await calculation_service.calculate("credit_card_payoff", params)
        
        return CalculationResult(**result)
        
    except Exception as e:
        logger.error(f"Credit card payoff calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Credit card payoff calculation failed")

@router.post("/savings-goal", response_model=CalculationResult)
async def calculate_savings_goal(
    request: CalculationRequest,
    calculation_service: CalculationService = Depends(get_calculation_service)
):
    """Calculate savings goal projection - matches client requirements exactly"""
    try:
        # Extract parameters for savings goal
        params = {
            "target_amount": request.target_amount,
            "timeframe_months": request.target_months,
            "current_savings": 0,  # Default to 0 if not provided
            "interest_rate": request.interest_rate
        }
        
        # Perform calculation
        result = await calculation_service.calculate("savings_goal", params)
        
        return CalculationResult(**result)
        
    except Exception as e:
        logger.error(f"Savings goal calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Savings goal calculation failed")

@router.post("/student-loan", response_model=CalculationResult)
async def calculate_student_loan_amortization(
    request: CalculationRequest,
    calculation_service: CalculationService = Depends(get_calculation_service)
):
    """Calculate student loan amortization - matches client requirements exactly"""
    try:
        # Extract parameters for student loan amortization
        params = {
            "principal": request.principal,
            "apr": request.interest_rate,
            "term_months": request.target_months or 360,  # Default to 30 years
            "monthly_payment": request.monthly_payment
        }
        
        # Perform calculation
        result = await calculation_service.calculate("student_loan", params)
        
        return CalculationResult(**result)
        
    except Exception as e:
        logger.error(f"Student loan amortization calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Student loan amortization calculation failed")

@router.post("/calculate")
async def generic_calculation(
    calculation_data: Dict[str, Any],
    calculation_service: CalculationService = Depends(get_calculation_service)
):
    """Generic calculation endpoint - matches client requirements exactly"""
    try:
        # Validate required fields
        if "type" not in calculation_data:
            raise HTTPException(status_code=400, detail="Calculation type is required")
        
        calculation_type = calculation_data["type"]
        inputs = calculation_data.get("inputs", {})
        
        # Perform calculation
        result = await calculation_service.calculate(calculation_type, inputs)
        
        return {
            "success": True,
            "data": result,
            "disclaimer": "Estimates only. Verify with a certified financial professional."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generic calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Calculation failed")

@router.get("/health")
async def health_check():
    """Health check endpoint for the calculation service"""
    return {
        "status": "healthy",
        "service": "calc-fn",
        "timestamp": datetime.utcnow().isoformat()
    } 