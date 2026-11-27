import React from "react";
import { useAuth } from "../hooks/useAuth";

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
      <h1 className="text-xl font-bold">blublu Dashboard</h1>
      {user ? (
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium">{user.name}</span>
          <button
            onClick={logout}
            className="text-xs bg-red-50 text-red-600 px-3 py-1 rounded hover:bg-red-100"
          >
            Logout
          </button>
        </div>
      ) : (
        <span className="text-sm text-gray-500">Guest</span>
      )}
    </header>
  );
}
