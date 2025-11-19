# Frontend Performance Baseline - v10.0.0

**Date**: 2025-11-19
**System**: v10 Unified Maximum - Pure Black Design
**Framework**: Next.js 15 (App Router)
**Target**: Lighthouse Score 90+ (all categories)

---

## Executive Summary

### Performance Targets
| Metric | Target | Industry Standard | Status |
|--------|--------|-------------------|--------|
| First Contentful Paint | <1.8s | <2.5s | ✅ Excellent |
| Time to Interactive | <3.8s | <5.0s | ✅ Good |
| Largest Contentful Paint | <2.5s | <4.0s | ✅ Excellent |
| Cumulative Layout Shift | <0.1 | <0.25 | ✅ Excellent |
| Total Blocking Time | <200ms | <600ms | ✅ Excellent |
| Build Time (cold) | <3min | <5min | ✅ Good |
| Build Time (hot) | <30s | <60s | ✅ Excellent |

### Quick Stats
- **Framework**: Next.js 15 + React 19
- **Bundle Size**: ~150-300 KB (gzipped)
- **Pages**: 10+ routes
- **Components**: 60+ UI components
- **Design System**: Pure Black (#000000), NO icons

---

## 1. Build Performance

### Cold Build (No Cache)

**What it measures**: First-time build or after `rm -rf .next`

#### Test Commands
```bash
cd /home/rkqksk/projects/new_rag/apps/web

# Clean build
rm -rf .next
time pnpm build

# Or with npm
rm -rf .next
time npm run build
```

#### Expected Output
```
Route (app)                                Size     First Load JS
┌ ○ /                                      5.2 kB         150 kB
├ ○ /search                                8.1 kB         153 kB
├ ○ /products                              12.3 kB        157 kB
├ ○ /qa                                    6.4 kB         151 kB
└ ○ /api/health                            1.2 kB         146 kB

○  (Static)  prerendered as static content
●  (SSG)     automatically generated as static HTML + JSON
ƒ  (Dynamic) server-rendered on demand

✓ Compiled successfully
✓ Linting and checking validity of types
✓ Collecting page data
✓ Generating static pages (10/10)
✓ Finalizing page optimization

Build Time: 2m 34s
```

**Performance Metrics**:
- **TypeScript Compilation**: 30-60s
- **Code Generation**: 20-40s
- **Bundle Creation**: 40-80s
- **Static Generation**: 20-40s
- **Optimization**: 20-40s
- **Total**: 130-260s (2-4 minutes)

**Factors Affecting Build Time**:
- Number of pages: 10 pages = ~2min, 100 pages = ~5min
- Dependencies: ~100 packages in package.json
- TypeScript strictness: Strict mode adds 10-20%
- Static generation: 5-10s per page
- Image optimization: 2-5s per image

---

### Hot Build (With Cache)

**What it measures**: Incremental build after code changes

#### Test Commands
```bash
cd /home/rkqksk/projects/new_rag/apps/web

# Make a small change
echo "// Updated" >> src/app/page.tsx

# Rebuild
time pnpm build
```

#### Expected Output
```
✓ Compiled successfully
Build Time: 18s
```

**Performance Metrics**:
- **Changed files**: 5-15s
- **Dependency changes**: 20-40s
- **Config changes**: 30-60s (cache invalidation)
- **Total**: 5-60s

**Cache Effectiveness**:
- First build: 100% compilation
- Hot build: 5-20% compilation
- **Speed improvement**: 10-30x faster

---

## 2. Bundle Size Analysis

### Total Bundle Size

**Target**: <200 KB initial load (gzipped)

#### Analysis Commands
```bash
cd /home/rkqksk/projects/new_rag/apps/web

# Build and analyze
pnpm build

# Analyze bundle (if webpack-bundle-analyzer installed)
ANALYZE=true pnpm build

# Or use Next.js built-in analysis
npx @next/bundle-analyzer
```

#### Expected Bundle Breakdown

**By Route**:
```
Route                    Raw Size    Gzipped    First Load
/                        45 KB       12 KB      150 KB
/search                  82 KB       22 KB      153 KB
/products                125 KB      34 KB      157 KB
/qa                      67 KB       18 KB      151 KB
```

**By Category**:
```
JavaScript (total)       450 KB      150 KB
  - Framework (Next.js)  180 KB      60 KB
  - React                120 KB      40 KB
  - UI Components        80 KB       25 KB
  - Business Logic       50 KB       18 KB
  - Utilities            20 KB       7 KB

CSS (total)              25 KB       8 KB
  - Tailwind Base        15 KB       5 KB
  - Components           8 KB        2.5 KB
  - Custom Styles        2 KB        0.5 KB

Fonts                    40 KB       40 KB
  - Inter Variable       40 KB       40 KB

Images (lazy loaded)     500 KB      -
  - Product Images       400 KB      -
  - Icons (if any)       100 KB      -
```

**Total First Load**: 150-160 KB (gzipped)

---

### Dependency Size Analysis

**Largest Dependencies**:
```
next                     ~100 KB (gzipped)
react + react-dom        ~50 KB (gzipped)
@rag/ui components       ~25 KB (gzipped)
@rag/core                ~15 KB (gzipped)
socket.io-client         ~30 KB (gzipped)
```

**Optimization Opportunities**:
- Use dynamic imports for heavy components
- Remove unused dependencies
- Use lighter alternatives (e.g., date-fns instead of moment)
- Tree-shake unused code

---

## 3. Runtime Performance (Lighthouse)

### Lighthouse Metrics

**What it measures**: Real user experience in Chrome browser

#### Test Commands
```bash
# Install Lighthouse
npm install -g lighthouse

# Run test (requires frontend running)
cd /home/rkqksk/projects/new_rag/apps/web
pnpm dev &

# Wait for server to start
sleep 10

# Run Lighthouse
lighthouse http://localhost:3000 \
  --output html \
  --output-path /home/rkqksk/projects/new_rag/reports/lighthouse-report.html \
  --chrome-flags="--headless"

# Kill dev server
pkill -f "next dev"
```

#### Expected Lighthouse Scores

**Performance**: 90-100 (Target: >90)
- First Contentful Paint: 1.2s
- Speed Index: 2.1s
- Largest Contentful Paint: 1.8s
- Time to Interactive: 2.4s
- Total Blocking Time: 150ms
- Cumulative Layout Shift: 0.05

**Accessibility**: 95-100 (Target: >95)
- Proper ARIA labels
- Sufficient color contrast (Pure Black on white = 21:1 ratio)
- Keyboard navigation
- Screen reader support

**Best Practices**: 95-100 (Target: >90)
- HTTPS enabled
- No console errors
- Proper image aspect ratios
- No deprecated APIs

**SEO**: 90-100 (Target: >90)
- Meta tags present
- Proper heading hierarchy
- Mobile-friendly
- Valid robots.txt

---

### Core Web Vitals

**Largest Contentful Paint (LCP)**:
- Target: <2.5s
- Good: <2.5s | Needs Improvement: 2.5-4s | Poor: >4s
- Our Target: <2.0s
- Measures: When main content is visible

**First Input Delay (FID)**:
- Target: <100ms
- Good: <100ms | Needs Improvement: 100-300ms | Poor: >300ms
- Our Target: <50ms
- Measures: Responsiveness to user interaction

**Cumulative Layout Shift (CLS)**:
- Target: <0.1
- Good: <0.1 | Needs Improvement: 0.1-0.25 | Poor: >0.25
- Our Target: <0.05
- Measures: Visual stability

**Additional Metrics**:

**First Contentful Paint (FCP)**:
- Target: <1.8s
- Our Target: <1.5s
- Measures: When first content appears

**Time to Interactive (TTI)**:
- Target: <3.8s
- Our Target: <3.0s
- Measures: When page is fully interactive

**Total Blocking Time (TBT)**:
- Target: <200ms
- Our Target: <150ms
- Measures: Main thread blocking time

---

## 4. Page-specific Performance

### Home Page (`/`)

**Purpose**: Landing page, search entry point

**Expected Performance**:
- LCP: <1.5s (hero text)
- FCP: <1.0s
- TTI: <2.0s
- Bundle: 150 KB

**Critical Resources**:
- HTML: 5 KB
- CSS: 8 KB
- JS: 150 KB
- Total: 163 KB

**Optimization**:
- Inline critical CSS
- Defer non-critical JS
- Preload fonts

---

### Search Page (`/search`)

**Purpose**: Product search interface

**Expected Performance**:
- LCP: <2.0s (search results)
- FCP: <1.2s
- TTI: <2.5s
- Bundle: 153 KB

**Critical Resources**:
- HTML: 6 KB
- CSS: 9 KB
- JS: 153 KB
- API: 5-10 KB (search results)
- Total: 173-178 KB

**Optimization**:
- Debounce search input (300ms)
- Cache search results
- Lazy load images in results
- Use virtual scrolling for >50 results

---

### Products Page (`/products`)

**Purpose**: Product listing and browsing

**Expected Performance**:
- LCP: <2.5s (product grid)
- FCP: <1.5s
- TTI: <3.0s
- Bundle: 157 KB

**Critical Resources**:
- HTML: 8 KB
- CSS: 10 KB
- JS: 157 KB
- API: 10-50 KB (product data)
- Images: 200-500 KB (lazy loaded)
- Total: 185-225 KB (initial)

**Optimization**:
- Pagination (20 items/page)
- Lazy load images (Intersection Observer)
- Prefetch next page on scroll
- Use low-quality image placeholders (LQIP)

---

### QA Page (`/qa`)

**Purpose**: Question answering interface

**Expected Performance**:
- LCP: <2.0s (chat interface)
- FCP: <1.2s
- TTI: <2.5s
- Bundle: 151 KB + Socket.IO (30 KB)
- Total: 181 KB

**Critical Resources**:
- HTML: 7 KB
- CSS: 9 KB
- JS: 181 KB
- WebSocket: Real-time connection
- Total: 197 KB

**Optimization**:
- Streaming responses (SSE or WebSocket)
- Optimistic UI updates
- Cache previous Q&A pairs
- Show loading state immediately

---

## 5. Network Performance

### Resource Loading Timeline

**Typical Page Load**:
```
0ms     → HTML request starts
50ms    → HTML received (5-10 KB)
60ms    → CSS request starts
100ms   → CSS received (8-10 KB)
110ms   → JS request starts
300ms   → JS received (150 KB gzipped)
310ms   → Parse and execute JS
500ms   → First Contentful Paint (FCP)
800ms   → API request for data
1200ms  → API response received
1300ms  → Render complete
1500ms  → Largest Contentful Paint (LCP)
2000ms  → Time to Interactive (TTI)
2100ms  → All resources loaded
```

---

### HTTP/2 Multiplexing

**Benefits**:
- Parallel requests (6+ simultaneous)
- Header compression (HPACK)
- Server push (for critical resources)

**Without HTTP/2** (HTTP/1.1):
- 6 parallel requests max
- Each request has full headers
- ~15-20% slower

**With HTTP/2**:
- Unlimited parallel requests
- Compressed headers
- ~15-20% faster

**Verify HTTP/2**:
```bash
curl -I --http2 http://localhost:3000
# Should show: HTTP/2 200
```

---

## 6. Caching Strategy

### Browser Caching

**Static Assets** (immutable):
```
Cache-Control: public, max-age=31536000, immutable
```
- JavaScript bundles: `/_next/static/chunks/[hash].js`
- CSS files: `/_next/static/css/[hash].css`
- Images: `/images/[hash].webp`

**HTML Pages** (dynamic):
```
Cache-Control: public, max-age=60, stale-while-revalidate=300
```
- Dynamic pages: `/search`, `/products`
- Allows stale content while revalidating

**API Responses**:
```
Cache-Control: public, max-age=300
```
- Search results: 5 minutes cache
- Product data: 5 minutes cache
- QA responses: No cache (dynamic)

---

### Service Worker (PWA)

**Cache Strategy**:
- **Network First**: API calls (fresh data)
- **Cache First**: Static assets (performance)
- **Stale While Revalidate**: HTML pages (balance)

**Configuration** (`apps/pwa/sw.js`):
```javascript
// Cache static assets aggressively
workbox.routing.registerRoute(
  /\.(js|css|woff2)$/,
  new workbox.strategies.CacheFirst({
    cacheName: 'static-assets',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
      }),
    ],
  })
);

// API calls with network first
workbox.routing.registerRoute(
  /\/api\//,
  new workbox.strategies.NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 5 * 60, // 5 minutes
      }),
    ],
  })
);
```

---

## 7. Image Optimization

### Next.js Image Component

**Automatic Optimizations**:
- WebP/AVIF format conversion
- Responsive images (srcset)
- Lazy loading (Intersection Observer)
- Blur placeholder (Low-Quality Image Placeholder)

**Usage**:
```tsx
import Image from 'next/image'

<Image
  src="/products/bottle.jpg"
  alt="50ml PET 용기"
  width={300}
  height={300}
  loading="lazy"
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,..."
/>
```

**Performance Impact**:
- Original JPEG: 500 KB
- Optimized WebP: 80 KB (84% reduction)
- With lazy loading: Only loads when visible
- With blur placeholder: Instant visual feedback

---

### Image CDN

**Cloudflare Images** (Recommended):
- Automatic format conversion
- Automatic resizing
- Global CDN
- Cost: $5/month (100k images)

**Configuration**:
```javascript
// next.config.js
module.exports = {
  images: {
    loader: 'cloudflare',
    path: 'https://your-domain.com/cdn-cgi/image/',
    domains: ['your-domain.com'],
  },
}
```

---

## 8. Code Splitting

### Route-based Splitting

**Automatic** (Next.js default):
- Each route is a separate bundle
- Shared code is automatically chunked
- Common dependencies are in shared chunks

**Example**:
```
Page        | Bundle Size | Shared Chunks
------------|-------------|---------------
/           | 12 KB       | framework.js (60 KB)
/search     | 22 KB       | framework.js (60 KB)
/products   | 34 KB       | framework.js (60 KB)
/qa         | 18 KB       | framework.js (60 KB)
```

**Total on /**: 12 + 60 = 72 KB
**Total on /search**: 22 + 60 = 82 KB (only 22 KB additional)

---

### Component-level Splitting

**Dynamic Imports**:
```tsx
// Heavy component (e.g., Chart library)
const Chart = dynamic(() => import('@/components/Chart'), {
  loading: () => <div>Loading chart...</div>,
  ssr: false,
})

// Only loads when component is rendered
<Chart data={data} />
```

**Bundle Impact**:
- Without dynamic import: +100 KB on every page
- With dynamic import: +100 KB only on pages using Chart
- **Savings**: 100 KB * (N-1) pages

---

## 9. Development Performance

### Dev Server Startup

**Cold Start** (first time):
```bash
cd /home/rkqksk/projects/new_rag/apps/web
time pnpm dev
```

**Expected**:
- Dependency scan: 2-5s
- TypeScript compilation: 5-10s
- Server startup: 1-2s
- Total: 8-17s

**Hot Restart** (after code change):
- Fast Refresh: 100-500ms
- Full page reload: 1-3s

---

### Hot Module Replacement (HMR)

**Performance**:
- Small change (1 component): 100-300ms
- Medium change (5 components): 300-800ms
- Large change (20+ components): 1-3s

**Fast Refresh**:
- Preserves React state
- Updates only changed components
- ~10x faster than full reload

---

## 10. Memory Usage

### Browser Memory

**Expected Usage**:
- Initial load: 50-80 MB
- After navigation: 80-120 MB
- With images: 120-200 MB
- Memory leaks: Monitor for >500 MB

**Monitoring**:
```javascript
// In browser console
console.log(performance.memory)
// {
//   totalJSHeapSize: 45000000,
//   usedJSHeapSize: 30000000,
//   jsHeapSizeLimit: 2172649472
// }
```

---

### Node.js Memory (Dev Server)

**Expected Usage**:
- Dev server idle: 200-400 MB
- During compilation: 500-1000 MB
- Memory leaks: Monitor for >2 GB

**Monitoring**:
```bash
# Check Node.js process memory
ps aux | grep "next dev"
```

---

## 11. Performance Testing Tools

### Lighthouse CI

**Setup**:
```bash
# Install Lighthouse CI
npm install -g @lhci/cli

# Configure
cat > lighthouserc.json << 'EOF'
{
  "ci": {
    "collect": {
      "url": ["http://localhost:3000"],
      "numberOfRuns": 3
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", {"minScore": 0.9}],
        "categories:accessibility": ["error", {"minScore": 0.95}]
      }
    }
  }
}
EOF

# Run
lhci autorun
```

---

### WebPageTest

**Online Tool**: https://www.webpagetest.org/

**What it provides**:
- Real device testing
- Multiple locations
- Film strip view
- Detailed waterfall
- Connection throttling

**Test URL**: http://your-production-domain.com

---

### Chrome DevTools Performance

**Usage**:
1. Open Chrome DevTools (F12)
2. Go to Performance tab
3. Click Record
4. Interact with page
5. Stop recording
6. Analyze flame chart

**Key Metrics**:
- Scripting time
- Rendering time
- Painting time
- Loading time

---

## 12. Mobile Performance

### Mobile vs Desktop

**Typical Differences**:
- Mobile CPU: 4-5x slower than desktop
- Mobile Network: 2-10x slower (3G/4G)
- Mobile Memory: 2-4x less RAM

**Performance Adjustments**:
- Desktop LCP: <2.5s → Mobile LCP: <4s
- Desktop FCP: <1.8s → Mobile FCP: <3s
- Desktop TTI: <3.8s → Mobile TTI: <6s

---

### Mobile-specific Optimizations

**1. Reduce JavaScript**:
- Desktop: 150 KB OK
- Mobile: Target <100 KB

**2. Optimize Images**:
- Serve smaller images on mobile (srcset)
- Use lower quality (80% vs 90%)

**3. Lazy Load Everything**:
- Images below fold
- Non-critical CSS
- Non-critical JS

**4. Reduce Network Requests**:
- Inline critical CSS
- Combine small assets
- Use HTTP/2 server push

---

## 13. Progressive Web App (PWA)

### PWA Features

**Installability**:
- Add to home screen
- Standalone window
- App icon

**Offline Support**:
- Service Worker caching
- Offline fallback page
- Background sync

**Performance Benefits**:
- Cached assets: 0ms load time
- Instant navigation
- Better perceived performance

---

### PWA Checklist

- [ ] HTTPS enabled
- [ ] Service Worker registered
- [ ] Manifest.json configured
- [ ] App icons provided (192x192, 512x512)
- [ ] Offline page implemented
- [ ] Install prompt shown
- [ ] Works on mobile devices
- [ ] Lighthouse PWA score: 100

---

## 14. Optimization Recommendations

### Immediate Actions (0 cost)

**1. Enable Static Generation**
```javascript
// app/page.tsx
export const revalidate = 60 // Revalidate every 60s

export default function Home() {
  return <div>...</div>
}
```
Expected: 50-90% faster page loads

**2. Optimize Images**
```tsx
// Use Next.js Image component everywhere
import Image from 'next/image'

// Before: <img src="/image.jpg" />
// After:
<Image src="/image.jpg" width={300} height={300} />
```
Expected: 70-85% smaller images

**3. Add Loading States**
```tsx
// app/search/loading.tsx
export default function Loading() {
  return <div>Loading search results...</div>
}
```
Expected: Better perceived performance

**4. Implement Code Splitting**
```tsx
// Lazy load heavy components
const Chart = dynamic(() => import('@/components/Chart'))
const Map = dynamic(() => import('@/components/Map'))
```
Expected: 30-50% smaller initial bundle

**5. Enable Compression**
```javascript
// next.config.js
module.exports = {
  compress: true, // Enable gzip
}
```
Expected: 70% smaller responses

---

### Medium-term Actions (minimal cost)

**6. Add CDN**
- Use Vercel (free tier) or Cloudflare
- Automatic edge caching
- Expected: 50-80% faster for global users
- Cost: $0-20/month

**7. Optimize Fonts**
```javascript
// app/layout.tsx
import { Inter } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})
```
Expected: Eliminate font loading flash

**8. Implement Prefetching**
```tsx
// Prefetch next page on hover
<Link href="/products" prefetch>
  View Products
</Link>
```
Expected: Instant navigation feel

---

### Long-term Actions (with budget)

**9. Move to Vercel/Netlify**
- Automatic optimizations
- Edge caching
- Image optimization
- Expected: 40-60% faster globally
- Cost: $0-100/month

**10. Implement Analytics**
- Real User Monitoring (RUM)
- Track actual user performance
- Expected: Better visibility
- Cost: $0-50/month (Vercel Analytics free)

---

## 15. Industry Benchmarks

### Comparison with Similar Apps

| Metric | Our Target | E-commerce Average | Status |
|--------|-----------|-------------------|---------|
| LCP | <2.5s | 3.5s | ✅ Better |
| FCP | <1.8s | 2.5s | ✅ Better |
| TTI | <3.8s | 5.0s | ✅ Better |
| Bundle Size | 150 KB | 300 KB | ✅ Better |
| Lighthouse Score | >90 | 70-80 | ✅ Better |

---

## 16. Testing Checklist

### Pre-deployment Testing

- [ ] Run Lighthouse on all main pages
- [ ] Test on 3G network (Chrome DevTools)
- [ ] Test on mobile devices (real devices)
- [ ] Check bundle sizes (<200 KB initial)
- [ ] Verify images are optimized
- [ ] Test offline functionality (PWA)
- [ ] Check for console errors
- [ ] Verify all pages load <3s
- [ ] Test with React DevTools Profiler
- [ ] Document all findings

---

## 17. Baseline Test Results

### Test Environment
- **Date**: 2025-11-19
- **System**: v10.0.0 Unified Maximum
- **Browser**: Chrome 120+
- **Network**: Fast 3G (1.6 Mbps, 150ms RTT)

### Results Summary

| Test | Target | Actual | Status |
|------|--------|--------|--------|
| Build time (cold) | <3min | [TBD] | ⏳ |
| Build time (hot) | <30s | [TBD] | ⏳ |
| Bundle size | <200 KB | [TBD] | ⏳ |
| Lighthouse Performance | >90 | [TBD] | ⏳ |
| LCP | <2.5s | [TBD] | ⏳ |

**Note**: Run `cd apps/web && pnpm build` and Lighthouse tests to populate these results.

---

## 18. Next Steps

1. **Run Build Tests**: Execute build commands and measure times
2. **Run Lighthouse**: Test all main pages
3. **Implement Optimizations**: Apply the 0-cost optimizations
4. **Setup Monitoring**: Configure Vercel Analytics or similar
5. **Test on Real Devices**: Use actual mobile devices

---

## Resources

- **Lighthouse**: https://developers.google.com/web/tools/lighthouse
- **WebPageTest**: https://www.webpagetest.org/
- **Next.js Docs**: https://nextjs.org/docs/advanced-features/measuring-performance
- **Web Vitals**: https://web.dev/vitals/

---

**Document Version**: 1.0
**Last Updated**: 2025-11-19
**Status**: Ready for Testing
**Next Review**: After first Lighthouse test
