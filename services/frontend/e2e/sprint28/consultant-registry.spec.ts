import { test, expect } from "@playwright/test";

test.describe("S28 consultant registry", () => {
  test("danisman page creates consultant without assign", async ({ page }) => {
    await page.goto("/danisman");
    await expect(page.getByTestId("consultant-panel")).toBeVisible();
    await expect(page.getByTestId("consultant-create-btn")).toHaveText("Oluştur");
    await expect(page.getByTestId("consultant-assign-btn")).toHaveCount(0);
    await page.getByTestId("consultant-first-name").fill("E2E");
    await page.getByTestId("consultant-last-name").fill(`S28-${Date.now()}`);
    await page.getByTestId("expertise-multi-select").getByRole("button", { name: "Uzmanlık seç…" }).click();
    await page.getByLabel("Snowflake").check();
    await page.getByTestId("consultant-create-btn").click();
    await expect(page.getByText("Danışman oluşturuldu.")).toBeVisible({ timeout: 10000 });
  });
});
