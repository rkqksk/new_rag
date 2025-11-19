/**
 * Unit tests for API types
 */

import { UserRole, TenantStatus, SubscriptionPlan } from './api.types'

describe('UserRole', () => {
  it('should have correct values', () => {
    expect(UserRole.SUPER_ADMIN).toBe('super_admin')
    expect(UserRole.ADMIN).toBe('admin')
    expect(UserRole.STAFF).toBe('staff')
    expect(UserRole.CUSTOMER).toBe('customer')
  })
})

describe('TenantStatus', () => {
  it('should have correct values', () => {
    expect(TenantStatus.ACTIVE).toBe('active')
    expect(TenantStatus.SUSPENDED).toBe('suspended')
    expect(TenantStatus.CANCELLED).toBe('cancelled')
  })
})

describe('SubscriptionPlan', () => {
  it('should have correct values', () => {
    expect(SubscriptionPlan.FREE).toBe('free')
    expect(SubscriptionPlan.STARTER).toBe('starter')
    expect(SubscriptionPlan.PROFESSIONAL).toBe('professional')
    expect(SubscriptionPlan.ENTERPRISE).toBe('enterprise')
  })
})
