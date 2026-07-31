import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,           // e2e shares a single Django live_server; do not parallelize
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,                     // Single worker to match the single live_server
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:8000',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    // Automatically start Django runserver as the system under test (live_server equivalent)
    command: 'TREE_COMMENTS_DB_BACKEND=postgres TREE_COMMENTS_DB_NAME=tree_comments_e2e TREE_COMMENTS_DB_PORT=5433 uv run python manage.py runserver 127.0.0.1:8000 --noreload',
    url: 'http://127.0.0.1:8000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
    cwd: '../examples/default',
  },
});
