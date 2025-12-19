import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';

// Placeholder Pages for Menu
const Defects = () => <div className="p-8 text-white">Defect Analysis Page (Coming Soon in Phase 2)</div>;
const Dimension = () => <div className="p-8 text-white">Dimension Measurement Page (Coming Soon in Phase 3)</div>;

function App() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <BrowserRouter>
      <div className="flex h-screen w-full bg-[#0f172a] overflow-hidden font-sans">
        {/* Sidebar */}
        <aside 
          className={`${isSidebarOpen ? 'w-64' : 'w-20'} bg-[#001e45] text-white flex flex-col border-r border-white/5 transition-all duration-300 ease-in-out`}
        >
          {/* Header & Logo */}
          <div className="p-4 border-b border-white/5 flex items-center justify-between">
            <div className={`font-bold tracking-tight text-white flex items-center gap-2 overflow-hidden whitespace-nowrap ${!isSidebarOpen && 'justify-center w-full'}`}>
              <div className="bg-blue-600 w-10 h-10 rounded flex items-center justify-center font-black text-xs shrink-0 shadow-lg shadow-blue-500/30">
                MSQC
              </div>
              <div className={`transition-opacity duration-200 ${isSidebarOpen ? 'opacity-100' : 'opacity-0 w-0'}`}>
                <span className="text-lg">Detector<span className="text-blue-400">.ai</span></span>
              </div>
            </div>
          </div>
          
          {/* Nav Links */}
          <nav className="flex-1 p-3 flex flex-col gap-2 overflow-hidden">
            <Link to="/" className={`flex items-center gap-3 px-3 py-3 rounded-lg bg-[#003473] text-white shadow-lg shadow-blue-900/20 ${!isSidebarOpen && 'justify-center'}`} title="Dashboard">
              <span className="w-5 h-5 bg-white/20 rounded-sm shrink-0"></span> {/* Icon placeholder */}
              {isSidebarOpen && <span className="font-medium">Dashboard</span>}
            </Link>
            <Link to="/defects" className={`flex items-center gap-3 px-3 py-3 rounded-lg text-gray-400 hover:bg-white/5 hover:text-white transition-colors ${!isSidebarOpen && 'justify-center'}`} title="Defect Analysis">
              <span className="w-5 h-5 border border-gray-600 rounded-sm shrink-0"></span>
              {isSidebarOpen && <span className="font-medium">Defects</span>}
            </Link>
            <Link to="/dimensions" className={`flex items-center gap-3 px-3 py-3 rounded-lg text-gray-400 hover:bg-white/5 hover:text-white transition-colors ${!isSidebarOpen && 'justify-center'}`} title="Dimensions">
              <span className="w-5 h-5 border border-gray-600 rounded-sm shrink-0"></span>
              {isSidebarOpen && <span className="font-medium">Dimensions</span>}
            </Link>
          </nav>

          {/* Setup / Collapse Toggle */}
          <div className="p-4 border-t border-white/5 flex flex-col items-center gap-4">
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 rounded hover:bg-white/10 text-gray-400 hover:text-white transition-colors w-full flex justify-center"
            >
              {isSidebarOpen ? '<< Collapse' : '>>'}
            </button>
            {isSidebarOpen && (
              <div className="text-xs text-gray-500 text-center">
                v2.0.0-beta<br/>
                RTX 4090
              </div>
            )}
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
