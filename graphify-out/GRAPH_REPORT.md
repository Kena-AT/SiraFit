# Graph Report - .  (2026-07-05)

## Corpus Check
- 202 files · ~63,829 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1418 nodes · 2567 edges · 111 communities (100 shown, 11 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 290 edges (avg confidence: 0.69)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Job API Endpoints|Job API Endpoints]]
- [[_COMMUNITY_Profile API & Models|Profile API & Models]]
- [[_COMMUNITY_Frontend Route Tree|Frontend Route Tree]]
- [[_COMMUNITY_Frontend Dependencies|Frontend Dependencies]]
- [[_COMMUNITY_Logging Infrastructure|Logging Infrastructure]]
- [[_COMMUNITY_UI Components (SeparatorSheet)|UI Components (Separator/Sheet)]]
- [[_COMMUNITY_Job Import Service|Job Import Service]]
- [[_COMMUNITY_Backend Models|Backend Models]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_Frontend Route Tree|Frontend Route Tree]]
- [[_COMMUNITY_Frontend Package Config|Frontend Package Config]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_Analytics Routes|Analytics Routes]]
- [[_COMMUNITY_UI Alert Dialog|UI Alert Dialog]]
- [[_COMMUNITY_UI Avatar & Card|UI Avatar & Card]]
- [[_COMMUNITY_Resume API Endpoints|Resume API Endpoints]]
- [[_COMMUNITY_Pydantic Schemas|Pydantic Schemas]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_Auth Tests|Auth Tests]]
- [[_COMMUNITY_Rate Limiting|Rate Limiting]]
- [[_COMMUNITY_Auth API Core|Auth API Core]]
- [[_COMMUNITY_TypeScript Config|TypeScript Config]]
- [[_COMMUNITY_Auth API Endpoints|Auth API Endpoints]]
- [[_COMMUNITY_Components Config|Components Config]]
- [[_COMMUNITY_Resume Generation Service|Resume Generation Service]]
- [[_COMMUNITY_Profile Models|Profile Models]]
- [[_COMMUNITY_UI Command Components|UI Command Components]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_UI Menubar|UI Menubar]]
- [[_COMMUNITY_Resume Generation Service|Resume Generation Service]]
- [[_COMMUNITY_Resume Generation Service|Resume Generation Service]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_React Contexts|React Contexts]]
- [[_COMMUNITY_Email Service|Email Service]]
- [[_COMMUNITY_SiraFit Bits Components|SiraFit Bits Components]]
- [[_COMMUNITY_UI Carousel|UI Carousel]]
- [[_COMMUNITY_Settings API|Settings API]]
- [[_COMMUNITY_Resume Generation Service|Resume Generation Service]]
- [[_COMMUNITY_Test Conftest|Test Conftest]]
- [[_COMMUNITY_Applications API|Applications API]]
- [[_COMMUNITY_Dashboard API|Dashboard API]]
- [[_COMMUNITY_UI Form Components|UI Form Components]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_Frontend Library Utils|Frontend Library Utils]]
- [[_COMMUNITY_Backend Core|Backend Core]]
- [[_COMMUNITY_API Endpoints|API Endpoints]]
- [[_COMMUNITY_Resume Generation Service|Resume Generation Service]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_Backend Models|Backend Models]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_Frontend Route Tree|Frontend Route Tree]]
- [[_COMMUNITY_Security & Tokens|Security & Tokens]]
- [[_COMMUNITY_Backend Code|Backend Code]]
- [[_COMMUNITY_Backend Tests|Backend Tests]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_Backend Core|Backend Core]]
- [[_COMMUNITY_UI Input & Label|UI Input & Label]]
- [[_COMMUNITY_Misc Code|Misc Code]]
- [[_COMMUNITY_Backend Core|Backend Core]]
- [[_COMMUNITY_Pydantic Schemas|Pydantic Schemas]]
- [[_COMMUNITY_Backend Code|Backend Code]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_Backend Tests|Backend Tests]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_Custom Components|Custom Components]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_UI Components|UI Components]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_Frontend Library Utils|Frontend Library Utils]]
- [[_COMMUNITY_Analytics Routes|Analytics Routes]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_App Routes|App Routes]]
- [[_COMMUNITY_Frontend Route Tree|Frontend Route Tree]]

## God Nodes (most connected - your core abstractions)
1. `cn()` - 79 edges
2. `Job` - 57 edges
3. `FileRoutesByPath` - 46 edges
4. `Panel()` - 29 edges
5. `apiFetch()` - 27 edges
6. `PageBody()` - 26 edges
7. `Button` - 26 edges
8. `Profile` - 25 edges
9. `PageHeader()` - 25 edges
10. `calculate_match_score()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `sample_job()` --calls--> `Job`  [INFERRED]
  backend/tests/test_resume_generation.py → backend/app/models/job.py
- `create_application()` --calls--> `AuditLog`  [INFERRED]
  backend/app/api/applications.py → backend/app/models/job.py
- `create_application()` --indirect_call--> `Job`  [INFERRED]
  backend/app/api/applications.py → backend/app/models/job.py
- `create_application()` --indirect_call--> `Profile`  [INFERRED]
  backend/app/api/applications.py → backend/app/models/profile.py
- `create_application()` --calls--> `analyze_match_score()`  [INFERRED]
  backend/app/api/applications.py → backend/app/services/scoring.py

## Import Cycles
- 1-file cycle: `frontend/src/components/ui/input-otp.tsx -> frontend/src/components/ui/input-otp.tsx`
- 1-file cycle: `frontend/src/components/ui/sonner.tsx -> frontend/src/components/ui/sonner.tsx`
- 2-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/lib/api/client.ts`
- 4-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.settings.ai.tsx -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/contexts/AuthContext.tsx -> frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/__root.tsx -> frontend/src/contexts/AuthContext.tsx`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.jobs.history.tsx -> frontend/src/lib/api/jobs.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.jobs.import.tsx -> frontend/src/lib/api/jobs.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.jobs.index.tsx -> frontend/src/lib/api/jobs.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.jobs.$jobId.tsx -> frontend/src/lib/api/jobs.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.match.tsx -> frontend/src/lib/api/jobs.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.ranking.tsx -> frontend/src/lib/api/jobs.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.resumes.builder.tsx -> frontend/src/lib/api/jobs.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.resumes.builder.tsx -> frontend/src/lib/api/resumes.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.resumes.$id.tsx -> frontend/src/lib/api/resumes.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.resumes.$id.editor.tsx -> frontend/src/lib/api/profiles.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.resumes.index.tsx -> frontend/src/lib/api/resumes.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.resumes.profiles.tsx -> frontend/src/lib/api/profiles.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/_app.settings.index.tsx -> frontend/src/lib/api/profiles.ts -> frontend/src/lib/api/client.ts`
- 5-file cycle: `frontend/src/contexts/AuthContext.tsx -> frontend/src/lib/api/client.ts -> frontend/src/router.tsx -> frontend/src/routeTree.gen.ts -> frontend/src/routes/login.tsx -> frontend/src/contexts/AuthContext.tsx`

## Communities (111 total, 11 thin omitted)

### Community 0 - "Job API Endpoints"
Cohesion: 0.06
Nodes (62): get_import_detail(), get_import_history(), get_job(), get_job_analysis(), get_match_score(), import_jobs(), list_jobs(), list_ranked_jobs() (+54 more)

### Community 1 - "Profile API & Models"
Cohesion: 0.06
Nodes (40): get_my_profile(), Any, Session, User, Get the current user's profile.     If no profile exists, creates an empty one a, Update the current user's profile monolithically.     Nested objects (experience, update_my_profile(), Certification (+32 more)

### Community 2 - "Frontend Route Tree"
Cohesion: 0.03
Nodes (66): AppAnalyticsIndexRoute, AppAnalyticsMarketRoute, AppAnalyticsRoute, AppAnalyticsRouteChildren, AppAnalyticsRouteWithChildren, AppAnalyticsSkillsRoute, AppApplicationsFollowupsRoute, AppApplicationsIdRoute (+58 more)

### Community 3 - "Frontend Dependencies"
Cohesion: 0.04
Nodes (52): dependencies, class-variance-authority, clsx, cmdk, date-fns, embla-carousel-react, @hookform/resolvers, lucide-react (+44 more)

### Community 4 - "Logging Infrastructure"
Cohesion: 0.06
Nodes (34): add_request_id(), add_timestamp(), configure_logging(), get_request_id(), log_audit_event(), Inject request_id into every log entry if not already present., Inject an ISO-8601 timestamp into every log entry., Configure structlog for JSON structured logging. (+26 more)

### Community 5 - "UI Components (Separator/Sheet)"
Cohesion: 0.05
Nodes (38): Separator, SheetContent, SheetContentProps, SheetDescription, SheetFooter(), SheetHeader(), SheetOverlay, SheetTitle (+30 more)

### Community 6 - "Job Import Service"
Cohesion: 0.09
Nodes (18): check_duplicate(), detect_platform(), extract_field_from_text(), extract_job_id_from_url(), extract_tags_from_text(), normalize_for_dedup(), normalize_job(), parse_job_from_description() (+10 more)

### Community 7 - "Backend Models"
Cohesion: 0.08
Nodes (12): Job, Tests for job search, filtering, sorting, and pagination., Tests for job filtering functionality., Tests for job search functionality., Tests for job sorting functionality., Tests for job pagination functionality., Tests for job list response structure., TestJobFiltering (+4 more)

### Community 8 - "App Routes"
Cohesion: 0.09
Nodes (16): ArrayItemProps, InputProps, SectionCardProps, TextareaProps, ValidationDisplayProps, getProfile(), updateProfile(), validateProfile() (+8 more)

### Community 9 - "Frontend Route Tree"
Cohesion: 0.06
Nodes (34): Route, Route, Route, Route, Route, Route, Route, Route (+26 more)

### Community 10 - "Frontend Package Config"
Cohesion: 0.07
Nodes (29): devDependencies, eslint, eslint-config-prettier, @eslint/js, eslint-plugin-prettier, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals (+21 more)

### Community 11 - "App Routes"
Cohesion: 0.14
Nodes (18): AnalysisInsights(), AnalysisSkeleton(), ScoreMeter(), getJob(), getJobAnalysis(), getJobs(), getMatchScore(), JobSearchParams (+10 more)

### Community 12 - "Analytics Routes"
Cohesion: 0.19
Nodes (10): PageHeader(), Panel(), Stat(), statusMap, StatusPill(), PageBody(), funnel, events (+2 more)

### Community 13 - "UI Alert Dialog"
Cohesion: 0.12
Nodes (23): AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter(), AlertDialogHeader(), AlertDialogOverlay, AlertDialogTitle (+15 more)

### Community 14 - "UI Avatar & Card"
Cohesion: 0.07
Nodes (16): Avatar, AvatarFallback, AvatarImage, Checkbox, HoverCardContent, PopoverContent, Progress, RadioGroup (+8 more)

### Community 15 - "Resume API Endpoints"
Cohesion: 0.20
Nodes (25): create_resume(), create_resume_version(), delete_resume(), generate_resume(), _generate_resume_background(), get_resume(), get_resume_versions(), get_resumes() (+17 more)

### Community 16 - "Pydantic Schemas"
Cohesion: 0.15
Nodes (25): CertificationBase, CertificationCreate, CertificationResponse, CertificationUpdate, EducationBase, EducationCreate, EducationResponse, EducationUpdate (+17 more)

### Community 17 - "App Routes"
Cohesion: 0.15
Nodes (19): ScorePill(), Tag(), apiFetch(), tryRefreshToken(), getImportDetail(), createResume(), createResumeVersion(), deleteResume() (+11 more)

### Community 18 - "Auth Tests"
Cohesion: 0.09
Nodes (7): Auth endpoint tests — covers registration, login, token refresh, logout, forgot/, TestForgotResetPassword, TestLogin, TestLogout, TestRefreshToken, TestRegister, TestUserProfile

### Community 19 - "Rate Limiting"
Cohesion: 0.12
Nodes (15): add_rate_limit_headers(), check_rate_limit(), get_client_ip(), Request, RateLimiter, Rate limiting middleware and utilities for API endpoints. Implements token buck, Reset rate limit for a key (for testing or admin purposes)., Remove entries older than max_age to prevent memory leaks. (+7 more)

### Community 20 - "Auth API Core"
Cohesion: 0.18
Nodes (20): _clear_auth_cookies(), forgot_password(), logout(), Any, Request, Response, Session, User (+12 more)

### Community 21 - "TypeScript Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, jsx, lib, module, moduleResolution, noEmit, noFallthroughCasesInSwitch (+11 more)

### Community 22 - "Auth API Endpoints"
Cohesion: 0.16
Nodes (18): login_access_token(), Refresh access token using refresh token (cookie or body)., OAuth2 compatible token login, get an access token for future requests., refresh_token(), create_access_token(), create_refresh_token(), decrypt_value(), encrypt_value() (+10 more)

### Community 23 - "Components Config"
Cohesion: 0.11
Nodes (18): aliases, components, hooks, lib, ui, utils, iconLibrary, registries (+10 more)

### Community 24 - "Resume Generation Service"
Cohesion: 0.18
Nodes (13): ResumeVersion, _generate_with_gemini(), _generate_with_openrouter(), _parse_ai_response(), Resume generation service. Orchestrates AI-powered resume tailoring with validat, Parse and validate AI response into TailoredResume., Generate resume using Google Gemini., Generate resume using OpenRouter. (+5 more)

### Community 25 - "Profile Models"
Cohesion: 0.14
Nodes (10): Profile, Tests for resume generation service., Test that missing name raises validation error., Test serializing a profile with all fields., Test serializing a profile with experiences., Test parsing a valid JSON response., Test parsing JSON wrapped in markdown code fences., sample_job() (+2 more)

### Community 26 - "UI Command Components"
Cohesion: 0.12
Nodes (14): Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandSeparator, CommandShortcut() (+6 more)

### Community 27 - "App Routes"
Cohesion: 0.21
Nodes (9): Input, Label, labelVariants, useAuth(), MODELS, Route, Route, LoginPage() (+1 more)

### Community 28 - "UI Menubar"
Cohesion: 0.12
Nodes (11): Menubar, MenubarCheckboxItem, MenubarContent, MenubarItem, MenubarLabel, MenubarRadioItem, MenubarSeparator, MenubarShortcut() (+3 more)

### Community 29 - "Resume Generation Service"
Cohesion: 0.15
Nodes (14): generate_tailored_resume(), Job, Profile, Session, Convert a Profile ORM object to a text representation for the prompt., Convert a Job ORM object to a text representation for the prompt., Call async fn up to max_attempts with exponential backoff., Generate a tailored resume for a specific job.      Args:         db: Database s (+6 more)

### Community 30 - "Resume Generation Service"
Cohesion: 0.16
Nodes (11): Render a resume JSON into HTML using the specified template.     Returns the HTM, Render the minimal template., Render the technical template (skills and projects forward)., _render_minimal_template(), render_resume_html(), _render_technical_template(), Test that minimal template produces valid HTML., Test that technical template produces valid HTML. (+3 more)

### Community 31 - "App Routes"
Cohesion: 0.24
Nodes (4): AuthShell(), Button, Textarea, sections

### Community 32 - "React Contexts"
Cohesion: 0.16
Nodes (9): AuthContext, AuthContextType, AuthProvider(), User, LovableErrorOptions, LovableEvents, reportLovableError(), Window (+1 more)

### Community 33 - "Email Service"
Cohesion: 0.22
Nodes (7): EmailService, Send password reset email, Create SMTP connection with STARTTLS, Send job application status update email, Send an email using Brevo SMTP, Send email verification email, EmailStr

### Community 34 - "SiraFit Bits Components"
Cohesion: 0.20
Nodes (5): AgentDot(), MarketingShell(), NAV, NavGroup, NavItem

### Community 35 - "UI Carousel"
Cohesion: 0.14
Nodes (12): Carousel, CarouselApi, CarouselContent, CarouselContext, CarouselContextProps, CarouselItem, CarouselNext, CarouselOptions (+4 more)

### Community 36 - "Settings API"
Cohesion: 0.31
Nodes (12): AIConfigResponse, AIConfigUpdate, delete_ai_config(), get_ai_config(), Session, User, Settings API routes. Provides CRUD for user-stored AI configuration (encrypted A, Delete the user's AI configuration (clear encrypted keys and reset preferences). (+4 more)

### Community 37 - "Resume Generation Service"
Cohesion: 0.21
Nodes (8): Validate a generated resume JSON structure.     Returns (is_valid, list_of_issue, validate_resume_json(), Test that a complete resume passes validation., Test that missing required fields are caught., Test that experience entries without bullets are flagged., Test that more than 30 skills are flagged., Test that no skills fails validation., TestValidateResumeJson

### Community 38 - "Test Conftest"
Cohesion: 0.17
Nodes (12): auth_headers(), auth_tokens(), db(), override_get_db(), Shared pytest fixtures for backend tests. Uses an in-memory SQLite database for, Generate auth headers for function-scoped tests., Create all tables once per test session, then drop them., Register a user once and return the response data. (+4 more)

### Community 39 - "Applications API"
Cohesion: 0.30
Nodes (11): create_application(), get_applications(), Any, Session, User, UUID, Retrieve current user's job applications., Create a new job application and calculate initial score. (+3 more)

### Community 40 - "Dashboard API"
Cohesion: 0.18
Nodes (8): get_dashboard_stats(), Any, Session, User, Retrieve dashboard statistics for the current user., lifespan(), Application lifespan: startup and shutdown events., FastAPI

### Community 41 - "UI Form Components"
Cohesion: 0.17
Nodes (9): FormControl, FormDescription, FormFieldContext, FormFieldContextValue, FormItem, FormItemContext, FormItemContextValue, FormLabel (+1 more)

### Community 42 - "App Routes"
Cohesion: 0.21
Nodes (8): SelectContent, SelectItem, SelectLabel, SelectScrollDownButton, SelectScrollUpButton, SelectSeparator, SelectTrigger, TEMPLATES

### Community 43 - "Frontend Library Utils"
Cohesion: 0.29
Nodes (7): consumeLastCapturedError(), renderErrorPage(), fetch(), getServerEntry(), normalizeCatastrophicSsrResponse(), ServerEntry, errorMiddleware

### Community 44 - "Backend Core"
Cohesion: 0.20
Nodes (8): ASGIApp, Request, Response, Middleware to add request timing and logging, RequestTimingMiddleware, RateLimitHeaderMiddleware, Middleware to add rate limit headers to all responses., BaseHTTPMiddleware

### Community 45 - "API Endpoints"
Cohesion: 0.25
Nodes (10): get_current_user(), Any, Request, Session, User, Dependency to get the currently authenticated user.     Accepts the JWT from eit, Get current user profile., Update current user profile. (+2 more)

### Community 46 - "Resume Generation Service"
Cohesion: 0.24
Nodes (7): _calculate_ats_score(), Calculate a basic ATS readiness score., Test that a complete resume gets a high ATS score., Test that missing summary lowers the score., Test that an empty resume gets a low score., Test that keyword matching affects score., TestCalculateATSScore

### Community 47 - "App Routes"
Cohesion: 0.20
Nodes (6): EmptyState(), getImportHistory(), importJobs(), formatDate(), JobDetails(), JobData

### Community 48 - "UI Components"
Cohesion: 0.22
Nodes (8): MatchScoreCard(), MatchScoreCardProps, Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle

### Community 49 - "UI Components"
Cohesion: 0.18
Nodes (7): ChartConfig, ChartContainer, ChartContext, ChartContextProps, ChartLegendContent, ChartTooltipContent, THEMES

### Community 50 - "UI Components"
Cohesion: 0.20
Nodes (9): ContextMenuCheckboxItem, ContextMenuContent, ContextMenuItem, ContextMenuLabel, ContextMenuRadioItem, ContextMenuSeparator, ContextMenuShortcut(), ContextMenuSubContent (+1 more)

### Community 51 - "UI Components"
Cohesion: 0.20
Nodes (9): DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuRadioItem, DropdownMenuSeparator, DropdownMenuShortcut(), DropdownMenuSubContent (+1 more)

### Community 52 - "Backend Models"
Cohesion: 0.22
Nodes (6): get_password_hash(), RefreshToken, User, Create a test user for function-scoped tests., test_user(), Test that users can only access their own profiles

### Community 53 - "UI Components"
Cohesion: 0.22
Nodes (8): Table, TableBody, TableCaption, TableCell, TableFooter, TableHead, TableHeader, TableRow

### Community 54 - "UI Components"
Cohesion: 0.25
Nodes (7): Breadcrumb, BreadcrumbEllipsis(), BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator()

### Community 55 - "UI Components"
Cohesion: 0.25
Nodes (6): DrawerContent, DrawerDescription, DrawerFooter(), DrawerHeader(), DrawerOverlay, DrawerTitle

### Community 56 - "UI Components"
Cohesion: 0.25
Nodes (7): NavigationMenu, NavigationMenuContent, NavigationMenuIndicator, NavigationMenuList, NavigationMenuTrigger, navigationMenuTriggerStyle, NavigationMenuViewport

### Community 57 - "Frontend Route Tree"
Cohesion: 0.29
Nodes (6): ApiError, navigateToLogin(), getRouter(), Register, routeTree, startInstance

### Community 58 - "Security & Tokens"
Cohesion: 0.29
Nodes (6): decode_token(), Decode and validate JWT token, global_exception_handler(), Request, Global exception handler to mask internal errors., Exception

### Community 59 - "Backend Code"
Cohesion: 0.33
Nodes (6): get_database_url(), Get database URL from environment or config, Run migrations in 'offline' mode.      This configures the context with just a U, Run migrations in 'online' mode.      In this scenario we need to create an Engi, run_migrations_offline(), run_migrations_online()

### Community 60 - "Backend Tests"
Cohesion: 0.29
Nodes (4): POST /jobs/{id}/analyze should return immediately with status=processing or done, GET /jobs/{id}/analysis should 404 when no analysis exists., GET /jobs/{id}/analysis should return stored analysis., TestAnalysisAPI

### Community 61 - "UI Components"
Cohesion: 0.33
Nodes (5): ToggleGroup, ToggleGroupContext, ToggleGroupItem, Toggle, toggleVariants

### Community 62 - "Backend Core"
Cohesion: 0.33
Nodes (5): health_live(), health_ready(), Session, Liveness probe - checks if the service is running, Readiness probe - checks if the service can handle requests

### Community 63 - "UI Input & Label"
Cohesion: 0.40
Nodes (5): input-otp, InputOTP, InputOTPGroup, InputOTPSeparator, InputOTPSlot

### Community 64 - "Misc Code"
Cohesion: 0.33
Nodes (5): buildCommand, env, VITE_API_URL, framework, outputDirectory

### Community 65 - "Backend Core"
Cohesion: 0.40
Nodes (3): Config, Settings, BaseSettings

### Community 66 - "Pydantic Schemas"
Cohesion: 0.40
Nodes (4): LogoutRequest, RefreshTokenRequest, ResetPasswordRequest, VerifyEmailRequest

### Community 67 - "Backend Code"
Cohesion: 0.70
Nodes (4): analyze_match_score(), _keyword_match_score(), Job, Profile

### Community 68 - "UI Components"
Cohesion: 0.40
Nodes (4): Alert, AlertDescription, AlertTitle, alertVariants

### Community 69 - "Backend Tests"
Cohesion: 0.50
Nodes (3): Simple script to test email configuration Run: python test_email.py, Test sending a verification email, test_email()

### Community 72 - "UI Components"
Cohesion: 0.50
Nodes (3): AccordionContent, AccordionItem, AccordionTrigger

### Community 73 - "UI Components"
Cohesion: 0.67
Nodes (3): Badge(), BadgeProps, badgeVariants

## Knowledge Gaps
- **382 isolated node(s):** `Config`, `Config`, `$schema`, `style`, `rsc` (+377 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `cn()` connect `UI Alert Dialog` to `UI Components (Separator/Sheet)`, `App Routes`, `Analytics Routes`, `UI Avatar & Card`, `App Routes`, `UI Command Components`, `App Routes`, `UI Menubar`, `App Routes`, `SiraFit Bits Components`, `UI Carousel`, `UI Form Components`, `App Routes`, `UI Components`, `UI Components`, `UI Components`, `UI Components`, `UI Components`, `UI Components`, `UI Components`, `UI Components`, `UI Components`, `UI Input & Label`, `UI Components`, `UI Components`, `UI Components`, `App Routes`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `dependencies` connect `Frontend Dependencies` to `Frontend Package Config`, `UI Components`, `UI Input & Label`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Why does `Job` connect `Backend Models` to `Job API Endpoints`, `Profile API & Models`, `Logging Infrastructure`, `Resume Generation Service`, `Job Import Service`, `Applications API`, `Resume Generation Service`, `Resume API Endpoints`, `Resume Generation Service`, `Profile Models`, `Backend Tests`, `Resume Generation Service`, `Resume Generation Service`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `Job` (e.g. with `create_application()` and `get_job()`) actually correct?**
  _`Job` has 55 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Retrieve current user's job applications.`, `Create a new job application and calculate initial score.`, `Update a job application.` to the rest of the system?**
  _535 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Job API Endpoints` be split into smaller, more focused modules?**
  _Cohesion score 0.057971014492753624 - nodes in this community are weakly interconnected._
- **Should `Profile API & Models` be split into smaller, more focused modules?**
  _Cohesion score 0.06331976481230213 - nodes in this community are weakly interconnected._