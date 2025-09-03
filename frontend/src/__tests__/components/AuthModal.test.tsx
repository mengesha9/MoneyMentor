import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import AuthModal, { logout } from '../../components/AuthModal'
import { registerUser, loginUser, logoutUser } from '../../utils/chatWidget/api'
import { storeAuthData } from '../../utils/sessionUtils'
import Cookies from 'js-cookie'

// Mock the API functions
vi.mock('../../utils/chatWidget/api', () => ({
  registerUser: vi.fn(),
  loginUser: vi.fn(),
  logoutUser: vi.fn(),
}))

vi.mock('../../utils/sessionUtils', () => ({
  storeAuthData: vi.fn(),
}))

vi.mock('js-cookie', () => ({
  default: {
    get: vi.fn((key: string) => undefined),
    set: vi.fn(),
    remove: vi.fn(),
  },
}))

describe('AuthModal', () => {
  const mockOnAuthSuccess = vi.fn()
  
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset module-level variable
    vi.doUnmock('../../components/AuthModal')
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Login Functionality', () => {
    it('should render login form by default', () => {
      render(<AuthModal isOpen={true} onAuthSuccess={mockOnAuthSuccess} />)
      
      expect(screen.getByText('Welcome Back')).toBeInTheDocument()
      expect(screen.getByText('Sign in to continue')).toBeInTheDocument()
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('should handle successful login with timing', async () => {
      const user = userEvent.setup()
      const mockLoginResponse = {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        user: { id: 'test-user-id' }
      }
      
      vi.mocked(loginUser).mockResolvedValue(mockLoginResponse)
      
      render(<AuthModal isOpen={true} onAuthSuccess={mockOnAuthSuccess} />)
      
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      // Fill form
      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      
      // Measure timing
      const startTime = performance.now()
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(loginUser).toHaveBeenCalledWith('test@example.com', 'password123')
      })
      
      const endTime = performance.now()
      const executionTime = endTime - startTime
      
      expect(storeAuthData).toHaveBeenCalledWith(mockLoginResponse)
      expect(mockOnAuthSuccess).toHaveBeenCalled()
      expect(executionTime).toBeLessThan(5000) // Should complete within 5 seconds
    })

    it('should handle login error with timing', async () => {
      const user = userEvent.setup()
      const errorMessage = 'Invalid credentials'
      
      vi.mocked(loginUser).mockRejectedValue(new Error(errorMessage))
      
      render(<AuthModal isOpen={true} onAuthSuccess={mockOnAuthSuccess} />)
      
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'wrongpassword')
      
      const startTime = performance.now()
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
      })
      
      const endTime = performance.now()
      const executionTime = endTime - startTime
      
      expect(executionTime).toBeLessThan(3000) // Error should be shown quickly
      expect(mockOnAuthSuccess).not.toHaveBeenCalled()
    })

    it('should show loading state during login', async () => {
      const user = userEvent.setup()
      
      // Create a promise that doesn't resolve immediately
      let resolveLogin: (value: any) => void
      const loginPromise = new Promise((resolve) => {
        resolveLogin = resolve
      })
      
      vi.mocked(loginUser).mockReturnValue(loginPromise)
      
      render(<AuthModal isOpen={true} onAuthSuccess={mockOnAuthSuccess} />)
      
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')
      
      const startTime = performance.now()
      await user.click(submitButton)
      
      // Check loading state appears quickly
      await waitFor(() => {
        expect(screen.getByText('Loading...')).toBeInTheDocument()
      }, { timeout: 1000 })
      
      const loadingTime = performance.now() - startTime
      expect(loadingTime).toBeLessThan(1000) // Loading state should appear within 1 second
      
      // Resolve the promise
      resolveLogin!({
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        user: { id: 'test-user-id' }
      })
      
      await waitFor(() => {
        expect(mockOnAuthSuccess).toHaveBeenCalled()
      })
    })
  })

  describe('Register Functionality', () => {
    it('should switch to register mode', async () => {
      const user = userEvent.setup()
      render(<AuthModal isOpen={true} onAuthSuccess={mockOnAuthSuccess} />)
      
      const signUpLink = screen.getByText('Sign Up')
      await user.click(signUpLink)
      
      expect(screen.getByRole('heading', { name: 'Create Account' })).toBeInTheDocument()
      expect(screen.getByText('Join MoneyMentor to start your financial journey')).toBeInTheDocument()
      expect(screen.getByLabelText(/first name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/last name/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
    })

    it('should handle successful registration with timing', async () => {
      const user = userEvent.setup()
      const mockRegisterResponse = {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        user: { id: 'test-user-id' }
      }
      
      vi.mocked(registerUser).mockResolvedValue(mockRegisterResponse)
      
      render(<AuthModal isOpen={true} onAuthSuccess={mockOnAuthSuccess} />)
      
      // Switch to register mode
      const signUpLink = screen.getByText('Sign Up')
      await user.click(signUpLink)
      
      // Fill form
      const firstNameInput = screen.getByLabelText(/first name/i)
      const lastNameInput = screen.getByLabelText(/last name/i)
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /create account/i })
      
      await user.type(firstNameInput, 'John')
      await user.type(lastNameInput, 'Doe')
      await user.type(emailInput, 'john.doe@example.com')
      await user.type(passwordInput, 'password123')
      
      const startTime = performance.now()
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(registerUser).toHaveBeenCalledWith(
          'john.doe@example.com',
          'password123',
          'John',
          'Doe'
        )
      })
      
      const endTime = performance.now()
      const executionTime = endTime - startTime
      
      expect(storeAuthData).toHaveBeenCalledWith(mockRegisterResponse)
      expect(mockOnAuthSuccess).toHaveBeenCalled()
      expect(executionTime).toBeLessThan(5000) // Should complete within 5 seconds
    })

    it('should handle registration error with timing', async () => {
      const user = userEvent.setup()
      const errorMessage = 'Email already exists'
      
      vi.mocked(registerUser).mockRejectedValue(new Error(errorMessage))
      
      render(<AuthModal isOpen={true} onAuthSuccess={mockOnAuthSuccess} />)
      
      // Switch to register mode
      const signUpLink = screen.getByText('Sign Up')
      await user.click(signUpLink)
      
      // Fill form
      const firstNameInput = screen.getByLabelText(/first name/i)
      const lastNameInput = screen.getByLabelText(/last name/i)
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /create account/i })
      
      await user.type(firstNameInput, 'John')
      await user.type(lastNameInput, 'Doe')
      await user.type(emailInput, 'existing@example.com')
      await user.type(passwordInput, 'password123')
      
      const startTime = performance.now()
      await user.click(submitButton)
      
      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument()
      })
      
      const endTime = performance.now()
      const executionTime = endTime - startTime
      
      expect(executionTime).toBeLessThan(3000) // Error should be shown quickly
      expect(mockOnAuthSuccess).not.toHaveBeenCalled()
    })
  })

  describe('Form Validation', () => {
    it('should validate required fields', async () => {
      const user = userEvent.setup()
      render(<AuthModal isOpen={true} onAuthSuccess={mockOnAuthSuccess} />)
      
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      const startTime = performance.now()
      await user.click(submitButton)
      const endTime = performance.now()
      
      // Form validation should be instant
      expect(endTime - startTime).toBeLessThan(100)
      
      // HTML5 validation should prevent submission
      expect(loginUser).not.toHaveBeenCalled()
    })

    it('should validate email format', async () => {
      const user = userEvent.setup()
      render(<AuthModal isOpen={true} onAuthSuccess={mockOnAuthSuccess} />)
      
      const emailInput = screen.getByLabelText(/email/i)
      const passwordInput = screen.getByLabelText(/password/i)
      const submitButton = screen.getByRole('button', { name: /sign in/i })
      
      await user.type(emailInput, 'invalid-email')
      await user.type(passwordInput, 'password123')
      
      const startTime = performance.now()
      await user.click(submitButton)
      const endTime = performance.now()
      
      // Email validation should be instant
      expect(endTime - startTime).toBeLessThan(100)
      expect(loginUser).not.toHaveBeenCalled()
    })
  })
})

describe('Logout Function', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset module-level variable by re-importing
    vi.doUnmock('../../components/AuthModal')
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should handle successful logout with timing', async () => {
    vi.mocked(logoutUser).mockResolvedValue({ success: true })
    vi.mocked(Cookies.get).mockReturnValue({ refreshToken: 'test-refresh-token' })
    
    const startTime = performance.now()
    await logout()
    const endTime = performance.now()
    
    const executionTime = endTime - startTime
    
    expect(logoutUser).toHaveBeenCalledWith({ refreshToken: 'test-refresh-token' })
    expect(Cookies.remove).toHaveBeenCalledWith('auth_token')
    expect(Cookies.remove).toHaveBeenCalledWith('refresh_token')
    expect(localStorage.removeItem).toHaveBeenCalledWith('auth_token_expires')
    expect(localStorage.removeItem).toHaveBeenCalledWith('moneymentor_user_id')
    expect(localStorage.removeItem).toHaveBeenCalledWith('moneymentor_session_id')
    expect(window.location.reload).toHaveBeenCalled()
    expect(executionTime).toBeLessThan(3000) // Should complete within 3 seconds
  })

  it('should handle logout without refresh token', async () => {
    vi.mocked(Cookies.get).mockReturnValue(undefined)
    
    const startTime = performance.now()
    await logout()
    const endTime = performance.now()
    
    const executionTime = endTime - startTime
    
    expect(logoutUser).not.toHaveBeenCalled()
    expect(Cookies.remove).toHaveBeenCalledWith('auth_token')
    expect(Cookies.remove).toHaveBeenCalledWith('refresh_token')
    expect(window.location.reload).toHaveBeenCalled()
    expect(executionTime).toBeLessThan(100) // Should be very fast without API call
  })

  it('should handle logout error gracefully', async () => {
    vi.mocked(logoutUser).mockRejectedValue(new Error('Network error'))
    vi.mocked(Cookies.get).mockReturnValue({ refreshToken: 'test-refresh-token' })
    
    const startTime = performance.now()
    await logout()
    const endTime = performance.now()
    
    const executionTime = endTime - startTime
    
    expect(logoutUser).toHaveBeenCalledWith({ refreshToken: 'test-refresh-token' })
    expect(Cookies.remove).toHaveBeenCalledWith('auth_token')
    expect(Cookies.remove).toHaveBeenCalledWith('refresh_token')
    expect(window.location.reload).toHaveBeenCalled()
    expect(executionTime).toBeLessThan(3000) // Should complete even with error
  })

  it('should prevent multiple concurrent logout attempts', async () => {
    vi.mocked(logoutUser).mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 1000))
    )
    vi.mocked(Cookies.get).mockReturnValue({ refreshToken: 'test-refresh-token' })
    
    const startTime = performance.now()
    
    // Start multiple logout attempts
    const logout1 = logout()
    const logout2 = logout()
    const logout3 = logout()
    
    await Promise.all([logout1, logout2, logout3])
    
    const endTime = performance.now()
    const executionTime = endTime - startTime
    
    // Only one logout call should be made
    expect(logoutUser).toHaveBeenCalledTimes(1)
    expect(executionTime).toBeLessThan(2000) // Should not take 3 seconds
  })
}) 