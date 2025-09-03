# Financial disclaimer
FINANCIAL_DISCLAIMER = """
⚠️ Important Disclaimer:
The financial calculations and advice provided are estimates only. 
Please verify all calculations and consult with a certified financial professional 
before making any financial decisions. Past performance is not indicative of future results.
"""

# Retry configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "initial_delay": 1,  # seconds
    "max_delay": 10,     # seconds
    "exponential_base": 2
}

# Quiz configuration
QUIZ_CONFIG = {
    "diagnostic_questions": 10,
    "micro_quiz_interval": 3,  # chat turns
    "confidence_levels": {
        1: "Not confident at all",
        2: "Somewhat not confident",
        3: "Neutral",
        4: "Somewhat confident",
        5: "Very confident"
    }
}

# Calculation types
CALCULATION_TYPES = {
    "credit_card": "Credit Card Payoff",
    "savings": "Savings Goal",
    "student_loan": "Student Loan",
    "investment": "Investment Growth"
} 