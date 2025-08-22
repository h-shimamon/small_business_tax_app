import { expect, Page } from '@playwright/test';

export async function loginIfNeeded(page: Page) {
  // 既にログイン済みならスキップ
  await page.goto('/company/info');
  if (!/\/company\/login/.test(page.url())) return;

  const user = process.env.TEST_USERNAME || '';
  const pass = process.env.TEST_PASSWORD || '';
  if (!user || !pass) {
    // 資格情報がない場合はスキップ理由を明示
    return expect.soft(false, 'Set TEST_USERNAME/TEST_PASSWORD to run authenticated tests').toBe(true);
  }

  await page.goto('/company/login');
  await page.getByLabel(/ユーザー名|username/i).fill(user);
  await page.getByLabel(/パスワード|password/i).fill(pass);
  await page.getByRole('button', { name: /ログイン|login/i }).click();

  // ログイン結果を軽く確認（会社情報に遷移 or ログイン必須が外れる）
  await page.waitForLoadState('networkidle');
  expect(/\/company\//.test(page.url())).toBeTruthy();
}

export async function selectSoftware(page: Page, value: 'moneyforward' | 'freee' | 'yayoi' | 'other' = 'moneyforward') {
  await page.goto('/company/select_software');
  // RadioFieldのvalueに合わせて選択
  const radio = page.locator(`input[type=\"radio\"][value=\"${value}\"]`);
  if (await radio.count()) {
    await radio.first().check();
  } else {
    // 互換: セレクトやボタンの場合
    const combo = page.getByRole('combobox').first();
    if (await combo.isVisible()) await combo.selectOption(value);
  }
  const submit = page.getByRole('button', { name: /次へ|進む|開始|保存/i }).first();
  if (await submit.isVisible()) await submit.click();
}

