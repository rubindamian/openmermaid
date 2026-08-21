import { env } from '$env/dynamic/public';
import { apiOriginFrom } from './studio';

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
	return apiOriginFrom(env.PUBLIC_API_ORIGIN);
}

async function csrfToken(): Promise<string> {
	const response = await fetch(`${origin()}/auth/csrf/`, { credentials: 'include' });
	if (!response.ok) {
		throw new Error('Could not bootstrap CSRF');
	}
	const body = (await response.json()) as { csrfToken: string };
	return body.csrfToken;
}

async function request(path: string, init: RequestInit = {}): Promise<Response> {
	const headers = new Headers(init.headers);
	if (init.method && init.method !== 'GET' && init.method !== 'HEAD') {
		headers.set('X-CSRFToken', await csrfToken());
		if (!headers.has('Content-Type') && init.body) {
			headers.set('Content-Type', 'application/json');
		}
	}
	return fetch(`${origin()}${path}`, {
		...init,
		headers,
		credentials: 'include'
	});
}

export async function fetchMe(): Promise<{ status: number; me: Me | null }> {
	const response = await request('/api/me/');
	if (response.status === 401) return { status: 401, me: null };
	if (!response.ok) return { status: response.status, me: null };
	return { status: response.status, me: (await response.json()) as Me };
}

export async function listDiagrams(): Promise<{ status: number; diagrams: Diagram[] }> {
	const response = await request('/api/diagrams/');
	if (!response.ok) return { status: response.status, diagrams: [] };
	const body = (await response.json()) as { diagrams: Diagram[] };
	return { status: response.status, diagrams: body.diagrams };
}

export async function createDiagram(title = 'Untitled'): Promise<{ status: number; diagram: Diagram | null }> {
	const response = await request('/api/diagrams/', {
		method: 'POST',
		body: JSON.stringify({ title })
	});
	if (!response.ok) return { status: response.status, diagram: null };
	return { status: response.status, diagram: (await response.json()) as Diagram };
}

export async function getDiagram(id: string): Promise<{ status: number; diagram: Diagram | null }> {
	const response = await request(`/api/diagrams/${id}/`);
	if (!response.ok) return { status: response.status, diagram: null };
	return { status: response.status, diagram: (await response.json()) as Diagram };
}

export async function patchDraft(
	id: string,
	sourceDraft: string
): Promise<{ status: number; diagram: Diagram | null }> {
	const response = await request(`/api/diagrams/${id}/`, {
		method: 'PATCH',
		body: JSON.stringify({ source_draft: sourceDraft })
	});
	if (!response.ok) return { status: response.status, diagram: null };
	return { status: response.status, diagram: (await response.json()) as Diagram };
}

export async function saveDiagram(id: string): Promise<{ status: number; diagram: Diagram | null; detail?: string }> {
	const response = await request(`/api/diagrams/${id}/save/`, { method: 'POST' });
	if (!response.ok) {
		let detail = 'Save failed.';
		try {
			const body = (await response.json()) as { detail?: string };
			if (body.detail) detail = body.detail;
		} catch {
			/* ignore */
		}
		return { status: response.status, diagram: null, detail };
	}
	return { status: response.status, diagram: (await response.json()) as Diagram };
}

export { origin as publicApiOrigin };
export { csrfToken };
