import React, { useEffect, useState, useRef } from 'react';
import io from 'socket.io-client';

const LiveStream = ({ onCountUpdate }) => {
  const [frame, setFrame] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    // Initialize Socket.IO connection
    // Note: In development with proxy, /socket.io works automatically due to vite.config
    socketRef.current = io('/', { path: '/socket.io' });

    socketRef.current.on('connect', () => {
      console.log('Socket connected');
      setIsConnected(true);
    });

    socketRef.current.on('disconnect', () => {
      console.log('Socket disconnected');
      setIsConnected(false);
    });

    socketRef.current.on('video_frame', (data) => {
      // data contains { image: base64..., count: 123 }
      setFrame(`data:image/jpeg;base64,${data.image}`);
      if (onCountUpdate) {
        onCountUpdate(data.count);
      }
    });

    return () => {
      if (socketRef.current) socketRef.current.disconnect();
    };
  }, [onCountUpdate]);

  return (
    <div className="relative w-full h-full bg-black rounded-lg overflow-hidden border-2 border-primary shadow-lg shadow-blue-900/20">
      {!isConnected && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-500">
          Connecting to Stream...
        </div>
      )}
      {frame && (
        <img 
          src={frame} 
          alt="Live Stream" 
          className="w-full h-full object-contain"
        />
      )}
      <div className="absolute top-2 right-2 px-2 py-1 bg-black/60 text-xs rounded text-green-400">
        {isConnected ? 'LIVE' : 'OFFLINE'}
      </div>
    </div>
  );
};

export default LiveStream;
