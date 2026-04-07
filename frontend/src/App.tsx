import { BrowserRouter, Routes, Route } from "react-router-dom";
import PersonTable from "./components/PersonTable";
import ControlBar from "./components/ControlBar";
import { useQueryParams } from "./hooks/useQueryParams";

function AppContent() {
  const { state, update } = useQueryParams();

  return (
    <div className="flex flex-col h-screen w-screen">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-xl font-bold text-gray-900">People of Interest</h1>
      </header>
      <ControlBar state={state} onUpdate={update} />
      <main className="flex-1 overflow-auto p-6">
        <PersonTable state={state} onUpdate={update} />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="*" element={<AppContent />} />
      </Routes>
    </BrowserRouter>
  );
}
