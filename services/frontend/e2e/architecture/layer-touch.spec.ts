import { test, expect } from "@playwright/test";

test.describe("Knowledge Architecture — layer stack", () => {
  test("renders 4 layer cards", async ({ page }) => {
    await page.goto("/mimari");
    await expect(page.getByTestId("layer-stack")).toBeVisible();
    for (const layer of ["agent", "knowledge", "information", "data"]) {
      await expect(page.getByTestId(`layer-card-${layer}`)).toBeVisible();
    }
  });

  test("shows touch timeline section", async ({ page }) => {
    await page.goto("/mimari");
    await expect(page.getByText("Katman Dokunuşları")).toBeVisible();
  });
});

test.describe("Interview — layer trace mini panel", () => {
  test("mimari nav link is visible", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("link", { name: "Mimari" })).toBeVisible();
  });
});
