import { test, expect } from "@playwright/test";

test.describe("S27 overview cleanup", () => {
  test("no workstream grid when assessment selected", async ({ page }) => {
    await page.goto("/");
    const card = page.getByTestId("assessment-card-live").first();
    if (!(await card.isVisible())) return;
    await card.click();
    await expect(page.getByText("Workstream Durumu")).toHaveCount(0);
    await expect(page.getByTestId("consultant-panel")).toHaveCount(0);
    await expect(page.getByTestId("workstream-card-kubernetes")).toHaveCount(0);
  });
});
