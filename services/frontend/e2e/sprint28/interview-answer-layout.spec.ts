import { test, expect } from "@playwright/test";

async function pickAssessmentId(page: import("@playwright/test").Page): Promise<string | null> {
  await page.goto("/");
  const selector = page.getByTestId("assessment-selector");
  await selector.waitFor({ state: "visible" });
  const count = await selector.locator("option").count();
  if (count <= 1) return null;
  return selector.inputValue();
}

test.describe("S28 interview answer layout", () => {
  test("question card shows customer answer before consultant", async ({ page }) => {
    const assessmentId = await pickAssessmentId(page);
    if (!assessmentId) return;
    await page.goto(`/interview?assessment_id=${assessmentId}`);
    const musteri = page.getByText("Müşteri Yanıtı").first();
    await expect(musteri).toBeVisible({ timeout: 15000 });
    const danisman = page.getByText("Danışman Yorumları").first();
    if (await danisman.isVisible().catch(() => false)) {
      const musteriBox = await musteri.boundingBox();
      const danismanBox = await danisman.boundingBox();
      if (musteriBox && danismanBox) {
        expect(musteriBox.y).toBeLessThan(danismanBox.y);
      }
    }
    await expect(page.getByTestId("ai-yorum-btn").first()).toBeVisible();
  });
});
