/**
 * Date utility functions for fund valuation system.
 */

/**
 * 根据估值时间判断应该显示的估值日期
 * 规则：
 * - 如果时间在 00:00-09:30 之间，属于昨天收盘后的数据，显示昨天日期
 * - 如果时间在 09:30-15:00 之间，属于当天实时数据，显示当天日期
 * - 如果时间在 15:00-23:59 之间，也是当天的数据
 *
 * @param dateNum 日期数字 (YYYYMMDD)
 * @param timeStr 时间字符串 (HH:MM)
 * @returns 格式化后的日期字符串 (MM-DD)
 */
export function getEstimationDateLabel(dateNum: number, timeStr?: string): string {
  if (!dateNum) return '';

  // Parse dateNum (YYYYMMDD) to year, month, day
  const year = Math.floor(dateNum / 10000);
  const month = Math.floor((dateNum % 10000) / 100);
  const day = dateNum % 100;

  // Create date object (in local timezone)
  const date = new Date(year, month - 1, day);

  // If time is before 09:30, it's yesterday's data
  if (timeStr) {
    const [hours, minutes] = timeStr.split(':').map(Number);
    const totalMinutes = hours * 60 + minutes;
    const marketOpenMinutes = 9 * 60 + 30; // 09:30

    if (totalMinutes < marketOpenMinutes) {
      // Before market open, use yesterday's date
      date.setDate(date.getDate() - 1);
    }
  }

  // Format as MM-DD
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const dd = String(date.getDate()).padStart(2, '0');

  return `${mm}-${dd}`;
}

/**
 * Format a date number (YYYYMMDD) to MM-DD string
 *
 * @param dateNum 日期数字 (YYYYMMDD)
 * @returns 格式化后的日期字符串 (MM-DD)
 */
export function formatDateNumToMMDD(dateNum: number): string {
  if (!dateNum) return '';

  const month = Math.floor((dateNum % 10000) / 100);
  const day = dateNum % 100;

  const mm = String(month).padStart(2, '0');
  const dd = String(day).padStart(2, '0');

  return `${mm}-${dd}`;
}
