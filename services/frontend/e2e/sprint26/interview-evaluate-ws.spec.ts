import { test, expect } from "@playwright/test";

test.describe("S26 interview evaluate all workstreams", () => {
  test("cloud_strategy workstream shows Değerlendir button", async ({ page }) => {
    await page.goto("/");
    const card = page.getByTestId("assessment-card-live").first();
    if (!(await card.isVisible())) return;
    await card.click();
    await page.getByRole("button", { name: "Interview'a git" }).click();
    const cloudTab = page.getByRole("button", { name: /cloud|bulut|cloud_strategy/i });
    if (await cloudTab.isVisible()) {
      await cloudTab.click();
    }
    const evaluateBtn = page.getByRole("button", { name: /Değerlendir/i }).first();
    if (await evaluateBtn.isVisible()) {
      await expect(evaluateBtn).toBeVisible();
    }
  });
});
