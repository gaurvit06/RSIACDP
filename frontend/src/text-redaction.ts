export const SUBMITTER_REDACTION_MARKER = '[REDACTED BY SUBMITTER]';

/** Replace a non-empty UTF-16 textarea selection without retaining its original text. */
export function redactSelectedText(value: string, start: number, end: number): string {
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 0 || end <= start || end > value.length) {
    return value;
  }
  return `${value.slice(0, start)}${SUBMITTER_REDACTION_MARKER}${value.slice(end)}`;
}
