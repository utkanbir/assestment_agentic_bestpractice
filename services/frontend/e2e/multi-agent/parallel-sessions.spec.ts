import { test, expect } from "@playwright/test";
import { seedAssessmentWithTasks } from "../fixtures/api";
import { InterviewRoomPage } from "../pages/InterviewRoomPage";

test.describe("Interview flow (replaces ParallelSessions)", () => {
  test("interview room loads for assessment with tasks", async ({ page }) => {
    const { assessmentId } = await seedAssessmentWithTasks(["kubernetes", "lakehouse", "governance"]);
    const interviewPage = new InterviewRoomPage(page);
    await interviewPage.goto(assessmentId);
    await interviewPage.expectNoPageErrors();
  });

  test("interview tab accessible from overview link", async ({ page }) => {
    const { assessmentId } = await seedAssessmentWithTasks(["kubernetes"]);
    await page.goto(`/?assessment_id=${assessmentId}`);
    await page.getByTestId("workstream-card-kubernetes").getByRole("button", { name: "Interview" }).click();
    await expect(page).toHaveURL(new RegExp(`/interview.*assessment_id=${assessmentId}`));
  });
});
