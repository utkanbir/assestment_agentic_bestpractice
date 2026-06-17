import { test, expect } from "@playwright/test";
import { createAssessment, listTasks } from "../fixtures/api";
import { AgentSelectionPage } from "../pages/AgentSelectionPage";

test.describe("AgentSelection — multi-agent launch", () => {
  test("renders 8 workstream cards", async ({ page }) => {
    const { id } = await createAssessment();
    const agentPage = new AgentSelectionPage(page);
    await agentPage.goto(id);
    await agentPage.expectAllWorkstreamCards();
  });

  test("multi-select and launch creates tasks", async ({ page }) => {
    test.setTimeout(120_000);
    const { id } = await createAssessment();
    const agentPage = new AgentSelectionPage(page);
    await agentPage.goto(id);

    const selected = ["kubernetes", "lakehouse", "cdp"] as const;
    await agentPage.selectWorkstreams(...selected);
    await agentPage.expectLaunchEnabled(3);
    await agentPage.launch();

    await agentPage.expectNavigatedToSessions(id);

    const tasks = await listTasks(id);
    const workstreams = tasks.map((t) => t.workstream);
    for (const ws of selected) {
      expect(workstreams).toContain(ws);
    }
    expect(tasks.filter((t) => selected.includes(t.workstream as typeof selected[number]))).toHaveLength(3);
  });
});
