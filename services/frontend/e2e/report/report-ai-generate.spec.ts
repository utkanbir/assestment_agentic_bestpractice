import { test, expect } from "@playwright/test";

test.describe("Sprint20 report AI generate", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector('[data-testid="assessment-selector"]');
    const count = await page.locator('[data-testid="assessment-selector"] option').count();
    if (count > 1) {
      await page.selectOption('[data-testid="assessment-selector"]', { index: 1 });
    }
  });

  test("section AI button writes content", async ({ page }) => {
    const assessmentId = await page.locator('[data-testid="assessment-selector"]').inputValue();
    if (!assessmentId) test.skip();

    await page.goto(`/report?assessment_id=${assessmentId}`);
    await expect(page.getByTestId("report-studio")).toBeVisible();

    const composeBtn = page.getByRole("button", { name: /Rapor Oluştur/i }).first();
    if (await composeBtn.isVisible()) {
      await composeBtn.click();
      await page.waitForTimeout(2000);
    }

    const aiBtn = page.locator('[data-testid^="section-ai-"]').first();
    if (!(await aiBtn.isVisible())) test.skip();

    await aiBtn.click();
    await expect(page.getByText(/AI tamamlandı|kaydedildi/i)).toBeVisible({ timeout: 90000 });
  });
});
