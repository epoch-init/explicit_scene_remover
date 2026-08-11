import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import FileBrowser from './components/FileBrowser';

const socket = io('http://localhost:5000');

function App() {
  const [status, setStatus] = useState('Idle');
  const [progress, setProgress] = useState(0);
  const [cuts, setCuts] = useState(null);

  const [selectedVideo, setSelectedVideo] = useState(null);
  const [selectedSubtitle, setSelectedSubtitle] = useState(null);
  const [fps, setFps] = useState(1.0);

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
    if (!selectedVideo) {
      alert("Please select a video file first.");
      return;
    }

    setStatus('Initializing task...');
    setProgress(0);
    setCuts(null);

    try {
      const response = await fetch('http://localhost:5000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_path: selectedVideo,
          srt_path: selectedSubtitle,
          fps: parseFloat(fps)
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Failed to start analysis");
      }
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-8 text-center">AutoCleanse Dashboard</h1>

      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">

        {/* Left Column: File Browser */}
        <div className="space-y-4">
          <FileBrowser
            onSelectVideo={setSelectedVideo}
            onSelectSubtitle={setSelectedSubtitle}
          />

          {/* Selection Status */}
          <div className="bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-700 text-sm space-y-2">
            <div>
              <span className="font-semibold text-gray-400">Selected Video: </span>
              <span className={selectedVideo ? "text-green-400" : "text-red-400"}>
                {selectedVideo || "None selected"}
              </span>
            </div>
            <div>
              <span className="font-semibold text-gray-400">Selected Subtitle: </span>
              <span className={selectedSubtitle ? "text-yellow-400" : "text-gray-500"}>
                {selectedSubtitle || "None selected (Optional)"}
              </span>
            </div>
            {selectedSubtitle && (
              <button
                onClick={() => setSelectedSubtitle(null)}
                className="text-xs text-red-400 hover:underline"
              >
                Clear Subtitle
              </button>
            )}
          </div>
        </div>

        {/* Right Column: Settings & Progress */}
        <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700 flex flex-col">
          <h2 className="text-xl font-semibold mb-4">Analysis Settings</h2>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Extraction FPS: {fps}
            </label>
            <input
              type="range"
              min="0.1" max="2.0" step="0.1"
              value={fps}
              onChange={(e) => setFps(e.target.value)}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-xs text-gray-500 mt-1">Lower = Faster analysis, Higher = Better accuracy</p>
          </div>

          <button
            onClick={startAnalysis}
            disabled={!selectedVideo}
            className={`w-full font-bold py-3 px-4 rounded mb-6 transition ${selectedVideo
                ? 'bg-blue-600 hover:bg-blue-500 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
              }`}
          >
            Start Analysis
          </button>

          <div className="mt-auto">
            <div className="mb-2 text-sm text-gray-300 flex justify-between">
              <span>Status: {status}</span>
              <span>{progress}%</span>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-700 rounded-full h-4 mb-4 overflow-hidden">
              <div
                className="bg-green-500 h-4 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>

            {cuts && (
              <div className="mt-4 p-4 bg-gray-900 rounded border border-gray-700">
                <h3 className="font-bold text-green-400 mb-2">Task Complete!</h3>
                <p className="text-xs text-gray-400 mb-2">Check the backend `temp/` folder to see the extracted frames and audio.</p>
                <pre className="text-xs overflow-x-auto text-gray-300">{JSON.stringify(cuts, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;