import React, { useState, useEffect } from 'react';
import { streamAPI, sessionAPI } from '../services/api';
import { Play, Square, Upload, Settings } from 'lucide-react';

const LiveMonitor = () => {
  const [sessionStatus, setSessionStatus] = useState({
    count: 0,
    target: 0,
    active: false,
    name: '-'
  });
  const [streamSource, setStreamSource] = useState('rtsp'); // 'rtsp' or 'file'
  const [rtspUrl, setRtspUrl] = useState('rtsp://192.168.1.10:8554/live');
  const [loading, setLoading] = useState(false);

  // Poll Session Status
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await sessionAPI.getStatus();
        setSessionStatus(res.data);
      } catch (err) {
        console.error("Failed to fetch status", err);
      }
    }, 1000); // 1 sec poll
    return () => clearInterval(interval);
  }, []);

  const handleStartSession = async () => {
    try {
        await sessionAPI.start("Batch-" + Date.now(), 100);
    } catch (e) {
        alert("Error starting session");
    }
  };

  const handleStopSession = async () => {
      await sessionAPI.stop();
  };

  const handleFileUpload = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      const formData = new FormData();
      formData.append('file', file);
      
      setLoading(true);
      try {
          const res = await streamAPI.uploadVideo(formData);
          // Set source to this file
          await streamAPI.setSource('file', res.data.path);
          setStreamSource('file');
      } catch (err) {
          alert("Upload failed");
      } finally {
          setLoading(false);
      }
  };

  const handleSetRTSP = async () => {
      await streamAPI.setSource('rtsp', rtspUrl);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Video Feed */}
        <div className="lg:col-span-2 bg-black rounded-lg overflow-hidden border border-gray-700 shadow-xl relative aspect-video">
          <img 
            src="/api/v1/streams/video_feed" 
            alt="Live Stream" 
            className="w-full h-full object-contain"
          />
          
          {/* Status Overlay */}
          <div className="absolute top-4 left-4 flex space-x-2">
            <span className={`px-3 py-1 rounded text-xs font-bold uppercase ${sessionStatus.active ? 'bg-green-600' : 'bg-red-600'}`}>
                {sessionStatus.active ? 'Monitoring Active' : 'Paused'}
            </span>
            <span className="bg-gray-800/80 px-3 py-1 rounded text-xs text-white">
                Source: {streamSource.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Right Column: Controls */}
        <div className="space-y-6">
          {/* Big Counter */}
          <div className="bg-dark-surface p-6 rounded-lg text-center border border-gray-700">
             <h3 className="text-gray-400 text-sm uppercase tracking-wider mb-2">Current Count</h3>
             <div className={`text-7xl font-bold mb-2 ${sessionStatus.count >= sessionStatus.target && sessionStatus.target > 0 ? 'text-red-500 animate-pulse' : 'text-primary-light'}`}>
                 {sessionStatus.count}
             </div>
             <p className="text-gray-500">Target: {sessionStatus.target}</p>
          </div>

          {/* Session Controls */}
          <div className="bg-dark-surface p-6 rounded-lg border border-gray-700 space-y-4">
              <h3 className="text-white font-semibold flex items-center gap-2">
                  <Settings size={18} /> Session Control
              </h3>
              
              {!sessionStatus.active ? (
                  <button 
                    onClick={handleStartSession}
                    className="w-full py-4 bg-primary hover:bg-primary-light text-white rounded-lg font-bold flex items-center justify-center gap-2 transition-colors">
                      <Play size={20} /> START SESSION
                  </button>
              ) : (
                  <button 
                    onClick={handleStopSession}
                    className="w-full py-4 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold flex items-center justify-center gap-2 transition-colors">
                      <Square size={20} /> STOP SESSION
                  </button>
              )}
          </div>
          
          {/* Source Controls */}
          <div className="bg-dark-surface p-6 rounded-lg border border-gray-700 space-y-4">
              <h3 className="text-white font-semibold">Video Source</h3>
              
              <div className="space-y-2">
                  <div className="flex gap-2">
                      <input 
                        type="text" 
                        value={rtspUrl}
                        onChange={(e) => setRtspUrl(e.target.value)}
                        className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm w-full text-white"
                        placeholder="rtsp://..."
                      />
                      <button onClick={handleSetRTSP} className="bg-gray-700 hover:bg-gray-600 px-3 py-2 rounded text-white text-xs">Set</button>
                  </div>
                  
                  <div className="relative">
                      <input 
                        type="file" 
                        onChange={handleFileUpload}
                        className="hidden" 
                        id="video-upload"
                        accept="video/*"
                      />
                      <label htmlFor="video-upload" className="w-full flex items-center justify-center gap-2 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2 rounded cursor-pointer border border-dashed border-gray-600 transition-colors">
                          <Upload size={16} /> 
                          {loading ? "Uploading..." : "Upload Video File"}
                      </label>
                  </div>
              </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMonitor;
