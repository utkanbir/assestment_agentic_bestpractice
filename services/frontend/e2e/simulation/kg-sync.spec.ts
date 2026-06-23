import { test, expect } from "@playwright/test";

test.describe("S21 KG sync for simulated assessment", () => {
  test("knowledge graph page shows simulated banner", async ({ page, request }) => {
    const suffix = Math.random().toString(36).slice(2, 8);
    const res = await request.post("http://localhost:8000/api/v1/assessments/simulated", {
      data: {
        client_name: "E2E-KG",
        project_name: `KG-${suffix}`,
        company_profile: { industry: "retail" },
      },
    });
    expect(res.ok()).toBeTruthy();
    const body = await res.json();
    const assessmentId = body.id as string;

    await page.goto(`/kg-graf?assessment_id=${assessmentId}`);
    await expect(page.getByTestId("kg-simulated-banner")).toBeVisible({ timeout: 15000 });
  });
});
