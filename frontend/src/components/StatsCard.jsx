import React from 'react';

const StatsCard = ({ title, value, subtext, alert }) => {
  return (
    <div className={`p-6 rounded-xl border border-white/10 backdrop-blur-md bg-white/5 shadow-xl ${alert ? 'border-red-500 bg-red-900/20' : ''}`}>
      <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2">{title}</h3>
      <div className={`text-4xl font-bold ${alert ? 'text-red-400' : 'text-white'}`}>
        {value}
      </div>
      {subtext && (
        <p className="text-gray-500 text-xs mt-2">{subtext}</p>
      )}
    </div>
  );
};

export default StatsCard;
