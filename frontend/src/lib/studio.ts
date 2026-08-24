// Synthetic status for a request that never reached the API (DNS, refused, CORS).
export const API_UNREACHABLE = 0;

export function apiOriginFrom(value: string | undefined): string {
  return (value || "http://localhost:8082").replace(/\/$/, "");
}

const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1"]);

// Keep the API on the same loopback spelling as the page. localhost and
// 127.0.0.1 are different sites to the browser, so mixing them drops the
// SameSite=Lax session cookie and every call comes back 401.
export function alignLoopbackOrigin(
  apiOrigin: string | undefined,
  pageOrigin?: string,
): string {
  const api = apiOriginFrom(apiOrigin);
  if (!pageOrigin) return api;
  try {
    const apiUrl = new URL(api);
    const pageUrl = new URL(pageOrigin);
    if (
      LOOPBACK_HOSTS.has(apiUrl.hostname) &&
      LOOPBACK_HOSTS.has(pageUrl.hostname) &&
      apiUrl.hostname !== pageUrl.hostname
    ) {
      apiUrl.hostname = pageUrl.hostname;
      return apiUrl.origin;
    }
  } catch {
    return api;
  }
  return api;
}

export function googleLoginUrl(apiOrigin: string): string {
  return `${apiOriginFrom(apiOrigin)}/auth/login/google-oauth2/`;
}

export function editorPath(id: string): string {
  return `/d/${id}`;
}

export function signInPath(next?: string): string {
  if (!next) return "/signin";
  return `/signin?next=${encodeURIComponent(next)}`;
}

export function isSignInRequired(status: number): boolean {
  return status === 401;
}

export function isApiUnreachable(status: number): boolean {
  return status === API_UNREACHABLE;
}

export function isForbidden(status: number): boolean {
  return status === 403;
}

export type ShareState = {
  pictureUrl: string | null;
  editorUrl: string | null;
  publicToken: string | null;
};

export function shareStateFromSave(payload: {
  picture_url?: string | null;
  editor_url?: string | null;
  public_token?: string | null;
}): ShareState {
  return {
    pictureUrl: payload.picture_url ?? null,
    editorUrl: payload.editor_url ?? null,
    publicToken: payload.public_token ?? null,
  };
}

export function keepShareOnSaveError(
  previous: ShareState,
  succeeded: boolean,
  next?: ShareState,
): ShareState {
  if (!succeeded) return previous;
  return next ?? previous;
}

export function clipboardTextFromSource(source: string): string {
  return source;
}

export function tokenAfterSave(
  existing: string | null,
  incoming: string | null,
): string | null {
  return incoming || existing;
}

export const DEFAULT_TITLE = "Untitled";
const TITLE_MAX_LENGTH = 255;

// Mirrors the server's clamp so an inline rename shows the stored value, not a
// blank heading the API silently replaced.
export function normalizeTitle(value: string): string {
  const trimmed = value.trim().replace(/\s+/g, " ");
  if (!trimmed) return DEFAULT_TITLE;
  return trimmed.slice(0, TITLE_MAX_LENGTH);
}

const MINUTE = 60;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

function plural(count: number, unit: string): string {
  return `${count} ${unit}${count === 1 ? "" : "s"} ago`;
}

// Card subtitles read as "Edited 4 days ago". Falls back to a plain date past a
// month, where an ever-growing day count stops being useful.
export function formatRelativeTime(
  iso: string | null | undefined,
  now: Date = new Date(),
): string {
  if (!iso) return "Never saved";
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return "Never saved";

  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);
  if (seconds < MINUTE) return "just now";
  if (seconds < HOUR) return plural(Math.floor(seconds / MINUTE), "minute");
  if (seconds < DAY) return plural(Math.floor(seconds / HOUR), "hour");
  if (seconds < 30 * DAY) return plural(Math.floor(seconds / DAY), "day");
  return then.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// The first non-empty, non-directive line stands in for a title-less diagram.
export function diagramSummary(source: string): string {
  const line = source
    .split("\n")
    .map((entry) => entry.trim())
    .find((entry) => entry && !entry.startsWith("%%"));
  return line || "Empty diagram";
}
