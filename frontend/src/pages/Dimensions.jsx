import React from 'react';

const Dimensions = () => {
  return (
    <div className="flex items-center justify-center h-full p-4 md:p-8">
      <div className="text-center max-w-md">
        {/* Icon */}
        <div className="text-6xl md:text-8xl mb-6 animate-pulse">📏</div>
        
        {/* Title */}
        <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">
          Dimension Measurement
        </h2>
        
        {/* Subtitle */}
        <p className="text-sm md:text-base text-gray-400 mb-6">
          Measure metal sheet dimensions with precision calibration
        </p>
        
        {/* Feature List */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4 md:p-6 text-left backdrop-blur-sm">
          <h3 className="text-base md:text-lg font-semibold text-white mb-4">
            Coming Soon
          </h3>
          <ul className="space-y-3 text-sm text-gray-400">
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-0.5">✓</span>
              <span>Pixel-to-millimeter calibration</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-0.5">✓</span>
              <span>Width & height measurement</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-0.5">✓</span>
              <span>Area calculation</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-0.5">✓</span>
              <span>Tolerance checking & alerts</span>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-green-400 mt-0.5">✓</span>
              <span>Dimension reports & exports</span>
            </li>
          </ul>
        </div>
        
        {/* Footer */}
        <p className="text-xs text-gray-500 mt-6">
          This feature is currently in development
        </p>
      </div>
    </div>
  );
};

export default Dimensions;
