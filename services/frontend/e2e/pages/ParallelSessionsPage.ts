import { type Page, expect } from "@playwright/test";
import { WORKSTREAM_LABELS } from "../fixtures/api";

export class ParallelSessionsPage {
  constructor(private page: Page) {}

  async goto(assessmentId: string) {
    await this.page.goto(`/sessions?assessment_id=${assessmentId}`);
    await expect(this.page.getByRole("heading", { name: "Paralel Oturumlar" })).toBeVisible();
  }

  async expectActiveCount(count: number) {
    await expect(this.page.getByText(`${count} workstream ajanı eş zamanlı çalışıyor`)).toBeVisible();
  }

  async expectPanelCount(count: number) {
    const panels = this.page.locator('[data-testid^="session-panel-"]');
    await expect(panels).toHaveCount(count);
  }

  async expectPanelWorkstream(workstream: string) {
    const panel = this.page.getByTestId(`session-panel-${workstream}`);
    await expect(panel).toBeVisible();
    await expect(panel.getByRole("heading", { name: WORKSTREAM_LABELS[workstream] })).toBeVisible();
  }

  async openInterviewTab(workstream: string) {
    const panel = this.page.getByTestId(`session-panel-${workstream}`);
    await panel.getByRole("button", { name: /Mülakat/ }).click();
  }

  async expectInterviewQuestionsLoaded(workstream: string) {
    const panel = this.page.getByTestId(`session-panel-${workstream}`);
    await expect(panel.getByRole("button", { name: "+ Yeni Mülakat" })).toBeVisible();
    await panel.getByRole("button", { name: "+ Yeni Mülakat" }).click();
    await expect(panel.getByRole("heading", { name: "Yeni Mülakat", level: 4 })).toBeVisible();
    await panel.getByPlaceholder("Görüşülen kişi adı *").fill("E2E Consultant");
    await panel.getByRole("button", { name: "Oluştur" }).click();
    await expect(panel.getByText("Soru bankasından sorular yükleniyor…")).toBeHidden({
      timeout: 30_000,
    });
    await expect(panel.locator("p strong").first()).toBeVisible({ timeout: 30_000 });
  }

  async expectNoPageErrors() {
    const errors: string[] = [];
    this.page.on("pageerror", (err) => errors.push(err.message));
    await this.page.waitForTimeout(500);
    expect(errors.filter((e) => e.includes("WebSocket"))).toHaveLength(0);
  }
}
