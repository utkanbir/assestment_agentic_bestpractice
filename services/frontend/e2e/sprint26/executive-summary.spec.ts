import { test, expect } from "@playwright/test";

test.describe("S26 executive summary export", () => {
  test("generate summary and txt export button", async ({ page }) => {
    await page.goto("/");
    const card = page.getByTestId("assessment-card-live").first();
    if (!(await card.isVisible())) return;
    await card.click();
    await page.goto("/executive?assessment_id=" + await page.getByTestId("assessment-selector").inputValue());
    const genBtn = page.getByRole("button", { name: /Özet Oluştur|Yeniden Üret/ });
    await genBtn.click();
    await expect(page.getByTestId("export-summary-txt")).toBeVisible({ timeout: 60000 });
  });
});
