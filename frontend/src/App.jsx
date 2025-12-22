import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Sessions from './pages/Sessions';
import Dimensions from './pages/Dimensions';

// Placeholder Page
const Defects = () => <div className="p-8 text-white">Defect Analysis Page (Coming Soon in Phase 2)</div>;

function AppContent() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <div className="flex h-screen w-full bg-[#0f172a] overflow-hidden font-sans">
        {/* Mobile overlay */}
        {isMobileMenuOpen && (
          <div 
            className="fixed inset-0 bg-black/50 lg:hidden z-40"
            onClick={() => setIsMobileMenuOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside 
          className={`
            fixed lg:relative inset-y-0 left-0 z-50
            ${ isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
            lg:translate-x-0
            transition-transform duration-300
            ${isSidebarOpen ? 'w-64' : 'w-20'}
            bg-[#001e45] text-white flex flex-col border-r border-white/5
          `}
        >
          {/* Header & Logo */}
          <div className="p-4 border-b border-white/5 flex items-center justify-center">
            <div className={`font-bold tracking-tight text-white flex items-center gap-2 overflow-hidden whitespace-nowrap`}>
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
            <Link to="/" className={`flex items-center gap-3 px-3 py-3 rounded-lg ${
              isActive('/') 
                ? 'bg-[#003473] text-white shadow-lg shadow-blue-900/20' 
                : 'text-gray-400 hover:bg-white/5 hover:text-white'
            } transition-colors ${!isSidebarOpen && 'justify-center'}`} title="Dashboard">
              {/* Dashboard Icon */}
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0"><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
              {isSidebarOpen && <span className="font-medium">Dashboard</span>}
            </Link>
            <Link to="/sessions" className={`flex items-center gap-3 px-3 py-3 rounded-lg ${
              isActive('/sessions') 
                ? 'bg-[#003473] text-white shadow-lg shadow-blue-900/20' 
                : 'text-gray-400 hover:bg-white/5 hover:text-white'
            } transition-colors ${!isSidebarOpen && 'justify-center'}`} title="Sessions History">
              {/* Sessions Icon (Clock/History) */}
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              {isSidebarOpen && <span className="font-medium">Sessions</span>}
            </Link>
            <Link to="/defects" className={`flex items-center gap-3 px-3 py-3 rounded-lg ${
              isActive('/defects') 
                ? 'bg-[#003473] text-white shadow-lg shadow-blue-900/20' 
                : 'text-gray-400 hover:bg-white/5 hover:text-white'
            } transition-colors ${!isSidebarOpen && 'justify-center'}`} title="Defect Analysis">
              {/* Defects Icon (Microscope/Search) */}
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
              {isSidebarOpen && <span className="font-medium">Defects</span>}
            </Link>
            <Link to="/dimensions" className={`flex items-center gap-3 px-3 py-3 rounded-lg ${
              isActive('/dimensions') 
                ? 'bg-[#003473] text-white shadow-lg shadow-blue-900/20' 
                : 'text-gray-400 hover:bg-white/5 hover:text-white'
            } transition-colors ${!isSidebarOpen && 'justify-center'}`} title="Dimensions">
              {/* Dimensions Icon (Ruler) */}
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="shrink-0"><path d="M21.3 15.3a2.4 2.4 0 0 1 0 3.4l-2.6 2.6a2.4 2.4 0 0 1-3.4 0L2.7 8.7a2.41 2.41 0 0 1 0-3.4l2.6-2.6a2.41 2.41 0 0 1 3.4 0Z"/><path d="m14.5 12.5 2-2"/><path d="m11.5 9.5 2-2"/><path d="m8.5 6.5 2-2"/><path d="m17.5 15.5 2-2"/></svg>
              {isSidebarOpen && <span className="font-medium">Dimensions</span>}
            </Link>
          </nav>

          {/* Footer Info */}
          <div className={`p-4 border-t border-white/5 flex flex-col items-center gap-2 ${!isSidebarOpen && 'hidden'}`}>
             <div className="text-xs text-gray-500 text-center">
                v2.0.0-beta<br/>
                RTX 4090
              </div>
          </div>
        </aside>

        {/* Mobile Menu Toggle Button - Floating */}
        <button
          className="lg:hidden fixed top-4 left-4 z-50 p-3 bg-[#003473] hover:bg-[#004a99] text-white rounded-lg shadow-lg transition-colors"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          title="Toggle Menu"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>

        {/* Desktop Sidebar Toggle - Floating at edge */}
        <button 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className={`hidden lg:block fixed top-4 ${isSidebarOpen ? 'left-60' : 'left-16'} z-50 p-2 rounded-md bg-[#003473] hover:bg-[#004a99] text-white shadow-lg transition-all duration-300`}
          title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
        >
          {isSidebarOpen ? (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
          )}
        </button>

        {/* Main Content */}
        <main className="flex-1 overflow-auto bg-[#0f172a]">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/sessions" element={<Sessions />} />
            <Route path="/defects" element={<Defects />} />
            <Route path="/dimensions" element={<Dimensions />} />
          </Routes>
        </main>
      </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
