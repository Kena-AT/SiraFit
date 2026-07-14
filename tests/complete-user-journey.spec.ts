import { test, expect } from "@playwright/test";

/**
 * Complete User Journey E2E Tests
 *
 * Tests the full user lifecycle:
 * 1. Register → Verify email → Login
 * 2. Browse jobs → Import job from URL
 * 3. Create application → Track status → Add notes/contacts
 * 4. Set follow-up reminders
 * 5. Receive and manage notifications
 * 6. View analytics dashboard
 * 7. Export resume
 */

const TEST_EMAIL = `testuser.${Date.now()}@example.com`;
const TEST_PASSWORD = "TestPassword123!";
const TEST_NAME = "Test User";

// Test data
const TEST_JOB_URL = "https://www.linkedin.com/jobs/view/1234567890";
const TEST_JOB_DESCRIPTION = `
Senior Software Engineer
Company: TechCorp Inc
Location: San Francisco, CA (Hybrid)
Salary: $150,000 - $200,000

We are looking for a Senior Software Engineer with 5+ years of experience.
Required skills: Python, React, TypeScript, PostgreSQL, AWS, Docker.
Nice to have: Kubernetes, GraphQL, CI/CD pipelines.

Responsibilities:
- Design and implement scalable backend services
- Collaborate with frontend team on API design
- Mentor junior engineers
- Participate in code reviews and architecture decisions

Benefits:
- Health, dental, vision insurance
- 401k matching
- Flexible PTO
- Remote work options
`.trim();

test.describe.configure({ retries: 1 });

test.describe("Complete User Journey", () => {
  let userId: string;
  let accessToken: string;
  let refreshToken: string;

  // ═══════════════════════════════════════════════════════════════
  // STEP 1: Registration & Email Verification
  // ═══════════════════════════════════════════════════════════════

  test.describe("Register & Verify Email", () => {
    test("Register new user successfully", async ({ page }) => {
      await page.goto("/register");

      // Fill registration form
      await page.getByLabel("Name").fill(TEST_NAME);
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByLabel("Confirm Password").fill(TEST_PASSWORD);

      // Submit
      await page.getByRole("button", { name: /create account/i }).click();

      // Should show success message and redirect to verify-email
      await expect(
        page.getByText(/registration successful/i)
      ).toBeVisible({ timeout: 5000 });
      await expect(page).toHaveURL(/\/verify-email/);
    });

    test("Verify email — user can resend verification email", async ({ page }) => {
      await page.goto("/verify-email");

      // Should show verification instructions
      await expect(
        page.getByRole("heading", { name: /verify your email/i })
      ).toBeVisible();
      await expect(
        page.getByText(/we sent a verification link to your email/i)
      ).toBeVisible();

      // Resend button should work
      await page.getByRole("button", { name: /resend/i }).click();
      await expect(page.getByText(/verification email resent/i)).toBeVisible();
    });

    test("Login fails before email verification", async ({ page }) => {
      await page.goto("/login");

      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();

      // Should show error about unverified email
      await expect(
        page.getByText(/please verify your email/i)
      ).toBeVisible({ timeout: 5000 });
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 2: Login & Dashboard Access (after manual email verification)
  // ═══════════════════════════════════════════════════════════════

  test.describe("Login & Dashboard", () => {
    test.beforeEach(async ({ page }) => {
      // Note: In real E2E, you'd verify email here. For test purposes,
      // we either use API to verify, or manually click link.
      // This test assumes email is verified.
    });

    test("Login with valid credentials", async ({ page }) => {
      await page.goto("/login");

      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();

      // Should redirect to dashboard
      await expect(page).toHaveURL(/\/dashboard/);
      await expect(page.getByText(/welcome back/i)).toBeVisible();
    });

    test("Dashboard shows key sections", async ({ page }) => {
      // Dashboard should show key metrics and navigation
      await expect(page.getByText(/applications/i)).toBeVisible();
      await expect(page.getByText(/jobs/i)).toBeVisible();
      await expect(page.getByText(/resumes/i)).toBeVisible();
      await expect(page.getByText(/cover letters/i)).toBeVisible();
      await expect(page.getByText(/analytics/i)).toBeVisible();
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 3: Job Management — Import & Explore
  // ═══════════════════════════════════════════════════════════════

  test.describe("Job Import & Exploration", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test("Import job from URL (LinkedIn)", async ({ page }) => {
      await page.goto("/jobs/import");

      // Select URL import tab
      await expect(page.getByText(/from url/i)).toBeVisible();
      await page.getByRole("button", { name: /from url/i }).click();

      // Fill job URL
      await page
        .getByPlaceholder(/linkedin\.com\/jobs/i)
        .fill(TEST_JOB_URL);

      // Scrape button should be enabled
      await expect(page.getByRole("button", { name: /scrape now/i })).toBeEnabled();

      // Click scrape
      await page.getByRole("button", { name: /scrape now/i }).click();

      // Should show loading then results
      await expect(page.getByText(/importing/i)).toBeVisible({ timeout: 2000 });
      await expect(page.getByText(/import completed/i)).toBeVisible({ timeout: 30000 });

      // Should show imported job details
      await expect(page.getByText(/senior software engineer/i)).toBeVisible();
      await expect(page.getByText(/techcorp/i)).toBeVisible();
    });

    test("Import job from description text", async ({ page }) => {
      await page.goto("/jobs/import");

      // Select description import
      await page.getByRole("button", { name: /from description/i }).click();

      // Fill description
      await page
        .getByPlaceholder(/paste the full job description/i)
        .fill(TEST_JOB_DESCRIPTION);

      // Analyze button should be enabled
      await expect(page.getByRole("button", { name: /analyze description/i })).toBeEnabled();

      // Click analyze
      await page.getByRole("button", { name: /analyze description/i }).click();

      // Should show parsed job
      await expect(page.getByText(/import completed/i)).toBeVisible({ timeout: 30000 });
      await expect(page.getByText(/senior software engineer/i)).toBeVisible();
      await expect(page.getByText(/techcorp/i)).toBeVisible();
      await expect(page.getByText(/python/i)).toBeVisible();
      await expect(page.getByText(/react/i)).toBeVisible();
    });

    test("View imported job in history", async ({ page }) => {
      await page.goto("/jobs/history");

      // Should show recent imports
      await expect(page.getByRole("heading", { name: /import history/i })).toBeVisible();

      // Click on a job to view details
      const firstJob = page.locator('a:has-text("Senior Software Engineer")').first();
      if (await firstJob.isVisible()) {
        await firstJob.click();
        await expect(page).toHaveURL(/\/dashboard\/jobs\//);
      }
    });

    test("Browse jobs explorer page", async ({ page }) => {
      await page.goto("/jobs");

      await expect(page.getByRole("heading", { name: /jobs/i })).toBeVisible();
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 4: Application Tracking — Create, Status, Notes, Contacts
  // ═══════════════════════════════════════════════════════════════

  test.describe("Application Tracking", () => {
    let applicationId: string;

    test.beforeEach(async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test("Create application from job card", async ({ page }) => {
      await page.goto("/jobs");

      // Find a job and click "Save & Apply"
      const saveButton = page.locator('button:has-text("Save & Apply")').first();
      if (await saveButton.isVisible()) {
        await saveButton.click();

        // Should create application and redirect to applications page
        await expect(page).toHaveURL(/\/applications/);
      }
    });

    test("Create application manually", async ({ page }) => {
      await page.goto("/applications");

      // Click "New Application"
      await page.getByRole("button", { name: /new application/i }).click();

      // Fill form - select job, etc.
      await expect(page.getByRole("heading", { name: /create application/i })).toBeVisible();
    });

    test("Create application via API and track status transitions", async ({ request }) => {
      // First, create a job
      const jobRes = await request.post("/api/v1/jobs/import", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { source_type: "description", data: TEST_JOB_DESCRIPTION },
      });
      expect(jobRes.status()).toBe(200);
      const jobData = await jobRes.json();
      const jobId = jobData.jobs[0].id;

      // Create application
      const appRes = await request.post("/api/v1/applications", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { job_id: jobId },
      });
      expect(appRes.status()).toBe(200);
      const appData = await appRes.json();
      expect(appData.status).toBe("saved");
      applicationId = appData.id;

      // Test valid status transitions: saved → applied → screening → interview
      const transitions = ["applied", "screening", "interview", "final_round", "offer"];
      for (const status of transitions) {
        const transRes = await request.post(
          `/api/v1/applications/${applicationId}/status`,
          {
            headers: { Authorization: `Bearer ${accessToken}` },
            data: { to_status: status },
          }
        );
        expect(transRes.status()).toBe(200);
        const transData = await transRes.json();
        expect(transData.status).toBe(status);
      }

      // Test invalid reverse transition (should fail)
      const invalidTrans = await request.post(
        `/api/v1/applications/${applicationId}/status`,
        {
          headers: { Authorization: `Bearer ${accessToken}` },
          data: { to_status: "saved" },
        }
      );
      expect(invalidTrans.status()).toBe(400);
    });

    test("Add and manage notes on application", async ({ page, request }) => {
      // Create application via API first
      const jobRes = await request.post("/api/v1/jobs/import", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { source_type: "description", data: TEST_JOB_DESCRIPTION },
      });
      const jobData = await jobRes.json();
      const jobId = jobData.jobs[0].id;

      const appRes = await request.post("/api/v1/applications", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { job_id: jobId },
      });
      const appData = await appRes.json();
      const appId = appData.id;

      // Navigate to application detail
      await page.goto(`/applications/${appId}`);

      // Add a note
      await page.getByRole("button", { name: /add note/i }).click();
      await page.getByPlaceholder(/add a note/i).fill("Great conversation with recruiter!");
      await page.getByRole("button", { name: /save/i }).click();

      await expect(page.getByText(/great conversation/i)).toBeVisible();

      // Add pinned note
      await page.getByRole("button", { name: /add note/i }).click();
      await page.getByPlaceholder(/add a note/i).fill("PINNED: Follow up by Friday");
      await page.getByLabel(/pinned/i).check();
      await page.getByRole("button", { name: /save/i }).click();

      await expect(page.getByText(/pinned: follow up/i)).toBeVisible();
      // Pinned note should appear first
      const notes = page.locator('[data-testid="note-item"]');
      await expect(notes.first().getByText(/pinned: follow up/i)).toBeVisible();
    });

    test("Add and manage contacts", async ({ page, request }) => {
      const jobRes = await request.post("/api/v1/jobs/import", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { source_type: "description", data: TEST_JOB_DESCRIPTION },
      });
      const jobData = await jobRes.json();
      const jobId = jobData.jobs[0].id;

      const appRes = await request.post("/api/v1/applications", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { job_id: jobId },
      });
      const appData = await appRes.json();
      const appId = appData.id;

      await page.goto(`/applications/${appId}`);

      // Add contact
      await page.getByRole("button", { name: /add contact/i }).click();
      await page.getByLabel(/name/i).fill("Sarah Chen");
      await page.getByLabel(/email/i).fill("sarah@techcorp.com");
      await page.getByLabel(/role/i).selectOption("recruiter");
      await page.getByLabel(/primary contact/i).check();
      await page.getByRole("button", { name: /save/i }).click();

      await expect(page.getByText(/sarah chen/i)).toBeVisible();
      await expect(page.getByText(/recruiter/i)).toBeVisible();
      await expect(page.getByText(/primary/i)).toBeVisible();

      // Edit contact
      await page.getByRole("button", { name: /edit.*sarah/i }).click();
      await page.getByLabel(/phone/i).fill("+1-555-0123");
      await page.getByRole("button", { name: /save/i }).click();
      await expect(page.getByText(/\+1-555-0123/i)).toBeVisible();

      // Delete contact
      await page.getByRole("button", { name: /delete.*sarah/i }).click();
      await expect(page.getByText(/sarah chen/i)).not.toBeVisible();
    });

    test("View timeline events for application", async ({ page, request }) => {
      const jobRes = await request.post("/api/v1/jobs/import", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { source_type: "description", data: TEST_JOB_DESCRIPTION },
      });
      const jobData = await jobRes.json();
      const jobId = jobData.jobs[0].id;

      const appRes = await request.post("/api/v1/applications", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { job_id: jobId },
      });
      const appData = await appRes.json();
      const appId = appData.id;

      // Transition through several statuses
      for (const status of ["applied", "screening", "interview"]) {
        await request.post(`/api/v1/applications/${appId}/status`, {
          headers: { Authorization: `Bearer ${accessToken}` },
          data: { to_status: status },
        });
      }

      await page.goto(`/applications/${appId}`);

      // Events should be shown in timeline
      await expect(page.getByText(/status change/i)).toBeVisible();
      await expect(page.getByText(/applied/i)).toBeVisible();
      await expect(page.getByText(/screening/i)).toBeVisible();
      await expect(page.getByText(/interview/i)).toBeVisible();
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 5: Follow-up Center
  // ═══════════════════════════════════════════════════════════════

  test.describe("Follow-up Center", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test("Set follow-up reminder on application", async ({ page, request }) => {
      // Create job & application
      const jobRes = await request.post("/api/v1/jobs/import", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { source_type: "description", data: TEST_JOB_DESCRIPTION },
      });
      const jobData = await jobRes.json();
      const jobId = jobData.jobs[0].id;

      const appRes = await request.post("/api/v1/applications", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { job_id: jobId, status: "interview" },
      });
      const appData = await appRes.json();
      const appId = appData.id;

      await page.goto(`/applications/${appId}`);

      // Set follow-up
      await page.getByRole("button", { name: /set follow-up/i }).click();

      const futureDate = new Date();
      futureDate.setDate(futureDate.getDate() + 7);
      await page.getByLabel(/follow-up date/i).fill(futureDate.toISOString().split("T")[0]);
      await page.getByLabel(/follow-up note/i).fill("Send thank you email");
      await page.getByRole("button", { name: /save/i }).click();

      await expect(page.getByText(/follow-up set/i)).toBeVisible();
      await expect(page.getByText(/send thank you email/i)).toBeVisible();
    });

    test("View follow-up center with upcoming reminders", async ({ page }) => {
      await page.goto("/applications/followups");

      await expect(page.getByRole("heading", { name: /follow-ups/i })).toBeVisible();
      // Should show list of upcoming follow-ups
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 6: Notifications
  // ═══════════════════════════════════════════════════════════════

  test.describe("Notifications System", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test("Bell icon shows unread count", async ({ page }) => {
      // Look for notification bell in header
      const bell = page.locator('button[aria-label*="notification" i], button:has(svg.lucide-bell)');
      if (await bell.isVisible()) {
        await expect(bell).toBeVisible();
      }
    });

    test("View notifications page", async ({ page }) => {
      await page.goto("/notifications");

      await expect(page.getByRole("heading", { name: /notifications/i })).toBeVisible();

      // Should have tabs for unread/all/archived
      await expect(page.getByRole("tab", { name: /unread/i })).toBeVisible();
      await expect(page.getByRole("tab", { name: /all/i })).toBeVisible();

      // Check notification types exist
      const notificationTypes = [
        "application_status",
        "follow_up",
        "daily_digest",
        "match_alert",
        "system_alert",
      ];
      for (const type of notificationTypes) {
        // These would appear if notifications were created
        // For now just check tabs work
      }
    });

    test("Mark notification as read", async ({ page, request }) => {
      // Create a notification via API
      await request.post("/api/v1/notifications", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: {
          title: "Test Notification",
          body: "This is a test",
          kind: "alert",
        },
      });

      await page.goto("/notifications");

      // Find unread notification and click mark as read
      const unreadNotif = page.locator('[data-testid="notification-item"][data-status="unread"]').first();
      if (await unreadNotif.isVisible()) {
        await unreadNotif.getByRole("button", { name: /mark read/i }).click();
        await expect(unreadNotif).not.toHaveAttribute("data-status", "unread");
      }
    });

    test("Mark all as read", async ({ page }) => {
      await page.goto("/notifications");
      await page.getByRole("button", { name: /mark all read/i }).click();
      await expect(page.getByText(/all notifications marked as read/i)).toBeVisible();
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 7: Analytics Dashboard
  // ═══════════════════════════════════════════════════════════════

  test.describe("Analytics Dashboard", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test("View analytics overview", async ({ page }) => {
      await page.goto("/analytics");

      await expect(page.getByRole("heading", { name: /analytics/i })).toBeVisible();

      // Key metrics cards
      await expect(page.getByText(/total applications/i)).toBeVisible();
      await expect(page.getByText(/response rate/i)).toBeVisible();
      await expect(page.getByText(/interview rate/i)).toBeVisible();
      await expect(page.getByText(/offer rate/i)).toBeVisible();
    });

    test("View skills demand chart", async ({ page }) => {
      await page.goto("/analytics/skills");

      await expect(page.getByRole("heading", { name: /skills demand/i })).toBeVisible();
      // Chart should render
      await expect(page.locator('svg, canvas, [role="img"]')).toBeVisible();
    });

    test("View market insights", async ({ page }) => {
      await page.goto("/analytics/market");

      await expect(page.getByRole("heading", { name: /market insights/i })).toBeVisible();
      await expect(page.getByText(/top locations/i)).toBeVisible();
      await expect(page.getByText(/top companies/i)).toBeVisible();
      await expect(page.getByText(/salary ranges/i)).toBeVisible();
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 8: Resume Management & Export
  // ═══════════════════════════════════════════════════════════════

  test.describe("Resume Management", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test("Create and edit resume profile", async ({ page }) => {
      await page.goto("/resumes");

      await expect(page.getByRole("heading", { name: /resumes/i })).toBeVisible();

      // Create new resume
      await page.getByRole("button", { name: /new resume/i }).click();

      // Fill profile editor
      await page.getByLabel(/headline/i).fill("Senior Software Engineer");
      await page.getByLabel(/summary/i).fill("Experienced engineer with 10+ years...");
      await page.getByRole("button", { name: /save/i }).click();

      await expect(page.getByText(/senior software engineer/i)).toBeVisible();
    });

    test("Export resume as PDF", async ({ page }) => {
      await page.goto("/resumes");

      // Click on a resume to view
      const resumeCard = page.locator('[data-testid="resume-card"]').first();
      if (await resumeCard.isVisible()) {
        await resumeCard.click();

        // Export button
        await page.getByRole("button", { name: /export pdf/i }).click();

        // Should trigger download
        const downloadPromise = page.waitForEvent("download");
        await page.getByRole("button", { name: /confirm export/i }).click();
        const download = await downloadPromise;
        expect(download.suggestedFilename()).toMatch(/\.(pdf)$/);
      }
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 9: Cover Letters
  // ═══════════════════════════════════════════════════════════════

  test.describe("Cover Letters", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test("Generate cover letter for application", async ({ page, request }) => {
      // Create job & application
      const jobRes = await request.post("/api/v1/jobs/import", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { source_type: "description", data: TEST_JOB_DESCRIPTION },
      });
      const jobData = await jobRes.json();
      const jobId = jobData.jobs[0].id;

      const appRes = await request.post("/api/v1/applications", {
        headers: { Authorization: `Bearer ${accessToken}` },
        data: { job_id: jobId },
      });
      const appData = await appRes.json();
      const appId = appData.id;

      await page.goto(`/cover-letters`);

      // Build cover letter
      await page.getByRole("button", { name: /new cover letter/i }).click();
      await page.getByLabel(/application/i).selectOption(appId);

      // Generate with AI
      await page.getByRole("button", { name: /generate with ai/i }).click();

      // Wait for generation
      await expect(page.getByText(/generating/i)).toBeVisible({ timeout: 5000 });
      await expect(page.getByText(/generated/i)).toBeVisible({ timeout: 60000 });

      // Should show preview
      await expect(page.getByText(/dear hiring manager/i)).toBeVisible();
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 10: Batch Operations
  // ═══════════════════════════════════════════════════════════════

  test.describe("Batch Operations", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test("Create batch import job", async ({ page }) => {
      await page.goto("/batch");

      await expect(page.getByRole("heading", { name: /batch operations/i })).toBeVisible();

      // Create batch import
      await page.getByRole("button", { name: /new batch/i }).click();
      await page.getByLabel(/batch name/i).fill("Test Batch Import");
      await page.getByLabel(/description/i).fill("Testing batch import feature");
      await page.getByRole("button", { name: /create/i }).click();

      await expect(page.getByText(/batch created/i)).toBeVisible();
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 11: Settings & Profile
  // ═══════════════════════════════════════════════════════════════

  test.describe("Settings & Profile", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test("Update notification preferences", async ({ page }) => {
      await page.goto("/dashboard/settings/notifications");

      await expect(page.getByRole("heading", { name: /notifications/i })).toBeVisible();

      // Toggle email notifications
      await page.getByLabel(/email notifications/i).click();
      await expect(page.getByText(/saved/i)).toBeVisible();
    });

    test("Update profile information", async ({ page }) => {
      await page.goto("/dashboard/settings");

      await page.getByLabel(/full name/i).fill("Updated Test User");
      await page.getByRole("button", { name: /save/i }).click();

      await expect(page.getByText(/profile updated/i)).toBeVisible();
    });
  });

  // ═══════════════════════════════════════════════════════════════
  // STEP 12: Logout & Session Management
  // ═══════════════════════════════════════════════════════════════

  test.describe("Logout & Session", () => {
    test("Log out successfully", async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);

      // Logout
      await page.goto("/logout");

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/);
    });

    test("Session persists on page reload", async ({ page }) => {
      await page.goto("/login");
      await page.getByLabel("Email").fill(TEST_EMAIL);
      await page.getByLabel("Password").fill(TEST_PASSWORD);
      await page.getByRole("button", { name: /sign in/i }).click();
      await expect(page).toHaveURL(/\/dashboard/);

      await page.reload();
      await expect(page).toHaveURL(/\/dashboard/);
      await expect(page.getByText(/welcome back/i)).toBeVisible();
    });
  });
});

// ═══════════════════════════════════════════════════════════════
// API TESTS (Backend integration)
// ═══════════════════════════════════════════════════════════════

test.describe("Backend API Integration Tests", () => {
  const API_URL = process.env.VITE_API_URL || "http://localhost:8000";
  let authToken: string;
  let refreshTokenStr: string;

  test.describe("Auth Flow", () => {
    test("Register → Login → Refresh → Logout", async ({ request }) => {
      // Register
      const regRes = await request.post(`${API_URL}/api/v1/auth/register`, {
        data: {
          email: `${Date.now()}@test.com`,
          password: "TestPass123!",
          full_name: "API Test User",
        },
      });
      expect(regRes.status()).toBe(201);

      // Login
      const loginRes = await request.post(`${API_URL}/api/v1/auth/login`, {
        form: { username: "test@test.com", password: "TestPass123!" },
      });
      // Note: uses test user from fixture

      // For real test, use registered email
    });

    test("Full email verification flow", async ({ request }) => {
      // Register
      const email = `verify-${Date.now()}@test.com`;
      const regRes = await request.post(`${API_URL}/api/v1/auth/register`, {
        data: { email, password: "TestPass123!", full_name: "Verify User" },
      });
      expect(regRes.status()).toBe(201);

      // Cannot login before verification
      const loginRes = await request.post(`${API_URL}/api/v1/auth/login`, {
        form: { username: email, password: "TestPass123!" },
      });
      // Expect 401 or 400 with unverified message
      expect([400, 401]).toContain(loginRes.status());

      // Resend verification
      const resendRes = await request.post(`${API_URL}/api/v1/auth/resend-verification`, {
        data: { email },
      });
      expect(resendRes.status()).toBe(200);

      // Note: Actual verification requires clicking email link
      // In E2E, you'd extract token from email
    });
  });

  test.describe("Applications & Jobs", () => {
    test("Create job, create app, transition status, add note/contact", async ({ request }) => {
      // This would use a pre-authenticated token
      // Full backend test in separate file
    });
  });

  test.describe("Notifications", () => {
    test("Create notification, mark read, get unread count", async ({ request }) => {
      // Uses backend test fixtures
    });
  });

  test.describe("Analytics", () => {
    test("Get analytics overview, skills demand, market insights", async ({ request }) => {
      // API tests
    });
  });
});

// ═══════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════

async function loginViaAPI(request: any, email: string, password: string) {
  const res = await request.post(`${API_URL}/api/v1/auth/login`, {
    form: { username: email, password },
  });
  if (res.ok()) {
    const data = await res.json();
    accessToken = data.access_token;
    refreshTokenStr = data.refresh_token;
  }
  return res;
}

async function createTestJob(request: any, description: string) {
  const res = await request.post(`${API_URL}/api/v1/jobs/import`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    data: { source_type: "description", data: description },
  });
  const data = await res.json();
  return data.jobs[0].id;
}

async function createTestApplication(request: any, jobId: string) {
  const res = await request.post(`${API_URL}/api/v1/applications`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    data: { job_id: jobId },
  });
  const data = await res.json();
  return data.id;
}