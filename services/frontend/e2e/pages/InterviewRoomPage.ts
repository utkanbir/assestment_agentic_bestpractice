import { type Page, expect } from "@playwright/test";
import { ALL_WORKSTREAMS, WORKSTREAM_LABELS } from "../fixtures/api";

export class InterviewRoomPage {
  constructor(private page: Page) {}

  async goto(assessmentId: string) {
    await this.page.goto(`/interview?assessment_id=${assessmentId}`);
  }

  async expectAllWorkstreamTabs() {
    for (const ws of ALL_WORKSTREAMS) {
      await expect(this.page.getByTestId(`ws-tab-${ws}`)).toBeVisible();
    }
  }

  async selectTab(workstream: string) {
    await this.page.getByTestId(`ws-tab-${workstream}`).click();
  }

  async expectWorkstreamHeading(workstream: string) {
    await expect(
      this.page.getByRole("heading", { name: WORKSTREAM_LABELS[workstream], level: 2 }),
    ).toBeVisible();
  }

  async expectQuestionsLoaded(minCount = 1) {
    await expect(this.page.getByText("Sorular yükleniyor…")).toBeHidden({ timeout: 60_000 });
    await expect(this.page.getByText(/Sorular \(\d+\)/)).toBeVisible({ timeout: 60_000 });
    await expect(this.page.locator("span", { hasText: /^S\d+$/ }).first()).toBeVisible();
    const countText = await this.page.getByText(/Sorular \(\d+\)/).textContent();
    const match = countText?.match(/\((\d+)\)/);
    expect(match).toBeTruthy();
    expect(Number(match![1])).toBeGreaterThanOrEqual(minCount);
  }

  private async firstQuestionText(): Promise<string | null> {
    const badge = this.page.locator("span", { hasText: /^S1$/ }).first();
    await expect(badge).toBeVisible({ timeout: 60_000 });
    return badge.locator("xpath=following-sibling::p[1]").textContent();
  }

  async expectDifferentQuestionSets(wsA: string, wsB: string) {
    await this.selectTab(wsA);
    await this.expectWorkstreamHeading(wsA);
    await this.expectQuestionsLoaded();
    const firstA = await this.firstQuestionText();

    await this.selectTab(wsB);
    await this.expectWorkstreamHeading(wsB);
    await expect(this.page.getByText("Sorular yükleniyor…")).toBeHidden({ timeout: 60_000 });
    await this.expectQuestionsLoaded();
    const firstB = await this.firstQuestionText();

    expect(firstA).toBeTruthy();
    expect(firstB).toBeTruthy();
    expect(firstA).not.toEqual(firstB);
  }

  async expectStatusBarVisible() {
    await expect(this.page.getByText("Ajan Durumu")).toBeVisible({ timeout: 15_000 });
  }
}
