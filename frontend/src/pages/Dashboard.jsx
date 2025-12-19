import React, { useState } from 'react';
import LiveStream from '../components/LiveStream';
import StatsCard from '../components/StatsCard';
import { startSession, stopSession, setSource } from '../services/api';

const Dashboard = () => {
  const [sessionName, setSessionName] = useState('');
  const [maxCount, setMaxCount] = useState(100);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [currentCount, setCurrentCount] = useState(0);
  const [sourceInput, setSourceInput] = useState('0'); // Default to '0' for webcam

  const handleStart = async () => {
    try {
      await startSession({ name: sessionName, max_count: parseInt(maxCount) });
      setIsSessionActive(true);
      setCurrentCount(0);
    } catch (err) {
      console.error(err);
      alert('Failed to start session');
    }
  };

  const handleStop = async () => {
    try {
      await stopSession();
      setIsSessionActive(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSetSource = async () => {
    try {
      await setSource(sourceInput);
      alert('Source updated');
    } catch (err) {
      console.error(err);
      alert('Failed to set source');
    }
  };

  return (
    <div className="p-8 h-full flex flex-col gap-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Production Dashboard</h1>
          <p className="text-gray-400">Real-time Metal Sheet Counting & QC</p>
        </div>
        <div className={`px-4 py-2 rounded-full font-bold ${isSessionActive ? 'bg-green-500/20 text-green-400 border border-green-500/50' : 'bg-gray-800 text-gray-500'}`}>
          {isSessionActive ? 'SESSION ACTIVE' : 'IDLE'}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1">
        
        {/* Left Column: Video Feed */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex-1 min-h-[400px]">
            <LiveStream onCountUpdate={setCurrentCount} />
          </div>
          
          {/* Source Controls */}
          <div className="bg-white/5 border border-white/10 p-4 rounded-lg flex gap-4 items-center backdrop-blur-sm">
            <span className="text-sm font-medium text-gray-300">Input Source:</span>
            <input 
              type="text" 
              value={sourceInput}
              onChange={(e) => setSourceInput(e.target.value)}
              placeholder="RTSP URL or File Path or '0'"
              className="flex-1 bg-black/40 border border-white/10 rounded px-3 py-1 text-sm text-white focus:outline-none focus:border-primary"
            />
            <button 
              onClick={handleSetSource}
              className="bg-gray-700 hover:bg-gray-600 px-4 py-1 rounded text-sm transition-colors"
            >
              Set Source
            </button>
          </div>
        </div>

        {/* Right Column: Stats & Controls */}
        <div className="flex flex-col gap-6">
          <StatsCard 
            title="Total Count" 
            value={currentCount} 
            subtext={`Target: ${maxCount}`}
            alert={currentCount > maxCount}
          />
          
          {/* Session Control Panel */}
          <div className="bg-[#003473]/10 border border-[#003473]/50 p-6 rounded-xl backdrop-blur-md flex flex-col gap-4">
            <h3 className="text-[#003473] font-bold uppercase tracking-wider text-sm bg-white/10 inline-block w-max px-2 py-1 rounded">Session Control</h3>
            
            <div className="flex flex-col gap-2">
              <label className="text-xs text-gray-400 uppercase">Session Name</label>
              <input 
                type="text" 
                disabled={isSessionActive}
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                className="bg-black/20 border border-white/10 rounded px-3 py-2 text-white disabled:opacity-50"
                placeholder="Batch-001"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs text-gray-400 uppercase">Max Count Limit</label>
              <input 
                type="number" 
                disabled={isSessionActive}
                value={maxCount}
                onChange={(e) => setMaxCount(e.target.value)}
                className="bg-black/20 border border-white/10 rounded px-3 py-2 text-white disabled:opacity-50"
              />
            </div>

            <div className="mt-4 flex gap-4">
              {!isSessionActive ? (
                <button 
                  onClick={handleStart}
                  className="flex-1 bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-lg shadow-lg shadow-green-900/20 transition-all hover:scale-105"
                >
                  START SESSION
                </button>
              ) : (
                <button 
                  onClick={handleStop}
                  className="flex-1 bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded-lg shadow-lg shadow-red-900/20 transition-all hover:scale-105"
                >
                  STOP SESSION
                </button>
              )}
            </div>
          </div>
          
          <div className="bg-blue-500/5 p-4 rounded-lg border border-blue-500/10">
            <h4 className="text-blue-400 font-bold mb-2">System Status</h4>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              YOLO-World: Ready
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-400 mt-1">
              <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
              SAM 3 Analyzer: Idle
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Dashboard;
