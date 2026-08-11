import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000');

function App() {
  const [status, setStatus] = useState('Idle');
  const [progress, setProgress] = useState(0);
  const [cuts, setCuts] = useState(null);

  useEffect(() => {
    socket.on('connect', () => console.log('Connected to WebSocket'));

    socket.on('task_progress', (data) => {
      setStatus(data.status);
      setProgress(data.progress);
    });

    socket.on('task_complete', (data) => {
      setStatus(data.status);
      setProgress(data.progress);
      setCuts(data.cuts);
    });

    return () => {
      socket.off('connect');
      socket.off('task_progress');
      socket.off('task_complete');
    };
  }, []);

  const startAnalysis = async () => {
    setStatus('Starting...');
    setProgress(0);
    setCuts(null);
    await fetch('http://localhost:5000/api/analyze', { method: 'POST' });
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-8">AutoCleanse Dashboard</h1>

      <div className="w-full max-w-md bg-gray-800 p-6 rounded-lg shadow-lg">
        <button
          onClick={startAnalysis}
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded mb-6 transition"
        >
          Start Mock Analysis
        </button>

        <div className="mb-2 text-sm text-gray-300">Status: {status}</div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-700 rounded-full h-4 mb-4">
          <div className="bg-green-500 h-4 rounded-full transition-all duration-500" style={{ width: `${progress}%` }}></div>
        </div>

        {cuts && (
          <div className="mt-4 p-4 bg-gray-700 rounded">
            <h3 className="font-bold text-green-400">Analysis Complete! Mock Results:</h3>
            <pre className="text-xs mt-2 overflow-x-auto text-gray-300">{JSON.stringify(cuts, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;