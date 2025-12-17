import { useState } from 'react'
import LiveMonitor from './pages/LiveMonitor'
import DefectAnalysis from './pages/DefectAnalysis'
import SettingsPage from './pages/SettingsPage'
import { LayoutDashboard, Scan, Settings } from 'lucide-react'

function App() {
  const [activeTab, setActiveTab] = useState('monitor'); // monitor, defects, settings

  return (
    <div className="min-h-screen flex flex-col bg-dark-bg text-dark-text">
      {/* Header */}
      <header className="bg-dark-surface border-b border-gray-700 px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center font-bold text-xl">AI</div>
            <div>
                <h1 className="text-xl font-bold text-white tracking-tight">Metal Sheet Monitor</h1>
                <p className="text-xs text-gray-400">Orin Nano Edition</p>
            </div>
        </div>
        
        <nav className="flex bg-gray-900 rounded-lg p-1">
            <button 
                onClick={() => setActiveTab('monitor')}
                className={`px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-all ${activeTab === 'monitor' ? 'bg-primary text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
            >
                <LayoutDashboard size={18} /> Live Monitor
            </button>
            <button 
                onClick={() => setActiveTab('defects')}
                className={`px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-all ${activeTab === 'defects' ? 'bg-primary text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
            >
                <Scan size={18} /> Defect Analysis
            </button>
            <button 
                onClick={() => setActiveTab('settings')}
                className={`px-4 py-2 rounded-md text-sm font-medium flex items-center gap-2 transition-all ${activeTab === 'settings' ? 'bg-primary text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
            >
                <Settings size={18} /> Settings
            </button>
        </nav>
      </header>
      
      <main className="flex-1 overflow-auto">
        {activeTab === 'monitor' && <LiveMonitor />}
        {activeTab === 'defects' && <DefectAnalysis />}
        {activeTab === 'settings' && <SettingsPage />}
      </main>
    </div>
  )
}

export default App
