# Frontend Consolidation Plan

## Problem
Two separate frontend projects exist:
1. `frontend/` - Next.js with auth, custom components, resume editor
2. `sirafit-2/` - TanStack Start with shadcn UI components

## Analysis

### What sirafit-2 has:
- ✅ 46 shadcn UI components
- ✅ components/sirafit/ (bits.tsx, shell.tsx)
- ✅ hooks/use-mobile.tsx
- ✅ lib utilities
- ✅ 47 route files

### What frontend has (MISSING from sirafit-2):
- ✅ 6 custom UI components (ArrayItem, Input, SectionCard, StatusBadge, Textarea, ValidationDisplay)
- ✅ Resume editor route (_app.resumes.$id.editor.tsx)
- ✅ Auth context (AuthContext.tsx)
- ✅ API layer (jobs.ts, profiles.ts)
- ✅ Validation (profile.ts)
- ✅ Type definitions (job.ts, profile.ts)

## Decision

**Keep `frontend/` as the primary project** because it has:
- Auth system
- Custom components
- API layer
- Type safety
- Resume editor (Sprint 2)

**Cherry-pick from `sirafit-2/`**:
- shadcn UI components (if better)
- Updated route files
- Modern build config

## Consolidation Steps

### Phase 1: Backup
1. ✅ Create backup of frontend/
2. ✅ Document current state

### Phase 2: Compare & Merge
1. Compare UI components (46 files)
2. Compare sirafit components (2 files)
3. Compare routes (47 vs 48 files)
4. Compare lib utilities
5. Compare config files

### Phase 3: Copy Updates
1. Copy newer shadcn components if different
2. Copy updated sirafit components
3. Merge route files (keep all 48)
4. Copy updated utilities
5. Update config files

### Phase 4: Verify
1. Run `npm install`
2. Run `npm run dev`
3. Test all routes
4. Verify auth works
5. Test resume editor
6. Test Sprint 2 features

### Phase 5: Cleanup
1. Archive sirafit-2/
2. Update documentation
3. Commit changes

## Risks & Mitigation

### Risk 1: Breaking Auth
- **Mitigation**: Keep AuthContext.tsx untouched
- **Rollback**: Git revert if needed

### Risk 2: Lost Custom Components
- **Mitigation**: Don't delete, only add/update
- **Backup**: Archive before changes

### Risk 3: Route Conflicts
- **Mitigation**: Merge carefully, keep both versions
- **Test**: Verify all routes load

## Files to Preserve (DO NOT OVERWRITE)

### Critical Files in frontend/:
```
src/contexts/AuthContext.tsx
src/lib/api/jobs.ts
src/lib/api/profiles.ts
src/lib/validation/profile.ts
src/types/job.ts
src/types/profile.ts
src/components/ArrayItem.tsx
src/components/Input.tsx
src/components/SectionCard.tsx
src/components/StatusBadge.tsx
src/components/Textarea.tsx
src/components/ValidationDisplay.tsx
src/routes/_app.resumes.$id.editor.tsx
```

## Files to Update (from sirafit-2/)

### UI Components (46 files):
```
src/components/ui/*.tsx
```

### Sirafit Components:
```
src/components/sirafit/bits.tsx
src/components/sirafit/shell.tsx
```

### Hooks:
```
src/hooks/use-mobile.tsx
```

### Lib Utilities:
```
src/lib/utils.ts
src/lib/error-capture.ts
src/lib/error-page.ts
src/lib/lovable-error-reporting.ts
src/lib/mock.ts
```

### Routes (47 files, ADD to frontend):
```
src/routes/*.tsx (merge with existing 48 routes)
```

### Config:
```
package.json (merge dependencies)
vite.config.ts (update if newer)
tsconfig.json (merge)
.env (merge)
```

## Execution Plan

### Step 1: Document Current State
```bash
cd frontend
git status
git add -A
git commit -m "backup: frontend before consolidation"
```

### Step 2: Compare Projects
```bash
# List differences
diff -r frontend/src/components/ui sirafit-2/src/components/ui
diff -r frontend/src/routes sirafit-2/src/routes
```

### Step 3: Selective Copy
```bash
# Copy UI components
cp -r sirafit-2/src/components/ui/* frontend/src/components/ui/

# Copy sirafit components
cp sirafit-2/src/components/sirafit/* frontend/src/components/sirafit/

# Copy hooks
cp sirafit-2/src/hooks/use-mobile.tsx frontend/src/hooks/

# Copy lib utilities (selective)
cp sirafit-2/src/lib/*.ts frontend/src/lib/
```

### Step 4: Merge Routes
```bash
# Copy routes, don't overwrite editor route
cp sirafit-2/src/routes/*.tsx frontend/src/routes/
# Restore editor route
git checkout frontend/src/routes/_app.resumes.$id.editor.tsx
```

### Step 5: Update Dependencies
```bash
cd frontend
npm install
```

### Step 6: Test
```bash
npm run dev
```

### Step 7: Archive sirafit-2
```bash
mv sirafit-2 sirafit-2-archived
```

## Success Criteria

- [ ] All routes load without errors
- [ ] Auth system works (login/logout)
- [ ] Resume editor loads and saves
- [ ] Job import pages exist (if implemented)
- [ ] No TypeScript errors
- [ ] No build errors
- [ ] All Sprint 2 features work
- [ ] shadcn components render correctly

## Rollback Plan

If consolidation fails:
```bash
cd frontend
git reset --hard HEAD~1
```

## Status

**Current**: Plan created
**Next**: Execute consolidation
**Owner**: Developer
**Priority**: High (blocks Sprint 3 frontend work)
