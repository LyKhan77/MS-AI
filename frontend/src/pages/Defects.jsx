import React, { useState, useEffect } from 'react';

const DEFECT_COLORS = {
  scratch: '#FF0000',
  dent: '#00FF00',
  rust: '#FFA500',
  hole: '#FFFF00',
  coating_bubble: '#FF00FF',
  oil_stain: '#0000FF',
  discoloration: '#808080',
  pitting: '#FFC0CB',
  edge_burr: '#A52A2A',
  warping: '#00FFFF'
};

const DEFECT_TYPES = [
  { id: 'scratch', label: 'Scratches', prompt: 'linear scratch mark on metal surface' },
  { id: 'dent', label: 'Dents', prompt: 'dent or deformation on metal sheet' },
  { id: 'rust', label: 'Rust/Corrosion', prompt: 'rust spot or corrosion on metal' },
  { id: 'hole', label: 'Holes/Perforations', prompt: 'hole or perforation in metal' },
  { id: 'coating_bubble', label: 'Coating Bubbles', prompt: 'paint bubble or coating defect' },
  { id: 'oil_stain', label: 'Oil Stains', prompt: 'oil or grease stain on metal' },
  { id: 'discoloration', label: 'Discoloration', prompt: 'color irregularity or uneven tint' },
  { id: 'pitting', label: 'Pitting', prompt: 'small pits or indentations on surface' },
  { id: 'edge_burr', label: 'Edge Burrs', prompt: 'rough or sharp edge burr' },
  { id: 'warping', label: 'Warping', prompt: 'warped or bent metal deformation' }
];

const Defects = () => {
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [defects, setDefects] = useState([]);
  const [defectStats, setDefectStats] = useState(null);
  const [showImagesModal, setShowImagesModal] = useState(false);
  const [captures, setCaptures] = useState([]);
  const [loadingCaptures, setLoadingCaptures] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedDefectTypes, setSelectedDefectTypes] = useState(() => {
    try {
      const saved = localStorage.getItem('defectTypesConfig');
      return saved ? JSON.parse(saved) : ['scratch'];
    } catch {
      return ['scratch'];
    }
  });
  const [toast, setToast] = useState({ show: false, message: '', type: 'error' });
  const [viewMode, setViewMode] = useState('image');
  const [groupedDefects, setGroupedDefects] = useState([]);
  const [showDefectDetailModal, setShowDefectDetailModal] = useState(false);
  const [selectedImageDefects, setSelectedImageDefects] = useState(null);
  const [showCropModal, setShowCropModal] = useState(false);
  const [selectedCrop, setSelectedCrop] = useState(null);
  const [isCropping, setIsCropping] = useState(false);

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    localStorage.setItem('defectTypesConfig', JSON.stringify(selectedDefectTypes));
  }, [selectedDefectTypes]);

  const handleDefectToggle = (type) => {
    setSelectedDefectTypes(prev =>
      prev.includes(type)
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const handleSelectAll = () => {
    setSelectedDefectTypes(DEFECT_TYPES.map(d => d.id));
  };

  const handleClearAll = () => {
    setSelectedDefectTypes([]);
  };

  const handleSaveConfig = () => {
    setShowConfigModal(false);
  };

  const showToast = (message, type = 'error') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: '', type: '' }), 3000);
  };

  const groupDefectsByImage = (defectsList) => {
    const groups = {};
    defectsList.forEach(defect => {
      if (!groups[defect.image_filename]) {
        groups[defect.image_filename] = [];
      }
      groups[defect.image_filename].push(defect);
    });

    return Object.entries(groups)
      .map(([filename, defectsList]) => ({ filename, defects: defectsList, count: defectsList.length }))
      .sort((a, b) => a.filename.localeCompare(b.filename));
  };

  const handleViewModeToggle = (mode) => {
    setViewMode(mode);
  };

  const handleImageClick = (imageDefects) => {
    setSelectedImageDefects(imageDefects);
    setShowDefectDetailModal(true);
  };

  const handleCropClick = (defect) => {
    setSelectedCrop(defect);
    setShowCropModal(true);
  };

  const handleCropDefect = async (defect) => {
    if (!selectedSession) return;

    setIsCropping(true);
    try {
      const response = await fetch(`/api/sessions/${selectedSession.id}/crop_defects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_filename: defect.image_filename })
      });
      const data = await response.json();

      if (data.status === 'completed') {
        await fetchDefects(selectedSession.id);
      } else {
        alert('Crop failed: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      console.error(err);
      alert('Crop error: ' + err.message);
    } finally {
      setIsCropping(false);
    }
  };

  const handleCropDefectsForImage = async (imageDefects) => {
    if (!selectedSession) return;

    setIsCropping(true);
    try {
      const response = await fetch(`/api/sessions/${selectedSession.id}/crop_defects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_filename: imageDefects.filename })
      });
      const data = await response.json();

      if (data.status === 'completed') {
        await fetchDefects(selectedSession.id);
        alert(`Cropped ${data.crop_count} defect(s)`);
      } else {
        alert('Crop failed: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      console.error(err);
      alert('Crop error: ' + err.message);
    } finally {
      setIsCropping(false);
    }
  };

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/sessions/list?per_page=100');
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDefects = async (sessionId) => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}/defects`);
      const data = await response.json();
      setDefects(data.defects || []);
      setDefectStats({
        by_type: data.stats_by_type || {},
        by_severity: data.stats_by_severity || {}
      });
      setGroupedDefects(groupDefectsByImage(data.defects || []));
    } catch (err) {
      console.error('Failed to fetch defects:', err);
    }
  };

  const handleSelectSession = async (session) => {
    setSelectedSession(session);
    setDefects([]);
    setDefectStats(null);
    
    // Load existing defects if available
    if (session.defects_found && session.defects_found > 0) {
      await fetchDefects(session.id);
    }
  };

  const handleViewImages = async (session) => {
    setSelectedSession(session);
    setShowImagesModal(true);
    setLoadingCaptures(true);
    try {
      const response = await fetch(`/api/sessions/${session.id}/captures`);
      const data = await response.json();
      setCaptures(data.captures || []);
    } catch (err) {
      console.error('Failed to fetch captures:', err);
    } finally {
      setLoadingCaptures(false);
    }
  };

  const handleRunSegmentation = async () => {
    if (!selectedSession) {
      showToast('Please select a session first', 'error');
      return;
    }

    if (selectedDefectTypes.length === 0) {
      showToast('No Defect Type selected.', 'error');
      return;
    }

    if (!confirm(`Run defect analysis on "${selectedSession.name}"?\n\nThis may take several minutes depending on the number of captures.`)) {
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await fetch(`/api/sessions/${selectedSession.id}/analyze_defects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ defect_types: selectedDefectTypes })
      });
      const data = await response.json();

      if (data.status === 'completed') {
        setDefects(data.results.defects || []);

        // Show different message based on results
        if (data.results.defects_found === 0) {
          alert(`Analysis Complete!\n\nNo defects detected\nMetal sheets are safe\nSession quality: PASS\n\nProcessing time: ${data.results.processing_time.toFixed(1)}s`);
        } else {
          alert(`Analysis complete!\n\nFound ${data.results.defects_found} defects in ${data.results.processing_time.toFixed(1)}s\n\nReview defects below.`);
        }

        // Refresh defect data
        await fetchDefects(selectedSession.id);
        // Refresh sessions list to update stats
        await fetchSessions();
      } else {
        alert('❌ Analysis failed: ' + (data.error || 'Unknown error'));
      }
    } catch (err) {
      console.error(err);
      alert('❌ Analysis error: ' + err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  const handleExportDefects = () => {
    if (!selectedSession) return;
    window.open(`/api/sessions/${selectedSession.id}/defects/export`, '_blank');
  };

  return (
    <div className="p-4 md:p-8 pb-12 h-full flex flex-col gap-6 md:gap-8 overflow-y-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl md:text-3xl font-bold text-white">Defect Analysis</h1>
        <p className="text-sm md:text-base text-gray-400">SAM-3 powered defect detection for metal sheets</p>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left: Session Selector */}
        <div className="lg:col-span-1 bg-white/5 border border-white/10 rounded-lg backdrop-blur-sm overflow-hidden">
          <div className="p-4 border-b border-white/10 bg-white/5">
            <h2 className="text-lg font-semibold text-white">Select Session</h2>
            <p className="text-xs text-gray-400 mt-1">Choose a completed session to analyze</p>
          </div>
          
          <div className="overflow-y-auto max-h-[600px]">
            {loading ? (
              <div className="p-8 text-center text-gray-400">
                <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary border-t-transparent mx-auto mb-3"/>
                Loading sessions...
              </div>
            ) : sessions.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                <p>No sessions found</p>
                <p className="text-xs mt-2">Complete a session first</p>
              </div>
            ) : (
              <div className="flex flex-col">
                {sessions
                  .filter(s => s.status === 'completed')
                  .map((session) => (
                  <button
                    key={session.id}
                    onClick={() => handleSelectSession(session)}
                    className={`p-4 border-b border-white/5 text-left transition-colors ${
                      selectedSession?.id === session.id
                        ? 'bg-primary/20 border-l-4 border-l-primary'
                        : 'hover:bg-white/5'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="font-medium text-white text-sm">{session.name}</div>
                        <div className="text-xs text-gray-400 mt-1">
                          {new Date(session.start_time).toLocaleDateString()} • {session.total_count} sheets
                        </div>
                        {session.defects_found > 0 && (
                          <div className="text-xs text-green-400 mt-1 flex items-center gap-1">
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                            {session.defects_found} defects found
                          </div>
                        )}
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewImages(session);
                        }}
                        className="p-1.5 hover:bg-white/10 rounded transition-colors"
                        title="View captured images"
                      >
                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </button>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Analysis Panel */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          
          {/* Analysis Controls */}
          <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-white/10 rounded-lg p-4 md:p-6 backdrop-blur-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex-1">
                <h3 className="text-base md:text-lg font-semibold text-white flex items-center gap-2">
                  Defect Segmentation
                </h3>
                <p className="text-xs md:text-sm text-gray-400 mt-1">
                  Detect Defects using SAM-3
                </p>
                {selectedSession && (
                  <p className="text-xs text-blue-400 mt-2">
                    Selected: <span className="font-semibold">{selectedSession.name}</span>
                  </p>
                )}
              </div>
              <div className="flex flex-col gap-2 sm:gap-3">
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleViewModeToggle('image')}
                    className={`px-3 py-1.5 text-sm rounded transition-colors ${
                      viewMode === 'image'
                        ? 'bg-primary text-white'
                        : 'bg-white/10 text-gray-400 hover:bg-white/20'
                    }`}
                  >
                    Image View
                  </button>
                  <button
                    onClick={() => handleViewModeToggle('crops')}
                    className={`px-3 py-1.5 text-sm rounded transition-colors ${
                      viewMode === 'crops'
                        ? 'bg-primary text-white'
                        : 'bg-white/10 text-gray-400 hover:bg-white/20'
                    }`}
                  >
                    Crop List
                  </button>
                </div>
                <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                <button
                  onClick={() => setShowConfigModal(true)}
                  className="flex-1 sm:flex-none px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded-lg text-white font-medium transition-all text-sm flex items-center justify-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>Configuration</span>
                  {selectedDefectTypes.length > 0 && (
                    <span className="bg-primary px-1.5 py-0.5 rounded text-[10px] leading-none">{selectedDefectTypes.length}</span>
                  )}
                </button>
                <button
                  onClick={handleRunSegmentation}
                  disabled={isAnalyzing || !selectedSession}
                  className="flex-1 sm:flex-none px-4 py-2 bg-primary hover:bg-secondary rounded-lg text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm flex items-center justify-center gap-2"
                >
                  {isAnalyzing ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                      </svg>
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                      <span>Run Segmentation</span>
                    </>
                  )}
                </button>
                {defects.length > 0 && (
                  <button
                    onClick={handleExportDefects}
                    className="flex-1 sm:flex-none px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg text-white font-medium transition-all text-sm flex items-center justify-center gap-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    <span>Export ZIP</span>
                  </button>
                )}
                </div>
              </div>
            </div>
          </div>

          {/* Defect Results */}
          {defects.length > 0 ? (
            <>
              {/* Stats Cards */}
              {defectStats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-white/5 border border-white/10 p-4 rounded-lg">
                    <div className="text-gray-400 text-xs mb-1">Total Defects</div>
                    <div className="text-3xl font-bold text-white">{defects.length}</div>
                  </div>
                  {Object.entries(defectStats.by_severity).map(([severity, count]) => (
                    <div key={severity} className="bg-white/5 border border-white/10 p-4 rounded-lg">
                      <div className={`text-xs font-semibold mb-1 ${
                        severity === 'critical' ? 'text-red-400' :
                        severity === 'moderate' ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        {severity.toUpperCase()}
                      </div>
                      <div className="text-3xl font-bold text-white">{count}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Defect Gallery */}
              {viewMode === 'crops' ? (
                <div className="bg-white/5 border border-white/10 rounded-lg p-4 md:p-6">
                  <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Detected Defects
                  </h3>
                  <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2">
                    {defects.map((defect, idx) => (
                      <div key={idx} className="bg-black/20 rounded-lg overflow-hidden border border-white/10 hover:border-primary transition-colors group">
                        <div className="relative aspect-square">
                          <img
                            src={`/api/sessions/${selectedSession.id}/defects/${defect.crop_filename}`}
                            alt={`${defect.defect_type} defect`}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23333" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" fill="%23666" text-anchor="middle" dy=".3em"%3EError%3C/text%3E%3C/svg%3E';
                            }}
                          />
                          <div className={`absolute top-2 right-2 w-3 h-3 rounded-full ${
                            defect.severity === 'critical' ? 'bg-red-500' :
                            defect.severity === 'moderate' ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`} />
                        </div>
                        <div className="p-2">
                          <div className="text-xs font-semibold text-white truncate capitalize">
                            {defect.defect_type.replace('_', ' ')}
                          </div>
                          <div className="text-xs text-gray-400">
                            {(defect.confidence * 100).toFixed(0)}% • {defect.area_pixels}px²
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                // Image View - 2-column grid
                <div className="grid grid-cols-2 gap-4">
                  {groupedDefects.map((img, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleImageClick(img)}
                      className="bg-white/5 border border-white/10 rounded-lg overflow-hidden hover:border-primary transition-all group text-left"
                    >
                      <div className="relative aspect-square">
                        <img
                          src={`/api/sessions/${selectedSession.id}/defects/segmented/${img.filename}`}
                          alt={img.filename}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.src = `/api/sessions/${selectedSession.id}/captures/${img.filename}`;
                          }}
                        />
                        <div className="absolute top-2 right-2 px-2 py-1 bg-black/70 rounded text-xs text-white">
                          {img.count} defects
                        </div>
                      </div>
                      <div className="p-3">
                        <div className="text-xs text-gray-400 truncate mb-1">
                          {img.filename}
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          {img.defects.some(d => d.severity === 'critical') && (
                            <span className="text-red-400">● Critical</span>
                          )}
                          {img.defects.some(d => d.severity === 'moderate') && (
                            <span className="text-yellow-400">● Moderate</span>
                          )}
                          {img.defects.some(d => d.severity === 'minor') && (
                            <span className="text-green-400">● Minor</span>
                          )}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </>
          ) : selectedSession ? (
            selectedSession.defects_analyzed > 0 && selectedSession.defects_found === 0 ? (
              // Session analyzed but no defects found - SAFE
              <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg p-12 text-center">
                <div className="mb-6">
                  <svg className="w-24 h-24 mx-auto text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-2xl font-bold text-green-400 mb-3">All Clear!</h3>
                <p className="text-lg text-white mb-2">No defects detected</p>
                <p className="text-gray-400 mb-6">
                  Metal sheets in this session passed quality inspection
                </p>
                <div className="inline-flex items-center gap-3 bg-white/5 border border-white/10 rounded-lg px-6 py-3">
                  <div className="flex flex-col text-left">
                    <span className="text-xs text-gray-400">Session Status</span>
                    <span className="text-lg font-bold text-green-400">SAFE ✓</span>
                  </div>
                  <div className="h-10 w-px bg-white/10"/>
                  <div className="flex flex-col text-left">
                    <span className="text-xs text-gray-400">Images Analyzed</span>
                    <span className="text-lg font-semibold text-white">{selectedSession.defects_analyzed}</span>
                  </div>
                </div>
              </div>
            ) : (
              // Not analyzed yet
              <div className="bg-white/5 border border-white/10 rounded-lg p-12 text-center">
                <div className="mb-4">
                  <svg className="w-16 h-16 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">No Defects Analyzed Yet</h3>
                <p className="text-gray-400 mb-4">Click "Run Segmentation" to analyze this session</p>
                <p className="text-sm text-gray-500">
                  Session: {selectedSession.name} • {selectedSession.total_count} captures
                </p>
              </div>
            )
          ) : (
            <div className="bg-white/5 border border-white/10 rounded-lg p-12 text-center">
              <div className="mb-4">
                <svg className="w-16 h-16 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">Select a Session</h3>
              <p className="text-gray-400">Choose a completed session from the left to begin defect analysis</p>
            </div>
          )}

        </div>
      </div>

      {/* Images Modal */}
      {showImagesModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowImagesModal(false)}>
          <div className="bg-[#1a1a2e] border border-white/10 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-white/5">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Captured Images
                </h2>
                {selectedSession && (
                  <p className="text-sm text-gray-400 mt-1">
                    {selectedSession.name} • {captures.length} images
                  </p>
                )}
              </div>
              <button
                onClick={() => setShowImagesModal(false)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-100px)]">
              {loadingCaptures ? (
                <div className="flex items-center justify-center p-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"/>
                </div>
              ) : captures.length === 0 ? (
                <div className="text-center p-12 text-gray-400">
                  <svg className="w-16 h-16 mx-auto mb-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <p>No images found</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                  {captures.map((capture, idx) => (
                    <div key={idx} className="bg-black/20 rounded-lg overflow-hidden border border-white/10 hover:border-primary transition-colors group">
                      <div className="relative aspect-square">
                        <img
                          src={`/api/sessions/${selectedSession.id}/captures/${capture.filename}`}
                          alt={`Capture ${idx + 1}`}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23333" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" fill="%23666" text-anchor="middle" dy=".3em"%3EError%3C/text%3E%3C/svg%3E';
                          }}
                        />
                      </div>
                      <div className="p-2">
                        <div className="text-xs text-gray-400 truncate">
                          {capture.filename}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {new Date(capture.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Configuration Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowConfigModal(false)}>
          <div className="bg-[#1a1a2e] border border-white/10 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-white/5">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Defect Configuration
                </h2>
                <p className="text-sm text-gray-400 mt-1">Select defect types to detect</p>
              </div>
              <button
                onClick={() => setShowConfigModal(false)}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              >
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
              <div className="grid grid-cols-2 gap-3">
                {DEFECT_TYPES.map((defect) => (
                  <button
                    key={defect.id}
                    onClick={() => handleDefectToggle(defect.id)}
                    className={`flex items-center gap-3 p-4 rounded-lg border transition-all ${
                      selectedDefectTypes.includes(defect.id)
                        ? 'bg-primary/20 border-primary text-white'
                        : 'bg-white/5 border-white/10 text-gray-400 hover:bg-white/10'
                    }`}
                  >
                    <div className="w-4 h-4 rounded-full" style={{ backgroundColor: DEFECT_COLORS[defect.id] }} />
                    <div className={`w-5 h-5 rounded border flex items-center justify-center ${
                      selectedDefectTypes.includes(defect.id)
                        ? 'bg-primary border-primary'
                        : 'border-gray-500'
                    }`}>
                      {selectedDefectTypes.includes(defect.id) && (
                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                    <span className="text-sm font-medium">{defect.label}</span>
                  </button>
                ))}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/10">
                <div className="flex gap-2">
                  <button
                    onClick={handleSelectAll}
                    className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-sm text-gray-300 rounded transition-colors"
                  >
                    Select All
                  </button>
                  <button
                    onClick={handleClearAll}
                    className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-sm text-gray-300 rounded transition-colors"
                  >
                    Clear All
                  </button>
                </div>
                <div className="text-sm text-gray-400">
                  {selectedDefectTypes.length} of {DEFECT_TYPES.length} selected
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-white/10 bg-white/5 flex justify-end">
              <button
                onClick={handleSaveConfig}
                className="px-6 py-2 bg-primary hover:bg-secondary rounded-lg text-white font-medium transition-colors"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {toast.show && (
        <div className={`fixed top-4 right-4 z-[100] px-4 py-3 rounded-lg border shadow-lg transition-all ${
          toast.type === 'error'
            ? 'bg-red-900/90 border-red-500 text-white'
            : 'bg-green-900/90 border-green-500 text-white'
        }`}>
          <div className="flex items-center gap-2">
            {toast.type === 'error' ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
            <span className="text-sm font-medium">{toast.message}</span>
          </div>
        </div>
      )}

      {/* Defect Detail Modal */}
      {showDefectDetailModal && selectedImageDefects && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowDefectDetailModal(false)}>
          <div className="bg-[#1a1a2e] border border-white/10 rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden flex" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setShowDefectDetailModal(false)}
              className="absolute top-4 right-4 p-2 bg-white/10 hover:bg-white/20 rounded-lg text-gray-400 z-10"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Left Panel - Segmented Image */}
            <div className="w-1/2 flex flex-col border-r border-white/10 min-h-0">
              <div className="p-4 border-b border-white/10 bg-white/5">
                <h3 className="text-lg font-semibold text-white truncate">
                  {selectedImageDefects.filename}
                </h3>
                <p className="text-sm text-gray-400">
                  {selectedImageDefects.count} defects detected
                </p>
              </div>
              <div className="flex-1 p-4 flex items-center justify-center">
                <img
                  src={`/api/sessions/${selectedSession.id}/defects/segmented/${selectedImageDefects.filename}`}
                  alt="Segmented"
                  className="max-w-full max-h-full object-contain rounded"
                  onError={(e) => {
                    e.target.src = `/api/sessions/${selectedSession.id}/captures/${selectedImageDefects.filename}`;
                  }}
                />
              </div>
            </div>

            {/* Right Panel - Crop Grid */}
            <div className="w-1/2 flex flex-col min-h-0">
              <div className="p-4 border-b border-white/10 bg-white/5">
                <h3 className="text-lg font-semibold text-white">Detected Regions</h3>
              </div>
              <div className="flex-1 p-4 overflow-y-auto">
                <div className="grid grid-cols-2 gap-3">
                  {selectedImageDefects.defects.map((defect, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleCropClick(defect)}
                      className="bg-white/5 border border-white/10 rounded-lg overflow-hidden hover:border-primary transition-all group"
                    >
                      <div className="relative aspect-square">
                        {defect.cropped && defect.crop_filename ? (
                          <img
                            src={`/api/sessions/${selectedSession.id}/defects/${defect.crop_filename}`}
                            alt={defect.defect_type}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full bg-gray-800 flex items-center justify-center">
                            <svg className="w-8 h-8 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                          </div>
                        )}
                        <div className={`absolute top-2 right-2 w-3 h-3 rounded-full ${
                          defect.severity === 'critical' ? 'bg-red-500' :
                          defect.severity === 'moderate' ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`} />
                      </div>
                      <div className="p-2">
                        <div className="text-xs font-semibold text-white truncate capitalize">
                          {defect.defect_type.replace('_', ' ')}
                        </div>
                        <div className="text-xs text-gray-400">
                          {(defect.confidence * 100).toFixed(0)}%
                        </div>
                        {!defect.cropped && (
                          <div className="text-xs text-yellow-400 mt-1">
                            Not cropped
                          </div>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
                <button
                  onClick={() => handleCropDefectsForImage(selectedImageDefects)}
                  disabled={isCropping || selectedImageDefects.defects.every(d => d.cropped)}
                  className="mt-4 w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors flex items-center justify-center gap-2"
                >
                  {isCropping ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                      </svg>
                      <span>Cropping...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      <span>Crop Segmentation</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Enlarged Crop Modal */}
      {showCropModal && selectedCrop && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-sm flex items-center justify-center z-[60] p-4" onClick={() => setShowCropModal(false)}>
          <div className="max-w-4xl w-full" onClick={(e) => e.stopPropagation()}>
            <img
              src={`/api/sessions/${selectedSession.id}/defects/${selectedCrop.crop_filename}`}
              alt={selectedCrop.defect_type}
              className="w-full rounded-lg"
            />
            <div className="mt-3 bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white capitalize">
                    {selectedCrop.defect_type.replace('_', ' ')}
                  </h3>
                  <p className="text-sm text-gray-400">
                    {selectedCrop.image_filename}
                  </p>
                </div>
                <div className={`px-3 py-1 rounded text-sm font-semibold ${
                  selectedCrop.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                  selectedCrop.severity === 'moderate' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-green-500/20 text-green-400'
                }`}>
                  {selectedCrop.severity.toUpperCase()}
                </div>
              </div>
              <div className="mt-3 grid grid-cols-3 gap-3 text-sm">
                <div>
                  <span className="text-gray-400">Confidence</span>
                  <div className="text-white font-semibold">
                    {(selectedCrop.confidence * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <span className="text-gray-400">Area</span>
                  <div className="text-white font-semibold">
                    {selectedCrop.area_pixels}px²
                  </div>
                </div>
                <div>
                  <span className="text-gray-400">Severity</span>
                  <div className={`font-semibold ${
                    selectedCrop.severity === 'critical' ? 'text-red-400' :
                    selectedCrop.severity === 'moderate' ? 'text-yellow-400' :
                    'text-green-400'
                  }`}>
                    {selectedCrop.severity.toUpperCase()}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Defects;
