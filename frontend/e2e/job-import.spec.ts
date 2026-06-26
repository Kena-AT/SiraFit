import { test, expect } from '@playwright/test';

/**
 * Job Import System - E2E Tests
 *
 * Tests for the import page and history page.
 * Note: These tests check UI rendering since they run against the frontend.
 * Full API integration is tested in backend tests.
 */

test.describe('Job Import Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/jobs/import');
  });

  test('renders the import page with all sections', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /import jobs/i })).toBeVisible();
    await expect(page.getByText(/from url/i)).toBeVisible();
    await expect(page.getByText(/from description/i)).toBeVisible();
    await expect(page.getByText(/batch import/i)).toBeVisible();
    await expect(page.getByText(/recent imports/i)).toBeVisible();
  });

  test('shows supported platforms', async ({ page }) => {
    await expect(page.getByText('LinkedIn')).toBeVisible();
    await expect(page.getByText('Indeed')).toBeVisible();
    await expect(page.getByText('Glassdoor')).toBeVisible();
    await expect(page.getByText('Greenhouse')).toBeVisible();
  });

  test('URL import button is disabled when input is empty', async ({ page }) => {
    const scrapeButton = page.getByRole('button', { name: /scrape now/i });
    await expect(scrapeButton).toBeDisabled();
  });

  test('URL import button is enabled when input has text', async ({ page }) => {
    await page.getByPlaceholder(/https:\/\/jobs\.lever\.co/i).fill('https://example.com/job/123');
    const scrapeButton = page.getByRole('button', { name: /scrape now/i });
    await expect(scrapeButton).toBeEnabled();
  });

  test('description import button is disabled when textarea is empty', async ({ page }) => {
    const analyzeButton = page.getByRole('button', { name: /analyze description/i });
    await expect(analyzeButton).toBeDisabled();
  });

  test('description import button is enabled when textarea has text', async ({ page }) => {
    await page.getByPlaceholder(/paste the full job description/i).fill('Software Engineer position at a great company looking for Python and React skills.');
    const analyzeButton = page.getByRole('button', { name: /analyze description/i });
    await expect(analyzeButton).toBeEnabled();
  });

  test('has link to import history', async ({ page }) => {
    const historyLink = page.getByRole('link', { name: /import history/i });
    await expect(historyLink).toBeVisible();
    await expect(historyLink).toHaveAttribute('href', '/jobs/history');
  });

  test('view all link in recent imports navigates to history', async ({ page }) => {
    const viewAllLink = page.getByRole('link', { name: /view all/i });
    await expect(viewAllLink).toBeVisible();
    await expect(viewAllLink).toHaveAttribute('href', '/jobs/history');
  });

  test('shows empty state when no recent imports', async ({ page }) => {
    await expect(page.getByText(/no imports yet/i)).toBeVisible();
  });
});

test.describe('Import History Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/jobs/history');
  });

  test('renders the history page', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /import history/i })).toBeVisible();
  });

  test('has a refresh button', async ({ page }) => {
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    await expect(refreshButton).toBeVisible();
  });

  test('has a link to new import', async ({ page }) => {
    const newImportLink = page.getByRole('link', { name: /new import/i });
    await expect(newImportLink).toBeVisible();
    await expect(newImportLink).toHaveAttribute('href', '/jobs/import');
  });

  test('shows empty state when no history', async ({ page }) => {
    await expect(page.getByText(/no imports yet/i)).toBeVisible();
  });

  test('shows import jobs link in empty state', async ({ page }) => {
    const importLink = page.getByRole('link', { name: /import jobs/i });
    await expect(importLink).toBeVisible();
    await expect(importLink).toHaveAttribute('href', '/jobs/import');
  });
});

test.describe('Job Import Navigation', () => {
  test('can navigate from import to history', async ({ page }) => {
    await page.goto('/jobs/import');
    await page.getByRole('link', { name: /import history/i }).click();
    await expect(page).toHaveURL(/\/jobs\/history/);
  });

  test('can navigate from history to import', async ({ page }) => {
    await page.goto('/jobs/history');
    await page.getByRole('link', { name: /new import/i }).click();
    await expect(page).toHaveURL(/\/jobs\/import/);
  });
});
