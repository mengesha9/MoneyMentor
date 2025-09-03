import React from 'react';
import { CalculationResult as CalculationResultType } from '../../types';
import '../../styles/ChatWidget.css';

interface CalculationResultProps {
  result: CalculationResultType;
}

export const CalculationResult: React.FC<CalculationResultProps> = ({ result }) => {
  const getCalculationIcon = (type: string) => {
    switch (type) {
      case 'credit_card_payoff':
        return '💳';
      case 'savings_goal':
        return '💰';
      case 'loan_amortization':
        return '🏠';
      default:
        return '📊';
    }
  };

  const getCalculationTitle = (type: string) => {
    switch (type) {
      case 'credit_card_payoff':
        return 'Credit Card Payoff Plan';
      case 'savings_goal':
        return 'Savings Goal Plan';
      case 'loan_amortization':
        return 'Loan Payment Plan';
      default:
        return 'Financial Calculation';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatMonths = (months: number) => {
    if (months < 12) {
      return `${months} month${months !== 1 ? 's' : ''}`;
    }
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    if (remainingMonths === 0) {
      return `${years} year${years !== 1 ? 's' : ''}`;
    }
    return `${years} year${years !== 1 ? 's' : ''} ${remainingMonths} month${remainingMonths !== 1 ? 's' : ''}`;
  };

  return (
    <div className="calculation-result">
      <div className="calculation-header">
        <span className="calculation-icon">{getCalculationIcon(result.type)}</span>
        <h3 className="calculation-title">{getCalculationTitle(result.type)}</h3>
      </div>
      
      <div className="calculation-summary">
        {result.monthlyPayment && (
          <div className="calculation-item">
            <span className="calculation-label">Monthly Payment:</span>
            <span className="calculation-value">{formatCurrency(result.monthlyPayment)}</span>
          </div>
        )}
        
        {result.monthsToPayoff && (
          <div className="calculation-item">
            <span className="calculation-label">
              {result.type === 'savings_goal' ? 'Time to Goal:' : 
               result.type === 'credit_card_payoff' ? 'Payoff Time:' : 'Loan Term:'}
            </span>
            <span className="calculation-value">{formatMonths(result.monthsToPayoff)}</span>
          </div>
        )}
        
        <div className="calculation-item">
          <span className="calculation-label">
            {result.type === 'savings_goal' ? 'Interest Earned:' : 'Total Interest:'}
          </span>
          <span className="calculation-value">{formatCurrency(result.totalInterest)}</span>
        </div>
        
        <div className="calculation-item">
          <span className="calculation-label">
            {result.type === 'savings_goal' ? 'Target Amount:' : 'Total Amount:'}
          </span>
          <span className="calculation-value total-amount">{formatCurrency(result.totalAmount)}</span>
        </div>
      </div>

      {result.stepByStepPlan && result.stepByStepPlan.length > 0 && (
        <div className="calculation-details">
          <h4 className="details-title">📋 Details</h4>
          <ul className="step-by-step-plan">
            {result.stepByStepPlan.slice(0, 5).map((step, index) => (
              <li key={index} className="plan-step">{step}</li>
            ))}
          </ul>
        </div>
      )}

      {result.disclaimer && (
        <div className="calculation-disclaimer">
          <p className="disclaimer-text">⚠️ {result.disclaimer}</p>
        </div>
      )}
    </div>
  );
}; 