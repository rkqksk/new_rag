# Component Architecture Diagrams

Visual representations of the multi-platform component system.

---

## 1. Monorepo Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                         rag-components/                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                        packages/                          │  │
│  │                                                            │  │
│  │  ┌─────────────────┐  ┌─────────────────┐                │  │
│  │  │ design-tokens   │  │    ui-core      │                │  │
│  │  │                 │  │                 │                │  │
│  │  │ • colors.ts     │  │ • Button.types  │                │  │
│  │  │ • spacing.ts    │  │ • Input.types   │                │  │
│  │  │ • typography.ts │  │ • Card.types    │                │  │
│  │  │ • shadows.ts    │  │ • ...           │                │  │
│  │  └────────┬────────┘  └────────┬────────┘                │  │
│  │           │                     │                          │  │
│  │           └──────────┬──────────┘                          │  │
│  │                      │                                     │  │
│  │     ┌────────────────┼────────────────┐                   │  │
│  │     │                │                │                   │  │
│  │  ┌──▼──────────┐  ┌──▼──────────┐  ┌─▼──────────┐        │  │
│  │  │   ui-web    │  │  ui-mobile  │  │  ui-pwa    │        │  │
│  │  │             │  │             │  │            │        │  │
│  │  │ • Button    │  │ • Button    │  │ • Button   │        │  │
│  │  │ • Input     │  │ • Input     │  │ • Input    │        │  │
│  │  │ • Card      │  │ • Card      │  │ • Card     │        │  │
│  │  │ • Sidebar   │  │ • BottomTab │  │ • PWA only │        │  │
│  │  │ • DataTable │  │ • Swipeable │  │ • ...      │        │  │
│  │  └─────────────┘  └─────────────┘  └────────────┘        │  │
│  │                                                            │  │
│  │                    ┌──────────────┐                        │  │
│  │                    │    domain    │                        │  │
│  │                    │              │                        │  │
│  │                    │ • ProductCard│                        │  │
│  │                    │ • OrderItem  │                        │  │
│  │                    │ • UserProfile│                        │  │
│  │                    └──────────────┘                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                          apps/                            │  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │     web      │  │    mobile    │  │  storybook   │   │  │
│  │  │              │  │              │  │              │   │  │
│  │  │ Next.js 14   │  │ React Native │  │ Component    │   │  │
│  │  │ @rag/ui-web  │  │ @rag/ui-mobile│ │ docs         │   │  │
│  │  │ @rag/domain  │  │ @rag/domain  │  │              │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Classification Hierarchy

```
                    ┌──────────────────────────┐
                    │   RAG Component Library   │
                    └────────────┬─────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
      ┌─────▼─────┐       ┌─────▼─────┐       ┌─────▼─────┐
      │   Core    │       │   Domain  │       │  Layout   │
      │ Universal │       │ Business  │       │ Universal │
      └─────┬─────┘       └─────┬─────┘       └─────┬─────┘
            │                   │                    │
   ┌────────┴────────┐         │           ┌────────┴────────┐
   │                 │         │           │                 │
Button    Input    Card    ProductCard   Container      Stack
Badge     Select   Modal   OrderItem     Grid           Center
Avatar    Switch   Alert   UserProfile   Flex           SafeArea
Spinner   Checkbox Toast   NotificationItem

            ┌────────────────────┴────────────────────┐
            │                                         │
      ┌─────▼─────┐                             ┌─────▼─────┐
      │  Web Only │                             │Mobile Only│
      │  Desktop  │                             │   Touch   │
      └─────┬─────┘                             └─────┬─────┘
            │                                         │
   ┌────────┴────────┐                       ┌────────┴────────┐
   │                 │                       │                 │
Sidebar        DataTable               PullToRefresh    BottomSheet
Navbar         AdvancedSearch          SwipeableItem    BottomTabNav
Dropdown       MultiColumn             FAB              HapticFeedback

                    ┌────────────────────┐
                    │  Platform Adaptive │
                    │ Different per OS   │
                    └─────────┬──────────┘
                              │
                   ┌──────────┴──────────┐
                   │                     │
              AuthForm               SearchBar
              DatePicker             FileUpload
              ImageViewer            MapView
```

---

## 3. Component Flow (Button Example)

```
┌─────────────────────────────────────────────────────────────────┐
│                          Developer                               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Import Button        │
                    │  from '@rag/ui'       │
                    └───────────┬───────────┘
                                │
                                │ Platform Detection
                                │
                    ┌───────────▼───────────┐
                    │   Platform.OS?        │
                    └───────────┬───────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
         ┌──────▼──────┐  ┌────▼─────┐  ┌─────▼──────┐
         │   'web'     │  │ 'ios' /  │  │   'pwa'    │
         │             │  │ 'android'│  │            │
         └──────┬──────┘  └────┬─────┘  └─────┬──────┘
                │              │              │
         ┌──────▼──────┐  ┌────▼─────┐  ┌─────▼──────┐
         │ @rag/ui-web │  │@rag/ui-  │  │ @rag/ui-   │
         │ Button.tsx  │  │mobile    │  │ pwa        │
         │             │  │Button.tsx│  │ Button.html│
         └──────┬──────┘  └────┬─────┘  └─────┬──────┘
                │              │              │
         ┌──────▼──────┐  ┌────▼─────┐  ┌─────▼──────┐
         │ HTML button │  │Touchable │  │HTML button │
         │ + Tailwind  │  │Opacity   │  │+ CSS       │
         │ + Radix UI  │  │+ Style   │  │+ Touch opt │
         └──────┬──────┘  └────┬─────┘  └─────┬──────┘
                │              │              │
                └──────────────┼──────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Design Tokens     │
                    │                     │
                    │ • colors.primary    │
                    │ • spacing.md        │
                    │ • typography.base   │
                    │ • shadows.md        │
                    └─────────────────────┘
```

---

## 4. Design Token Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    @rag/design-tokens                           │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐    │
│  │ colors.ts│  │spacing.ts│  │typography  │  │shadows.ts│    │
│  │          │  │          │  │    .ts     │  │          │    │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  └────┬─────┘    │
│       │             │              │              │           │
└───────┼─────────────┼──────────────┼──────────────┼───────────┘
        │             │              │              │
        └─────────────┴──────────────┴──────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
   ┌────▼─────┐               ┌─────▼────┐
   │   Web    │               │  Mobile  │
   │          │               │          │
   │ Tailwind │               │StyleSheet│
   │ Config   │               │  Values  │
   └────┬─────┘               └─────┬────┘
        │                           │
        │                           │
   ┌────▼─────────────┐       ┌─────▼──────────┐
   │ CSS Classes:     │       │ RN Styles:     │
   │ • bg-stone-700   │       │ • backgroundColor│
   │ • px-4           │       │   colors.stone700│
   │ • text-base      │       │ • paddingHorizontal│
   │ • rounded-lg     │       │   spacing[4]    │
   │ • shadow-md      │       │ • borderRadius: 12│
   └──────────────────┘       │ • elevation: 4  │
                              └─────────────────┘
```

---

## 5. Data Flow (Domain Component)

```
┌────────────────────────────────────────────────────────────────┐
│                         Backend API                             │
│                  http://localhost:8001/api/v1                   │
└────────────────────────────┬───────────────────────────────────┘
                             │
                             │ JSON Response
                             │
                 ┌───────────▼───────────┐
                 │   API Client Layer    │
                 │   (React Query)       │
                 └───────────┬───────────┘
                             │
                             │ Typed Data
                             │
                 ┌───────────▼───────────┐
                 │   Domain Component    │
                 │   ProductCard         │
                 │                       │
                 │ interface Product {   │
                 │   id: string          │
                 │   name: string        │
                 │   price: number       │
                 │   imageUrl: string    │
                 │   ...                 │
                 │ }                     │
                 └───────────┬───────────┘
                             │
                 ┌───────────┼───────────┐
                 │           │           │
          ┌──────▼──────┐   │   ┌───────▼──────┐
          │  UI Web     │   │   │  UI Mobile   │
          │  Components │   │   │  Components  │
          │             │   │   │              │
          │ • Button    │   │   │ • Button     │
          │ • Card      │   │   │ • Card       │
          │ • Badge     │   │   │ • Badge      │
          │ • Image     │   │   │ • Image      │
          └─────────────┘   │   └──────────────┘
                            │
                ┌───────────▼───────────┐
                │  User Interactions    │
                │                       │
                │ • onClick/onPress     │
                │ • Add to Cart         │
                │ • View Details        │
                └───────────┬───────────┘
                            │
                            │ Events
                            │
                ┌───────────▼───────────┐
                │   Event Handlers      │
                │   (Parent Component)  │
                └───────────────────────┘
```

---

## 6. Testing Pyramid

```
                         ┌──────────────┐
                         │     E2E      │
                         │  (Detox /    │
                         │  Playwright) │
                         │              │
                         │  10 tests    │
                         └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    │   Integration Tests   │
                    │   (React Testing Lib) │
                    │                       │
                    │      50 tests         │
                    └───────────┬───────────┘
                                │
                ┌───────────────┴───────────────┐
                │         Unit Tests             │
                │         (Jest)                 │
                │                                │
                │         200+ tests             │
                │                                │
                │ • Component props              │
                │ • Event handlers               │
                │ • Utility functions            │
                │ • Design token values          │
                └────────────────────────────────┘

Target Coverage:
┌─────────────────┬──────────┐
│ Package         │ Coverage │
├─────────────────┼──────────┤
│ design-tokens   │   100%   │
│ ui-core         │   100%   │
│ ui-web          │   85%    │
│ ui-mobile       │   85%    │
│ domain          │   80%    │
└─────────────────┴──────────┘
```

---

## 7. Build Pipeline (Turborepo)

```
┌────────────────────────────────────────────────────────────────┐
│                        turbo.json                               │
│                                                                  │
│  "pipeline": {                                                  │
│    "build": { "dependsOn": ["^build"] }                        │
│  }                                                              │
└────────────────────────────┬───────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Dependency     │
                    │  Graph Analysis │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐         ┌────▼─────┐        ┌────▼─────┐
   │  design- │         │ ui-core  │        │   ...    │
   │  tokens  │         │          │        │          │
   │          │         │          │        │          │
   │ Build ✓  │         │ Build ✓  │        │ Build ✓  │
   └────┬─────┘         └────┬─────┘        └────┬─────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐         ┌────▼─────┐        ┌────▼─────┐
   │ ui-web   │         │ui-mobile │        │  domain  │
   │          │         │          │        │          │
   │ Build ✓  │         │ Build ✓  │        │ Build ✓  │
   └────┬─────┘         └────┬─────┘        └────┬─────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐         ┌────▼─────┐        ┌────▼─────┐
   │   web    │         │  mobile  │        │storybook │
   │   app    │         │   app    │        │          │
   │          │         │          │        │          │
   │ Build ✓  │         │ Build ✓  │        │ Build ✓  │
   └──────────┘         └──────────┘        └──────────┘

✨ Cached builds are reused (10x faster!)
```

---

## 8. Deployment Flow

```
┌────────────────────────────────────────────────────────────────┐
│                     Developer Commits                           │
└────────────────────────────┬───────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   GitHub PR     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ GitHub Actions  │
                    │                 │
                    │ • Lint          │
                    │ • Type Check    │
                    │ • Test          │
                    │ • Build         │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Chromatic      │
                    │  (Visual Tests) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  PR Approved    │
                    │  Merge to main  │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐         ┌────▼─────┐        ┌────▼─────┐
   │   Web    │         │  Mobile  │        │   NPM    │
   │          │         │          │        │          │
   │ Deploy   │         │ Build    │        │ Publish  │
   │ Vercel   │         │ iOS/Andr │        │ Registry │
   └──────────┘         └──────────┘        └──────────┘
        │                    │                    │
        │                    │                    │
   Production           App Store           @rag/ui-web@1.0.0
   https://app          + Play Store        @rag/ui-mobile@1.0.0
   .rag.com             Distribution        @rag/domain@1.0.0
```

---

## 9. Component Reusability Matrix

```
                    Web    PWA    React Native
                    ───    ───    ────────────
Core Components
  Button            ●●●    ●●●        ●●●      95% shared
  Input             ●●●    ●●●        ●●●      90% shared
  Card              ●●●    ●●●        ●●●      95% shared
  Badge             ●●●    ●●●        ●●●      95% shared

Form Components
  Select            ●●●    ◐◐◐        ○○○      40% shared
  Checkbox          ●●●    ●●●        ●●◐      80% shared
  DatePicker        ●●●    ◐◐◐        ○○○      30% shared

Layout Components
  Container         ●●●    ●●●        ●●●      95% shared
  Grid              ●●●    ●●●        ◐◐◐      70% shared
  SafeAreaView      ○○○    ●●●        ●●●      100% (mobile)

Navigation
  Sidebar           ●●●    ○○○        ○○○      100% (web)
  BottomTabNav      ○○○    ●●●        ●●●      100% (mobile)
  Navbar            ●●●    ●●◐        ●●◐      50% shared

Domain Components
  ProductCard       ●●●    ●●●        ●●●      85% shared
  OrderItem         ●●●    ●●●        ●●●      85% shared
  UserProfile       ●●●    ●●●        ●●●      80% shared

Legend:
  ●●● = Fully supported
  ●●◐ = Mostly supported (minor adaptations)
  ◐◐◐ = Partially supported (major adaptations)
  ○○○ = Not supported
```

---

## 10. Performance Budget

```
┌────────────────────────────────────────────────────────────────┐
│                         Web (Next.js)                           │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Initial Bundle        ████████░░░░░░  150 KB / 200 KB          │
│  First Contentful Paint████████████░░  1.5s / 2.0s             │
│  Time to Interactive   ████████████░░  3.5s / 4.0s             │
│  Lighthouse Score      ██████████████  92 / 100                │
│                                                                  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                            PWA                                  │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Initial Bundle        ████████████░░  50 KB / 75 KB            │
│  First Contentful Paint██████████████  1.0s / 1.5s             │
│  Time to Interactive   ██████████████  2.0s / 2.5s             │
│  Offline Load          ██████████████  0.5s / 1.0s             │
│                                                                  │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                       React Native                              │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  JS Bundle Size        ████████████░░  2 MB / 3 MB              │
│  App Launch (iOS)      ██████████████  2.0s / 2.5s             │
│  App Launch (Android)  ████████████░░  3.0s / 3.5s             │
│  Frame Rate            ██████████████  60 fps / 60 fps          │
│  Memory Usage          ████████████░░  100 MB / 150 MB          │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

**Last Updated**: 2025-11-12
**Format**: ASCII Diagrams
**Purpose**: Visual documentation for component architecture
