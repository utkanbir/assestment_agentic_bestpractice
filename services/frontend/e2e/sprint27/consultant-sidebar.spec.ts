import { test, expect } from "@playwright/test";

test.describe("S27 consultant sidebar", () => {
  test("danisman route shows consultant panel", async ({ page }) => {
    await page.goto("/danisman");
    await expect(page.getByTestId("consultant-panel")).toBeVisible();
    await expect(page.getByTestId("consultant-first-name")).toBeVisible();
    await expect(page.getByTestId("consultant-create-btn")).toHaveText("Oluştur");
  });

  test("sidebar has Danışman link", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: "Danışman" })).toBeVisible();
  });
});
