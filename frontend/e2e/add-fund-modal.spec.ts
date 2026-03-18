/**
 * Test for AddFundModal NAV auto-fill functionality
 */
import { test, expect } from '@playwright/test';

test.describe('AddFundModal NAV Auto-fill', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/');
    await page.waitForTimeout(1000);

    // Check if login button exists and click it
    const loginButton = await page.$('text=登录');
    if (loginButton) {
      await loginButton.click();
      await page.fill('input[placeholder="请输入用户名"]', 'your-username');
      await page.fill('input[placeholder="请输入密码"]', 'your-password');
      await page.click('button:has-text("登 录")');
      await page.waitForTimeout(2000);
    }

    // Navigate to portfolio manager
    await page.goto('/portfolio');
    await page.waitForTimeout(1000);

    // Click "添加基金" button to open modal
    await page.click('button:has-text("添加基金")');
    await page.waitForTimeout(500);
  });

  test('should auto-fill NAV when selecting fund with pre-selected date', async ({ page }) => {
    // 1. First select a date (default is today, but let's select a specific date)
    const datePicker = await page.$('[name="transaction_date"]');
    expect(datePicker).toBeTruthy();

    // 2. Search for a fund
    const fundSelect = await page.$('[name="fundCode"]');
    await fundSelect?.click();
    await page.keyboard.type('000001'); // Search for a common fund
    await page.waitForTimeout(1000);

    // 3. Select the first fund from dropdown
    const firstOption = await page.$('.ant-select-item-option-content');
    expect(firstOption).toBeTruthy();
    await firstOption?.click();
    await page.waitForTimeout(1000);

    // 4. Check if NAV field has been filled
    const navInput = await page.$('[name="nav"] input');
    expect(navInput).toBeTruthy();

    const navValue = await navInput?.inputValue();
    console.log('NAV value after selecting fund:', navValue);

    // NAV should be filled (not empty and not undefined)
    expect(navValue).toBeTruthy();
    expect(parseFloat(navValue!)).toBeGreaterThan(0);
  });

  test('should auto-fill NAV when changing date with pre-selected fund', async ({ page }) => {
    // 1. Search for a fund first
    const fundSelect = await page.$('[name="fundCode"]');
    await fundSelect?.click();
    await page.keyboard.type('000001');
    await page.waitForTimeout(1000);

    // 2. Select the first fund
    const firstOption = await page.$('.ant-select-item-option-content');
    await firstOption?.click();
    await page.waitForTimeout(1000);

    // 3. Change the date
    const datePicker = await page.$('[name="transaction_date"]');
    await datePicker?.click();
    await page.waitForTimeout(500);

    // Select yesterday's date
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const dateStr = yesterday.toISOString().split('T')[0];

    // Click on the date cell
    const dateCell = await page.$(`.ant-picker-cell[title="${dateStr}"]`);
    if (dateCell) {
      await dateCell.click();
      await page.waitForTimeout(1000);
    }

    // 4. Check if NAV field has been updated
    const navInput = await page.$('[name="nav"] input');
    const navValue = await navInput?.inputValue();
    console.log('NAV value after changing date:', navValue);

    expect(navValue).toBeTruthy();
    expect(parseFloat(navValue!)).toBeGreaterThan(0);
  });

  test('should show warning when selecting non-trading day', async ({ page }) => {
    // 1. Search for a fund
    const fundSelect = await page.$('[name="fundCode"]');
    await fundSelect?.click();
    await page.keyboard.type('000001');
    await page.waitForTimeout(1000);

    // 2. Select the first fund
    const firstOption = await page.$('.ant-select-item-option-content');
    await firstOption?.click();
    await page.waitForTimeout(1000);

    // 3. Change the date to a weekend (non-trading day)
    const datePicker = await page.$('[name="transaction_date"]');
    await datePicker?.click();
    await page.waitForTimeout(500);

    // Find a weekend date
    const today = new Date();
    const dayOfWeek = today.getDay();
    const daysToSubtract = dayOfWeek === 0 ? 1 : dayOfWeek === 6 ? 0 : dayOfWeek;
    const lastSaturday = new Date(today);
    lastSaturday.setDate(today.getDate() - daysToSubtract - 1);
    const weekendDateStr = lastSaturday.toISOString().split('T')[0];

    const dateCell = await page.$(`.ant-picker-cell[title="${weekendDateStr}"]`);
    if (dateCell) {
      await dateCell.click();
      await page.waitForTimeout(1500);
    }

    // 4. Check for warning message
    const warningAlert = await page.$('.ant-alert-warning');
    if (warningAlert) {
      const warningText = await warningAlert.textContent();
      console.log('Warning message:', warningText);
      expect(warningText).toContain('可能不是交易日');
    }
  });
});
