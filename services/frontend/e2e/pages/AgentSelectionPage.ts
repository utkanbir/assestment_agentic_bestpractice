import { type Page, expect } from "@playwright/test";
import { ALL_WORKSTREAMS, WORKSTREAM_LABELS } from "../fixtures/api";

export class AgentSelectionPage {
  constructor(private page: Page) {}

  async goto(assessmentId: string) {
    await this.page.goto(`/agents?assessment_id=${assessmentId}`);
    await expect(this.page.getByRole("heading", { name: "Ajan Seçimi" })).toBeVisible();
  }

  async expectAllWorkstreamCards() {
    for (const ws of ALL_WORKSTREAMS) {
      await expect(this.page.getByTestId(`agent-card-${ws}`)).toBeVisible();
      await expect(
        this.page.getByTestId(`agent-card-${ws}`).getByRole("heading", {
          name: WORKSTREAM_LABELS[ws],
        }),
      ).toBeVisible();
    }
  }

  async selectWorkstreams(...workstreams: string[]) {
    for (const ws of workstreams) {
      await this.page.getByTestId(`agent-card-${ws}`).click();
    }
  }

  async expectLaunchEnabled(count: number) {
    const btn = this.page.getByTestId("agent-launch-btn");
    await expect(btn).toBeEnabled();
    await expect(btn).toContainText(`${count} Ajan Başlat`);
  }

  async launch() {
    const btn = this.page.getByTestId("agent-launch-btn");
    await btn.click();
    await expect(btn).toContainText("Task'lar oluşturuluyor", { timeout: 5_000 });
  }

  async expectNavigatedToSessions(assessmentId: string) {
    await expect(this.page).toHaveURL(
      new RegExp(`/sessions\\?assessment_id=${assessmentId}`),
      { timeout: 60_000 },
    );
    await expect(this.page.getByRole("heading", { name: "Paralel Oturumlar" })).toBeVisible();
  }
}
