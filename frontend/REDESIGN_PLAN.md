# Frontend Redesign Implementation Plan

## Priority Order

1. **login.html** ✅ DONE
2. **register.html** - Auth flow (next)
3. **chat.html** - Main product search (most complex, most important)
4. **dashboard.html** - Collection management
5. **profile.html** - User profile
6. **rag_dashboard.html** - RAG operations
7. **analytics-dashboard.html** - Metrics
8. **realtime-demo.html** - Real-time features
9. **streaming-demo.html** - Streaming demo

## Key Changes Per File

### register.html
- Remove emoji (🚀)
- Remove gradient backgrounds
- Use design-system.css
- Password strength indicator styling
- Form validation with clean errors

### chat.html (CRITICAL - Main UI)
- Remove emoji from collection indicator
- Gray-tone only design
- Product cards with neutral styling
- Loading states with spinner
- Natural shadows and borders
- Preserve all functionality (gallery, progressive loading, etc.)

### dashboard.html
- Remove emoji from headers
- Collection cards with badges
- Stats in neutral colors
- Clean action buttons

### profile.html
- Remove avatar background gradient
- Clean info display
- Password change form with design system
- Profile badges in neutral style

### rag_dashboard.html
- Remove emoji from titles
- Upload area with neutral styling
- Progress bars in neutral colors
- Log display with monospace

### analytics-dashboard.html
- Remove emoji from title (📊)
- Charts in neutral colors (grays, subtle blues)
- Table styling with design system
- Clean badges for performance levels

### realtime-demo.html
- Remove emoji from title (⚡)
- Dark theme to neutral light theme
- Connection status in badges
- Clean logs and output areas

### streaming-demo.html
- Remove emoji from title (🔄)
- Neutral mode selector
- Event display with type-based borders
- Clean status indicators

## Design System Application

Each file will:
1. Link to `/css/design-system.css`
2. Use HSL color variables
3. Apply consistent component classes
4. Remove all inline emojis
5. Use text-based indicators where needed

## Testing Strategy

After each file:
1. Visual check (no emojis, consistent colors)
2. Functional check (all JS works)
3. Responsive check (mobile layout)
4. Accessibility check (focus states, contrast)

