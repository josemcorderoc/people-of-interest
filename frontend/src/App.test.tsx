import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";

// Mock fetch to avoid real API calls
beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          total: 0,
          page: 1,
          per_page: 50,
          results: [],
          categories: [],
          languages: ["en"],
        }),
    }),
  );
});

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  );
}

describe("App", () => {
  it("renders the application header", () => {
    renderApp();
    expect(screen.getByText("People of Interest")).toBeInTheDocument();
  });

  it("renders the control bar with view toggle", () => {
    renderApp();
    expect(screen.getByText("Popularity")).toBeInTheDocument();
    expect(screen.getByText("Trending")).toBeInTheDocument();
  });

  it("renders the window selector", () => {
    renderApp();
    expect(screen.getByDisplayValue("Daily")).toBeInTheDocument();
  });

  it("renders the search box", () => {
    renderApp();
    expect(screen.getByPlaceholderText("Search people...")).toBeInTheDocument();
  });

  it("renders the table headers", () => {
    renderApp();
    expect(screen.getByText("#")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Category")).toBeInTheDocument();
    expect(screen.getByText("Score")).toBeInTheDocument();
  });
});
