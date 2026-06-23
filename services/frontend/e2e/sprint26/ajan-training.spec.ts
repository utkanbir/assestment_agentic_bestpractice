import { test, expect } from "@playwright/test";

async function pickAssessmentId(page: import("@playwright/test").Page): Promise<string | null> {
  await page.goto("/");
  const selector = page.getByTestId("assessment-selector");
  await selector.waitFor({ state: "visible" });
  const count = await selector.locator("option").count();
  if (count <= 1) return null;
  return selector.inputValue();
}

test.describe("S26 agent training", () => {
  test("OWL export button visible on ajan yonetimi", async ({ page }) => {
    const assessmentId = await pickAssessmentId(page);
    if (!assessmentId) return;
    await page.goto(`/ajan-yonetimi?assessment_id=${assessmentId}`);
    await page.getByRole("button", { name: "Kubernetes" }).click();
    await expect(page.getByTestId("owl-export-btn")).toBeVisible({ timeout: 15000 });
  });

  test("AAHA consultant select visible", async ({ page }) => {
    const assessmentId = await pickAssessmentId(page);
    if (!assessmentId) return;
    await page.goto(`/ajan-yonetimi?assessment_id=${assessmentId}`);
    await page.getByRole("button", { name: "Kubernetes" }).click();
    await page.getByRole("button", { name: /AAHA/i }).click();
    await expect(page.getByTestId("aaha-consultant-select")).toBeVisible();
  });
});
