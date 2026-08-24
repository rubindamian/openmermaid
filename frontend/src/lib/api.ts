import { env } from "$env/dynamic/public";
import { API_UNREACHABLE, alignLoopbackOrigin } from "./studio";

export type Diagram = {
  id: string;
  title: string;
  source_draft: string;
  source_published: string;
  public_token: string | null;
  picture_url: string | null;
  editor_url: string;
  saved_at: string | null;
  updated_at: string | null;
};

export type Me = {
  id: number;
  email: string;
  username: string;
};

function origin(): string {
  return alignLoopbackOrigin(
    env.PUBLIC_API_ORIGIN,
    typeof window === "undefined" ? undefined : window.location.origin,
  );
}

// Cached because the token is stable for the session, and a draft flushed
// during page unload only has time for one request, not a bootstrap plus a save.
let cachedCsrfToken: string | null = null;

async function csrfToken(): Promise<string> {
  if (cachedCsrfToken) return cachedCsrfToken;
  const response = await fetch(`${origin()}/auth/csrf/`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error("Could not bootstrap CSRF");
  }
  const body = (await response.json()) as { csrfToken: string };
  cachedCsrfToken = body.csrfToken;
  return cachedCsrfToken;
}

// Returns null when the API could not be reached at all, so callers can report
// that instead of leaving a view stuck on its loading state.
async function request(
  path: string,
  init: RequestInit = {},
): Promise<Response | null> {
  const headers = new Headers(init.headers);
  try {
    if (init.method && init.method !== "GET" && init.method !== "HEAD") {
      headers.set("X-CSRFToken", await csrfToken());
      if (!headers.has("Content-Type") && init.body) {
        headers.set("Content-Type", "application/json");
      }
    }
    const response = await fetch(`${origin()}${path}`, {
      ...init,
      headers,
      credentials: "include",
    });
    // A rotated session invalidates the cached token; drop it so the next
    // attempt bootstraps a fresh one instead of failing forever.
    if (response.status === 403) cachedCsrfToken = null;
    return response;
  } catch {
    return null;
  }
}

export async function fetchMe(): Promise<{ status: number; me: Me | null }> {
  const response = await request("/api/me/");
  if (!response) return { status: API_UNREACHABLE, me: null };
  if (response.status === 401) return { status: 401, me: null };
  if (!response.ok) return { status: response.status, me: null };
  return { status: response.status, me: (await response.json()) as Me };
}

export async function listDiagrams(): Promise<{
  status: number;
  diagrams: Diagram[];
}> {
  const response = await request("/api/diagrams/");
  if (!response) return { status: API_UNREACHABLE, diagrams: [] };
  if (!response.ok) return { status: response.status, diagrams: [] };
  const body = (await response.json()) as { diagrams: Diagram[] };
  return { status: response.status, diagrams: body.diagrams };
}

export async function createDiagram(
  title = "Untitled",
): Promise<{ status: number; diagram: Diagram | null }> {
  const response = await request("/api/diagrams/", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  if (!response) return { status: API_UNREACHABLE, diagram: null };
  if (!response.ok) return { status: response.status, diagram: null };
  return {
    status: response.status,
    diagram: (await response.json()) as Diagram,
  };
}

export async function getDiagram(
  id: string,
): Promise<{ status: number; diagram: Diagram | null }> {
  const response = await request(`/api/diagrams/${id}/`);
  if (!response) return { status: API_UNREACHABLE, diagram: null };
  if (!response.ok) return { status: response.status, diagram: null };
  return {
    status: response.status,
    diagram: (await response.json()) as Diagram,
  };
}

// `keepalive` lets a draft written while the page is closing outlive the
// document, so the last keystrokes are not dropped on navigate or tab close.
export async function patchDraft(
  id: string,
  sourceDraft: string,
  options: { keepalive?: boolean } = {},
): Promise<{ status: number; diagram: Diagram | null }> {
  const response = await request(`/api/diagrams/${id}/`, {
    method: "PATCH",
    body: JSON.stringify({ source_draft: sourceDraft }),
    keepalive: options.keepalive ?? false,
  });
  if (!response) return { status: API_UNREACHABLE, diagram: null };
  if (!response.ok) return { status: response.status, diagram: null };
  return {
    status: response.status,
    diagram: (await response.json()) as Diagram,
  };
}

export async function patchTitle(
  id: string,
  title: string,
): Promise<{ status: number; diagram: Diagram | null }> {
  const response = await request(`/api/diagrams/${id}/`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
  if (!response) return { status: API_UNREACHABLE, diagram: null };
  if (!response.ok) return { status: response.status, diagram: null };
  return {
    status: response.status,
    diagram: (await response.json()) as Diagram,
  };
}

export async function saveDiagram(
  id: string,
): Promise<{ status: number; diagram: Diagram | null; detail?: string }> {
  const response = await request(`/api/diagrams/${id}/save/`, {
    method: "POST",
  });
  if (!response) {
    return {
      status: API_UNREACHABLE,
      diagram: null,
      detail: "The API is not reachable.",
    };
  }
  if (!response.ok) {
    let detail = "Save failed.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    return { status: response.status, diagram: null, detail };
  }
  return {
    status: response.status,
    diagram: (await response.json()) as Diagram,
  };
}

export { origin as publicApiOrigin };
export { csrfToken };
