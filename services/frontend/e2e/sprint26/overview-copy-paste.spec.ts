import { test, expect } from "@playwright/test";

test.describe("S26 overview copy paste", () => {
  test("visible copy buttons and paste toolbar", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("paste-assessment-btn")).toBeVisible();
    const card = page.getByTestId("assessment-card-live").first();
    if (await card.isVisible()) {
      await card.getByRole("button", { name: "Kopyala" }).click();
      await expect(page.getByTestId("confirm-duplicate-btn")).toBeVisible();
      await page.getByRole("button", { name: "İptal" }).click();
    }
  });

  test("card select does not navigate away", async ({ page }) => {
    await page.goto("/");
    const card = page.getByTestId("assessment-card-live").first();
    if (await card.isVisible()) {
      await card.click();
      await expect(page).toHaveURL(/\/(\?|$)/);
      await expect(page.getByText("Assessment Genel Bakış")).toBeVisible();
    }
  });
});
