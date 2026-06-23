import { test, expect } from "@playwright/test";
import { createAssessment, listTasks } from "../fixtures/api";

test.describe("Workstream launch from Genel Bakış (replaces AgentSelection)", () => {
  test("renders 8 workstream cards when assessment selected", async ({ page }) => {
    const { id } = await createAssessment();
    await page.goto(`/?assessment_id=${id}`);
    for (const ws of ["kubernetes", "lakehouse", "cdp"]) {
      await expect(page.getByTestId(`workstream-card-${ws}`)).toBeVisible();
    }
  });

  test("launch creates tasks", async ({ page }) => {
    test.setTimeout(120_000);
    const { id } = await createAssessment();
    await page.goto(`/?assessment_id=${id}`);
    const selected = ["kubernetes", "lakehouse", "cdp"] as const;
    for (const ws of selected) {
      await page.getByTestId(`launch-agent-${ws}`).click();
    }
    const tasks = await listTasks(id);
    for (const ws of selected) {
      expect(tasks.map((t) => t.workstream)).toContain(ws);
    }
  });
});
