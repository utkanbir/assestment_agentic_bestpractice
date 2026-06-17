import { test } from "@playwright/test";
import { createAssessment } from "../fixtures/api";
import { InterviewRoomPage } from "../pages/InterviewRoomPage";

test.describe("InterviewRoom — workstream tabs", () => {
  test("shows 8 workstream tabs", async ({ page }) => {
    const { id } = await createAssessment();
    const room = new InterviewRoomPage(page);
    await room.goto(id);
    await room.expectAllWorkstreamTabs();
  });

  test("kubernetes tab loads questions from question bank", async ({ page }) => {
    const { id } = await createAssessment();
    const room = new InterviewRoomPage(page);
    await room.goto(id);

    await room.selectTab("kubernetes");
    await room.expectWorkstreamHeading("kubernetes");
    await room.expectQuestionsLoaded(1);
  });

  test("lakehouse tab shows different question set", async ({ page }) => {
    const { id } = await createAssessment();
    const room = new InterviewRoomPage(page);
    await room.goto(id);

    await room.expectDifferentQuestionSets("kubernetes", "lakehouse");
  });

  test("agent status bar appears after loading", async ({ page }) => {
    const { id } = await createAssessment();
    const room = new InterviewRoomPage(page);
    await room.goto(id);
    await room.selectTab("kubernetes");
    await room.expectStatusBarVisible();
  });
});
