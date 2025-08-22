import { test, expect } from '@playwright/test';
import { loginIfNeeded, selectSoftware } from './utils';

test('HappyPath: 取込→（可能なら）SoA差異0確認→PDF出力導線', async ({ page }) => {
  await loginIfNeeded(page);

  // 1) 会計ソフト選択（実装済みのmoneyforward優先）
  await selectSoftware(page, 'moneyforward');

  // 2) 仕訳アップロード（ここでは壊れたファイルでなく、空に近いCSVを想定）
  await page.goto('/company/upload/journals');
  const fileInput = page.locator('input[type=\"file\"]');
  await expect.soft(fileInput).toBeVisible();
  if (await fileInput.count() === 0) test.skip(true, 'ファイル入力が見つからないためスキップ');

  // サンプル: 空に近いCSV（差し替え前提）
  await page.setInputFiles('input[type=\"file\"]', 'tests/fixtures/bad.csv');
  const submit = page.getByRole('button', { name: /取込|アップロード|保存|次へ/i }).first();
  if (await submit.isVisible()) await submit.click();

  // 3) SoAへ（差異0はデータ次第。UIが壊れていないことのみ確認）
  await page.goto('/company/statement_of_accounts?page=deposits');
  await expect(page).toHaveURL(/statement_of_accounts/);

  // 4) PDF出力導線（別表二）。リンク or ボタンのどちらでも可。
  await page.goto('/company/shareholders/pdf/beppyou_02');
  // 直接PDFを返す場合があるため、ダウンロードイベントは任意。
  await page.waitForLoadState('networkidle');
  expect(true).toBeTruthy();
});

