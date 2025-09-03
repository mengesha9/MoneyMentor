from typing import Dict, Any, List
import logging
from datetime import datetime
import math

logger = logging.getLogger(__name__)

class CalculationService:
    """Deterministic financial calculation service matching client requirements"""
    
    def __init__(self):
        self.calculation_types = {
            "credit_card_payoff": self._calculate_credit_card_payoff,
            "savings_goal": self._calculate_savings_goal,
            "student_loan": self._calculate_student_loan_amortization
        }
    
    def _calculate_monthly_payment(self, principal: float, monthly_rate: float, term_months: int) -> float:
        """Calculate monthly payment using amortization formula"""
        if monthly_rate > 0:
            return principal * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
        else:
            return principal / term_months
    
    def _validate_positive_values(self, **kwargs):
        """Validate that all provided values are positive"""
        for name, value in kwargs.items():
            if value <= 0:
                raise ValueError(f"{name.replace('_', ' ').title()} must be greater than 0")
    
    async def calculate(self, calculation_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deterministic financial calculation with step-by-step plan"""
        try:
            if calculation_type not in self.calculation_types:
                raise ValueError(f"Unsupported calculation type: {calculation_type}")
            
            # Perform calculation
            result = await self.calculation_types[calculation_type](params)
            
            return result
            
        except Exception as e:
            logger.error(f"Calculation failed: {e}")
            raise
    
    async def _calculate_credit_card_payoff(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate credit card payoff timeline - only with real extracted data"""
        try:
            # Validate that we have the minimum required parameters
            if 'balance' not in params:
                raise ValueError("Missing required parameter: balance (loan amount)")
            if 'apr' not in params:
                raise ValueError("Missing required parameter: apr (interest rate)")
            
            balance = float(params['balance'])
            apr = float(params['apr'])
            monthly_payment = params.get('monthly_payment')
            target_months = params.get('target_months')
            
            self._validate_positive_values(balance=balance, apr=apr)
            monthly_rate = apr / 100 / 12
            
            # Calculate required payment if not provided
            if not monthly_payment:
                if target_months:
                    monthly_payment = self._calculate_monthly_payment(balance, monthly_rate, target_months)
                else:
                    # If no target months specified, we can't calculate without making assumptions
                    raise ValueError("Missing required parameter: target_months or monthly_payment")
            
            # Calculate actual payoff timeline
            remaining_balance = balance
            months = 0
            total_interest = 0
            
            while remaining_balance > 0 and months < 600:  # 50 years max
                interest_charge = remaining_balance * monthly_rate
                principal_payment = min(monthly_payment - interest_charge, remaining_balance)
                
                remaining_balance -= principal_payment
                total_interest += interest_charge
                months += 1
            
            # Generate step-by-step plan
            step_by_step_plan = [
                f"Starting balance: ${balance:,.2f}",
                f"APR: {apr}% (monthly rate: {monthly_rate*100:.2f}%)",
                f"Monthly payment: ${monthly_payment:,.2f}",
                f"Month 1: Pay ${principal_payment:,.2f} principal, ${interest_charge:,.2f} interest",
                f"Remaining balance after month 1: ${remaining_balance:,.2f}",
                f"Continue this pattern for {months} months",
                f"Total interest paid: ${total_interest:,.2f}",
                f"Total amount paid: ${balance + total_interest:,.2f}"
            ]
            
            return {
                "monthly_payment": round(monthly_payment, 2),
                "months_to_payoff": months,
                "total_interest": round(total_interest, 2),
                "step_by_step_plan": step_by_step_plan,
                "total_amount": round(balance + total_interest, 2)
            }
            
        except Exception as e:
            logger.error(f"Credit card payoff calculation failed: {e}")
            raise
    
    async def _calculate_savings_goal(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate savings goal projection - only with real extracted data"""
        try:
            # Validate that we have the minimum required parameters
            if 'target_amount' not in params:
                raise ValueError("Missing required parameter: target_amount")
            if 'target_months' not in params:
                raise ValueError("Missing required parameter: target_months (timeframe)")
            
            target_amount = float(params['target_amount'])
            timeframe_months = int(params['target_months'])
            current_savings = float(params.get('current_savings', 0))  # Default to 0 if not specified
            interest_rate = float(params.get('interest_rate', 0))  # Default to 0 if not specified
            
            if target_amount <= 0:
                raise ValueError("Target amount must be greater than 0")
            if timeframe_months <= 0:
                raise ValueError("Timeframe must be greater than 0")
            
            monthly_rate = interest_rate / 100 / 12
            needed_amount = target_amount - current_savings
            
            if needed_amount <= 0:
                # Already have enough savings
                return {
                    "monthly_payment": 0,
                    "months_to_payoff": 0,
                    "total_interest": 0,
                    "step_by_step_plan": [
                        f"Current savings: ${current_savings:,.2f}",
                        f"Target amount: ${target_amount:,.2f}",
                        "You already have enough savings to reach your goal!"
                    ],
                    "total_amount": current_savings
                }
            
            # Calculate required monthly contribution
            if monthly_rate > 0:
                # With compound interest
                future_value_of_current = current_savings * (1 + monthly_rate)**timeframe_months
                still_needed = target_amount - future_value_of_current
                
                if still_needed > 0:
                    monthly_payment = still_needed / (((1 + monthly_rate)**timeframe_months - 1) / monthly_rate)
                else:
                    monthly_payment = 0
            else:
                # No interest
                monthly_payment = needed_amount / timeframe_months
            
            # Calculate total interest earned
            total_contributions = current_savings + (monthly_payment * timeframe_months)
            total_interest = target_amount - total_contributions
            
            # Generate step-by-step plan
            step_by_step_plan = [
                f"Current savings: ${current_savings:,.2f}",
                f"Target amount: ${target_amount:,.2f}",
                f"Timeframe: {timeframe_months} months",
                f"Interest rate: {interest_rate}% annually",
                f"Monthly contribution needed: ${monthly_payment:,.2f}",
                f"Total contributions: ${total_contributions:,.2f}",
                f"Interest earned: ${max(0, total_interest):,.2f}",
                f"Final amount: ${target_amount:,.2f}"
            ]
            
            return {
                "monthly_payment": round(monthly_payment, 2),
                "months_to_payoff": timeframe_months,
                "total_interest": round(max(0, total_interest), 2),
                "step_by_step_plan": step_by_step_plan,
                "total_amount": round(target_amount, 2)
            }
            
        except Exception as e:
            logger.error(f"Savings goal calculation failed: {e}")
            raise
    
    async def _calculate_student_loan_amortization(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate student loan amortization - only with real extracted data"""
        try:
            # Validate that we have the minimum required parameters
            if 'balance' not in params and 'principal' not in params:
                raise ValueError("Missing required parameter: balance or principal (loan amount)")
            if 'apr' not in params:
                raise ValueError("Missing required parameter: apr (interest rate)")
            if 'target_months' not in params:
                raise ValueError("Missing required parameter: target_months (loan term)")
            
            principal = float(params.get('balance', params.get('principal')))
            apr = float(params['apr'])
            term_months = int(params['target_months'])
            monthly_payment = params.get('monthly_payment')
            
            self._validate_positive_values(principal=principal, apr=apr, term_months=term_months)
            monthly_rate = apr / 100 / 12
            
            # Calculate monthly payment if not provided
            if not monthly_payment:
                monthly_payment = self._calculate_monthly_payment(principal, monthly_rate, term_months)
            
            # Calculate total payments and interest
            total_payments = monthly_payment * term_months
            total_interest = total_payments - principal
            
            # Generate step-by-step plan
            step_by_step_plan = [
                f"Loan amount: ${principal:,.2f}",
                f"APR: {apr}% (monthly rate: {monthly_rate*100:.2f}%)",
                f"Loan term: {term_months} months ({term_months/12:.1f} years)",
                f"Monthly payment: ${monthly_payment:,.2f}",
                f"Total payments: ${total_payments:,.2f}",
                f"Total interest: ${total_interest:,.2f}",
                f"Total amount paid: ${total_payments:,.2f}"
            ]
            
            # Add first few payment breakdowns
            remaining_balance = principal
            for i in range(1, min(4, term_months + 1)):
                interest_payment = remaining_balance * monthly_rate
                principal_payment = monthly_payment - interest_payment
                remaining_balance -= principal_payment
                
                step_by_step_plan.append(
                    f"Payment {i}: ${principal_payment:,.2f} principal, ${interest_payment:,.2f} interest, ${remaining_balance:,.2f} remaining"
                )
            
            return {
                "monthly_payment": round(monthly_payment, 2),
                "months_to_payoff": term_months,
                "total_interest": round(total_interest, 2),
                "step_by_step_plan": step_by_step_plan,
                "total_amount": round(total_payments, 2)
            }
            
        except Exception as e:
            logger.error(f"Student loan amortization calculation failed: {e}")
            raise 