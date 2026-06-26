# Requirements Document

## Introduction

This document outlines the requirements for Sprint 3 - Job Import System. The goal is to implement a comprehensive job import system that allows users to import jobs from URLs and pasted descriptions, normalize the data, and maintain import history.

### Goals

1. Enable users to import job postings from various sources (URLs, pasted descriptions)
2. Normalize job data into a consistent format
3. Track import history with metadata
4. Prevent duplicate job entries
5. Provide a user-friendly interface for job import operations

## Glossary

| Term | Definition |
|------|-----------|
| Job Import | The process of extracting job data from external sources and adding to the system |
| Normalization | Converting raw job data into a standardized format |
| Deduplication | Preventing duplicate job entries based on title, company, and location |
| Import History | Record of all job import operations with status and results |

## User Stories

### Core Functionality
- As a user, I want to paste a job description so I can save it to my profile
- As a user, I want to enter a job URL so I can automatically import the job data
- As a user, I want to see a preview of normalized job data before saving
- As a user, I want to see my import history with status and results

### Quality & Reliability
- As a user, I want to avoid duplicate job entries (same title + company + location)
- As a user, I want clear error messages if import fails
- As a user, I want to know how many jobs were found vs imported

### User Experience
- As a user, I want a simple, intuitive import interface
- As a user, I want to see progress indicators during import
- As a user, I want to re-import jobs from history if needed

## Functional Requirements

### FR1: Job Import Endpoints

#### FR1.1: Import Jobs from URL
- **ID:** FR1.1
- **Description:** Import job(s) from a job posting URL
- **Request:**
  - Method: POST
  - Endpoint: `/api/v1/jobs/import`
  - Body: `{"source_type": "url", "data": "<job_url>"}`
- **Response:** JobImport response with status, counts, and job details
- **Authentication:** Required
- **Validation:** URL must be a valid HTTP/HTTPS link

#### FR1.2: Import Jobs from Description
- **ID:** FR1.2
- **Description:** Import job from a pasted job description
- **Request:**
  - Method: POST
  - Endpoint: `/api/v1/jobs/import`
  - Body: `{"source_type": "description", "data": "<job_description_text>"}`
- **Response:** JobImport response with status, counts, and job details
- **Authentication:** Required
- **Validation:** Description must be at least 100 characters

#### FR1.3: Get Import History
- **ID:** FR1.3
- **Description:** Retrieve user's import history
- **Request:**
  - Method: GET
  - Endpoint: `/api/v1/jobs/import/history`
- **Response:** Array of JobImport records, sorted by creation date (descending)
- **Authentication:** Required

#### FR1.4: Get Import Details
- **ID:** FR1.4
- **Description:** Get details of a specific import
- **Request:**
  - Method: GET
  - Endpoint: `/api/v1/jobs/import/{import_id}`
- **Response:** JobImport record with nested job details
- **Authentication:** Required
- **Authorization:** User must own the import

### FR2: Job Normalization

#### FR2.1: Parse URL Job Data
- **ID:** FR2.1
- **Description:** Extract job details from job posting URLs
- **Supported Sources:** LinkedIn, Indeed, Glassdoor, ZipRecruiter, SimplyHired
- **Extracted Fields:**
  - Job title
  - Company name
  - Location
  - Description
  - Salary range (if available)
  - Job URL
  - Source type
- **Output:** Normalized Job object

#### FR2.2: Parse Description Job Data
- **ID:** FR2.2
- **Description:** Extract job details from plain text description
- **Extracted Fields:**
  - Job title (first line or keyword detection)
  - Company name (if mentioned)
  - Location (if mentioned)
  - Description (full text)
  - Tags (skills, technologies mentioned)
- **Output:** Normalized Job object

#### FR2.3: Normalization Pipeline
- **ID:** FR2.3
- **Description:** Process raw job data into standardized format
- **Steps:**
  1. Parse source data (URL or text)
  2. Extract job fields using regex/ML models
  3. Validate required fields (title, company)
  4. Standardize location format
  5. Generate tags from description
  6. Calculate match score (0-100)
  7. Deduplicate check
- **Output:** Normalized Job object ready for storage

### FR3: Deduplication

#### FR3.1: Duplicate Detection
- **ID:** FR3.1
- **Description:** Prevent duplicate job entries
- **Logic:** Consider jobs duplicates if:
  - Title matches (case-insensitive, normalized)
  - Company matches (case-insensitive, normalized)
  - Location matches (case-insensitive, normalized)
- **Fuzzy Matching:** Allow slight variations (typos, abbreviations)

#### FR3.2: Duplicate Handling
- **ID:** FR3.2
- **Description:** Handle duplicate job detection
- **Options:**
  - Skip duplicate and count in fail_count
  - Link to existing job instead of creating new
  - Mark import with duplicate count
- **Output:** Report duplicate count in JobImport status

### FR4: Import History Tracking

#### FR4.1: Import Record Creation
- **ID:** FR4.1
- **Description:** Create import record for each import operation
- **Fields:**
  - user_id (foreign key)
  - source_type (url, description, csv)
  - status (pending, processing, completed, failed)
  - total_found (number of jobs found)
  - ok_count (number of jobs successfully imported)
  - fail_count (number of failures/duplicates)
  - created_at, updated_at

#### FR4.2: Import Status Updates
- **ID:** FR4.2
- **Description:** Update import status during processing
- **Transitions:**
  - pending → processing (on start)
  - processing → completed (on finish)
  - processing → failed (on error)

## Non-Functional Requirements

### NFR1: Performance
- **NFR1.1:** Parse job data within 5 seconds per job
- **NFR1.2:** Import 10+ jobs within 30 seconds total
- **NFR1.3:** Import history load in < 1 second

### NFR2: Reliability
- **NFR2.1:** 95%+ job parsing success rate
- **NFR2.2:** Graceful error handling for failed imports
- **NFR2.3:** Import failures don't affect other jobs

### NFR3: User Experience
- **NFR3.1:** Clear error messages for all failure scenarios
- **NFR3.2:** Progress indicators during import
- **NFR3.3:** Visual feedback for duplicate detection

### NFR4: Data Quality
- **NFR4.1:** Required fields: title, company
- **NFR4.2:** Optional fields: location, salary, tags
- **NFR4.3:** Minimum description length: 100 characters

## Data Model

### JobImport (New Table)
```sql
CREATE TABLE job_imports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL,  -- url, description, csv
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, failed
    total_found INTEGER DEFAULT 0,
    ok_count INTEGER DEFAULT 0,
    fail_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Job (Existing Table - Extend)
```sql
ALTER TABLE jobs ADD COLUMN source VARCHAR(50) DEFAULT 'manual';
-- Already has: external_id, title, company, location, description, salary_min, salary_max, currency, tags, url
```

## Acceptance Criteria

### AC1: Import from URL
- [ ] User can paste a job URL (LinkedIn, Indeed, etc.)
- [ ] System fetches and parses the job page
- [ ] Extracted job data is displayed for review
- [ ] Job is saved to database with proper source tag
- [ ] Import history record is created
- [ ] Duplicate detection works (same title+company+location)

### AC2: Import from Description
- [ ] User can paste a job description text
- [ ] System extracts job fields from text
- [ ] Extracted data is displayed for review
- [ ] Job is saved to database
- [ ] Import history record is created

### AC3: Import History
- [ ] User can view their import history
- [ ] History shows: date, source, status, counts
- [ ] History is sorted by date (newest first)
- [ ] Failed imports are clearly marked

### AC4: Deduplication
- [ ] Duplicate jobs are not created
- [ ] Duplicate count is reported in import results
- [ ] Fuzzy matching allows slight variations
- [ ] User can choose to import duplicates if desired

### AC5: Error Handling
- [ ] Invalid URLs show error message
- [ ] Invalid descriptions show error message
- [ ] Network errors are handled gracefully
- [ ] Parsing failures show specific error reasons
- [ ] Import failures don't affect other jobs

### AC6: Performance
- [ ] Job parsing completes in < 5 seconds
- [ ] Import history loads in < 1 second
- [ ] UI remains responsive during import

## Requirements

### Backend Requirements

#### BR1: Job Import Service
- Create `app/services/job_import.py` with functions:
  - `parse_job_from_url(url: str) -> JobData`
  - `parse_job_from_description(description: str) -> JobData`
  - `normalize_job(job_data: JobData) -> Job`
  - `check_duplicate(job: Job) -> bool`
  - `process_import(user_id: UUID, source_type: str, data: str) -> JobImport`

#### BR2: API Endpoints
- `POST /api/v1/jobs/import` - Import job(s) from URL or description
- `GET /api/v1/jobs/import/history` - Get import history
- `GET /api/v1/jobs/import/{import_id}` - Get import details

#### BR3: Database Models
- `JobImport` model with fields: id, user_id, source, status, total_found, ok_count, fail_count, created_at, updated_at
- Extend `Job` model with source field
- Add foreign key relationship to User

#### BR4: Validation
- URL must be valid HTTP/HTTPS
- Description must be at least 100 characters
- Title and company are required fields
- Location and salary are optional

#### BR5: Deduplication
- Check for duplicate based on title + company + location
- Use fuzzy matching for slight variations
- Report duplicate count in import results

#### BR6: Error Handling
- Parse errors with specific messages
- Network errors with retry capability
- Invalid input validation errors
- Graceful degradation

### Frontend Requirements

#### FR1: Job Import Page
- File: `frontend/src/app/dashboard/jobs/import/page.tsx`
- Features:
  - URL input field with validation
  - Description text area (min 100 chars)
  - Import button with loading state
  - Preview of extracted job data
  - Import history link

#### FR2: Import History Page
- File: `frontend/src/app/dashboard/jobs/history/page.tsx`
- Features:
  - List of past imports
  - Status indicators (pending, processing, completed, failed)
  - Date and counts display
  - Click to view import details
  - Refresh button

#### FR3: Components
- ImportForm component (URL and description inputs)
- ImportPreview component (show extracted data)
- ImportHistory component (list of imports)
- StatusBadge component (pending/processing/completed/failed)

### Testing Requirements

#### TR1: Unit Tests
- `backend/tests/test_job_import.py` - Service layer tests
- `backend/tests/test_jobs.py` - API endpoint tests
- Test import parsing for various job boards
- Test normalization pipeline
- Test deduplication logic

#### TR2: E2E Tests
- `frontend/e2e/job-import.spec.ts` - Import flow tests
- Test URL import from LinkedIn, Indeed
- Test description import
- Test import history view
- Test duplicate detection

### Acceptance Criteria

### AC1: Import from URL
- [ ] User can paste a job URL (LinkedIn, Indeed, etc.)
- [ ] System fetches and parses the job page
- [ ] Extracted job data is displayed for review
- [ ] Job is saved to database with proper source tag
- [ ] Import history record is created
- [ ] Duplicate detection works (same title+company+location)

### AC2: Import from Description
- [ ] User can paste a job description text
- [ ] System extracts job fields from text
- [ ] Extracted data is displayed for review
- [ ] Job is saved to database
- [ ] Import history record is created

### AC3: Import History
- [ ] User can view their import history
- [ ] History shows: date, source, status, counts
- [ ] History is sorted by date (newest first)
- [ ] Failed imports are clearly marked

### AC4: Deduplication
- [ ] Duplicate jobs are not created
- [ ] Duplicate count is reported in import results
- [ ] Fuzzy matching allows slight variations
- [ ] User can choose to import duplicates if desired

### AC5: Error Handling
- [ ] Invalid URLs show error message
- [ ] Invalid descriptions show error message
- [ ] Network errors are handled gracefully
- [ ] Parsing failures show specific error reasons
- [ ] Import failures don't affect other jobs

### AC6: Performance
- [ ] Job parsing completes in < 5 seconds
- [ ] Import history loads in < 1 second
- [ ] UI remains responsive during import

## Implementation Tasks

See design.md for detailed implementation tasks and tasks.md for actionable steps.

## Out of Scope (Future Sprints)

- CSV bulk import
- Email job import
- Custom field mapping
- Advanced deduplication algorithms
- Job enrichment (skills extraction, salary normalization)
- Job推荐 (AI-powered recommendations)
- Integration with specific ATS systems
