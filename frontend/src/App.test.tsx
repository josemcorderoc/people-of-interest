import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("App", () => {
  it("renders the application shell with header", () => {
    renderWithProviders(<App />);

    expect(screen.getByText("People of Interest")).toBeInTheDocument();
  });

  it("renders the person table placeholder", () => {
    renderWithProviders(<App />);

    expect(screen.getByText(/No data available/)).toBeInTheDocument();
  });

  it("renders table headers", () => {
    renderWithProviders(<App />);

    expect(screen.getByText("Rank")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Category")).toBeInTheDocument();
    expect(screen.getByText("Score")).toBeInTheDocument();
  });
});
