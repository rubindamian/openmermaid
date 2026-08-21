import { describe, expect, it } from "vitest";
import {
  clipboardTextFromSource,
  editorPath,
  googleLoginUrl,
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
});
