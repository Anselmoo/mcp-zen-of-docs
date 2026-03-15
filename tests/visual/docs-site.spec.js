const { test, expect } = require('@playwright/test');

const chapterPages = [
  { slug: 'guides', path: '/guides/' },
  { slug: 'frameworks', path: '/frameworks/' },
  { slug: 'contributing', path: '/contributing/' },
];

async function loadPage(page, path) {
  await page.goto(path, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle');
  await page.evaluate(async () => {
    if (document.fonts) {
      await document.fonts.ready;
    }
  });
}

async function findHomepageCardsSection(page) {
  const candidates = [
    page.locator('[data-visual="advanced-features"]'),
    page.locator('#advanced-features'),
    page.locator('.home-advanced-features'),
    page.locator('section').filter({
      has: page.getByRole('heading', { name: /advanced features/i }),
    }),
    page.locator('main .grid.cards').first(),
  ];

  for (const locator of candidates) {
    if ((await locator.count()) > 0) {
      return locator.first();
    }
  }

  throw new Error('Could not find the homepage advanced-features or card section.');
}

test.describe('docs site visual regression', () => {
  test('captures the homepage hero', async ({ page }) => {
    await loadPage(page, '/');

    const hero = page.locator('.zen-hero');
    await expect(hero).toBeVisible();
    await expect(hero).toHaveScreenshot('home-hero.png', {
      animations: 'disabled',
      caret: 'hide',
      maxDiffPixels: 1200,
    });
  });

  test('captures the homepage advanced features or cards section', async ({ page }) => {
    await loadPage(page, '/');

    const section = await findHomepageCardsSection(page);
    await expect(section).toBeVisible();
    await expect(section).toHaveScreenshot('home-advanced-features.png', {
      animations: 'disabled',
      caret: 'hide',
    });
  });

  for (const chapter of chapterPages) {
    test(`captures the ${chapter.slug} chapter banner`, async ({ page }) => {
      await loadPage(page, chapter.path);

      const banner = page.locator('figure.chapter-banner');
      await expect(banner).toBeVisible();
      await expect(banner).toHaveScreenshot(`${chapter.slug}-chapter-banner.png`, {
        animations: 'disabled',
        caret: 'hide',
      });
    });
  }
});
