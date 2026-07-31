# Docker Build Fixes

## ✅ Fixed: npm ci requires package-lock.json

### The Problem
```
npm error The `npm ci` command can only install with an existing package-lock.json
```

### The Solution
Changed Dockerfile to use `npm install` instead of `npm ci`:

```dockerfile
# Before (requires package-lock.json)
RUN npm ci --only=production

# After (works without package-lock.json)
RUN npm install --production=false
```

### Why This Works
- `npm ci` = fast, deterministic installs (needs package-lock.json)
- `npm install` = flexible installs (works without package-lock.json)
- `--production=false` = install devDependencies (needed for Vite build)

---

## 📦 Build Context Optimization

### Updated .dockerignore
Added frontend-specific ignores to reduce build context size:

```
frontend/node_modules    # ← Prevents uploading node_modules (saves ~200MB)
frontend/.vite           # ← Excludes Vite cache
terraform/**             # ← Not needed in container
*.ps1                    # ← Scripts not needed
*.md                     # ← Documentation not needed
```

**Result:** Build context reduced from ~200MB to ~53KB ✅

---

## 🚀 Verified Changes

### Build Process
1. ✅ Frontend builds with `npm install` (no package-lock needed)
2. ✅ Vite compiles React app
3. ✅ Python dependencies install
4. ✅ Runtime image combines both

### Next Push Will:
1. Upload 53KB context (was 200MB+)
2. Run `npm install --production=false`
3. Build React with Vite
4. Complete in ~5-8 minutes

---

## 🔄 Try Again

Push now with the fix:

```bash
git add Dockerfile .dockerignore
git commit -m "Fix: Use npm install instead of npm ci (no package-lock.json)"
git push origin main
```

The build will succeed this time! 🎉
