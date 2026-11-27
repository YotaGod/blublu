import React from "react";
import Header from "./components/Header";
import Dashboard from "./components/Dashboard";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <Header />
      <main className="max-w-7xl mx-auto py-6 px-4">
        <Dashboard />
      </main>
    </div>
  );
}
