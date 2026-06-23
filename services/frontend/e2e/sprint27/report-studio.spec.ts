import { test, expect } from "@playwright/test";

test.describe("S27 report studio", () => {
  test("top AI button only, no toolbar batch", async ({ page }) => {
    await page.goto("/");
    const selector = page.getByTestId("assessment-selector");
    await selector.waitFor({ state: "visible" });
    const count = await selector.locator("option").count();
    if (count <= 1) return;
    const assessmentId = await selector.inputValue();
    if (!assessmentId) return;
    await page.goto(`/report?assessment_id=${assessmentId}`);
    await expect(page.getByTestId("report-studio")).toBeVisible();
    const composeCta = page.getByTestId("report-compose-cta");
    if (await composeCta.isVisible()) {
      await composeCta.click();
    }
    await expect(page.getByTestId("report-ai-generate-all-top")).toBeVisible({ timeout: 30000 });
    await expect(page.getByTestId("report-ai-batch")).toHaveCount(0);
  });
});
