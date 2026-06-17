import { type Page, expect } from "@playwright/test";
import { ALL_WORKSTREAMS, WORKSTREAM_LABELS } from "../fixtures/api";
import * as path from "path";
import * as fs from "fs";
import * as os from "os";

export class AjanYonetimiPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto("/ajan-yonetimi");
    await expect(this.page.getByText("Ajan performansı ve bilgi yönetimi")).toBeVisible();
  }

  async expectAllWorkstreamSidebarItems() {
    for (const ws of ALL_WORKSTREAMS) {
      await expect(this.page.getByRole("button", { name: WORKSTREAM_LABELS[ws] })).toBeVisible();
    }
  }

  async selectWorkstream(workstream: string) {
    await this.page.getByRole("button", { name: WORKSTREAM_LABELS[workstream] }).click();
  }

  async expectMetricsVisible() {
    await expect(this.page.locator("main").getByText("Yükleniyor…")).toBeHidden({ timeout: 30_000 });
    await expect(this.page.locator("main").getByText("Toplam Soru", { exact: true })).toBeVisible({ timeout: 10_000 });
    await expect(this.page.locator("main").getByText("Yüklü Döküman", { exact: true })).toBeVisible();
  }

  async switchToDocsTab() {
    await this.page.getByRole("button", { name: "📚 Bilgi Tabanı" }).click();
  }

  async uploadTxtFile(filename: string, content: string) {
    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "e2e-doc-"));
    const filePath = path.join(tmpDir, filename);
    fs.writeFileSync(filePath, content, "utf-8");

    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    await expect(this.page.locator("main").getByText("⏳ Yükleniyor…")).toBeVisible({ timeout: 5_000 });
    await expect(this.page.locator("main").getByText("⏳ Yükleniyor…")).toBeHidden({ timeout: 120_000 });
    await expect(this.page.getByText(filename, { exact: true })).toBeVisible({ timeout: 10_000 });
  }
}
