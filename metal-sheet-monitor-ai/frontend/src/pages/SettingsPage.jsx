import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { Save } from 'lucide-react';

const SettingsPage = () => {
    const [ratio, setRatio] = useState(1.0);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        api.get('/settings/').then(res => {
            setRatio(res.data.calibration.pixel_to_mm_ratio);
        });
    }, []);

    const handleSave = async () => {
        try {
            await api.post('/settings/calibration', { pixel_to_mm_ratio: parseFloat(ratio) });
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
        } catch (err) {
            alert("Failed to save");
        }
    };

    return (
        <div className="p-8 max-w-2xl mx-auto text-white">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">System Configuration</h2>
            
            <div className="bg-dark-surface p-6 rounded-lg border border-gray-700 space-y-6">
                <div>
                    <h3 className="text-lg font-semibold mb-2">Calibration</h3>
                    <p className="text-gray-400 text-sm mb-4">
                        Set the Pixel-to-Millimeter ratio for dimension measurement.
                        (e.g., 0.5 means 1 pixel = 0.5mm)
                    </p>
                    
                    <div className="flex items-center gap-4">
                        <div className="flex-1">
                            <label className="block text-xs uppercase text-gray-500 font-bold mb-1">Ratio (mm/px)</label>
                            <input 
                                type="number" 
                                step="0.01"
                                value={ratio}
                                onChange={(e) => setRatio(e.target.value)}
                                className="w-full bg-gray-900 border border-gray-600 rounded px-3 py-2 text-white"
                            />
                        </div>
                    </div>
                </div>

                <div className="pt-4 border-t border-gray-700">
                    <button 
                        onClick={handleSave}
                        className="bg-primary hover:bg-primary-light text-white px-6 py-2 rounded flex items-center gap-2 transition-colors"
                    >
                        <Save size={18} /> Save Settings
                    </button>
                    {saved && <span className="text-green-500 text-sm mt-2 block">Settings saved successfully!</span>}
                </div>
            </div>
            
            <div className="mt-8 bg-dark-surface p-6 rounded-lg border border-gray-700 opacity-50">
                 <h3 className="text-lg font-semibold mb-2">Camera Config (Hardware)</h3>
                 <p className="text-gray-400 text-sm">Hardware settings are managed via Jetson ecosystem.</p>
            </div>
        </div>
    );
};

export default SettingsPage;
