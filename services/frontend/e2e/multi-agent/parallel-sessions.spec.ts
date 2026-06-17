import { test } from "@playwright/test";
import { seedAssessmentWithTasks } from "../fixtures/api";
import { ParallelSessionsPage } from "../pages/ParallelSessionsPage";

const PANEL_WORKSTREAMS = ["kubernetes", "ingestion", "cdp"] as const;

test.describe("ParallelSessions — multi-panel grid", () => {
  test("shows 3 session panels with workstream labels", async ({ page }) => {
    const { assessmentId } = await seedAssessmentWithTasks([...PANEL_WORKSTREAMS]);
    const sessionsPage = new ParallelSessionsPage(page);
    await sessionsPage.goto(assessmentId);

    await sessionsPage.expectActiveCount(3);
    await sessionsPage.expectPanelCount(3);
    for (const ws of PANEL_WORKSTREAMS) {
      await sessionsPage.expectPanelWorkstream(ws);
    }
  });

  test("interview tab loads question bank in a panel", async ({ page }) => {
    const { assessmentId } = await seedAssessmentWithTasks([...PANEL_WORKSTREAMS]);
    const sessionsPage = new ParallelSessionsPage(page);
    await sessionsPage.goto(assessmentId);

    await sessionsPage.openInterviewTab("kubernetes");
    await sessionsPage.expectInterviewQuestionsLoaded("kubernetes");
    await sessionsPage.expectNoPageErrors();
  });

  test("switches between panel tabs without errors", async ({ page }) => {
    const { assessmentId } = await seedAssessmentWithTasks([...PANEL_WORKSTREAMS]);
    const sessionsPage = new ParallelSessionsPage(page);
    await sessionsPage.goto(assessmentId);

    for (const ws of PANEL_WORKSTREAMS) {
      const panel = page.getByTestId(`session-panel-${ws}`);
      await panel.getByRole("button", { name: "Canlı Chat" }).click();
      await panel.getByRole("button", { name: /Mülakat/ }).click();
    }
    await sessionsPage.expectNoPageErrors();
  });
});
