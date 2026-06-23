import { test, expect } from "@playwright/test";

test.describe("Sprint17 assessment-first UX", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector('[data-testid="assessment-selector"]');
    const options = page.locator('[data-testid="assessment-selector"] option');
    const count = await options.count();
    if (count > 1) {
      await page.selectOption('[data-testid="assessment-selector"]', { index: 1 });
    }
  });

  test("assessment page header visible on executive page", async ({ page }) => {
    const assessmentId = await page.locator('[data-testid="assessment-selector"]').inputValue();
    if (!assessmentId) test.skip();
    await page.goto(`/executive?assessment_id=${assessmentId}`);
    await expect(page.getByTestId("assessment-page-header")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Yönetici Özeti" })).toBeVisible();
  });

  test("inceleme merkezi route works", async ({ page }) => {
    const assessmentId = await page.locator('[data-testid="assessment-selector"]').inputValue();
    if (!assessmentId) test.skip();
    await page.goto(`/approvals?assessment_id=${assessmentId}`);
    await expect(page.getByRole("heading", { name: "İnceleme Merkezi" })).toBeVisible();
  });

  test("workstream launch card on overview when assessment selected", async ({ page }) => {
    await page.goto("/");
    const selector = page.locator('[data-testid="assessment-selector"]');
    const val = await selector.inputValue();
    if (!val) test.skip();
    await expect(page.getByTestId("workstream-card-kubernetes")).toBeVisible();
  });
});
