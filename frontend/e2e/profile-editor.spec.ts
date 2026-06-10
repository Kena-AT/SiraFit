import { test, expect } from '@playwright/test';

test.describe('Profile Editor', () => {
  // We'll run a quick login flow before each test since profile is protected
  test.beforeEach(async ({ page }) => {
    // Navigate to login
    await page.goto('/login');
    // Assuming you have test credentials
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    // Wait for redirect to dashboard
    await page.waitForURL('/dashboard');
  });

  test('can navigate to profile editor and autosave a field', async ({ page }) => {
    // Navigate to profile page
    await page.goto('/dashboard/profile');
    
    // Check if the page loaded
    await expect(page.locator('h1', { hasText: 'Resume Profile' })).toBeVisible();
    
    // Fill in the headline
    const headlineInput = page.locator('input[name="headline"]');
    await headlineInput.fill('Senior Playwright Tester');
    
    // Autosave should trigger. The "Saved at..." text should appear.
    // Wait for the saving indicator to appear then disappear
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Saved at')).toBeVisible({ timeout: 10000 });
  });

  test('can add and remove an experience', async ({ page }) => {
    await page.goto('/dashboard/profile');
    
    // Click Add Experience
    await page.click('button:has-text("Add Experience")');
    
    // The new experience block should appear
    const newExperienceTitle = page.locator('input[name="experiences.0.title"]');
    await expect(newExperienceTitle).toBeVisible();
    await newExperienceTitle.fill('Test Engineer');
    
    const companyInput = page.locator('input[name="experiences.0.company"]');
    await companyInput.fill('SiraFit Test Corp');
    
    // Wait for save
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Saved at')).toBeVisible({ timeout: 10000 });
    
    // Now remove it
    await page.click('button:has(.lucide-trash2)');
    
    // Ensure it's removed
    await expect(newExperienceTitle).not.toBeVisible();
  });
});
