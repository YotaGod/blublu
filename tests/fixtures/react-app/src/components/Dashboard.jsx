import React from "react";

export default function Dashboard() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-100">
        <h2 className="text-sm font-semibold text-gray-500">Modules Tracked</h2>
        <p className="text-3xl font-bold mt-2">18</p>
      </div>
      <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-100">
        <h2 className="text-sm font-semibold text-gray-500">Verification Ratio</h2>
        <p className="text-3xl font-bold mt-2 text-green-600">100%</p>
      </div>
      <div className="p-6 bg-white rounded-lg shadow-sm border border-gray-100">
        <h2 className="text-sm font-semibold text-gray-500">Health Status</h2>
        <p className="text-3xl font-bold mt-2 text-blue-600">Healthy</p>
      </div>
    </div>
  );
}
