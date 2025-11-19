#!/usr/bin/env node
// Generate React component with tests

const fs = require('fs')
const path = require('path')

const componentName = process.argv[2]

if (!componentName) {
  console.error('Usage: node tools/generators/component.js ComponentName')
  process.exit(1)
}

const componentDir = path.join('packages/ui/src/components', componentName)

// Create directory
fs.mkdirSync(componentDir, { recursive: true })

// Component file
const componentContent = `import React from 'react'

interface ${componentName}Props {
  children?: React.ReactNode
}

export const ${componentName}: React.FC<${componentName}Props> = ({ children }) => {
  return (
    <div className="${componentName.toLowerCase()}">
      {children}
    </div>
  )
}
`

// Test file
const testContent = `import { render, screen } from '@testing-library/react'
import { ${componentName} } from './${componentName}'

describe('${componentName}', () => {
  it('should render children', () => {
    render(<${componentName}>Test</${componentName}>)
    expect(screen.getByText('Test')).toBeInTheDocument()
  })
})
`

// Index file
const indexContent = `export { ${componentName} } from './${componentName}'
`

fs.writeFileSync(path.join(componentDir, `${componentName}.tsx`), componentContent)
fs.writeFileSync(path.join(componentDir, `${componentName}.test.tsx`), testContent)
fs.writeFileSync(path.join(componentDir, 'index.ts'), indexContent)

console.log(`✅ Generated component: ${componentName}`)
console.log(`   Location: ${componentDir}`)
