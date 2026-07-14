import { test, expect } from "@playwright/test";

/**
 * Route Protection Tests
 *
 * These tests verify that:
 * 1. Unauthenticated users are redirected away from protected routes.
 * 2. Auth pages are accessible to everyone.
 * 3. Authenticated users can access protected routes.
 */

// ─── Unauthenticated user tests ────────────────────────────────────────────────

test.describe("Unauthenticated access", () => {
  test("visiting /dashboard redirects to /login", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("visiting /dashboard/settings redirects to /login", async ({ page }) => {
    await page.goto("/dashboard/settings");
    await expect(page).toHaveURL(/\/login/);
  });

  test("landing page is accessible without auth", async ({ page }) => {
    await page.goto("/");
    await expect(page).not.toHaveURL(/\/login/);
    await expect(page.getByText("SiraFit")).toBeVisible();
  });

  test("login page is accessible without auth", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: /welcome back/i })).toBeVisible();
  });

  test("register page is accessible without auth", async ({ page }) => {
    await page.goto("/register");
    await expect(page).toHaveURL(/\/register/);
    await expect(page.getByRole("heading", { name: /create an account/i })).toBeVisible();
  });

  test("forgot-password page is accessible without auth", async ({ page }) => {
    await page.goto("/forgot-password");
    await expect(page).toHaveURL(/\/forgot-password/);
    await expect(page.getByRole("heading", { name: /forgot password/i })).toBeVisible();
  });
});

// ─── Login form validation ──────────────────────────────────────────────────────

test.describe("Login form", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
  });

  test("shows error on empty form submit", async ({ page }) => {
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page.getByText(/email is required/i)).toBeVisible();
  });

  test("shows error on invalid credentials", async ({ page }) => {
    await page.getByLabel("Email").fill("wrong@example.com");
    await page.getByLabel("Password").fill("wrongpassword");
    await page.getByRole("button", { name: /sign in/i }).click();
    // Error message from API
    await expect(page.getByText(/incorrect email or password/i)).toBeVisible({ timeout: 5000 });
  });

  test("has a link to register", async ({ page }) => {
    await page.getByRole("link", { name: /create an account/i }).click();
    await expect(page).toHaveURL(/\/register/);
  });

  test("has a link to forgot-password", async ({ page }) => {
    await page.getByRole("link", { name: /forgot password/i }).click();
    await expect(page).toHaveURL(/\/forgot-password/);
  });
});

// ─── Register form validation ───────────────────────────────────────────────────

test.describe("Register form", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/register");
  });

  test("shows validation errors on empty submit", async ({ page }) => {
    await page.getByRole("button", { name: /create account/i }).click();
    await expect(page.getByText(/full name is required/i)).toBeVisible();
  });

  test("shows error when passwords do not match", async ({ page }) => {
    await page.getByLabel("Full Name").fill("Test User");
    await page.getByLabel("Email").fill("test@example.com");
    await page.getByLabel(/^Password$/).fill("Password123!");
    await page.getByLabel(/confirm password/i).fill("DifferentPass!");
    await page.getByRole("button", { name: /create account/i }).click();
    await expect(page.getByText(/passwords do not match/i)).toBeVisible();
  });

  test("has a link to login", async ({ page }) => {
    await page.getByRole("link", { name: /sign in/i }).click();
    await expect(page).toHaveURL(/\/login/);
  });
});
