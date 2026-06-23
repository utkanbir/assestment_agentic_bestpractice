import { test, expect } from "@playwright/test";

test.describe("S21 autonomous simulation watch mode", () => {
  test("start simulation modal and watch bar", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("open-simulation-modal").click();
    await expect(page.getByTestId("start-simulation-btn")).toBeVisible();
    await page.getByPlaceholder("Müşteri Adı *").fill("E2E-Sim");
    await page.getByPlaceholder("Proje Adı *").fill(`Sim-${Date.now()}`);
    await page.getByTestId("start-simulation-btn").click();
    await expect(page.getByTestId("simulation-watch-bar")).toBeVisible({ timeout: 30000 });
    await expect(page.getByTestId("stop-simulation-btn")).toBeVisible();
  });
});

test.describe("S21 simulated assessment card styling", () => {
  test("purple simulated badge on overview", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("open-simulation-modal").click();
    await page.getByPlaceholder("Müşteri Adı *").fill("E2E-Badge");
    await page.getByPlaceholder("Proje Adı *").fill(`Badge-${Date.now()}`);
    await page.getByTestId("start-simulation-btn").click();
    await page.waitForURL(/simulation=1/);
    await page.goto("/");
    await expect(page.getByTestId("assessment-card-simulated").first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId("ai-simulated-badge").first()).toHaveText(/AI Simulated/i);
  });
});
