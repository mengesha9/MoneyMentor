import { 
  CalculationInput, 
  CalculationResult, 
  CALC_DEFAULTS
} from '../types';
import { logger } from '../utils/logger';

export class CalcService {
  async calculate(input: CalculationInput): Promise<CalculationResult> {
    switch (input.type) {
      case 'credit_card_payoff':
        return this.calculateCreditCardPayoff(input.inputs);
      case 'savings_goal':
        return this.calculateSavingsGoal(input.inputs);
      case 'loan_amortization':
        return this.calculateLoanAmortization(input.inputs);
      default:
        throw new Error(`Unsupported calculation type: ${input.type}`);
    }
  }

  private calculateCreditCardPayoff(inputs: any): CalculationResult {
    const { principal, interestRate, monthlyPayment, targetMonths } = inputs;
    
    if (!principal || principal <= 0) {
      throw new Error('Principal amount must be greater than 0');
    }

    const monthlyRate = (interestRate || CALC_DEFAULTS.DEFAULT_CREDIT_CARD_APR) / 100 / 12;
    let balance = principal;
    let months = 0;
    let totalInterest = 0;
    const stepByStepPlan: string[] = [];

    // If no monthly payment specified, calculate minimum payment
    let payment = monthlyPayment;
    if (!payment) {
      // Calculate payment to pay off in target months (default 36 months)
      const targetMonthsToUse = targetMonths || 36;
      payment = this.calculatePaymentForTarget(principal, monthlyRate, targetMonthsToUse);
    }

    // Ensure minimum payment covers interest
    const minPayment = balance * monthlyRate + 10;
    if (payment < minPayment) {
      payment = minPayment;
      stepByStepPlan.push(`⚠️ Minimum payment increased to $${payment.toFixed(2)} to cover interest`);
    }

    // Calculate payoff schedule
    while (balance > 0 && months < 600) { // Cap at 50 years
      const interestPayment = balance * monthlyRate;
      const principalPayment = Math.min(payment - interestPayment, balance);
      
      balance -= principalPayment;
      totalInterest += interestPayment;
      months++;

      if (months <= 3 || months % 12 === 0 || balance <= 0) {
        stepByStepPlan.push(
          `Month ${months}: Balance $${balance.toFixed(2)}, Interest $${interestPayment.toFixed(2)}, Principal $${principalPayment.toFixed(2)}`
        );
      }
    }

    stepByStepPlan.push(`🎯 Strategy: Pay $${payment.toFixed(2)} monthly to eliminate debt faster`);
    stepByStepPlan.push(`💡 Tip: Consider transferring to a 0% APR card if available`);

    return {
      type: 'credit_card_payoff',
      monthlyPayment: payment,
      monthsToPayoff: months,
      totalInterest,
      totalAmount: principal + totalInterest,
      stepByStepPlan,
      disclaimer: 'These are estimates only. Consult with a certified financial advisor for personalized advice.',
      metadata: {
        inputValues: { principal, interestRate, monthlyPayment },
        calculationDate: new Date().toISOString()
      }
    };
  }

  private calculateSavingsGoal(inputs: any): CalculationResult {
    const { targetAmount, timeframe, currentSavings, interestRate } = inputs;
    
    if (!targetAmount || targetAmount <= 0) {
      throw new Error('Target amount must be greater than 0');
    }
    
    if (!timeframe || timeframe <= 0) {
      throw new Error('Timeframe must be greater than 0');
    }

    const currentBalance = currentSavings || 0;
    const remainingAmount = targetAmount - currentBalance;
    const monthlyRate = (interestRate || CALC_DEFAULTS.DEFAULT_SAVINGS_RATE) / 100 / 12;
    
    // Calculate required monthly savings with compound interest
    let monthlyPayment = 0;
    if (monthlyRate > 0) {
      // Future value of annuity formula
      monthlyPayment = remainingAmount / (((Math.pow(1 + monthlyRate, timeframe) - 1) / monthlyRate));
    } else {
      // Simple division if no interest
      monthlyPayment = remainingAmount / timeframe;
    }

    const totalSaved = monthlyPayment * timeframe;
    const totalInterest = totalSaved + currentBalance - targetAmount;

    const stepByStepPlan: string[] = [];
    stepByStepPlan.push(`💰 Starting amount: $${currentBalance.toFixed(2)}`);
    stepByStepPlan.push(`🎯 Target amount: $${targetAmount.toFixed(2)}`);
    stepByStepPlan.push(`📅 Timeframe: ${timeframe} months`);
    stepByStepPlan.push(`💵 Monthly savings needed: $${monthlyPayment.toFixed(2)}`);
    
    if (monthlyRate > 0) {
      stepByStepPlan.push(`📈 Estimated interest earned: $${Math.max(0, totalInterest).toFixed(2)}`);
      stepByStepPlan.push(`💡 Tip: Consider a high-yield savings account to maximize growth`);
    }
    
    stepByStepPlan.push(`🏆 Strategy: Set up automatic transfers to stay on track`);

    return {
      type: 'savings_goal',
      monthlyPayment,
      monthsToPayoff: timeframe,
      totalInterest: Math.max(0, totalInterest),
      totalAmount: targetAmount,
      stepByStepPlan,
      disclaimer: 'These are estimates only. Actual returns may vary based on market conditions.',
      metadata: {
        inputValues: { targetAmount, timeframe, currentSavings, interestRate },
        calculationDate: new Date().toISOString()
      }
    };
  }

  private calculateLoanAmortization(inputs: any): CalculationResult {
    const { principal, interestRate: apr, timeframe } = inputs;
    
    if (!principal || principal <= 0) {
      throw new Error('Principal amount must be greater than 0');
    }
    
    if (!apr || apr <= 0) {
      throw new Error('Interest rate must be greater than 0');
    }

    const monthlyRate = apr / 100 / 12;
    const numPayments = timeframe || 360; // Default to 30 years
    
    // Calculate monthly payment using amortization formula
    const monthlyPayment = principal * 
      (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
      (Math.pow(1 + monthlyRate, numPayments) - 1);

    const totalAmount = monthlyPayment * numPayments;
    const totalInterest = totalAmount - principal;

    const stepByStepPlan: string[] = [];
    stepByStepPlan.push(`🏠 Loan amount: $${principal.toFixed(2)}`);
    stepByStepPlan.push(`📊 Interest rate: ${apr}% APR`);
    stepByStepPlan.push(`📅 Term: ${Math.round(numPayments / 12)} years`);
    stepByStepPlan.push(`💳 Monthly payment: $${monthlyPayment.toFixed(2)}`);
    stepByStepPlan.push(`💰 Total interest: $${totalInterest.toFixed(2)}`);
    stepByStepPlan.push(`💡 Tip: Extra payments toward principal can save thousands in interest`);
    
    // Show first few payments breakdown
    let balance = principal;
    for (let i = 1; i <= 3; i++) {
      const interestPayment = balance * monthlyRate;
      const principalPayment = monthlyPayment - interestPayment;
      balance -= principalPayment;
      
      stepByStepPlan.push(
        `Payment ${i}: Interest $${interestPayment.toFixed(2)}, Principal $${principalPayment.toFixed(2)}, Balance $${balance.toFixed(2)}`
      );
    }

    return {
      type: 'loan_amortization',
      monthlyPayment,
      monthsToPayoff: numPayments,
      totalInterest,
      totalAmount,
      stepByStepPlan,
      disclaimer: 'These are estimates only. Actual loan terms may vary. Consult with a lender for exact details.',
      metadata: {
        inputValues: { principal, interestRate: apr, timeframe },
        calculationDate: new Date().toISOString()
      }
    };
  }

  private calculatePaymentForTarget(principal: number, monthlyRate: number, targetMonths: number): number {
    // Calculate payment needed to pay off in target months
    if (monthlyRate === 0) {
      return principal / targetMonths;
    }
    
    return principal * 
      (monthlyRate * Math.pow(1 + monthlyRate, targetMonths)) / 
      (Math.pow(1 + monthlyRate, targetMonths) - 1);
  }
} 