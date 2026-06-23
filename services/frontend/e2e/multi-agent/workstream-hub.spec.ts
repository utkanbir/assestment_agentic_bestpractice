import { test, expect } from "@playwright/test";
import { createAssessment, listTasks } from "../fixtures/api";

test.describe("Workstream hub on Genel Bakış (S17)", () => {
  test("launch workstream from overview", async ({ page }) => {
    const { id } = await createAssessment("S17-E2E");
    await page.goto(`/?assessment_id=${id}`);
    await page.getByTestId("launch-agent-kubernetes").click();
    await page.getByTestId("launch-agent-lakehouse").click();
    const tasks = await listTasks(id);
    expect(tasks.map((t) => t.workstream)).toEqual(
      expect.arrayContaining(["kubernetes", "lakehouse"]),
    );
  });
});
