import React, { useEffect, useState, useRef } from 'react';
import io from 'socket.io-client';

const LiveStream = ({ onCountUpdate, forceClear }) => {
  const [frame, setFrame] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(null);
  const onCountUpdateRef = useRef(onCountUpdate);

  // Keep ref updated without causing reconnection
  useEffect(() => {
    onCountUpdateRef.current = onCountUpdate;
  }, [onCountUpdate]);

  // Handle force clear prop
  useEffect(() => {
    if (forceClear) {
      setFrame(null);
    }
  }, [forceClear]);

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
      if (onCountUpdateRef.current) {
        onCountUpdateRef.current(data.count);
      }
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, []); // Empty dependency array - only connect once

  return (
    <div className="relative w-full h-full bg-black rounded-lg overflow-hidden border-2 border-primary shadow-lg shadow-blue-900/20">
      {!frame && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mb-3 opacity-50">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
          </svg>
          <span className="text-sm">No input source loaded</span>
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
