import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';

// Placeholder Pages for Menu
const Defects = () => <div className="p-8 text-white">Defect Analysis Page (Coming Soon in Phase 2)</div>;
const Dimension = () => <div className="p-8 text-white">Dimension Measurement Page (Coming Soon in Phase 3)</div>;

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen w-full bg-[#0f172a] overflow-hidden font-sans">
        {/* Sidebar */}
        <aside className="w-64 bg-[#001e45] text-white flex flex-col border-r border-white/5">
          <div className="p-6 border-b border-white/5">
            <h1 className="text-2xl font-bold tracking-tight text-white">MS Detector<span className="text-blue-400">.ai</span></h1>
            <p className="text-xs text-blue-300/60 mt-1">QC Intelligence System</p>
          </div>
          
          <nav className="flex-1 p-4 flex flex-col gap-2">
            <Link to="/" className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[#003473] text-white shadow-lg shadow-blue-900/20">
              <span className="font-medium">Dashboard</span>
            </Link>
            <Link to="/defects" className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-white/5 hover:text-white transition-colors">
              <span className="font-medium">Defect Analysis</span>
            </Link>
            <Link to="/dimensions" className="flex items-center gap-3 px-4 py-3 rounded-lg text-gray-400 hover:bg-white/5 hover:text-white transition-colors">
              <span className="font-medium">Dimensions</span>
            </Link>
          </nav>

          <div className="p-6 text-xs text-gray-500 border-t border-white/5">
            v2.0.0-beta<br/>
            Running on RTX 4090
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto bg-[#0f172a]">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/defects" element={<Defects />} />
            <Route path="/dimensions" element={<Dimension />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
