# Frontend Loading Error Fix

**Error**: `TypeError: error loading dynamically imported module: http://localhost:8080/src/routes/login.tsx`

---

## Problem

The frontend dev server is having issues loading the login route after recent changes. This is likely due to:
1. Dev server cache not cleared after route changes
2. Module import resolution issue
3. Hot Module Replacement (HMR) failing to update

---

## Quick Fix

### Option 1: Restart Dev Server (Fastest)
```bash
# Stop the frontend dev server (Ctrl+C)
cd frontend

# Clear the cache
rm -rf node_modules/.vite
# Windows PowerShell:
Remove-Item -Recurse -Force node_modules\.vite

# Restart
npm run dev
```

### Option 2: Full Rebuild
```bash
cd frontend

# Clear all caches and node_modules
rm -rf node_modules/.vite .tanstack node_modules
# Windows PowerShell:
Remove-Item -Recurse -Force node_modules\.vite, .tanstack, node_modules

# Reinstall dependencies
npm install

# Start dev server
npm run dev
```

### Option 3: Hard Refresh Browser
After restarting the server:
1. Open browser
2. Press `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
3. Or clear browser cache for localhost

---

## Root Cause Analysis

### Port Discrepancy
The error shows `http://localhost:8080` but the project should be running on `http://localhost:3030`.

**Check which port is actually running**:
```bash
# Windows
netstat -ano | findstr :3030
netstat -ano | findstr :8080

# Mac/Linux
lsof -i :3030
lsof -i :8080
```

### If Running on Wrong Port
The lovable/vite-tanstack-config package handles port configuration automatically. If it's running on 8080 instead of 3030:

1. **Kill any process on port 8080**:
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8080 | xargs kill -9
```

2. **Ensure no conflicting dev servers**:
```bash
# Check all node processes
# Windows
tasklist | findstr node

# Mac/Linux
ps aux | grep node
```

---

## If Problem Persists

### Check for Syntax Errors
The error might indicate a syntax error in the login file. Let's verify:

```bash
cd frontend
npx tsc --noEmit
```

If there are TypeScript errors, they'll be shown.

### Check Import Paths
Verify all imports in `src/routes/login.tsx` are correct:
```typescript
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router"; // ✓
import { useState } from "react"; // ✓
import { useAuth } from "@/contexts/AuthContext"; // ✓ Check this exists
import { AuthShell } from "@/components/sirafit/shell"; // ✓ Check this exists
import { Input } from "@/components/ui/input"; // ✓
import { Label } from "@/components/ui/label"; // ✓
import { Button } from "@/components/ui/button"; // ✓
```

### Verify Files Exist
```bash
cd frontend/src

# Check required files
ls contexts/AuthContext.tsx
ls components/sirafit/shell.tsx
ls components/ui/input.tsx
ls components/ui/label.tsx
ls components/ui/button.tsx
```

---

## Prevention

### After Making Route Changes
Always restart the dev server:
```bash
# Stop server (Ctrl+C)
# Clear cache
rm -rf node_modules/.vite
# Restart
npm run dev
```

### Update .gitignore
Ensure cache directories are ignored:
```
node_modules/
.vite/
.tanstack/
dist/
.turbo/
```

---

## Expected Behavior After Fix

1. Navigate to `http://localhost:3030` (or whatever port shows in terminal)
2. Click "Sign In" button
3. Login page loads without errors
4. Can enter credentials and submit form

---

## Alternative: Check if Backend is Running

The error might also occur if the backend isn't running. Verify:

```bash
# Check backend
curl http://localhost:8000/health/live

# Expected response
{"status":"ok"}
```

If backend is not running:
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

---

## Complete Restart Procedure

If nothing else works, do a complete restart:

```bash
# 1. Stop all servers (Ctrl+C in all terminals)

# 2. Kill any lingering processes
# Windows:
taskkill /F /IM node.exe
taskkill /F /IM python.exe

# Mac/Linux:
pkill node
pkill python

# 3. Clean frontend
cd frontend
rm -rf node_modules/.vite .tanstack
npm install

# 4. Start backend (Terminal 1)
cd backend
uvicorn app.main:app --reload --port 8000

# 5. Start frontend (Terminal 2)
cd frontend
npm run dev

# 6. Hard refresh browser (Ctrl+Shift+R)
```

---

## Quick Checklist

- [ ] Stopped dev server
- [ ] Cleared `.vite` cache
- [ ] Restarted dev server
- [ ] Hard refreshed browser
- [ ] Backend running on port 8000
- [ ] Frontend running on correct port (check terminal output)
- [ ] No TypeScript compilation errors
- [ ] All imported files exist

---

## If Still Broken

Check the terminal output when starting `npm run dev` for:
- Port number (should match browser URL)
- Any build errors
- Warning messages

**Post the terminal output** for further debugging.

---

**Most Common Solution**: Clear cache and restart dev server! 🔄
