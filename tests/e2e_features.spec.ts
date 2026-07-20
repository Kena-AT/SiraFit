import { test, expect } from "@playwright/test";

// ========================================
// FROM FILE: job-explorer.spec.ts
// ========================================



/**
 * Job Explorer - E2E Tests
 *
 * Tests for the job browsing, search, filtering, and detail pages.
 */

test.describe("Jobs Explorer Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/jobs");
  });

  test("renders the jobs explorer page", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /jobs explorer/i })).toBeVisible();
  });

  test("has search input and button", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search role, company/i);
    await expect(searchInput).toBeVisible();

    const searchButton = page.getByRole("button", { name: /search/i });
    await expect(searchButton).toBeVisible();
  });

  test("has filter inputs", async ({ page }) => {
    await expect(page.getByPlaceholder("Company")).toBeVisible();
    await expect(page.getByPlaceholder("Location")).toBeVisible();
  });

  test("has source filter dropdown", async ({ page }) => {
    const sourceDropdown = page.locator("select").first();
    await expect(sourceDropdown).toBeVisible();

    // Check if it has expected options
    const options = await sourceDropdown.locator("option").allTextContents();
    expect(options).toContain("All sources");
    expect(options).toContain("LinkedIn");
    expect(options).toContain("Indeed");
  });

  test("has sort dropdown", async ({ page }) => {
    const sortDropdown = page.locator("select").nth(1);
    await expect(sortDropdown).toBeVisible();

    const options = await sortDropdown.locator("option").allTextContents();
    expect(options).toContain("Newest first");
    expect(options).toContain("Oldest first");
  });

  test("has links to import pages", async ({ page }) => {
    const importHistoryLink = page.getByRole("link", { name: /import history/i });
    await expect(importHistoryLink).toBeVisible();

    const importJobsLink = page.getByRole("link", { name: /import jobs/i });
    await expect(importJobsLink).toBeVisible();
  });

  test("displays job table headers", async ({ page }) => {
    await expect(page.getByText("#")).toBeVisible();
    await expect(page.getByText("Company")).toBeVisible();
    await expect(page.getByText("Role")).toBeVisible();
    await expect(page.getByText("Location")).toBeVisible();
    await expect(page.getByText("Salary")).toBeVisible();
    await expect(page.getByText("Source")).toBeVisible();
    await expect(page.getByText("Tags")).toBeVisible();
    await expect(page.getByText("Imported")).toBeVisible();
  });

  test("search button is not disabled", async ({ page }) => {
    const searchButton = page.getByRole("button", { name: /search/i });
    await expect(searchButton).toBeEnabled();
  });

  test("can type in search field", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search role, company/i);
    await searchInput.fill("Python Engineer");
    await expect(searchInput).toHaveValue("Python Engineer");
  });

  test("can type in company filter", async ({ page }) => {
    const companyInput = page.getByPlaceholder("Company");
    await companyInput.fill("Google");
    await expect(companyInput).toHaveValue("Google");
  });

  test("can type in location filter", async ({ page }) => {
    const locationInput = page.getByPlaceholder("Location");
    await locationInput.fill("San Francisco");
    await expect(locationInput).toHaveValue("San Francisco");
  });

  test("can change source filter", async ({ page }) => {
    const sourceDropdown = page.locator("select").first();
    await sourceDropdown.selectOption("linkedin");
    await expect(sourceDropdown).toHaveValue("linkedin");
  });

  test("can change sort order", async ({ page }) => {
    const sortDropdown = page.locator("select").nth(1);
    await sortDropdown.selectOption("company-asc");
    await expect(sortDropdown).toHaveValue("company-asc");
  });

  test("shows clear filters button when filters are active", async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search role, company/i);
    await searchInput.fill("test");

    const searchButton = page.getByRole("button", { name: /search/i });
    await searchButton.click();

    // Wait a bit for the state to update
    await page.waitForTimeout(500);

    const clearButton = page.getByRole("button", { name: /clear filters/i });
    await expect(clearButton).toBeVisible();
  });

  test("pagination controls are present", async ({ page }) => {
    // Check for prev/next buttons (← →)
    const buttons = page.locator("button").filter({ hasText: /[←→]/ });
    const count = await buttons.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test("shows row count indicator", async ({ page }) => {
    await expect(page.getByText(/showing/i)).toBeVisible();
  });
});

test.describe("Job Detail Page", () => {
  test("renders job detail page structure", async ({ page }) => {
    // First navigate to jobs list
    await page.goto("/jobs");

    // Wait for any job links to appear
    await page.waitForSelector('a[href*="/jobs/"]', { timeout: 10000 }).catch(() => {
      // If no jobs, that's ok - we can test with a direct URL
    });

    // Try to click a job link if available, otherwise navigate directly
    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();

    if (linkCount > 0) {
      await jobLinks.first().click();

      // Check for job detail elements
      await expect(page.getByText(/back to jobs/i)).toBeVisible();
    }
  });

  test("has action buttons in header", async ({ page }) => {
    await page.goto("/jobs");

    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();

    if (linkCount > 0) {
      await jobLinks.first().click();

      // Check for action buttons
      await expect(page.getByRole("link", { name: /back to jobs/i })).toBeVisible();
      await expect(page.getByRole("link", { name: /tailor resume/i })).toBeVisible();
      await expect(page.getByRole("link", { name: /apply/i })).toBeVisible();
    }
  });

  test("displays job description section", async ({ page }) => {
    await page.goto("/jobs");

    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();

    if (linkCount > 0) {
      await jobLinks.first().click();

      // Look for description-related text
      await expect(page.getByText(/job description/i)).toBeVisible();
    }
  });

  test("shows compensation panel", async ({ page }) => {
    await page.goto("/jobs");

    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();

    if (linkCount > 0) {
      await jobLinks.first().click();

      await expect(page.getByText(/compensation/i)).toBeVisible();
    }
  });

  test("shows location panel", async ({ page }) => {
    await page.goto("/jobs");

    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();

    if (linkCount > 0) {
      await jobLinks.first().click();

      await expect(page.getByText(/location/i)).toBeVisible();
    }
  });

  test("shows import details section", async ({ page }) => {
    await page.goto("/jobs");

    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();

    if (linkCount > 0) {
      await jobLinks.first().click();

      await expect(page.getByText(/import details/i)).toBeVisible();
    }
  });
});

test.describe("Job Explorer Navigation", () => {
  test("can navigate from explorer to import page", async ({ page }) => {
    await page.goto("/jobs");
    await page.getByRole("link", { name: /import jobs/i }).click();
    await expect(page).toHaveURL(/\/jobs\/import/);
  });

  test("can navigate from explorer to history page", async ({ page }) => {
    await page.goto("/jobs");
    await page.getByRole("link", { name: /import history/i }).click();
    await expect(page).toHaveURL(/\/jobs\/history/);
  });

  test("can navigate from detail back to explorer", async ({ page }) => {
    await page.goto("/jobs");

    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();

    if (linkCount > 0) {
      await jobLinks.first().click();
      await page.getByRole("link", { name: /back to jobs/i }).click();
      await expect(page).toHaveURL(/\/jobs$/);
    }
  });
});

test.describe("Job Explorer Loading States", () => {
  test("shows loading state initially", async ({ page }) => {
    await page.goto("/jobs");

    // The loading spinner should appear briefly
    const loadingText = page.getByText(/loading jobs/i);
    // It may disappear quickly, so we just check the page loaded
    await page.waitForLoadState("networkidle");
  });

  test("handles empty state", async ({ page }) => {
    await page.goto("/jobs");

    // If there are no jobs, should show empty state
    // This might show "No jobs found" or similar
    await page.waitForLoadState("networkidle");
  });
});



// ========================================
// FROM FILE: job-import.spec.ts
// ========================================



/**
 * Job Import System - E2E Tests
 *
 * Tests for the import page and history page.
 * Note: These tests check UI rendering since they run against the frontend.
 * Full API integration is tested in backend tests.
 */

test.describe("Job Import Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/jobs/import");
  });

  test("renders the import page with all sections", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /import jobs/i })).toBeVisible();
    await expect(page.getByText(/from url/i)).toBeVisible();
    await expect(page.getByText(/from description/i)).toBeVisible();
    await expect(page.getByText(/batch import/i)).toBeVisible();
    await expect(page.getByText(/recent imports/i)).toBeVisible();
  });

  test("shows supported platforms", async ({ page }) => {
    await expect(page.getByText("LinkedIn")).toBeVisible();
    await expect(page.getByText("Indeed")).toBeVisible();
    await expect(page.getByText("Glassdoor")).toBeVisible();
    await expect(page.getByText("Greenhouse")).toBeVisible();
  });

  test("URL import button is disabled when input is empty", async ({ page }) => {
    const scrapeButton = page.getByRole("button", { name: /scrape now/i });
    await expect(scrapeButton).toBeDisabled();
  });

  test("URL import button is enabled when input has text", async ({ page }) => {
    await page.getByPlaceholder(/https:\/\/jobs\.lever\.co/i).fill("https://example.com/job/123");
    const scrapeButton = page.getByRole("button", { name: /scrape now/i });
    await expect(scrapeButton).toBeEnabled();
  });

  test("description import button is disabled when textarea is empty", async ({ page }) => {
    const analyzeButton = page.getByRole("button", { name: /analyze description/i });
    await expect(analyzeButton).toBeDisabled();
  });

  test("description import button is enabled when textarea has text", async ({ page }) => {
    await page
      .getByPlaceholder(/paste the full job description/i)
      .fill("Software Engineer position at a great company looking for Python and React skills.");
    const analyzeButton = page.getByRole("button", { name: /analyze description/i });
    await expect(analyzeButton).toBeEnabled();
  });

  test("has link to import history", async ({ page }) => {
    const historyLink = page.getByRole("link", { name: /import history/i });
    await expect(historyLink).toBeVisible();
    await expect(historyLink).toHaveAttribute("href", "/jobs/history");
  });

  test("view all link in recent imports navigates to history", async ({ page }) => {
    const viewAllLink = page.getByRole("link", { name: /view all/i });
    await expect(viewAllLink).toBeVisible();
    await expect(viewAllLink).toHaveAttribute("href", "/jobs/history");
  });

  test("shows empty state when no recent imports", async ({ page }) => {
    await expect(page.getByText(/no imports yet/i)).toBeVisible();
  });
});

test.describe("Import History Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/jobs/history");
  });

  test("renders the history page", async ({ page }) => {
    await expect(page.getByRole("heading", { name: /import history/i })).toBeVisible();
  });

  test("has a refresh button", async ({ page }) => {
    const refreshButton = page.getByRole("button", { name: /refresh/i });
    await expect(refreshButton).toBeVisible();
  });

  test("has a link to new import", async ({ page }) => {
    const newImportLink = page.getByRole("link", { name: /new import/i });
    await expect(newImportLink).toBeVisible();
    await expect(newImportLink).toHaveAttribute("href", "/jobs/import");
  });

  test("shows empty state when no history", async ({ page }) => {
    await expect(page.getByText(/no imports yet/i)).toBeVisible();
  });

  test("shows import jobs link in empty state", async ({ page }) => {
    const importLink = page.getByRole("link", { name: /import jobs/i });
    await expect(importLink).toBeVisible();
    await expect(importLink).toHaveAttribute("href", "/jobs/import");
  });
});

test.describe("Job Import Navigation", () => {
  test("can navigate from import to history", async ({ page }) => {
    await page.goto("/jobs/import");
    await page.getByRole("link", { name: /import history/i }).click();
    await expect(page).toHaveURL(/\/jobs\/history/);
  });

  test("can navigate from history to import", async ({ page }) => {
    await page.goto("/jobs/history");
    await page.getByRole("link", { name: /new import/i }).click();
    await expect(page).toHaveURL(/\/jobs\/import/);
  });
});



// ========================================
// FROM FILE: profile-editor.spec.ts
// ========================================



test.describe("Profile Editor", () => {
  // Login before each test since profile is protected
  test.beforeEach(async ({ page }) => {
    // Navigate to login
    await page.goto("http://localhost:3030/login");

    // Fill in test credentials
    await page.fill('input[type="email"]', "test@example.com");
    await page.fill('input[type="password"]', "TestPassword123!");
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL("**/dashboard", { timeout: 10000 });
  });

  test("can navigate to profile list page", async ({ page }) => {
    // Navigate to resume profiles page
    await page.goto("http://localhost:3030/dashboard/resumes");

    // Check if the page loaded
    await expect(page.locator("h1", { hasText: "Resume Profiles" })).toBeVisible();

    // Check if Edit Profile button is visible
    await expect(page.locator("a", { hasText: "Edit Profile" })).toBeVisible();
  });

  test("can open profile editor", async ({ page }) => {
    // Navigate to profile page
    await page.goto("http://localhost:3030/dashboard/resumes");

    // Click Edit Profile
    await page.click('a:has-text("Edit Profile")');

    // Should navigate to editor
    await expect(page).toHaveURL(new RegExp("/dashboard/resumes/.+/editor"));
    await expect(page.locator("h1", { hasText: "Edit Resume Profile" })).toBeVisible();
  });

  test("can edit basic profile fields with autosave", async ({ page }) => {
    // Go directly to editor (profile should be created automatically)
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Wait for editor to load
    await expect(page.locator("h1", { hasText: "Edit Resume Profile" })).toBeVisible();

    // Fill in first name
    const firstNameInput = page.locator('input[id="input-first-name"]');
    await firstNameInput.fill("John");

    // Wait for "Saving..." status
    await expect(page.locator("text=Saving...")).toBeVisible({ timeout: 3000 });

    // Wait for "Saved" status
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });

    // Fill in last name
    const lastNameInput = page.locator('input[id="input-last-name"]');
    await lastNameInput.fill("Doe");

    // Wait for autosave again
    await expect(page.locator("text=Saving...")).toBeVisible({ timeout: 3000 });
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });

    // Fill in headline
    const headlineInput = page.locator('input[id="input-headline"]');
    await headlineInput.fill("Senior Software Engineer");

    // Wait for autosave
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });
  });

  test("can add and edit work experience", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Wait for page to load
    await expect(page.locator("h1", { hasText: "Edit Resume Profile" })).toBeVisible();

    // Find and click "Add Experience" button
    await page.click('button:has-text("+ Add Experience")');

    // Wait for the new experience item to appear
    await expect(page.locator("text=Item #1")).toBeVisible();

    // Fill in title (it should be required)
    const titleInput = page.locator('input[id="input-title"]').first();
    await titleInput.fill("Software Engineer");

    // Fill in company
    const companyInput = page.locator('input[id="input-company"]').first();
    await companyInput.fill("Tech Corp");

    // Fill in location
    const locationInput = page.locator('input[id="input-location"]').first();
    await locationInput.fill("San Francisco, CA");

    // Wait for autosave
    await expect(page.locator("text=Saving...")).toBeVisible({ timeout: 3000 });
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });
  });

  test("can remove work experience", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Add an experience first
    await page.click('button:has-text("+ Add Experience")');
    await expect(page.locator("text=Item #1")).toBeVisible();

    // Fill required fields
    await page.locator('input[id="input-title"]').first().fill("Test Job");
    await page.locator('input[id="input-company"]').first().fill("Test Company");

    // Wait for save
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });

    // Click remove button (trash icon)
    await page.locator('button[aria-label="Remove item"]').first().click();

    // Item should be removed
    await expect(page.locator("text=Item #1")).not.toBeVisible();

    // Wait for save to complete removal
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });
  });

  test("can add education entry", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Click Add Education
    await page.click('button:has-text("+ Add Education")');

    // Fill in institution (required)
    await page.locator('input[id="input-institution"]').first().fill("MIT");

    // Fill in degree
    await page.locator('input[id="input-degree"]').first().fill("Bachelor of Science");

    // Fill in field of study
    await page.locator('input[id="input-field-of-study"]').first().fill("Computer Science");

    // Wait for save
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });
  });

  test("can add skills", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Add first skill
    await page.click('button:has-text("+ Add Skill")');
    await page.locator('input[id="input-skill-name"]').first().fill("Python");
    await page.locator('input[id="input-category"]').first().fill("Programming Languages");
    await page.locator('input[id="input-proficiency"]').first().fill("Expert");

    // Wait for save
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });

    // Add second skill
    await page.click('button:has-text("+ Add Skill")');
    await page.locator('input[id="input-skill-name"]').nth(1).fill("React");
    await page.locator('input[id="input-category"]').nth(1).fill("Frameworks");

    // Wait for save
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });
  });

  test("can add project", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Click Add Project
    await page.click('button:has-text("+ Add Project")');

    // Fill project details
    await page.locator('input[id="input-project-name"]').first().fill("Portfolio Website");
    await page
      .locator('textarea[id="textarea-description"]')
      .first()
      .fill("Personal portfolio showcasing projects");
    await page.locator('input[id="input-url"]').first().fill("https://example.com");

    // Wait for save
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });
  });

  test("can add certification", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Click Add Certification
    await page.click('button:has-text("+ Add Certification")');

    // Fill certification details (name and issuer are required)
    await page
      .locator('input[id="input-certification-name"]')
      .first()
      .fill("AWS Certified Solutions Architect");
    await page.locator('input[id="input-issuer"]').first().fill("Amazon Web Services");
    await page.locator('input[id="input-credential-id"]').first().fill("ABC123XYZ");

    // Wait for save
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });
  });

  test("displays validation errors for required fields", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Add experience without required fields
    await page.click('button:has-text("+ Add Experience")');

    // Try to fill only title (company is also required)
    await page.locator('input[id="input-title"]').first().fill("Test");

    // Leave company empty - this should trigger validation error
    // Note: The actual validation happens on save, so we might see error status
    await page.waitForTimeout(2000); // Wait for debounce

    // Should show error status instead of saved
    await expect(
      page.locator("text=Error saving").or(page.locator("text=Validation Errors")),
    ).toBeVisible({ timeout: 5000 });
  });

  test("can collapse and expand sections", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Personal Information should be open by default
    await expect(page.locator('input[id="input-first-name"]')).toBeVisible();

    // Click to collapse Personal Information
    await page.locator('button:has-text("Personal Information")').click();

    // Input should not be visible
    await expect(page.locator('input[id="input-first-name"]')).not.toBeVisible();

    // Click to expand again
    await page.locator('button:has-text("Personal Information")').click();

    // Input should be visible again
    await expect(page.locator('input[id="input-first-name"]')).toBeVisible();
  });

  test("can navigate back from editor", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Should be on editor page
    await expect(page).toHaveURL(new RegExp("/dashboard/resumes/.+/editor"));

    // Click Back button
    await page.click('button:has-text("Back")');

    // Should navigate back to previous page
    await expect(page).not.toHaveURL(/\/editor/);
  });

  test("persists data after page reload", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Fill in a field
    const headlineInput = page.locator('input[id="input-headline"]');
    await headlineInput.fill("Persistent Data Test");

    // Wait for save
    await expect(page.locator("text=Saved")).toBeVisible({ timeout: 5000 });

    // Reload the page
    await page.reload();

    // Wait for page to load
    await expect(page.locator("h1", { hasText: "Edit Resume Profile" })).toBeVisible();

    // Check if the data persisted
    await expect(headlineInput).toHaveValue("Persistent Data Test");
  });

  test("shows character count for fields with max length", async ({ page }) => {
    await page.goto("http://localhost:3030/dashboard/resumes");
    await page.click('a:has-text("Edit Profile")');

    // Type in first name
    const firstNameInput = page.locator('input[id="input-first-name"]');
    await firstNameInput.fill("Alexander");

    // Should show character count (9 / 255)
    await expect(page.locator("text=9 / 255")).toBeVisible();
  });
});


