import { test, expect } from "@playwright/test";

test.describe("Modality 1: WebRTC Voice Intelligence Copilot", () => {
  test("Pressing V opens Voice Copilot Drawer and renders AudioWaveformCanvas", async ({ page }) => {
    await page.goto("http://localhost:3000/");

    // Press 'V' to trigger global voice shortcut
    await page.keyboard.press("v");

    // Assert Drawer is visible
    const voiceDrawer = page.locator("text=Gemini Live Voice Copilot");
    await expect(voiceDrawer).toBeVisible({ timeout: 5000 });

    // Assert AudioWaveformCanvas is mounted
    const waveformCanvas = page.locator("canvas");
    await expect(waveformCanvas).toBeVisible();

    // Click quick diagnostic prompt
    const quickPrompt = page.locator("text=Why did Turn 3 fail?");
    if (await quickPrompt.isVisible()) {
      await quickPrompt.click();
      await expect(page.locator("text=Autonomous AST Healer")).toBeVisible({ timeout: 4000 });
    }
  });
});
