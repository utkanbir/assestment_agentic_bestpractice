import { test, expect } from "@playwright/test";

test.describe("Sprint19 execution plan narrative", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector('[data-testid="assessment-selector"]');
    const count = await page.locator('[data-testid="assessment-selector"] option').count();
    if (count > 1) {
      await page.selectOption('[data-testid="assessment-selector"]', { index: 1 });
    }
  });

  test("explain narrative panel visible", async ({ page }) => {
    const assessmentId = await page.locator('[data-testid="assessment-selector"]').inputValue();
    if (!assessmentId) test.skip();
    await page.goto(`/yurutme-plani?assessment_id=${assessmentId}`);
    await expect(page.getByRole("heading", { name: "Yürütme Planı" })).toBeVisible();
  });
});
