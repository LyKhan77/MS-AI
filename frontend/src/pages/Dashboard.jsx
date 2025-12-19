import React, { useState, useRef } from 'react';
import LiveStream from '../components/LiveStream';
import StatsCard from '../components/StatsCard';
import { startSession, stopSession, setSource } from '../services/api';

const Dashboard = () => {
  const [sessionName, setSessionName] = useState('');
  const [maxCount, setMaxCount] = useState(100);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [currentCount, setCurrentCount] = useState(0);
  const [sourceInput, setSourceInput] = useState({ mode: 'rtsp', value: '' });
  const [uploadedFile, setUploadedFile] = useState(null);
  const [playbackState, setPlaybackState] = useState({
    isPaused: false,
    currentFrame: 0,
    totalFrames: 0,
    fps: 0
  });
  
  // Ref for file input to reset it
  const fileInputRef = useRef(null);

  // Poll playback info when in video mode
  React.useEffect(() => {
    if (sourceInput.mode === 'upload') {
      const interval = setInterval(async () => {
        try {
          const response = await fetch('/api/playback/info');
          const data = await response.json();
          setPlaybackState({
            isPaused: data.is_paused,
            currentFrame: data.current_frame,
            totalFrames: data.total_frames,
            fps: data.fps
          });
        } catch (err) {
          console.error('Failed to fetch playback info:', err);
        }
      }, 500);
      return () => clearInterval(interval);
    }
  }, [sourceInput.mode]);

  const handleStart = async () => {
    try {
      await startSession({ name: sessionName, max_count: parseInt(maxCount) });
      setIsSessionActive(true);
      setCurrentCount(0);
      
      // If in video mode, auto-play from start
      if (sourceInput.mode === 'upload' && uploadedFile) {
        // Seek to frame 0
        await fetch('/api/playback/seek', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ frame: 0 })
        });
        
        // Resume playback
        await fetch('/api/playback/resume', { method: 'POST' });
      }
    } catch (err) {
      console.error(err);
      alert('Failed to start session');
    }
  };

  const handleStop = async () => {
    try {
      await stopSession();
      setIsSessionActive(false);
      
      // Pause video if in upload mode
      if (sourceInput.mode === 'upload' && uploadedFile) {
        await fetch('/api/playback/pause', { method: 'POST' });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSetSource = async () => {
    try {
      await setSource(sourceInput.value);
      alert('RTSP source connected');
    } catch (err) {
      console.error(err);
      alert('Failed to connect RTSP');
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setUploadedFile(file.name);
        alert(`Video uploaded: ${data.path}`);
      } else {
        alert(`Upload failed: ${data.error}`);
      }
    } catch (err) {
      console.error(err);
      alert('Upload error');
    }
  };

  const handleRemoveFile = async () => {
    try {
      await fetch('/api/camera/stop', { method: 'POST' });
      setUploadedFile(null);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      console.error('Failed to stop camera:', err);
      setUploadedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleRefresh = async () => {
    try {
      // Stop camera
      await fetch('/api/camera/stop', { method: 'POST' });
      
      // Reset all states
      setUploadedFile(null);
      setSourceInput({ mode: 'rtsp', value: '' });
      setCurrentCount(0);
      setPlaybackState({
        isPaused: false,
        currentFrame: 0,
        totalFrames: 0,
        fps: 0
      });
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Reload page to clear all cache
      window.location.reload();
    } catch (err) {
      console.error('Refresh error:', err);
      window.location.reload();
    }
  };

  const handlePlayPause = async () => {
    try {
      const endpoint = playbackState.isPaused ? '/api/playback/resume' : '/api/playback/pause';
      await fetch(endpoint, { method: 'POST' });
    } catch (err) {
      console.error('Playback control error:', err);
    }
  };

  const handleSeek = async (e) => {
    const frame = parseInt(e.target.value);
    try {
      await fetch('/api/playback/seek', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ frame })
      });
    } catch (err) {
      console.error('Seek error:', err);
    }
  };

  return (
    <div className="p-8 pb-12 h-full flex flex-col gap-8 overflow-y-auto">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Production Dashboard</h1>
          <p className="text-gray-400">Real-time Metal Sheet Counting & QC</p>
        </div>
        <div className="flex items-center gap-3">
          <div className={`px-4 py-2 rounded-full font-bold ${isSessionActive ? 'bg-green-500/20 text-green-400 border border-green-500/50' : 'bg-gray-800 text-gray-500'}`}>
            {isSessionActive ? 'SESSION ACTIVE' : 'IDLE'}
          </div>
          <button
            onClick={handleRefresh}
            className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
            title="Refresh & Clear Cache"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
            </svg>
          </button>
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
          <div className="bg-white/5 border border-white/10 p-4 rounded-lg backdrop-blur-sm space-y-4">
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-gray-300">Input Mode:</span>
              <label className="flex items-center gap-2 cursor-pointer">
                <input 
                  type="radio" 
                  name="inputMode" 
                  value="rtsp"
                  checked={sourceInput.mode === 'rtsp'}
                  onChange={() => setSourceInput({...sourceInput, mode: 'rtsp'})}
                  className="w-4 h-4 text-primary"
                />
                <span className="text-sm text-white">RTSP Stream</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input 
                  type="radio" 
                  name="inputMode" 
                  value="upload"
                  checked={sourceInput.mode === 'upload'}
                  onChange={() => setSourceInput({...sourceInput, mode: 'upload'})}
                  className="w-4 h-4 text-primary"
                />
                <span className="text-sm text-white">Upload Video</span>
              </label>
            </div>

            {sourceInput.mode === 'rtsp' ? (
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={sourceInput.value}
                  onChange={(e) => setSourceInput({...sourceInput, value: e.target.value})}
                  placeholder="rtsp://username:password@ip:port/stream"
                  className="flex-1 bg-black/40 border border-white/10 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-primary"
                />
                <button 
                  onClick={handleSetSource}
                  className="bg-primary hover:bg-secondary px-4 py-2 rounded text-sm transition-colors font-medium"
                >
                  Connect
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {!uploadedFile ? (
                  <div className="flex gap-2">
                    <input 
                      ref={fileInputRef}
                      type="file" 
                      accept="video/*"
                      onChange={handleFileUpload}
                      className="flex-1 bg-black/40 border border-white/10 rounded px-3 py-2 text-sm text-white file:mr-4 file:py-1 file:px-3 file:rounded file:border-0 file:text-sm file:bg-primary file:text-white hover:file:bg-secondary file:cursor-pointer"
                    />
                  </div>
                ) : (
                  <div className="flex items-center gap-2 p-3 bg-black/20 rounded border border-white/5">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary shrink-0"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="m10 11 2 2 4-4"/></svg>
                    <span className="flex-1 text-sm text-white truncate">{uploadedFile}</span>
                    <button 
                      onClick={handleRemoveFile}
                      className="p-1.5 rounded hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors"
                      title="Remove video"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
                    </button>
                  </div>
                )}
                
                {/* Playback Controls - Only show if file uploaded */}
                {uploadedFile && (
                  <div className="flex items-center gap-3 p-3 bg-black/20 rounded border border-white/5">
                    <button 
                      onClick={handlePlayPause}
                      disabled={isSessionActive}
                      className={`p-2 rounded transition-colors ${isSessionActive ? 'bg-gray-700 cursor-not-allowed opacity-50' : 'bg-primary hover:bg-secondary'}`}
                      title={isSessionActive ? "Disabled during session" : (playbackState.isPaused ? "Resume" : "Pause")}
                    >
                      {playbackState.isPaused ? (
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>
                      )}
                    </button>
                    
                    <div className="flex-1 flex items-center gap-2">
                      <input 
                        type="range" 
                        min="0" 
                        max={playbackState.totalFrames || 100}
                        value={playbackState.currentFrame}
                        onChange={handleSeek}
                        disabled={isSessionActive}
                        className={`flex-1 h-1 bg-gray-700 rounded-lg appearance-none accent-primary ${isSessionActive ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'}`}
                      />
                      <span className="text-xs text-gray-400 min-w-[80px]">
                        {playbackState.currentFrame} / {playbackState.totalFrames}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
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
