/**
 * Helpers for converting between datetime-local input values (which have no
 * explicit timezone) and ISO 8601 strings that preserve the local timezone
 * offset.
 */

/**
 * Convert a datetime-local input value such as "2026-06-28T14:00" into an
 * ISO 8601 string with the browser's local timezone offset, e.g.
 * "2026-06-28T14:00:00+08:00". This lets the backend interpret the value as
 * the same local clock time rather than as UTC.
 */
export function localDateTimeToISO(localValue: string): string {
  const date = new Date(localValue);
  const offsetMinutes = date.getTimezoneOffset();

  // `date` is the UTC instant that corresponds to the local clock time.
  // To format the local clock time as ISO, shift by the timezone offset.
  const localInstant = new Date(date.getTime() - offsetMinutes * 60 * 1000);
  const isoWithoutZone = localInstant.toISOString().replace("Z", "");

  const sign = offsetMinutes <= 0 ? "+" : "-";
  const absOffset = Math.abs(offsetMinutes);
  const offsetHours = String(Math.floor(absOffset / 60)).padStart(2, "0");
  const offsetMinutesStr = String(absOffset % 60).padStart(2, "0");

  return `${isoWithoutZone}${sign}${offsetHours}:${offsetMinutesStr}`;
}

/**
 * Convert an ISO 8601 string (with timezone) into a value suitable for a
 * datetime-local input, rendered in the browser's local timezone, e.g.
 * "2026-06-28T14:00".
 */
export function isoToLocalDateTime(isoValue: string | null | undefined): string {
  if (!isoValue) return "";
  const date = new Date(isoValue);
  if (isNaN(date.getTime())) return "";

  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(
    date.getDate()
  )}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/**
 * Convert a date input value such as "2026-06-28" into an ISO 8601 string
 * representing 23:59 in the browser's local timezone, e.g.
 * "2026-06-28T23:59:00+08:00".
 */
export function localDateToEndOfDayISO(localDate: string): string {
  const date = new Date(`${localDate}T23:59:00`);
  const offsetMinutes = date.getTimezoneOffset();
  const localInstant = new Date(date.getTime() - offsetMinutes * 60 * 1000);
  const isoWithoutZone = localInstant.toISOString().replace("Z", "");

  const sign = offsetMinutes <= 0 ? "+" : "-";
  const absOffset = Math.abs(offsetMinutes);
  const offsetHours = String(Math.floor(absOffset / 60)).padStart(2, "0");
  const offsetMinutesStr = String(absOffset % 60).padStart(2, "0");

  return `${isoWithoutZone}${sign}${offsetHours}:${offsetMinutesStr}`;
}

/**
 * Convert an ISO 8601 string (with timezone) into a value suitable for a
 * date input, rendered in the browser's local timezone, e.g. "2026-06-28".
 */
export function isoToLocalDate(isoValue: string | null | undefined): string {
  if (!isoValue) return "";
  const date = new Date(isoValue);
  if (isNaN(date.getTime())) return "";

  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/**
 * Format an ISO 8601 string as a short local date string.
 */
export function formatDate(isoValue: string | null | undefined): string {
  if (!isoValue) return "";
  const date = new Date(isoValue);
  if (isNaN(date.getTime())) return "";
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Return true if the given due date is before the current time.
 */
export function isOverdue(isoValue: string | null | undefined): boolean {
  if (!isoValue) return false;
  const date = new Date(isoValue);
  if (isNaN(date.getTime())) return false;
  return date.getTime() < Date.now();
}

/**
 * Format an ISO 8601 string as a short local date/time string.
 */
export function formatDateTime(isoValue: string | null | undefined): string {
  if (!isoValue) return "";
  const date = new Date(isoValue);
  if (isNaN(date.getTime())) return "";
  return date.toLocaleString("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
