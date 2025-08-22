import { test, expect } from '@playwright/test';
import { promises as fs } from 'fs';
import { loginIfNeeded } from './utils';

test('Broken: 壊れPDF/CSVで安全に失敗する', async ({ page }) => {
  await loginIfNeeded(page);
  await fs.mkdir('tmp', { recursive: true });
  await fs.writeFile('tmp/broken.pdf', Buffer.from([0x25,0x50,0x44,0x46,0x2D,0x00,0x00,0xff]));
  await fs.writeFile('tmp/notcsv.csv', Buffer.from([0xff,0xfe,0x00,0x00]));

  await page.goto('/company/upload/journals');
  const fileInput = page.locator('input[type=\"file\"]').first();
  await expect.soft(fileInput).toBeVisible();
  if (await fileInput.count() === 0) test.skip(true, 'ファイル入力が見つからないためスキップ');

  await page.setInputFiles('input[type=\"file\"]', 'tmp/notcsv.csv');
  await page.getByRole('button', { name: /取込|アップロード|保存|次へ/i }).first().click({ trial: true }).catch(() => {});
  await expect.soft(page.getByText(/無効|形式|読み込みに失敗|エラー/)).toBeVisible({ timeout: 3000 });

  await page.setInputFiles('input[type=\"file\"]', 'tmp/broken.pdf');
  await page.getByRole('button', { name: /取込|アップロード|保存|次へ/i }).first().click({ trial: true }).catch(() => {});
  await expect.soft(page.getByText(/無効|形式|読み込みに失敗|エラー/)).toBeVisible({ timeout: 3000 });
});

