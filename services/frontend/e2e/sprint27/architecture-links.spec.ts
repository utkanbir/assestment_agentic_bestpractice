import { test, expect } from "@playwright/test";

async function pickAssessmentId(page: import("@playwright/test").Page): Promise<string | null> {
  await page.goto("/");
  const selector = page.getByTestId("assessment-selector");
  await selector.waitFor({ state: "visible" });
  const count = await selector.locator("option").count();
  if (count <= 1) return null;
  return selector.inputValue();
}

test.describe("S27 architecture links", () => {
  test("mimari shows internal badge for cluster-only tech", async ({ page }) => {
    const assessmentId = await pickAssessmentId(page);
    if (!assessmentId) return;
    await page.goto(`/mimari?assessment_id=${assessmentId}`);
    await page.getByTestId("layer-card-information").click();
    await expect(page.getByText("Internal").first()).toBeVisible({ timeout: 10000 });
  });

  test("tech stack PG health link uses system path", async ({ page }) => {
    await page.goto("/teknoloji");
    const pgLink = page.locator('a[href="/health/db"]').first();
    await expect(pgLink).toBeVisible();
  });
});
