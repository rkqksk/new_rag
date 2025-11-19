module.exports = {
  projects: [
    {
      displayName: 'packages/core',
      testMatch: ['<rootDir>/packages/core/**/*.test.ts'],
      preset: 'ts-jest',
      testEnvironment: 'jsdom',
    },
    {
      displayName: 'packages/ui',
      testMatch: ['<rootDir>/packages/ui/**/*.test.tsx'],
      preset: 'ts-jest',
      testEnvironment: 'jsdom',
    },
  ],
  collectCoverageFrom: [
    'packages/*/src/**/*.{ts,tsx}',
    '!packages/*/src/**/*.d.ts',
    '!packages/*/src/**/*.test.{ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 80,
      statements: 80,
    },
  },
}
