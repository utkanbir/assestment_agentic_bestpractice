import { test, expect } from "@playwright/test";

test.describe("S27 simulation stop stays on interview", () => {
  test("stop does not navigate to report", async ({ page }) => {
    test.setTimeout(120_000);
    await page.goto("/");
    await page.getByTestId("open-simulation-modal").click();
    await page.getByPlaceholder("Müşteri Adı *").fill("E2E-S27");
    await page.getByPlaceholder("Proje Adı *").fill(`S27-${Date.now()}`);
    await page.getByTestId("start-simulation-btn").click();
    await page.waitForURL(/simulation=1/, { timeout: 60000 });
    await expect(page.getByTestId("simulation-watch-bar")).toBeVisible({ timeout: 60000 });
    await page.getByTestId("stop-simulation-btn").click();
    await expect(page.getByTestId("simulation-watch-bar")).toBeVisible({ timeout: 15000 });
    await expect(page).toHaveURL(/interview/);
    await expect(page).not.toHaveURL(/\/report/);
    await expect(page.getByTestId("finalize-simulation-btn")).toBeVisible({ timeout: 15000 });
  });
});
