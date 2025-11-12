# Component Library Skill

## Overview
Expert in building and maintaining reusable component libraries for multi-platform applications.

## Trigger Words
- component library
- shared components
- ui library
- design system
- component architecture
- atomic design

## Capabilities

### Component Architecture
- Atomic design principles (atoms, molecules, organisms)
- Component composition patterns
- Platform-specific variants
- Prop drilling prevention
- Context providers

### Multi-Platform Support
```typescript
// Platform-aware components
interface ComponentProps {
  platform?: 'web' | 'mobile' | 'pwa'
  variant?: 'default' | 'compact' | 'expanded'
}
```

### Component Organization
```
packages/ui/
├── components/
│   ├── atoms/
│   │   ├── Button/
│   │   ├── Input/
│   │   └── Icon/
│   ├── molecules/
│   │   ├── SearchBar/
│   │   ├── Card/
│   │   └── FormField/
│   └── organisms/
│       ├── Navigation/
│       ├── DataTable/
│       └── Dashboard/
```

### Documentation
- Storybook integration
- Props documentation
- Usage examples
- Visual testing
- Accessibility guidelines

### Testing Strategy
- Unit tests for logic
- Visual regression tests
- Interaction testing
- Cross-platform testing
- Accessibility testing

## Best Practices

### Component Design
1. **Single Responsibility**: Each component does one thing well
2. **Composition over Inheritance**: Use composition patterns
3. **Platform Variants**: Support platform-specific styling
4. **Accessibility First**: WCAG 2.1 AA compliance
5. **Performance**: Lazy loading, code splitting

### Code Quality
```typescript
// Example: Platform-aware Button
export const Button = forwardRef<
  HTMLButtonElement,
  ButtonProps
>(({ platform = 'web', variant, size, ...props }, ref) => {
  const styles = usePlatformStyles(platform, variant, size)

  return (
    <button
      ref={ref}
      className={styles}
      {...props}
    />
  )
})
```

### Export Strategy
```typescript
// Barrel exports with tree-shaking support
export { Button } from './components/atoms/Button'
export type { ButtonProps } from './components/atoms/Button'

// Lazy loading for large components
export const DataTable = lazy(() =>
  import('./components/organisms/DataTable')
)
```

## Integration Points

### With Design Tokens
- Use design-tokens skill for theming
- Platform-specific token overrides
- Dynamic theme switching

### With Storybook
- Component documentation
- Interactive playground
- Visual testing
- Design review

### With Testing
- Jest for unit tests
- React Testing Library
- Chromatic for visual regression
- Playwright for E2E

## Common Commands

```bash
# Build component library
pnpm build:ui

# Run Storybook
pnpm storybook

# Test components
pnpm test:ui

# Generate component
pnpm generate:component

# Publish to registry
pnpm publish:ui
```

## Progressive Disclosure

When building components:
1. Start with core functionality
2. Add platform variants
3. Implement accessibility
4. Add animations/transitions
5. Optimize performance
6. Document thoroughly

## Performance Optimization

### Bundle Size
- Tree-shaking support
- Dynamic imports
- CSS-in-JS optimization
- Icon sprite sheets

### Runtime Performance
- React.memo for expensive components
- useMemo/useCallback hooks
- Virtual scrolling for lists
- Intersection Observer for lazy loading

## Version Management

```json
{
  "version": "1.0.0",
  "exports": {
    ".": "./src/index.ts",
    "./styles": "./src/styles/index.css"
  },
  "sideEffects": ["*.css"]
}
```

## Related Skills
- design-tokens
- visual-testing
- frontend-platform
- mobile-ui
- pwa-optimization