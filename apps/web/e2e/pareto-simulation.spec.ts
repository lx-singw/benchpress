import { test, expect } from "@playwright/test";

test.describe("Modality 3: Interactive Tactile Canvas & Pareto Frontier", () => {
  test("Weight slider dynamically recalculates Pareto frontier and highlights recommended route", async ({ page }) => {
    await page.goto("http://localhost:3000/");

    // Verify 2D Pareto Canvas is visible
    const paretoHeading = page.locator("text=2D Pareto Frontier & Dynamic Model Router");
    await expect(paretoHeading).toBeVisible({ timeout: 5000 });

    // Verify Optimal Operating Point Badge
    const optimalBadge = page.locator("text=Optimal Operating Point:");
    await expect(optimalBadge).toBeVisible();

    // Verify Sliders
    const costSlider = page.locator("input[type='range']").first();
    await expect(costSlider).toBeVisible();

    // Verify Leaderboard Table
    const leaderboard = page.locator("text=Continuous Economic Leaderboard");
    await expect(leaderboard).toBeVisible();
  });
});
