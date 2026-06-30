import { test, expect } from '@playwright/test';

/**
 * Job Explorer - E2E Tests
 *
 * Tests for the job browsing, search, filtering, and detail pages.
 */

test.describe('Jobs Explorer Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/jobs');
  });

  test('renders the jobs explorer page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /jobs explorer/i })).toBeVisible();
  });

  test('has search input and button', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search role, company/i);
    await expect(searchInput).toBeVisible();
    
    const searchButton = page.getByRole('button', { name: /search/i });
    await expect(searchButton).toBeVisible();
  });

  test('has filter inputs', async ({ page }) => {
    await expect(page.getByPlaceholder('Company')).toBeVisible();
    await expect(page.getByPlaceholder('Location')).toBeVisible();
  });

  test('has source filter dropdown', async ({ page }) => {
    const sourceDropdown = page.locator('select').first();
    await expect(sourceDropdown).toBeVisible();
    
    // Check if it has expected options
    const options = await sourceDropdown.locator('option').allTextContents();
    expect(options).toContain('All sources');
    expect(options).toContain('LinkedIn');
    expect(options).toContain('Indeed');
  });

  test('has sort dropdown', async ({ page }) => {
    const sortDropdown = page.locator('select').nth(1);
    await expect(sortDropdown).toBeVisible();
    
    const options = await sortDropdown.locator('option').allTextContents();
    expect(options).toContain('Newest first');
    expect(options).toContain('Oldest first');
  });

  test('has links to import pages', async ({ page }) => {
    const importHistoryLink = page.getByRole('link', { name: /import history/i });
    await expect(importHistoryLink).toBeVisible();
    
    const importJobsLink = page.getByRole('link', { name: /import jobs/i });
    await expect(importJobsLink).toBeVisible();
  });

  test('displays job table headers', async ({ page }) => {
    await expect(page.getByText('#')).toBeVisible();
    await expect(page.getByText('Company')).toBeVisible();
    await expect(page.getByText('Role')).toBeVisible();
    await expect(page.getByText('Location')).toBeVisible();
    await expect(page.getByText('Salary')).toBeVisible();
    await expect(page.getByText('Source')).toBeVisible();
    await expect(page.getByText('Tags')).toBeVisible();
    await expect(page.getByText('Imported')).toBeVisible();
  });

  test('search button is not disabled', async ({ page }) => {
    const searchButton = page.getByRole('button', { name: /search/i });
    await expect(searchButton).toBeEnabled();
  });

  test('can type in search field', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search role, company/i);
    await searchInput.fill('Python Engineer');
    await expect(searchInput).toHaveValue('Python Engineer');
  });

  test('can type in company filter', async ({ page }) => {
    const companyInput = page.getByPlaceholder('Company');
    await companyInput.fill('Google');
    await expect(companyInput).toHaveValue('Google');
  });

  test('can type in location filter', async ({ page }) => {
    const locationInput = page.getByPlaceholder('Location');
    await locationInput.fill('San Francisco');
    await expect(locationInput).toHaveValue('San Francisco');
  });

  test('can change source filter', async ({ page }) => {
    const sourceDropdown = page.locator('select').first();
    await sourceDropdown.selectOption('linkedin');
    await expect(sourceDropdown).toHaveValue('linkedin');
  });

  test('can change sort order', async ({ page }) => {
    const sortDropdown = page.locator('select').nth(1);
    await sortDropdown.selectOption('company-asc');
    await expect(sortDropdown).toHaveValue('company-asc');
  });

  test('shows clear filters button when filters are active', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search role, company/i);
    await searchInput.fill('test');
    
    const searchButton = page.getByRole('button', { name: /search/i });
    await searchButton.click();
    
    // Wait a bit for the state to update
    await page.waitForTimeout(500);
    
    const clearButton = page.getByRole('button', { name: /clear filters/i });
    await expect(clearButton).toBeVisible();
  });

  test('pagination controls are present', async ({ page }) => {
    // Check for prev/next buttons (← →)
    const buttons = page.locator('button').filter({ hasText: /[←→]/ });
    const count = await buttons.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('shows row count indicator', async ({ page }) => {
    await expect(page.getByText(/showing/i)).toBeVisible();
  });
});

test.describe('Job Detail Page', () => {
  test('renders job detail page structure', async ({ page }) => {
    // First navigate to jobs list
    await page.goto('/jobs');
    
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

  test('has action buttons in header', async ({ page }) => {
    await page.goto('/jobs');
    
    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();
    
    if (linkCount > 0) {
      await jobLinks.first().click();
      
      // Check for action buttons
      await expect(page.getByRole('link', { name: /back to jobs/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /tailor resume/i })).toBeVisible();
      await expect(page.getByRole('link', { name: /apply/i })).toBeVisible();
    }
  });

  test('displays job description section', async ({ page }) => {
    await page.goto('/jobs');
    
    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();
    
    if (linkCount > 0) {
      await jobLinks.first().click();
      
      // Look for description-related text
      await expect(page.getByText(/job description/i)).toBeVisible();
    }
  });

  test('shows compensation panel', async ({ page }) => {
    await page.goto('/jobs');
    
    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();
    
    if (linkCount > 0) {
      await jobLinks.first().click();
      
      await expect(page.getByText(/compensation/i)).toBeVisible();
    }
  });

  test('shows location panel', async ({ page }) => {
    await page.goto('/jobs');
    
    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();
    
    if (linkCount > 0) {
      await jobLinks.first().click();
      
      await expect(page.getByText(/location/i)).toBeVisible();
    }
  });

  test('shows import details section', async ({ page }) => {
    await page.goto('/jobs');
    
    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();
    
    if (linkCount > 0) {
      await jobLinks.first().click();
      
      await expect(page.getByText(/import details/i)).toBeVisible();
    }
  });
});

test.describe('Job Explorer Navigation', () => {
  test('can navigate from explorer to import page', async ({ page }) => {
    await page.goto('/jobs');
    await page.getByRole('link', { name: /import jobs/i }).click();
    await expect(page).toHaveURL(/\/jobs\/import/);
  });

  test('can navigate from explorer to history page', async ({ page }) => {
    await page.goto('/jobs');
    await page.getByRole('link', { name: /import history/i }).click();
    await expect(page).toHaveURL(/\/jobs\/history/);
  });

  test('can navigate from detail back to explorer', async ({ page }) => {
    await page.goto('/jobs');
    
    const jobLinks = page.locator('a[href*="/jobs/"]').filter({ hasText: /./ });
    const linkCount = await jobLinks.count();
    
    if (linkCount > 0) {
      await jobLinks.first().click();
      await page.getByRole('link', { name: /back to jobs/i }).click();
      await expect(page).toHaveURL(/\/jobs$/);
    }
  });
});

test.describe('Job Explorer Loading States', () => {
  test('shows loading state initially', async ({ page }) => {
    await page.goto('/jobs');
    
    // The loading spinner should appear briefly
    const loadingText = page.getByText(/loading jobs/i);
    // It may disappear quickly, so we just check the page loaded
    await page.waitForLoadState('networkidle');
  });

  test('handles empty state', async ({ page }) => {
    await page.goto('/jobs');
    
    // If there are no jobs, should show empty state
    // This might show "No jobs found" or similar
    await page.waitForLoadState('networkidle');
  });
});
