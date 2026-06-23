import { test, expect } from '@playwright/test';

test.describe('Profile Editor', () => {
  // Login before each test since profile is protected
  test.beforeEach(async ({ page }) => {
    // Navigate to login
    await page.goto('http://localhost:3030/login');
    
    // Fill in test credentials
    await page.fill('input[type="email"]', 'test@example.com');
    await page.fill('input[type="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');
    
    // Wait for redirect to dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });
  });

  test('can navigate to profile list page', async ({ page }) => {
    // Navigate to resume profiles page
    await page.goto('http://localhost:3030/dashboard/resumes');
    
    // Check if the page loaded
    await expect(page.locator('h1', { hasText: 'Resume Profiles' })).toBeVisible();
    
    // Check if Edit Profile button is visible
    await expect(page.locator('a', { hasText: 'Edit Profile' })).toBeVisible();
  });

  test('can open profile editor', async ({ page }) => {
    // Navigate to profile page
    await page.goto('http://localhost:3030/dashboard/resumes');
    
    // Click Edit Profile
    await page.click('a:has-text("Edit Profile")');
    
    // Should navigate to editor
    await expect(page).toHaveURL(/\/dashboard/resumes\/.+\/editor/);
    await expect(page.locator('h1', { hasText: 'Edit Resume Profile' })).toBeVisible();
  });

  test('can edit basic profile fields with autosave', async ({ page }) => {
    // Go directly to editor (profile should be created automatically)
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Wait for editor to load
    await expect(page.locator('h1', { hasText: 'Edit Resume Profile' })).toBeVisible();
    
    // Fill in first name
    const firstNameInput = page.locator('input[id="input-first-name"]');
    await firstNameInput.fill('John');
    
    // Wait for "Saving..." status
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 3000 });
    
    // Wait for "Saved" status
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
    
    // Fill in last name
    const lastNameInput = page.locator('input[id="input-last-name"]');
    await lastNameInput.fill('Doe');
    
    // Wait for autosave again
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
    
    // Fill in headline
    const headlineInput = page.locator('input[id="input-headline"]');
    await headlineInput.fill('Senior Software Engineer');
    
    // Wait for autosave
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
  });

  test('can add and edit work experience', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Wait for page to load
    await expect(page.locator('h1', { hasText: 'Edit Resume Profile' })).toBeVisible();
    
    // Find and click "Add Experience" button
    await page.click('button:has-text("+ Add Experience")');
    
    // Wait for the new experience item to appear
    await expect(page.locator('text=Item #1')).toBeVisible();
    
    // Fill in title (it should be required)
    const titleInput = page.locator('input[id="input-title"]').first();
    await titleInput.fill('Software Engineer');
    
    // Fill in company
    const companyInput = page.locator('input[id="input-company"]').first();
    await companyInput.fill('Tech Corp');
    
    // Fill in location
    const locationInput = page.locator('input[id="input-location"]').first();
    await locationInput.fill('San Francisco, CA');
    
    // Wait for autosave
    await expect(page.locator('text=Saving...')).toBeVisible({ timeout: 3000 });
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
  });

  test('can remove work experience', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Add an experience first
    await page.click('button:has-text("+ Add Experience")');
    await expect(page.locator('text=Item #1')).toBeVisible();
    
    // Fill required fields
    await page.locator('input[id="input-title"]').first().fill('Test Job');
    await page.locator('input[id="input-company"]').first().fill('Test Company');
    
    // Wait for save
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
    
    // Click remove button (trash icon)
    await page.locator('button[aria-label="Remove item"]').first().click();
    
    // Item should be removed
    await expect(page.locator('text=Item #1')).not.toBeVisible();
    
    // Wait for save to complete removal
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
  });

  test('can add education entry', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Click Add Education
    await page.click('button:has-text("+ Add Education")');
    
    // Fill in institution (required)
    await page.locator('input[id="input-institution"]').first().fill('MIT');
    
    // Fill in degree
    await page.locator('input[id="input-degree"]').first().fill('Bachelor of Science');
    
    // Fill in field of study
    await page.locator('input[id="input-field-of-study"]').first().fill('Computer Science');
    
    // Wait for save
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
  });

  test('can add skills', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Add first skill
    await page.click('button:has-text("+ Add Skill")');
    await page.locator('input[id="input-skill-name"]').first().fill('Python');
    await page.locator('input[id="input-category"]').first().fill('Programming Languages');
    await page.locator('input[id="input-proficiency"]').first().fill('Expert');
    
    // Wait for save
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
    
    // Add second skill
    await page.click('button:has-text("+ Add Skill")');
    await page.locator('input[id="input-skill-name"]').nth(1).fill('React');
    await page.locator('input[id="input-category"]').nth(1).fill('Frameworks');
    
    // Wait for save
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
  });

  test('can add project', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Click Add Project
    await page.click('button:has-text("+ Add Project")');
    
    // Fill project details
    await page.locator('input[id="input-project-name"]').first().fill('Portfolio Website');
    await page.locator('textarea[id="textarea-description"]').first().fill('Personal portfolio showcasing projects');
    await page.locator('input[id="input-url"]').first().fill('https://example.com');
    
    // Wait for save
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
  });

  test('can add certification', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Click Add Certification
    await page.click('button:has-text("+ Add Certification")');
    
    // Fill certification details (name and issuer are required)
    await page.locator('input[id="input-certification-name"]').first().fill('AWS Certified Solutions Architect');
    await page.locator('input[id="input-issuer"]').first().fill('Amazon Web Services');
    await page.locator('input[id="input-credential-id"]').first().fill('ABC123XYZ');
    
    // Wait for save
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
  });

  test('displays validation errors for required fields', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Add experience without required fields
    await page.click('button:has-text("+ Add Experience")');
    
    // Try to fill only title (company is also required)
    await page.locator('input[id="input-title"]').first().fill('Test');
    
    // Leave company empty - this should trigger validation error
    // Note: The actual validation happens on save, so we might see error status
    await page.waitForTimeout(2000); // Wait for debounce
    
    // Should show error status instead of saved
    await expect(page.locator('text=Error saving').or(page.locator('text=Validation Errors'))).toBeVisible({ timeout: 5000 });
  });

  test('can collapse and expand sections', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
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

  test('can navigate back from editor', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Should be on editor page
    await expect(page).toHaveURL(/\/dashboard/resumes\/.+\/editor/);
    
    // Click Back button
    await page.click('button:has-text("Back")');
    
    // Should navigate back to previous page
    await expect(page).not.toHaveURL(/\/editor/);
  });

  test('persists data after page reload', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Fill in a field
    const headlineInput = page.locator('input[id="input-headline"]');
    await headlineInput.fill('Persistent Data Test');
    
    // Wait for save
    await expect(page.locator('text=Saved')).toBeVisible({ timeout: 5000 });
    
    // Reload the page
    await page.reload();
    
    // Wait for page to load
    await expect(page.locator('h1', { hasText: 'Edit Resume Profile' })).toBeVisible();
    
    // Check if the data persisted
    await expect(headlineInput).toHaveValue('Persistent Data Test');
  });

  test('shows character count for fields with max length', async ({ page }) => {
    await page.goto('http://localhost:3030/dashboard/resumes');
    await page.click('a:has-text("Edit Profile")');
    
    // Type in first name
    const firstNameInput = page.locator('input[id="input-first-name"]');
    await firstNameInput.fill('Alexander');
    
    // Should show character count (9 / 255)
    await expect(page.locator('text=9 / 255')).toBeVisible();
  });
});
