import { test, expect } from '@playwright/test';
import { loginIfNeeded } from './utils';

test('State: 戻る/進む/リロード/多タブで壊れない', async ({ page, context }) => {
  await loginIfNeeded(page);
  await page.goto('/company/select_software');
  const combo = page.getByRole('combobox').first();
  if (await combo.isVisible()) await combo.selectOption('moneyforward');

  for (let i = 0; i < 8; i++) {
    const r = Math.random();
    if (r < 0.25) await page.goBack({ waitUntil: 'load' }).catch(() => {});
    else if (r < 0.5) await page.goForward({ waitUntil: 'load' }).catch(() => {});
    else if (r < 0.75) await page.reload({ waitUntil: 'load' });
    else {
      const p2 = await context.newPage();
      await p2.goto('/company/upload/journals');
      await p2.close();
    }
  }

  await page.goto('/company/upload/journals');
  await expect(page.locator('input[type=\"file\"]')).toBeVisible();
});

