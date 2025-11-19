#!/usr/bin/env bash
# Bundle optimization and analysis

set -e

echo "📦 Bundle Optimization"
echo "======================"
echo ""

# Create reports directory
mkdir -p reports/bundle-analysis

# Install bundle analyzer if not present
if ! pnpm list -r @next/bundle-analyzer > /dev/null 2>&1; then
    echo "📥 Installing bundle analyzer..."
    pnpm add -D @next/bundle-analyzer
fi

# 1. Analyze current bundle
echo "1️⃣  Analyzing current bundle size..."
pnpm --filter @rag/web build > /dev/null 2>&1

if [ -d "apps/web/.next" ]; then
    # Get bundle sizes
    TOTAL_SIZE=$(du -sh apps/web/.next | cut -f1)
    STATIC_SIZE=$(du -sh apps/web/.next/static 2>/dev/null | cut -f1 || echo "N/A")

    echo "   Total: $TOTAL_SIZE"
    echo "   Static: $STATIC_SIZE"

    # Count number of chunks
    CHUNK_COUNT=$(find apps/web/.next/static/chunks -name "*.js" 2>/dev/null | wc -l || echo "0")
    echo "   Chunks: $CHUNK_COUNT files"
fi

# 2. Generate bundle analysis report
echo ""
echo "2️⃣  Generating detailed analysis..."

# Use webpack-bundle-analyzer
cat > reports/bundle-analysis/analysis-$(date +%Y%m%d).txt <<EOF
BUNDLE ANALYSIS REPORT
======================
Generated: $(date)

CURRENT STATE:
--------------
Total Size: $TOTAL_SIZE
Static Assets: $STATIC_SIZE
Number of Chunks: $CHUNK_COUNT

RECOMMENDATIONS:
----------------
1. Code Splitting:
   - Implement dynamic imports for large components
   - Use Next.js route-based code splitting
   - Lazy load heavy dependencies

2. Tree Shaking:
   - Ensure imports use named exports
   - Remove unused dependencies
   - Check package.json for unused packages

3. Compression:
   - Enable gzip/brotli compression
   - Optimize images (WebP, AVIF)
   - Minify CSS and JavaScript

4. Dependencies Optimization:
   - Review large dependencies:
     * moment.js → date-fns (smaller alternative)
     * lodash → lodash-es (tree-shakeable)
   - Use bundle analyzer to identify heavy packages

5. Next.js Optimizations:
   - Enable SWC minification
   - Use Image Optimization API
   - Implement Incremental Static Regeneration

QUICK WINS:
-----------
• Enable output: 'standalone' in next.config.js ✅
• Add modularizeImports for icon libraries
• Implement virtual scrolling for long lists
• Use CSS modules instead of runtime CSS-in-JS

MONITORING:
-----------
• Set up bundle size CI checks
• Monitor bundle size in each PR
• Track performance metrics in production
EOF

cat reports/bundle-analysis/analysis-$(date +%Y%m%d).txt

# 3. Check for large dependencies
echo ""
echo "3️⃣  Analyzing dependencies..."

if [ -f "package.json" ]; then
    # Create a simple dependency size report
    cat > reports/bundle-analysis/dependencies-$(date +%Y%m%d).txt <<EOF
LARGE DEPENDENCIES
==================

Top dependencies by size (estimate):
$(du -sh node_modules/* 2>/dev/null | sort -rh | head -10 || echo "N/A")

RECOMMENDATIONS:
• Consider lighter alternatives for large packages
• Use dynamic imports for optional dependencies
• Review if all dependencies are necessary
EOF
fi

# 4. Generate optimization script
echo ""
echo "4️⃣  Creating optimization checklist..."

cat > reports/bundle-analysis/optimization-checklist.md <<EOF
# Bundle Optimization Checklist

## Immediate Actions
- [ ] Enable \`output: 'standalone'\` in next.config.js
- [ ] Add \`.env.local\` with \`ANALYZE=true\` for bundle analysis
- [ ] Review and remove unused dependencies
- [ ] Implement code splitting for large routes

## Code Changes
- [ ] Convert static imports to dynamic imports
- [ ] Lazy load heavy components
- [ ] Use \`next/image\` for all images
- [ ] Implement virtual scrolling for lists

## Configuration
- [ ] Enable SWC minification
- [ ] Configure compression middleware
- [ ] Set up CDN for static assets
- [ ] Enable HTTP/2 server push

## Monitoring
- [ ] Set bundle size budget in CI
- [ ] Add Lighthouse CI
- [ ] Monitor Core Web Vitals
- [ ] Track bundle size trends

## Dependencies
- [ ] Replace moment.js with date-fns
- [ ] Use lodash-es instead of lodash
- [ ] Audit dependencies with \`pnpm why\`
- [ ] Remove duplicate dependencies

Generated: $(date)
EOF

echo ""
echo "✅ Bundle analysis complete!"
echo "   Reports: reports/bundle-analysis/"
echo ""
echo "📋 Next steps:"
echo "   1. Review: reports/bundle-analysis/analysis-$(date +%Y%m%d).txt"
echo "   2. Follow: reports/bundle-analysis/optimization-checklist.md"
echo "   3. Monitor: Set up bundle size CI checks"
