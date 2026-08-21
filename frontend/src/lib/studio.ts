export function apiOriginFrom(value: string | undefined): string {
  return (value || "http://localhost:8082").replace(/\/$/, "");
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
