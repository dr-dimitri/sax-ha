export function normalizeTime(value: string): string {
  const trimmed = value.trim();
  const candidate = /^\d{4}$/.test(trimmed)
    ? `${trimmed.slice(0, 2)}:${trimmed.slice(2)}`
    : trimmed;
  return timeSeconds(candidate) === null ? value : candidate;
}
export function timeSeconds(value: string): number | null {
  if (!/^([01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(value)) return null;
  const [hours, minutes, seconds = 0] = value.split(":").map(Number);
  return hours! * 3600 + minutes! * 60 + seconds;
}
