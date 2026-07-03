// @vitest-environment jsdom
import { beforeAll, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

beforeAll(() => {
  // jsdom lacks these; reduced-motion=true also short-circuits Lenis.
  window.matchMedia = ((query: string) => ({
    matches: query.includes("reduce"),
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;

  class MockObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  }
  (window as unknown as Record<string, unknown>).IntersectionObserver = MockObserver;
  (window as unknown as Record<string, unknown>).ResizeObserver = MockObserver;
});

describe("Landing", () => {
  it("renders every section heading", async () => {
    const { Landing } = await import("./Landing");
    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>,
    );
    expect(screen.getByText(/Every patient,/)).toBeTruthy();
    expect(screen.getByText(/every morning\./)).toBeTruthy();
    expect(screen.getByText(/How it/)).toBeTruthy();
    expect(screen.getByText(/\/bed\/month\./)).toBeTruthy();
    expect(screen.getByText(/your hospital\./)).toBeTruthy();
    expect(screen.getAllByText(/book a demo/i).length).toBeGreaterThanOrEqual(2);
  });
});
