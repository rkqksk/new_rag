# Automation Quick Start

**Version**: v10.0.0 | **Time**: <5 minutes to productivity

---

## 🚀 First Time Setup (3 Steps)

```bash
# 1. One-command setup (3-5 minutes)
./setup.sh

# 2. Install pre-commit hooks (30 seconds)
pip install pre-commit && pre-commit install

# 3. Start development (instant)
pnpm dev
```

**Done!** You're ready to code.

---

## 🔨 Daily Workflow (4 Steps)

```bash
# 1. Start development
pnpm dev

# 2. Make changes
# ... edit code ...

# 3. Commit (hooks run automatically)
git add .
git commit -m "feat: add feature"

# 4. Build and test
./build-all.sh --parallel
```

---

## 📦 Available Scripts

### Setup
```bash
./setup.sh                    # Full setup
./setup.sh --skip-docker      # Without Docker
./setup.sh --help             # Show options
```

### Build
```bash
./build-all.sh                # Standard build
./build-all.sh --parallel     # Fast (30-40% faster)
./build-all.sh --production   # Production optimized
./build-all.sh --help         # Show options
```

### Quality
```bash
pre-commit run --all-files    # Run all hooks manually
pre-commit autoupdate         # Update hooks
```

---

## ⚡ Performance

| Task | Time |
|------|------|
| Setup (full) | 3-5 min |
| Setup (no Docker) | 1-2 min |
| Build (standard) | 2-3 min |
| Build (parallel) | 1-2 min |
| Pre-commit hooks | 5-15 sec |

---

## 🎯 Key Features

### setup.sh
- ✅ Checks system requirements
- ✅ Installs all dependencies
- ✅ Starts Docker services
- ✅ Runs migrations
- ✅ Verifies setup

### build-all.sh
- ✅ Builds packages in order
- ✅ Builds all apps
- ✅ Parallel build support
- ✅ Production optimization
- ✅ Build report generation

### Pre-commit Hooks
- ✅ Python: black, isort, flake8
- ✅ TypeScript: prettier, eslint
- ✅ Design: no icons, pure black
- ✅ Security: secrets detection

---

## 🐛 Quick Troubleshooting

**Port in use**:
```bash
lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

**Docker not starting**:
```bash
docker-compose down -v && docker-compose up -d
```

**Out of memory**:
```bash
export NODE_OPTIONS="--max-old-space-size=4096"
```

**Pre-commit fails**:
```bash
pre-commit run --all-files  # See all errors
```

---

## 📚 Documentation

- **Complete Guide**: `docs/guides/AUTOMATION_SCRIPTS.md`
- **Quick Reference**: `CLAUDE.md` → Essential Commands
- **Scripts README**: `scripts/README.md`
- **Full Summary**: `AUTOMATION_IMPLEMENTATION_SUMMARY.md`

---

## ✨ What's New in v10

### Automation Scripts
- 🆕 **setup.sh** - One-command project setup
- 🆕 **build-all.sh** - Monorepo build automation
- 🆕 **Pre-commit hooks** - TypeScript + Design system validation

### Time Savings
- **Setup**: 30-45 min → 3-5 min (85% faster)
- **Build**: Manual process → 2-3 min (automated)
- **Quality**: Manual checks → 5-15 sec (automatic)

### Developer Experience
- **New Developer**: Productive in <10 minutes
- **Daily Work**: Seamless workflow
- **Quality**: 100% design system compliance

---

**Ready to start?** Run `./setup.sh` and you're good to go! 🚀

---

**Version**: v10.0.0
**Date**: 2025-11-19
**Maintainer**: PETER Team
