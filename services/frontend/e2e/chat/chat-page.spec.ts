import { test, expect } from "@playwright/test";

test.describe("Sprint19 chat page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector('[data-testid="assessment-selector"]');
    const count = await page.locator('[data-testid="assessment-selector"] option').count();
    if (count > 1) {
      await page.selectOption('[data-testid="assessment-selector"]', { index: 1 });
    }
  });

  test("full page chat route without workstream selector", async ({ page }) => {
    const assessmentId = await page.locator('[data-testid="assessment-selector"]').inputValue();
    if (!assessmentId) test.skip();
    await page.goto(`/chat?assessment_id=${assessmentId}`);
    await expect(page.getByTestId("chat-page")).toBeVisible();
    await expect(page.getByText("Workstream", { exact: true })).toHaveCount(0);
  });

  test("user message visible after send", async ({ page }) => {
    const assessmentId = await page.locator('[data-testid="assessment-selector"]').inputValue();
    if (!assessmentId) test.skip();
    await page.goto(`/chat?assessment_id=${assessmentId}`);
    const input = page.getByTestId("chat-input");
    await input.fill("Test kullanici mesaji S19");
    await page.getByTestId("chat-send").click();
    await expect(page.getByTestId("chat-msg-user").last()).toContainText("Test kullanici mesaji S19");
  });

  test("FAB navigates to chat", async ({ page }) => {
    const assessmentId = await page.locator('[data-testid="assessment-selector"]').inputValue();
    if (!assessmentId) test.skip();
    await page.goto(`/?assessment_id=${assessmentId}`);
    await page.getByTestId("chat-fab").click();
    await expect(page).toHaveURL(/\/chat/);
  });
});
