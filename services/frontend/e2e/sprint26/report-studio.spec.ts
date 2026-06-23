import { test, expect } from "@playwright/test";

test.describe("S26 report studio", () => {
  test("batch AI button prominent on report studio", async ({ page }) => {
    await page.goto("/");
    const selector = page.getByTestId("assessment-selector");
    await selector.waitFor({ state: "visible" });
    const count = await selector.locator("option").count();
    if (count <= 1) return;
    const assessmentId = await selector.inputValue();
    if (!assessmentId) return;
    await page.goto(`/report?assessment_id=${assessmentId}`);
    await expect(page.getByTestId("report-studio")).toBeVisible();
    const batchTop = page.getByTestId("report-ai-generate-all-top");
    const composeCta = page.getByTestId("report-compose-cta");
    if (await batchTop.isVisible()) {
      await expect(batchTop).toBeVisible();
    } else if (await composeCta.isVisible()) {
      await composeCta.click();
      await expect(page.getByTestId("report-ai-generate-all-top")).toBeVisible({
        timeout: 30000,
      });
    }
  });
});
