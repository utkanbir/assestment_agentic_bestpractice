import { test, expect } from "@playwright/test";

async function pickAssessmentId(page: import("@playwright/test").Page): Promise<string | null> {
  await page.goto("/");
  const selector = page.getByTestId("assessment-selector");
  await selector.waitFor({ state: "visible" });
  const count = await selector.locator("option").count();
  if (count <= 1) return null;
  return selector.inputValue();
}

test.describe("S26 architecture and tech stack links", () => {
  test("tech stack page renders rows", async ({ page }) => {
    await page.goto("/teknoloji");
    await expect(page.getByTestId("tech-stack-page")).toBeVisible();
    await expect(page.getByText("PostgreSQL")).toBeVisible();
  });

  test("architecture layer stack visible", async ({ page }) => {
    const assessmentId = await pickAssessmentId(page);
    if (!assessmentId) return;
    await page.goto(`/mimari?assessment_id=${assessmentId}`);
    await expect(page.getByTestId("layer-stack")).toBeVisible({ timeout: 15000 });
    for (const layer of ["agent", "knowledge", "information", "data"]) {
      await expect(page.getByTestId(`layer-card-${layer}`)).toBeVisible();
    }
  });
});
