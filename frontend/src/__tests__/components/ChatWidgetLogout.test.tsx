import React from 'react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { logout } from '../../components/AuthModal'
import * as api from '../../utils/chatWidget/api'
import Cookies from 'js-cookie'

// Mock js-cookie
vi.mock('js-cookie', () => ({
  default: {
    get: vi.fn(),
    set: vi.fn(),
    remove: vi.fn(),
  },
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

// Mock window.location.reload
Object.defineProperty(window, 'location', {
  value: { reload: vi.fn() },
  writable: true,
})

describe('ChatWidget Logout Functionality', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock authenticated state
    vi.mocked(Cookies.get).mockImplementation((key) => {
      if (key === 'auth_token') return 'test-auth-token'
      if (key === 'refresh_token') return 'test-refresh-token'
      return undefined
    })
    vi.mocked(localStorage.getItem).mockImplementation((key) => {
      if (key === 'moneymentor_user_id') return 'test-user-id'
      return null
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Concurrent Logout Prevention', () => {
    it('should prevent multiple concurrent logout calls', async () => {
      // Use the real logout function, but mock the API call
      let resolveLogoutUser: () => void
      const logoutUserPromise = new Promise<void>((resolve) => {
        resolveLogoutUser = resolve
      })
      const logoutUserMock = vi.spyOn(api, 'logoutUser').mockReturnValue(logoutUserPromise as any)

      // Start multiple logout attempts
      const logout1 = logout()
      const logout2 = logout()
      const logout3 = logout()

      // Only one API call should be made
      expect(logoutUserMock).toHaveBeenCalledTimes(1)

      // Resolve the API call
      resolveLogoutUser!()
      await Promise.all([logout1, logout2, logout3])
    })
  })
}) 