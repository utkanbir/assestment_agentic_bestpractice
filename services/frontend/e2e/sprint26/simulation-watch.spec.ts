import { test, expect } from "@playwright/test";

test.describe("S26 simulation watch", () => {
  test("watch bar with stop and progress on simulation", async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto("/");
    await page.getByTestId("open-simulation-modal").click();
    await page.getByPlaceholder("Müşteri Adı *").fill("E2E-S26");
    await page.getByPlaceholder("Proje Adı *").fill(`S26-${Date.now()}`);
    await page.getByTestId("start-simulation-btn").click();
    await page.waitForURL(/simulation=1/, { timeout: 60000 });
    await page.waitForURL(/assessment_id=/, { timeout: 15000 });
    await expect(page.getByTestId("simulation-watch-bar")).toBeVisible({ timeout: 60000 });
    await expect(page.getByTestId("simulation-progress-bar")).toBeVisible({ timeout: 15000 });
    await expect(page.getByTestId("stop-simulation-btn")).toBeVisible();
  });
});
