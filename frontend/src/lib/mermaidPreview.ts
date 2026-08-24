import mermaid from "mermaid";

// Must match MERMAID_THEME in config/settings/base.py, or the preview shows a
// different palette than the PNG published from the same source.
export const PREVIEW_THEME = "default";

let started = false;

export async function renderMermaidPreview(
  source: string,
): Promise<{ svg: string; error: string | null }> {
  if (!source.trim()) {
    return { svg: "", error: null };
  }
  if (!started) {
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: PREVIEW_THEME,
    });
    started = true;
  }
  try {
    const id = `preview-${Math.random().toString(36).slice(2)}`;
    const { svg } = await mermaid.render(id, source);
    return { svg, error: null };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Invalid Mermaid";
    return { svg: "", error: message };
  }
}
