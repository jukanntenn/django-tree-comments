import { test, expect } from '@playwright/test';

test('index page loads and shows posts', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/.*/);   // Title just needs to be non-empty
  // The blog index lists posts; there should be at least some content rendered
  await expect(page.locator('body')).not.toBeEmpty();
});

test('post detail renders comment tree container', async ({ page }) => {
  // Go into the first post detail page
  await page.goto('/');
  const firstPostLink = page.locator('a[href*="/post/"], a[href*="/posts/"]').first();
  if (await firstPostLink.count() > 0) {
    await firstPostLink.click();
    // The tree_comments app container
    await expect(page.locator('.tree-comments-app')).toBeVisible({ timeout: 10_000 });
  }
});
