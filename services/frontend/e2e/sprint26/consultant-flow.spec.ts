import { test, expect } from "@playwright/test";

test.describe("S26 consultant flow", () => {
  test("consultant panel on danisman page when assessment selected", async ({ page }) => {
    await page.goto("/");
    const selector = page.getByTestId("assessment-selector");
    await selector.waitFor({ state: "visible" });
    const count = await selector.locator("option").count();
    if (count <= 1) return;
    const assessmentId = await selector.inputValue();
    if (!assessmentId) return;
    await page.goto(`/danisman?assessment_id=${assessmentId}`);
    await expect(page.getByTestId("consultant-panel")).toBeVisible();
    await expect(page.getByTestId("consultant-first-name")).toBeVisible();
  });

  test("interview add consultant link when none assigned", async ({ page }) => {
    await page.goto("/");
    const card = page.getByTestId("assessment-card-live").first();
    if (!(await card.isVisible())) return;
    await card.getByRole("button", { name: "Interview'a git" }).click();
    const link = page.getByTestId("add-consultant-link");
    if (await link.isVisible()) {
      await expect(link).toContainText("Danışman ekle");
    }
    await expect(page.getByTestId("consultant-comment-field")).toBeVisible();
  });
});
