import PersonTable from "./components/PersonTable";

export default function App() {
  return (
    <div className="flex flex-col h-screen w-screen">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-xl font-bold text-gray-900">People of Interest</h1>
      </header>
      <main className="flex-1 overflow-auto p-6">
        <PersonTable />
      </main>
    </div>
  );
}
