import { test, expect } from "@playwright/test";

test.describe("Modality 2: Computer Vision Error Diagnostics", () => {
  test("Clicking sample trace triggers Gemini Vision OCR analysis and matched recipe", async ({ page }) => {
    await page.goto("http://localhost:3000/");

    // Verify Dropzone is visible
    const dropzone = page.locator("text=Screenshot Error Ingestor");
    await expect(dropzone).toBeVisible({ timeout: 5000 });

    // Click dropzone area to trigger sample trace
    const dropArea = page.locator("text=Drop screenshot here or click for sample trace");
    await dropArea.click();

    // Verify Matched Benchmark Vector displays
    const matchedVector = page.locator("text=Matched Benchmark Vector:");
    await expect(matchedVector).toBeVisible({ timeout: 6000 });
    await expect(page.locator("text=django.core.exceptions.ValidationError")).toBeVisible();
  });
});
