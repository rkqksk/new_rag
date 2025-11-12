# Component Compatibility Matrix

**Version**: 1.0.0
**Date**: 2025-11-12

Quick reference for component availability across platforms.

## Legend
- ✅ Fully Supported
- 🔶 Partial Support / Adapted
- ⚠️ Platform-Specific Implementation Required
- ❌ Not Supported
- 🚧 Planned

---

## Core UI Components

| Component | Web | PWA | React Native | Notes |
|-----------|-----|-----|--------------|-------|
| **Button** | ✅ | ✅ | ✅ | Universal component |
| **Input** | ✅ | ✅ | ✅ | Platform-specific keyboards |
| **Textarea** | ✅ | ✅ | ✅ | Auto-resize on mobile |
| **Checkbox** | ✅ | ✅ | ✅ | Custom styling on mobile |
| **Radio** | ✅ | ✅ | ✅ | Custom styling on mobile |
| **Switch** | ✅ | ✅ | ✅ | Native toggle on mobile |
| **Label** | ✅ | ✅ | ✅ | Universal |
| **Badge** | ✅ | ✅ | ✅ | Universal |
| **Avatar** | ✅ | ✅ | ✅ | Universal |
| **Separator** | ✅ | ✅ | ✅ | Universal |
| **Skeleton** | ✅ | ✅ | ✅ | Universal |
| **Spinner** | ✅ | ✅ | ✅ | Universal |
| **Progress** | ✅ | ✅ | ✅ | Universal |

---

## Form Components

| Component | Web | PWA | React Native | Notes |
|-----------|-----|-----|--------------|-------|
| **Select** | ✅ | 🔶 | ⚠️ | Radix UI / Native select / Picker |
| **Combobox** | ✅ | 🔶 | ⚠️ | Searchable dropdown |
| **DatePicker** | ✅ | 🔶 | ⚠️ | input[date] / Native modal |
| **TimePicker** | ✅ | 🔶 | ⚠️ | input[time] / Native modal |
| **FileUpload** | ✅ | 🔶 | ⚠️ | Drag-drop / Camera / DocumentPicker |
| **Slider** | ✅ | ✅ | ✅ | Touch-optimized on mobile |
| **ColorPicker** | ✅ | 🔶 | ❌ | Web only |

---

## Layout Components

| Component | Web | PWA | React Native | Notes |
|-----------|-----|-----|--------------|-------|
| **Container** | ✅ | ✅ | ✅ | Max-width wrapper |
| **Grid** | ✅ | ✅ | 🔶 | CSS Grid / Flexbox fallback |
| **Stack** | ✅ | ✅ | ✅ | Vertical/Horizontal spacing |
| **Center** | ✅ | ✅ | ✅ | Universal |
| **Flex** | ✅ | ✅ | ✅ | Universal |
| **SafeAreaView** | ❌ | ✅ | ✅ | Mobile only |
| **KeyboardAvoidingView** | ❌ | 🔶 | ✅ | Mobile only |

---

## Navigation Components

| Component | Web | PWA | React Native | Notes |
|-----------|-----|-----|--------------|-------|
| **Sidebar** | ✅ | ❌ | ❌ | Desktop only |
| **Navbar** | ✅ | 🔶 | 🔶 | Responsive variants |
| **BottomTabNav** | ❌ | ✅ | ✅ | Mobile only |
| **Hamburger Menu** | 🔶 | ✅ | ✅ | Mobile pattern |
| **Breadcrumb** | ✅ | 🔶 | ❌ | Desktop primarily |
| **Tabs** | ✅ | ✅ | ✅ | Universal |
| **Link** | ✅ | ✅ | 🔶 | Next.js Link / Linking API |

---

## Overlay Components

| Component | Web | PWA | React Native | Notes |
|-----------|-----|-----|--------------|-------|
| **Modal** | ✅ | ✅ | ✅ | Universal |
| **Dialog** | ✅ | ✅ | ✅ | Universal |
| **AlertDialog** | ✅ | ✅ | ✅ | Universal |
| **Drawer** | ✅ | 🔶 | 🔶 | Side panel |
| **BottomSheet** | ❌ | ✅ | ✅ | Mobile only |
| **Popover** | ✅ | 🔶 | ❌ | Desktop primarily |
| **Tooltip** | ✅ | 🔶 | ❌ | Desktop hover pattern |
| **DropdownMenu** | ✅ | 🔶 | ⚠️ | Context menu |

---

## Feedback Components

| Component | Web | PWA | React Native | Notes |
|-----------|-----|-----|--------------|-------|
| **Toast** | ✅ | ✅ | ✅ | Universal notification |
| **Alert** | ✅ | ✅ | ✅ | Universal |
| **Snackbar** | ✅ | ✅ | ✅ | Bottom notification |
| **LoadingOverlay** | ✅ | ✅ | ✅ | Universal |
| **EmptyState** | ✅ | ✅ | ✅ | Universal |
| **ErrorBoundary** | ✅ | ✅ | ✅ | Universal |

---

## Data Display Components

| Component | Web | PWA | React Native | Notes |
|-----------|-----|-----|--------------|-------|
| **Table** | ✅ | 🔶 | 🔶 | Card list on mobile |
| **DataTable** | ✅ | ❌ | ❌ | Desktop only |
| **Card** | ✅ | ✅ | ✅ | Universal |
| **List** | ✅ | ✅ | ✅ | Universal |
| **VirtualList** | ✅ | ✅ | ✅ | Performance critical |
| **Accordion** | ✅ | ✅ | ✅ | Universal |
| **StatCard** | ✅ | ✅ | ✅ | Dashboard widget |
| **Chart** | ✅ | ✅ | 🔶 | Victory Native on mobile |
| **JsonViewer** | ✅ | 🔶 | 🔶 | Limited on mobile |

---

## Advanced Components

| Component | Web | PWA | React Native | Notes |
|-----------|-----|-----|--------------|-------|
| **AdvancedSearch** | ✅ | 🔶 | 🔶 | Simplified on mobile |
| **SearchBar** | ✅ | ✅ | ✅ | Platform-adapted |
| **NotificationCenter** | ✅ | ✅ | ✅ | Universal |
| **UserProfile** | ✅ | ✅ | ✅ | Universal |
| **ImageViewer** | ✅ | ✅ | ✅ | Pinch-zoom on mobile |
| **VideoPlayer** | ✅ | ✅ | ✅ | Platform video controls |
| **MapView** | ✅ | ✅ | ⚠️ | Google Maps / React Native Maps |
| **QRScanner** | 🔶 | ✅ | ✅ | Camera required |

---

## Mobile-Specific Components

| Component | Web | PWA | React Native | Notes |
|-----------|-----|-----|--------------|-------|
| **PullToRefresh** | ❌ | ✅ | ✅ | Mobile gesture |
| **SwipeableItem** | ❌ | ✅ | ✅ | Touch gesture |
| **FAB** | 🔶 | ✅ | ✅ | Mobile pattern |
| **ActionSheet** | ❌ | ✅ | ✅ | iOS pattern |
| **StatusBar** | ❌ | ✅ | ✅ | Native mobile |
| **HapticFeedback** | ❌ | ❌ | ✅ | Native only |
| **Biometric** | ❌ | 🔶 | ✅ | Face ID / Touch ID |

---

## Domain Components

| Component | Web | PWA | React Native | Notes |
|-----------|-----|-----|--------------|-------|
| **ProductCard** | ✅ | ✅ | ✅ | Universal |
| **OrderItem** | ✅ | ✅ | ✅ | Universal |
| **UserAvatar** | ✅ | ✅ | ✅ | Universal |
| **NotificationItem** | ✅ | ✅ | ✅ | Universal |
| **ChatMessage** | ✅ | ✅ | ✅ | Universal |
| **DocumentViewer** | ✅ | 🔶 | 🔶 | PDF support varies |

---

## Implementation Priority Matrix

### Phase 1: Core (Week 1-2)
| Component | Priority | Complexity | Shared Code |
|-----------|----------|------------|-------------|
| Button | P0 | Low | 90% |
| Input | P0 | Low | 85% |
| Card | P0 | Low | 95% |
| Badge | P0 | Low | 95% |
| Spinner | P0 | Low | 90% |

### Phase 2: Forms (Week 3-4)
| Component | Priority | Complexity | Shared Code |
|-----------|----------|------------|-------------|
| Select | P1 | High | 40% |
| Checkbox | P1 | Low | 80% |
| Switch | P1 | Medium | 70% |
| DatePicker | P1 | High | 30% |
| FileUpload | P2 | High | 20% |

### Phase 3: Layout (Week 5)
| Component | Priority | Complexity | Shared Code |
|-----------|----------|------------|-------------|
| Container | P1 | Low | 95% |
| Stack | P1 | Low | 95% |
| Grid | P1 | Medium | 70% |
| SafeAreaView | P1 | Low | 100% (mobile) |

### Phase 4: Navigation (Week 6)
| Component | Priority | Complexity | Shared Code |
|-----------|----------|------------|-------------|
| Tabs | P1 | Medium | 80% |
| Navbar | P1 | High | 40% |
| Sidebar | P2 | Medium | 100% (web) |
| BottomTabNav | P1 | Medium | 100% (mobile) |

### Phase 5: Advanced (Week 7-8)
| Component | Priority | Complexity | Shared Code |
|-----------|----------|------------|-------------|
| Modal | P1 | Medium | 70% |
| SearchBar | P1 | High | 50% |
| Table | P2 | High | 30% |
| ImageViewer | P2 | High | 40% |

---

## Code Sharing Analysis

### High Reusability (80-100%)
- Button, Input, Card, Badge, Avatar
- Skeleton, Spinner, Progress
- Container, Stack, Center
- Alert, Toast, EmptyState

### Medium Reusability (40-79%)
- Select, Checkbox, Switch
- Tabs, Modal, Dialog
- SearchBar, List, Accordion
- ProductCard, OrderItem

### Low Reusability (0-39%)
- DataTable (web only)
- PullToRefresh (mobile only)
- DatePicker (platform native)
- FileUpload (different APIs)
- MapView (different libraries)

---

## Platform-Specific Challenges

### Web
- Hover states not applicable to touch
- Right-click context menus
- Keyboard navigation focus management
- Browser compatibility (Safari, Firefox)

### PWA
- Limited offline functionality
- Service worker cache strategy
- Add to home screen prompt
- iOS standalone mode quirks
- Touch target size (min 44px)

### React Native
- Platform differences (iOS vs Android)
- Navigation library choice
- Native module dependencies
- App size and performance
- Store approval process

---

## Testing Coverage Requirements

### Unit Tests (Jest)
- ✅ All core components
- ✅ All form components
- ✅ All domain components
- Target: > 80% coverage

### Visual Regression (Chromatic)
- ✅ All UI components in Storybook
- ✅ All variants and states
- ✅ Responsive breakpoints

### E2E Tests (Playwright/Detox)
- ✅ Critical user flows (login, search, checkout)
- ✅ Platform-specific features
- Target: > 60% coverage

### Accessibility Tests
- ✅ Screen reader compatibility
- ✅ Keyboard navigation
- ✅ Color contrast (WCAG AA)
- ✅ Touch target size (44x44px)

---

## Component Size Targets

### Web (Gzipped)
- Button: 2KB
- Input: 1.5KB
- Card: 1KB
- Select: 8KB (Radix UI)
- DataTable: 25KB
- **Total Core**: < 50KB
- **Total App**: < 150KB

### React Native (Bundle Size)
- Core Components: < 100KB
- Domain Components: < 200KB
- Navigation: < 150KB
- **Total App**: < 2MB

---

## Performance Benchmarks

### Web
- Time to Interactive: < 3.5s
- Lighthouse Score: > 90
- FCP: < 1.5s

### PWA
- Time to Interactive: < 2s
- Offline Load: < 500ms
- FCP: < 1s

### React Native
- App Launch: < 2s (iOS), < 3s (Android)
- Frame Rate: 60fps
- Memory: < 100MB

---

## Accessibility Compliance

| Feature | Web | PWA | React Native |
|---------|-----|-----|--------------|
| Screen Reader | ✅ ARIA | ✅ ARIA | ✅ accessibilityLabel |
| Keyboard Nav | ✅ tabIndex | ✅ tabIndex | 🔶 Limited |
| Focus Management | ✅ | ✅ | ✅ |
| Color Contrast | ✅ WCAG AA | ✅ WCAG AA | ✅ WCAG AA |
| Touch Targets | ✅ 44px min | ✅ 44px min | ✅ 44px min |
| Reduced Motion | ✅ | ✅ | ✅ |

---

## Decision Tree

```
Need a component?
│
├─ Is it for data entry?
│  └─ Use Form Components (Input, Select, Checkbox)
│
├─ Is it for navigation?
│  ├─ Desktop? → Sidebar, Navbar
│  └─ Mobile? → BottomTabNav, Hamburger
│
├─ Is it for feedback?
│  └─ Use Feedback Components (Toast, Alert, Spinner)
│
├─ Is it for data display?
│  ├─ Desktop? → Table, DataTable
│  └─ Mobile? → Card, List
│
└─ Is it platform-specific?
   ├─ Web only? → Check Web-Only Components
   ├─ Mobile only? → Check Mobile-Only Components
   └─ Universal? → Check Core Components
```

---

**Last Updated**: 2025-11-12
**Maintainer**: Frontend Team
**Review Cycle**: Monthly
