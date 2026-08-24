import { describe, expect, it } from "vitest";
import {
  API_UNREACHABLE,
  alignLoopbackOrigin,
  clipboardTextFromSource,
  DEFAULT_TITLE,
  diagramSummary,
  editorPath,
  normalizeTitle,
  formatRelativeTime,
  googleLoginUrl,
  isApiUnreachable,
  isForbidden,
  isSignInRequired,
  keepShareOnSaveError,
  signInPath,
  tokenAfterSave,
  type ShareState,
} from "./studio";

const previous: ShareState = {
  pictureUrl: "http://localhost:8082/p/abc.png",
  editorUrl: "/d/1",
  publicToken: "abc",
};

describe("studio helpers", () => {
  it("copies the current textarea source including unsaved draft", () => {
    const draft = "flowchart TD\n  unsaved-->draft";
    expect(clipboardTextFromSource(draft)).toBe(draft);
    expect(clipboardTextFromSource(draft)).not.toContain("screenshot");
  });

  it("sends unauthenticated editor visits to sign-in, not the PNG", () => {
    expect(isSignInRequired(401)).toBe(true);
    expect(signInPath("/d/abc")).toBe("/signin?next=%2Fd%2Fabc");
    expect(signInPath("/d/abc")).not.toContain(".png");
    expect(googleLoginUrl("http://localhost:8082")).toBe(
      "http://localhost:8082/auth/login/google-oauth2/",
    );
  });

  it("keeps previous published URLs when Save is invalid", () => {
    const kept = keepShareOnSaveError(previous, false);
    expect(kept).toEqual(previous);
  });

  it("does not claim a new token on a second Save", () => {
    expect(tokenAfterSave("abc", "abc")).toBe("abc");
    expect(tokenAfterSave("abc", null)).toBe("abc");
  });

  it("treats non-owner editor as forbidden, not a shared canvas", () => {
    expect(isForbidden(403)).toBe(true);
    expect(editorPath("uuid-1")).toBe("/d/uuid-1");
  });

  it("sends a fresh unauthenticated visit to sign-in", () => {
    expect(isSignInRequired(401)).toBe(true);
    expect(signInPath("/")).toBe("/signin?next=%2F");
  });

  it("separates an unreachable API from a signed-out visit", () => {
    expect(isApiUnreachable(API_UNREACHABLE)).toBe(true);
    expect(isApiUnreachable(401)).toBe(false);
    expect(isSignInRequired(API_UNREACHABLE)).toBe(false);
  });

  it("calls the API on the same loopback host as the page", () => {
    expect(
      alignLoopbackOrigin("http://localhost:8082", "http://127.0.0.1:3000"),
    ).toBe("http://127.0.0.1:8082");
    expect(
      alignLoopbackOrigin("http://127.0.0.1:8082", "http://localhost:3000"),
    ).toBe("http://localhost:8082");
  });

  it("leaves a non-loopback or matching API origin alone", () => {
    expect(
      alignLoopbackOrigin("http://localhost:8082", "http://localhost:3000"),
    ).toBe("http://localhost:8082");
    expect(
      alignLoopbackOrigin("https://api.example.com", "http://localhost:3000"),
    ).toBe("https://api.example.com");
    expect(alignLoopbackOrigin("http://localhost:8082", undefined)).toBe(
      "http://localhost:8082",
    );
  });

  it("describes card timestamps in relative terms", () => {
    const now = new Date("2026-08-23T18:00:00Z");
    const at = (iso: string) => formatRelativeTime(iso, now);
    expect(at("2026-08-23T17:59:30Z")).toBe("just now");
    expect(at("2026-08-23T17:30:00Z")).toBe("30 minutes ago");
    expect(at("2026-08-23T17:00:00Z")).toBe("1 hour ago");
    expect(at("2026-08-19T18:00:00Z")).toBe("4 days ago");
  });

  it("shows an unsaved diagram as never saved rather than a bad date", () => {
    const now = new Date("2026-08-23T18:00:00Z");
    expect(formatRelativeTime(null, now)).toBe("Never saved");
    expect(formatRelativeTime("not-a-date", now)).toBe("Never saved");
  });

  it("falls back to Untitled when a rename is cleared", () => {
    expect(normalizeTitle("   ")).toBe(DEFAULT_TITLE);
    expect(normalizeTitle("")).toBe(DEFAULT_TITLE);
  });

  it("trims and collapses whitespace in a renamed title", () => {
    expect(normalizeTitle("  Patient   Policy Update  ")).toBe(
      "Patient Policy Update",
    );
    expect(normalizeTitle("Geode RPA ERD")).toBe("Geode RPA ERD");
  });

  it("clamps a renamed title to the column width", () => {
    expect(normalizeTitle("x".repeat(300))).toHaveLength(255);
  });

  it("summarises a diagram by its first meaningful line", () => {
    expect(diagramSummary("\n%% a comment\nflowchart TD\n  a-->b")).toBe(
      "flowchart TD",
    );
    expect(diagramSummary("   \n  ")).toBe("Empty diagram");
  });
});
