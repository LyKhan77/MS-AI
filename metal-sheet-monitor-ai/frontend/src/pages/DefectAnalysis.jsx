import React, { useState, useEffect } from 'react';
import api, { defectAPI } from '../services/api';
import { Scan, ChevronRight, Image as ImageIcon, Loader2 } from 'lucide-react';

const DefectAnalysis = () => {
    const [sessions, setSessions] = useState([]);
    const [selectedSession, setSelectedSession] = useState(null);
    const [images, setImages] = useState([]);
    const [selectedImage, setSelectedImage] = useState(null);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [analyzing, setAnalyzing] = useState(false);

    useEffect(() => {
        fetchSessions();
    }, []);

    const fetchSessions = async () => {
        try {
            const res = await api.get('/sessions/list');
            setSessions(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    const handleSelectSession = async (sessionId) => {
        setSelectedSession(sessionId);
        setSelectedImage(null);
        setAnalysisResult(null);
        try {
            const res = await api.get(`/sessions/${sessionId}/images`);
            setImages(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    const handleAnalyze = async () => {
        if (!selectedImage) return;
        setAnalyzing(true);
        try {
            const res = await defectAPI.analyze(selectedImage.path);
            setAnalysisResult(res.data.defects);
        } catch (err) {
            alert("Analysis failed");
        } finally {
            setAnalyzing(false);
        }
    };

    const getImageUrl = (path) => {
        // Convert server path "data/media/..." to url "/media/..."
        return "http://localhost:8000/media/" + path.replace("data/media/", "");
    };

    return (
        <div className="h-full flex text-white">
            {/* Sidebar: Session List */}
            <div className="w-64 bg-dark-surface border-r border-gray-700 p-4">
                <h3 className="font-bold text-gray-400 mb-4 uppercase text-xs">Sessions</h3>
                <div className="space-y-2">
                    {sessions.map(s => (
                        <button 
                            key={s}
                            onClick={() => handleSelectSession(s)}
                            className={`w-full text-left px-3 py-2 rounded text-sm flex items-center justify-between ${selectedSession === s ? 'bg-primary text-white' : 'hover:bg-gray-800 text-gray-300'}`}
                        >
                            <span className="truncate">{s}</span>
                            <ChevronRight size={14} />
                        </button>
                    ))}
                    {sessions.length === 0 && <p className="text-gray-600 text-sm">No sessions found.</p>}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col">
                 {!selectedSession ? (
                     <div className="flex-1 flex items-center justify-center text-gray-500">
                         Select a session to view images
                     </div>
                 ) : (
                     <div className="flex-1 flex overflow-hidden">
                         {/* Image Grid */}
                         <div className="w-1/3 bg-dark-bg p-4 overflow-y-auto border-r border-gray-700">
                             <h3 className="font-bold mb-4">{images.length} Images</h3>
                             <div className="grid grid-cols-2 gap-4">
                                {images.map((img, idx) => (
                                    <div 
                                        key={idx} 
                                        onClick={() => { setSelectedImage(img); setAnalysisResult(null); }}
                                        className={`cursor-pointer rounded overflow-hidden border-2 ${selectedImage?.path === img.path ? 'border-primary' : 'border-transparent hover:border-gray-600'}`}
                                    >
                                        <img src={getImageUrl(img.path)} className="w-full h-24 object-cover" />
                                        <div className="p-2 text-xs truncate bg-gray-800">{img.name}</div>
                                    </div>
                                ))}
                             </div>
                         </div>

                         {/* Detail View */}
                         <div className="flex-1 p-6 bg-gray-900 flex flex-col items-center overflow-y-auto">
                            {selectedImage ? (
                                <div className="space-y-6 w-full max-w-3xl">
                                    <div className="bg-dark-surface p-4 rounded-lg shadow-lg">
                                        <div className="mb-4 flex justify-between items-center">
                                            <h2 className="text-xl font-bold">{selectedImage.name}</h2>
                                            <button 
                                                onClick={handleAnalyze}
                                                disabled={analyzing}
                                                className="bg-primary hover:bg-primary-light text-white px-6 py-2 rounded flex items-center gap-2 disabled:opacity-50"
                                            >
                                                {analyzing ? <Loader2 className="animate-spin" /> : <Scan />}
                                                ANALYZE DEFECTS (SAM 2)
                                            </button>
                                        </div>
                                        <img src={getImageUrl(selectedImage.path)} className="w-full rounded border border-gray-700" />
                                    </div>

                                    {/* Analysis Results */}
                                    {analysisResult && (
                                        <div className="bg-dark-surface p-4 rounded-lg border border-gray-700 animate-in fade-in slide-in-from-bottom-4">
                                            <h3 className="text-lg font-bold mb-4 text-red-400">Analysis Results ({analysisResult.length} Defects)</h3>
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                                {analysisResult.map((defect, i) => (
                                                    <div key={i} className="bg-gray-800 p-2 rounded border border-red-900/50">
                                                        <img src={getImageUrl(defect.crop_path)} className="w-full h-32 object-contain bg-black rounded mb-2" />
                                                        <div className="text-xs text-center font-mono text-red-300">Defect #{defect.id}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-gray-500 flex flex-col items-center mt-20">
                                    <ImageIcon size={48} className="mb-4 opacity-50" />
                                    <p>Select an image to analyze</p>
                                </div>
                            )}
                         </div>
                     </div>
                 )}
            </div>
        </div>
    );
};

export default DefectAnalysis;
