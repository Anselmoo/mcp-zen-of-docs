const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/visual',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: 'http://127.0.0.1:8000',
    browserName: 'chromium',
    colorScheme: 'light',
    locale: 'en-US',
    timezoneId: 'UTC',
    viewport: { width: 1440, height: 900 },
  },
  webServer: {
    command: 'uv run zensical serve --dev-addr 127.0.0.1:8000',
    url: 'http://127.0.0.1:8000',
    reuseExistingServer: !process.env.CI,
    stdout: 'ignore',
    stderr: 'pipe',
    timeout: 120 * 1000,
  },
});
