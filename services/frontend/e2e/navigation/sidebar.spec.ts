import { test, expect } from "@playwright/test";

test.describe("Sprint20 sidebar navigation", () => {
  test("sidebar visible and no horizontal top nav links", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("app-sidebar")).toBeVisible();
    await expect(page.getByTestId("app-topbar")).toBeVisible();

    const topNavLinks = page.locator('[data-testid="app-topbar"] a');
    await expect(topNavLinks).toHaveCount(0);

    await page.getByTestId("app-sidebar").getByRole("link", { name: /Rapor Stüdyosu/i }).click();
    await expect(page).toHaveURL(/\/report/);
    await expect(page.getByTestId("report-studio")).toBeVisible();
  });
});
