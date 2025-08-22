import { test, expect } from '@playwright/test';
import { loginIfNeeded } from './utils';

test('Monkey: 変な操作でも落ちない', async ({ page }) => {
  await loginIfNeeded(page);
  const errors: string[] = [];
  page.on('console', (msg) => { if (msg.type() === 'error') errors.push(msg.text()); });

  await page.goto('/company/select_software');
  await page.addScriptTag({ url: 'https://unpkg.com/gremlins.js' });
  await page.evaluate(async () => {
    await new Promise<void>((resolve) => {
      // @ts-ignore
      window.gremlins.createHorde({
        species: [
          // @ts-ignore
          window.gremlins.species.clicker().clickTypes(['click','dblclick']),
          // @ts-ignore
          window.gremlins.species.formFiller(),
          // @ts-ignore
          window.gremlins.species.typer(),
          // @ts-ignore
          window.gremlins.species.scroller()
        ],
        // @ts-ignore
        mogwais: [window.gremlins.mogwais.gizmo()],
      }).after(() => resolve()).unleash({ nb: 800, delay: 5 });
    });
  });

  expect.soft(errors, `Console errors: ${errors.join('\\n')}`).toHaveLength(0);
});

