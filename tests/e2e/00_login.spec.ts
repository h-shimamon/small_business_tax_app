import { test, expect } from '@playwright/test';
import { loginIfNeeded } from './utils';

test('Login: 認証できるか（資格情報が無ければソフトスキップ）', async ({ page }) => {
  await loginIfNeeded(page);
  // ログインできていれば /company/ 配下に居るはず
  await expect(/\/company\//.test(page.url())).toBeTruthy();
});

