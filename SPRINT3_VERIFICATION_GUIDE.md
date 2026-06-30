# Sprint 3 - Job Import System: Verification Guide

## Quick Start

### 1. Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```
Frontend will run on **port 3030** (as configured in vite.config)

### 3. Database Migration (if not already done)
```bash
cd backend
alembic upgrade head
```

## Testing the Job Import System

### Test 1: Import from URL

1. Navigate to `http://localhost:3030/jobs/import`
2. In the "From URL" section, paste a job URL from a supported platform:
   - LinkedIn: `https://www.linkedin.com/jobs/view/123456`
   - Greenhouse: `https://boards.greenhouse.io/company/jobs/123456`
   - Lever: `https://jobs.lever.co/company/abc-123`
   - Indeed: `https://www.indeed.com/viewjob?jk=123abc`
3. Click "Scrape now"
4. Verify:
   - ✅ Loading spinner appears
   - ✅ Import results show with job details
   - ✅ Platform is correctly detected
   - ✅ Tags are extracted (Python, React, AWS, etc.)
   - ✅ Salary range is parsed (if available)
   - ✅ Status shows "completed"

### Test 2: Import from Description

1. Navigate to `http://localhost:3030/jobs/import`
2. In the "From description" section, paste a job description:
```
Senior Full Stack Engineer - Remote
Acme Corp

We're looking for a Senior Full Stack Engineer to join our team.

Requirements:
- 5+ years experience with Python, React, and Node.js
- Experience with AWS, Docker, and Kubernetes
- Strong SQL skills (PostgreSQL preferred)
- Experience with REST APIs and GraphQL

Salary: $120,000 - $180,000
Location: Remote (US)

Apply now!
```
3. Click "Analyze description"
4. Verify:
   - ✅ Job title is extracted
   - ✅ Company name is parsed
   - ✅ Technologies are tagged (Python, React, Node, AWS, Docker, Kubernetes, SQL, PostgreSQL, REST, GraphQL)
   - ✅ Salary range is detected ($120,000 - $180,000)
   - ✅ Location is identified

### Test 3: Duplicate Detection

1. Import the same job URL twice
2. Verify:
   - ✅ First import shows job normally
   - ✅ Second import marks job as "duplicate"
   - ✅ Tag shows "duplicate" on the job card
   - ✅ Job is not re-created in database

### Test 4: Import History

1. Navigate to `http://localhost:3030/jobs/history`
2. Verify:
   - ✅ All past imports are listed in table
   - ✅ Each row shows: source, found count, ok count, fail count, date, status
   - ✅ Status badges display correctly (completed, failed, processing)
   - ✅ Date formatting is readable
   - ✅ "New import" button navigates to import page

### Test 5: Error Handling

1. Navigate to `http://localhost:3030/jobs/import`
2. Enter invalid URL: `https://invalid-url-test.com`
3. Click "Scrape now"
4. Verify:
   - ✅ Error message is displayed
   - ✅ UI remains usable
   - ✅ Can try again with different URL

5. Enter empty description
6. Verify:
   - ✅ "Analyze description" button is disabled
   - ✅ No API call is made

### Test 6: Recent Imports Widget

1. After importing several jobs, scroll down to "Recent imports" panel
2. Verify:
   - ✅ Shows last 3 imports
   - ✅ Each shows source type, counts, status
   - ✅ "View all →" link navigates to history page
   - ✅ Empty state shows if no imports

### Test 7: Navigation

1. Check sidebar navigation
2. Verify:
   - ✅ "Jobs" menu item exists
   - ✅ Clicking "Jobs" shows job-related routes
   - ✅ Can navigate between import and history pages
   - ✅ Browser back button works correctly

### Test 8: Authentication

1. Log out of the application
2. Try to access `http://localhost:3030/jobs/import`
3. Verify:
   - ✅ Redirected to login page
   - ✅ After login, can access import page
   - ✅ API calls include credentials

## Backend API Testing (Optional)

### Using curl or Postman:

#### 1. Import from URL
```bash
curl -X POST http://localhost:8000/api/v1/jobs/import \
  -H "Content-Type: application/json" \
  -d '{"source_type": "url", "data": "https://jobs.lever.co/company/123"}'
```

#### 2. Import from Description
```bash
curl -X POST http://localhost:8000/api/v1/jobs/import \
  -H "Content-Type: application/json" \
  -d '{"source_type": "description", "data": "Senior Python Engineer at Acme Corp..."}'
```

#### 3. Get Import History
```bash
curl http://localhost:8000/api/v1/jobs/import/history
```

#### 4. Get Import Details
```bash
curl http://localhost:8000/api/v1/jobs/import/{import_id}
```

#### 5. List Jobs
```bash
curl http://localhost:8000/api/v1/jobs
```

## Expected Behavior

### Supported Job Boards (9 total)
✅ LinkedIn  
✅ Indeed  
✅ Glassdoor  
✅ ZipRecruiter  
✅ SimplyHired  
✅ Lever  
✅ Greenhouse  
✅ Ashby  
✅ Workday  

### Extracted Skills/Tags (47 keywords)
Python, JavaScript, TypeScript, React, Angular, Vue, Node, Django, Flask, FastAPI, Java, Kotlin, Go, Rust, C++, C#, Ruby, PHP, Swift, SQL, PostgreSQL, MySQL, MongoDB, Redis, Docker, Kubernetes, AWS, Azure, GCP, Git, CI/CD, REST, GraphQL, Microservices, Machine Learning, AI, Data Science, DevOps, Agile, Scrum, TDD, Frontend, Backend, Full-stack, API, Mobile, Cloud

### Status Values
- `pending` - Import queued but not started
- `processing` - Import in progress
- `completed` - Import successful
- `failed` - Import failed with errors

## Troubleshooting

### Issue: "Failed to fetch import history"
**Solution**: Ensure backend is running on port 8000 and database is migrated

### Issue: "Authentication required"
**Solution**: Log in first at `http://localhost:3030/login`

### Issue: "Job not found" or empty results
**Solution**: 
- Check if URL is valid
- Verify job board is in supported list
- Check backend logs for parsing errors

### Issue: Frontend won't start
**Solution**:
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

### Issue: Migration errors
**Solution**:
```bash
cd backend
alembic downgrade base
alembic upgrade head
```

## Database Verification

### Check if tables exist:
```sql
-- In PostgreSQL
SELECT tablename FROM pg_tables WHERE schemaname = 'public';
```

Expected tables:
- `users`
- `jobs`
- `job_imports`
- `job_applications`
- `profiles`
- `experiences`
- `educations`
- `skills`
- `projects`
- `certifications`
- `resumes`
- `audit_logs`

### Query imported jobs:
```sql
SELECT id, title, company, source, tags, created_at 
FROM jobs 
ORDER BY created_at DESC 
LIMIT 10;
```

### Query import history:
```sql
SELECT id, source, status, total_found, ok_count, fail_count, created_at 
FROM job_imports 
ORDER BY created_at DESC 
LIMIT 10;
```

## Success Criteria

Sprint 3 is verified complete when:
- ✅ Can import jobs from URLs (all 9 platforms)
- ✅ Can import jobs from pasted descriptions
- ✅ Duplicate detection works
- ✅ Tags are automatically extracted
- ✅ Salary parsing works (when present)
- ✅ Import history tracks all imports
- ✅ Status badges display correctly
- ✅ Error handling is graceful
- ✅ Navigation works between pages
- ✅ Authentication protects routes
- ✅ Database records are created correctly

## Next Sprint Preview

After Sprint 3 verification, proceed to:
- **Sprint 4**: Job Matching & Scoring (match jobs to resume profiles)
- **Sprint 5**: Application Tracking (track application status)
- **Sprint 6**: Resume Generation (generate tailored resumes)

---

**Last Updated**: Context Transfer (Post-Consolidation)  
**Status**: Sprint 3 Complete ✅  
**Ready for Verification**: Yes ✅
