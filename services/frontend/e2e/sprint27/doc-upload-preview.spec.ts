import { test, expect } from "@playwright/test";

test.describe("S27 doc upload preview", () => {
  test("upload shows summary with preview on docs tab", async ({ page }) => {
    await page.goto("/");
    const selector = page.getByTestId("assessment-selector");
    await selector.waitFor({ state: "visible" });
    const count = await selector.locator("option").count();
    if (count <= 1) return;
    const assessmentId = await selector.inputValue();
    if (!assessmentId) return;
    await page.goto(`/ajan-yonetimi?assessment_id=${assessmentId}`);
    await page.getByRole("button", { name: /Bilgi Tabanı/ }).click();
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: "s27-e2e.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("Sprint 27 E2E preview content for document upload test."),
    });
    await expect(page.getByTestId("doc-upload-summary")).toBeVisible({ timeout: 30000 });
    await expect(page.getByTestId("doc-upload-preview")).toBeVisible();
  });
});
