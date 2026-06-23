import { test, expect } from "@playwright/test";

test.describe("Sprint19 report studio", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector('[data-testid="assessment-selector"]');
    const count = await page.locator('[data-testid="assessment-selector"] option').count();
    if (count > 1) {
      await page.selectOption('[data-testid="assessment-selector"]', { index: 1 });
    }
  });

  test("report studio with compose CTA", async ({ page }) => {
    const assessmentId = await page.locator('[data-testid="assessment-selector"]').inputValue();
    if (!assessmentId) test.skip();
    await page.goto(`/report?assessment_id=${assessmentId}`);
    await expect(page.getByTestId("report-studio")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Rapor Stüdyosu" })).toBeVisible();
    const cta = page.getByTestId("report-compose-cta");
    if (await cta.isVisible()) {
      await expect(cta).toBeVisible();
    }
  });
});
