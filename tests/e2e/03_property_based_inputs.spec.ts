import { test, expect } from '@playwright/test';
import fc from 'fast-check';
import { loginIfNeeded } from './utils';

test('Fuzz: 会社情報フォームが例外を出さない', async ({ page }) => {
  await loginIfNeeded(page);
  await page.goto('/company/info');

  await fc.assert(
    fc.asyncProperty(
      fc.record({
        name: fc.string({ minLength: 1, maxLength: 64 }),
        city: fc.string({ minLength: 1, maxLength: 50 }),
        date: fc.date(),
        phone: fc.string({ minLength: 1, maxLength: 20 })
      }),
      async (r) => {
        // 主要項目のみ（実装に合わせて要調整）
        const today = r.date.toISOString().slice(0,10);
        await page.getByLabel(/法人名|会社名/).fill(r.name + '🙂');
        await page.getByLabel(/市区町村/).fill(r.city);
        const dateInput = page.getByLabel(/設立|年月日/).first();
        if (await dateInput.isVisible()) await dateInput.fill(today);
        const phoneInput = page.getByLabel(/電話/).first();
        if (await phoneInput.isVisible()) await phoneInput.fill(r.phone);
        const save = page.getByRole('button', { name: /保存|更新|次へ/ });
        if (await save.isVisible()) await save.click();

        // 致命的エラーが出ないこと
        const fatal = page.getByText(/Traceback|500|例外|エラー/);
        expect(await fatal.count()).toBe(0);
      }
    ),
    { numRuns: 20, endOnFailure: true }
  );
});

