import React, { useState, useRef, useEffect, useCallback } from 'react';
import LiveStream from '../components/LiveStream';
import StatsCard from '../components/StatsCard';
import ConfirmDialog from '../components/ConfirmDialog';
import { useToast } from '../components/Toast';
import {
  startSession,
  stopSession,
  setSource,
  uploadVideo,
  stopCamera,
  pausePlayback,
  resumePlayback,
  seekPlayback,
  getPlaybackInfo
} from '../services/api';

const Dashboard = () => {
  const { success, error, warning } = useToast();

  // Load settings from localStorage
  const loadSettings = () => {
    const saved = localStorage.getItem('dashboardSettings');
    return saved ? JSON.parse(saved) : {};
  };

  const saveSettings = (settings) => {
    localStorage.setItem('dashboardSettings', JSON.stringify(settings));
  };

  const [sessionName, setSessionName] = useState(() => loadSettings().sessionName || '');
  const [maxCount, setMaxCount] = useState(() => loadSettings().maxCount || 100);
  const [confidenceThreshold, setConfidenceThreshold] = useState(() => loadSettings().confidenceThreshold || 0.25);
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

  // Loading states
  const [isLoading, setIsLoading] = useState({
    start: false,
    stop: false,
    upload: false,
    connect: false,
    remove: false,
    refresh: false
  });

  // Confirmation dialogs
  const [confirmDialog, setConfirmDialog] = useState({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: null
  });

  // Ref for file input to reset it
  const fileInputRef = useRef(null);
  const pollingIntervalRef = useRef(null);

  // Save settings when they change
  useEffect(() => {
    saveSettings({ sessionName, maxCount, confidenceThreshold });
  }, [sessionName, maxCount, confidenceThreshold]);

  // Auto-stop when count reaches max
  useEffect(() => {
    if (isSessionActive && currentCount >= maxCount) {
      warning(`Max count (${maxCount}) reached! Stopping session...`);
      handleStop();
    }
  }, [currentCount, maxCount, isSessionActive]);

  // Poll playback info when in video mode (reduced from 500ms to 1s)
  useEffect(() => {
    if (sourceInput.mode === 'upload' && uploadedFile) {
      pollingIntervalRef.current = setInterval(async () => {
        try {
          const response = await getPlaybackInfo();
          setPlaybackState({
            isPaused: response.data.is_paused,
            currentFrame: response.data.current_frame,
            totalFrames: response.data.total_frames,
            fps: response.data.fps
          });
        } catch (err) {
          console.error('Failed to fetch playback info:', err);
        }
      }, 1000); // Increased from 500ms to 1000ms
      return () => clearInterval(pollingIntervalRef.current);
    }
  }, [sourceInput.mode, uploadedFile]);

  // Cleanup on unmount or when leaving dashboard
  useEffect(() => {
    return () => {
      // Clear video when unmounting
      if (sourceInput.mode === 'upload' && uploadedFile) {
        handleRemoveVideo();
      }
      // Clear polling
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [sourceInput.mode, uploadedFile]);

  const validateSessionStart = () => {
    if (!sessionName.trim()) {
      error('Please enter a session name');
      return false;
    }
    if (maxCount < 1) {
      error('Max count must be at least 1');
      return false;
    }
    if (sourceInput.mode === 'rtsp' && !sourceInput.value) {
      error('Please enter an RTSP source URL');
      return false;
    }
    if (sourceInput.mode === 'upload' && !uploadedFile) {
      error('Please upload a video file first');
      return false;
    }
    return true;
  };

  const handleStart = async () => {
    if (!validateSessionStart()) return;

    setIsLoading(prev => ({ ...prev, start: true }));

    try {
      await startSession({
        name: sessionName,
        max_count: parseInt(maxCount),
        confidence: parseFloat(confidenceThreshold)
      });

      setIsSessionActive(true);
      setCurrentCount(0);
      success('Session started successfully');

      // If in video mode, seek and resume with delay to avoid race condition
      if (sourceInput.mode === 'upload' && uploadedFile) {
        await new Promise(resolve => setTimeout(resolve, 500)); // Wait for session to be ready

        try {
          await seekPlayback(0);
          await resumePlayback();
        } catch (err) {
          console.warn('Playback control failed:', err);
        }
      }
    } catch (err) {
      console.error(err);
      const errorMsg = err.response?.data?.error || err.message || 'Failed to start session';
      error(errorMsg);
    } finally {
      setIsLoading(prev => ({ ...prev, start: false }));
    }
  };

  const handleStop = async () => {
    setConfirmDialog({
      isOpen: true,
      title: 'Stop Session',
      message: 'Are you sure you want to stop the current session? The session will be marked as completed.',
      onConfirm: async () => {
        setIsLoading(prev => ({ ...prev, stop: true }));
        setConfirmDialog({ isOpen: false, title: '', message: '', onConfirm: null });

        try {
          await stopSession();
          setIsSessionActive(false);

          // Pause video if in upload mode
          if (sourceInput.mode === 'upload' && uploadedFile) {
            await pausePlayback();
          }

          success('Session stopped');
        } catch (err) {
          console.error(err);
          error('Failed to stop session');
        } finally {
          setIsLoading(prev => ({ ...prev, stop: false }));
        }
      }
    });
  };

  const handleSetSource = async () => {
    if (!sourceInput.value) {
      error('Please enter an RTSP source URL');
      return;
    }

    setIsLoading(prev => ({ ...prev, connect: true }));

    try {
      await setSource(sourceInput.value);
      success('RTSP source connected');
    } catch (err) {
      console.error(err);
      error('Failed to connect RTSP source');
    } finally {
      setIsLoading(prev => ({ ...prev, connect: false }));
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsLoading(prev => ({ ...prev, upload: true }));

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await uploadVideo(formData);
      if (response.data) {
        setUploadedFile(file.name);
        success(`Video uploaded: ${file.name}`);
      }
    } catch (err) {
      console.error(err);
      const errorMsg = err.response?.data?.error || 'Upload failed';
      error(errorMsg);
    } finally {
      setIsLoading(prev => ({ ...prev, upload: false }));
    }
  };

  const handleRemoveFile = () => {
    setConfirmDialog({
      isOpen: true,
      title: 'Remove Video',
      message: 'Are you sure you want to remove the uploaded video? The camera will be stopped.',
      onConfirm: async () => {
        setIsLoading(prev => ({ ...prev, remove: true }));
        setConfirmDialog({ isOpen: false, title: '', message: '', onConfirm: null });

        try {
          await stopCamera();
        } catch (err) {
          console.error('Failed to stop camera:', err);
        } finally {
          setUploadedFile(null);
          setPlaybackState({
            isPaused: false,
            currentFrame: 0,
            totalFrames: 0,
            fps: 0
          });

          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }

          setIsLoading(prev => ({ ...prev, remove: false }));
          success('Video removed');
        }
      }
    });
  };

  // Alias for cleanup effect
  const handleRemoveVideo = handleRemoveFile;

  const handleRefresh = () => {
    setConfirmDialog({
      isOpen: true,
      title: 'Refresh Dashboard',
      message: 'This will clear all cached data and reload the page. Any unsaved work will be lost. Continue?',
      onConfirm: () => {
        setConfirmDialog({ isOpen: false, title: '', message: '', onConfirm: null });
        window.location.reload();
      }
    });
  };

  const handlePlayPause = async () => {
    if (isSessionActive) return;

    try {
      if (playbackState.isPaused) {
        await resumePlayback();
      } else {
        await pausePlayback();
      }
    } catch (err) {
      console.error('Playback control error:', err);
      error('Failed to control playback');
    }
  };

  const handleSeek = async (e) => {
    if (isSessionActive) return;

    const frame = parseInt(e.target.value);
    try {
      await seekPlayback(frame);
    } catch (err) {
      console.error('Seek error:', err);
    }
  };

  return (
    <div className="p-4 md:p-8 pb-12 h-full flex flex-col gap-6 md:gap-8 overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white">Production Dashboard</h1>
          <p className="text-sm md:text-base text-gray-400">Real-time Metal Sheet Counting & QC</p>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className={`flex-1 md:flex-none text-center px-4 py-2 rounded-full font-bold text-xs md:text-sm ${isSessionActive ? 'bg-green-500/20 text-green-400 border border-green-500/50' : 'bg-gray-800 text-gray-500'}`}>
            {isSessionActive ? 'SESSION ACTIVE' : 'IDLE'}
          </div>
          <button
            onClick={handleRefresh}
            disabled={isLoading.refresh}
            className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors disabled:opacity-50"
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
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <span className="text-sm font-medium text-gray-300">Input Mode:</span>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="inputMode"
                    value="rtsp"
                    checked={sourceInput.mode === 'rtsp'}
                    onChange={() => {
                      setSourceInput({ mode: 'rtsp', value: '' });
                      setUploadedFile(null);
                    }}
                    className="w-4 h-4 text-primary"
                    disabled={isSessionActive}
                  />
                  <span className="text-sm text-white">RTSP Stream</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="inputMode"
                    value="upload"
                    checked={sourceInput.mode === 'upload'}
                    onChange={() => {
                      setSourceInput({ mode: 'upload', value: '' });
                    }}
                    className="w-4 h-4 text-primary"
                    disabled={isSessionActive}
                  />
                  <span className="text-sm text-white">Upload Video</span>
                </label>
              </div>
            </div>

            {sourceInput.mode === 'rtsp' ? (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={sourceInput.value}
                  onChange={(e) => setSourceInput({ ...sourceInput, value: e.target.value })}
                  placeholder="rtsp://username:password@ip:port/stream"
                  disabled={isSessionActive}
                  className="flex-1 bg-black/40 border border-white/10 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-primary disabled:opacity-50"
                />
                <button
                  onClick={handleSetSource}
                  disabled={isLoading.connect || isSessionActive}
                  className="bg-primary hover:bg-secondary px-4 py-2 rounded text-sm transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isLoading.connect ? (
                    <>
                      <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Connecting...
                    </>
                  ) : 'Connect'}
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
                      disabled={isLoading.upload || isSessionActive}
                      className="flex-1 bg-black/40 border border-white/10 rounded px-3 py-2 text-sm text-white file:mr-4 file:py-1 file:px-3 file:rounded file:border-0 file:text-xs md:text-sm file:bg-primary file:text-white hover:file:bg-secondary file:cursor-pointer w-full disabled:opacity-50"
                    />
                    {isLoading.upload && (
                      <div className="flex items-center gap-2 text-primary text-sm">
                        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Uploading...
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center gap-2 p-3 bg-black/20 rounded border border-white/5">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary shrink-0"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="m10 11 2 2 4-4"/></svg>
                    <span className="flex-1 text-sm text-white truncate min-w-0">{uploadedFile}</span>
                    <button
                      onClick={handleRemoveFile}
                      disabled={isLoading.remove}
                      className="p-1.5 rounded hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-colors shrink-0 disabled:opacity-50"
                      title="Remove video"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 6"/><path d="m6 6 12 12"/></svg>
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
            <h3 className="text-white font-bold uppercase tracking-wider text-sm bg-white/10 inline-block w-max px-2 py-1 rounded">Session Control</h3>

            <div className="flex flex-col gap-2">
              <label className="text-xs text-gray-400 uppercase">Session Name</label>
              <input
                type="text"
                disabled={isSessionActive}
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                className="bg-black/20 border border-white/10 rounded px-3 py-2 text-white disabled:opacity-50 focus:outline-none focus:border-primary"
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
                min="1"
                className="bg-black/20 border border-white/10 rounded px-3 py-2 text-white disabled:opacity-50 focus:outline-none focus:border-primary"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs text-gray-400 uppercase">Confidence Threshold</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0.1"
                  max="1.0"
                  step="0.05"
                  disabled={isSessionActive}
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(parseFloat(e.target.value))}
                  className="flex-1 accent-primary disabled:opacity-50"
                />
                <span className="text-white font-mono text-sm min-w-[50px]">{(confidenceThreshold * 100).toFixed(0)}%</span>
              </div>
              <p className="text-xs text-gray-500">Lower = more detections, Higher = more strict</p>
            </div>

            <div className="mt-4 flex gap-4">
              {!isSessionActive ? (
                <button
                  onClick={handleStart}
                  disabled={isLoading.start}
                  className="flex-1 bg-green-600 hover:bg-green-500 text-white font-bold py-3 rounded-lg shadow-lg shadow-green-900/20 transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
                >
                  {isLoading.start ? (
                    <>
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Starting...
                    </>
                  ) : 'START SESSION'}
                </button>
              ) : (
                <button
                  onClick={handleStop}
                  disabled={isLoading.stop}
                  className="flex-1 bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded-lg shadow-lg shadow-red-900/20 transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
                >
                  {isLoading.stop ? (
                    <>
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Stopping...
                    </>
                  ) : 'STOP SESSION'}
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

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={confirmDialog.title}
        message={confirmDialog.message}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog({ isOpen: false, title: '', message: '', onConfirm: null })}
      />
    </div>
  );
};

export default Dashboard;
