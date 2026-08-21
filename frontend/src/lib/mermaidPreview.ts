import mermaid from 'mermaid';

let started = false;

export async function renderMermaidPreview(source: string): Promise<{ svg: string; error: string | null }> {
	if (!source.trim()) {
		return { svg: '', error: null };
	}
	if (!started) {
		mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'neutral' });
		started = true;
	}
	try {
		const id = `preview-${Math.random().toString(36).slice(2)}`;
		const { svg } = await mermaid.render(id, source);
		return { svg, error: null };
	} catch (err) {
		const message = err instanceof Error ? err.message : 'Invalid Mermaid';
		return { svg: '', error: message };
	}
}
