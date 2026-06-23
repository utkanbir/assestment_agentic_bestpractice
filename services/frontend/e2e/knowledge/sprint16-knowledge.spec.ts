import { expect, test } from "@playwright/test";

test.describe("Sprint16 assessment context + knowledge pages", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => localStorage.removeItem("aakp_assessment_id"));
  });

  test("assessment selector visible in global nav", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("assessment-selector")).toBeVisible();
  });

  test("ontoloji page opens", async ({ page }) => {
    await page.goto("/ontoloji");
    await expect(page.getByRole("heading", { name: "Ontoloji" })).toBeVisible();
  });

  test("yurutme-plani route guarded by assessment", async ({ page }) => {
    await page.goto("/yurutme-plani");
    await expect(page.getByText("Bu sayfa assessment gerektiriyor")).toBeVisible();
  });
});
