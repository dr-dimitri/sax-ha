import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./browser",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:5190",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "webkit-light-de",
      testMatch: "tariff-editor.spec.ts",
      use: {
        ...devices["Desktop Safari"],
        locale: "de-DE",
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "desktop-light-de",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "desktop-dark-en",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "mobile-light-de",
      use: { ...devices["Pixel 7"], viewport: { width: 390, height: 844 } },
    },
    {
      name: "mobile-dark-en",
      use: { ...devices["Pixel 7"], viewport: { width: 390, height: 844 } },
    },
  ],
  webServer: {
    command: "npm run preview:browser",
    url: "http://127.0.0.1:5190",
    reuseExistingServer: !process.env.CI,
  },
});
