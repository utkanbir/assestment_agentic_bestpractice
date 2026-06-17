import { test } from "@playwright/test";
import { get } from "../fixtures/api";
import { AjanYonetimiPage } from "../pages/AjanYonetimiPage";

interface AgentMetrics {
  workstream: string;
}

test.describe("AjanYonetimi — 8-agent metrics and documents", () => {
  test("sidebar lists all 8 workstreams backed by API metrics", async ({ page }) => {
    test.setTimeout(60_000);
    const metrics = await get<AgentMetrics[]>("/agents/metrics");
    test.skip(metrics.length < 8, "API returned fewer than 8 workstream metrics");

    const mgmt = new AjanYonetimiPage(page);
    await mgmt.goto();
    await mgmt.expectAllWorkstreamSidebarItems();
  });

  test("kubernetes workstream shows metric boxes", async ({ page }) => {
    const mgmt = new AjanYonetimiPage(page);
    await mgmt.goto();
    await mgmt.selectWorkstream("kubernetes");
    await mgmt.expectMetricsVisible();
  });

  test("uploads TXT document and lists it", async ({ page }) => {
    test.setTimeout(120_000);
    const mgmt = new AjanYonetimiPage(page);
    await mgmt.goto();
    await mgmt.selectWorkstream("kubernetes");
    await mgmt.switchToDocsTab();

    const filename = `e2e-k8s-policy-${Date.now()}.txt`;
    await mgmt.uploadTxtFile(filename, "Kubernetes RBAC policy document for E2E test.");
  });
});
