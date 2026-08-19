import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import FileBrowser from './components/FileBrowser';
import VideoPlayer from './components/VideoPlayer';

const socket = io('http://localhost:5000');

function App() {
  const [status, setStatus] = useState('Idle');
  const [progress, setProgress] = useState(0);
  const [cuts, setCuts] = useState(null);

  const [selectedVideo, setSelectedVideo] = useState(null);
  const [selectedSubtitle, setSelectedSubtitle] = useState(null);

  // Settings State
  const [fps, setFps] = useState(1.0);
  const [threshold, setThreshold] = useState(0.7);
  const [padding, setPadding] = useState(1.0);
  const [exportMode, setExportMode] = useState('fast');
  
  const [targetLabels, setTargetLabels] = useState({
    'Nudity/NSFW': true,
    'Explicit Sounds': true, 
    'Profanity': true
  });

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

    socket.on('export_complete', (data) => {
      setStatus(`Saved to: ${data.video_path}`);
      setProgress(100);
      alert(`Export Successful!\nSaved to: ${data.video_path}`);
    });

    return () => {
      socket.off('connect');
      socket.off('task_progress');
      socket.off('task_complete');
      socket.off('export_complete');
    };
  }, []);

  const handleLabelToggle = (label) => {
    setTargetLabels(prev => ({ ...prev, [label]: !prev[label] }));
  };

  const startAnalysis = async () => {
    if (!selectedVideo) return alert("Please select a video file first.");
    const labelsToProcess = Object.keys(targetLabels).filter(k => targetLabels[k]);
    if (labelsToProcess.length === 0) return alert("Please select a target label.");

    setStatus('Initializing analysis...');
    setProgress(0);
    setCuts(null);

    await fetch('http://localhost:5000/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_path: selectedVideo,
        srt_path: selectedSubtitle,
        fps: parseFloat(fps),
        threshold: parseFloat(threshold),
        padding: parseFloat(padding),
        target_labels: labelsToProcess
      })
    });
  };

  const handleExport = async (finalCuts) => {
    setStatus('Initializing export...');
    setProgress(0);
    setCuts(null); // Hide player during export

    await fetch('http://localhost:5000/api/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        video_path: selectedVideo,
        srt_path: selectedSubtitle,
        cuts: finalCuts,
        mode: exportMode
      })
    });
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold mb-8 text-center text-blue-400">AutoCleanse Dashboard</h1>

      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* Left Column */}
        <div className="space-y-4">
          <FileBrowser onSelectVideo={setSelectedVideo} onSelectSubtitle={setSelectedSubtitle} />
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700 text-sm space-y-2">
            <div><span className="font-semibold text-gray-400">Video: </span> <span className={selectedVideo ? "text-green-400" : "text-red-400"}>{selectedVideo || "None"}</span></div>
            <div><span className="font-semibold text-gray-400">Subtitle: </span> <span className={selectedSubtitle ? "text-yellow-400" : "text-gray-500"}>{selectedSubtitle || "None"}</span></div>
          </div>
        </div>

        {/* Right Column */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 flex flex-col">
          <h2 className="text-xl font-semibold mb-4 border-b border-gray-700 pb-2">Detection & Export Settings</h2>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Target Labels</label>
              <div className="space-y-2 mb-4">
                {Object.keys(targetLabels).map(label => (
                  <label key={label} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-700 p-1 rounded">
                    <input type="checkbox" checked={targetLabels[label]} onChange={() => handleLabelToggle(label)} className="accent-blue-500 w-4 h-4" />
                    {label}
                  </label>
                ))}
              </div>

              <label className="block text-sm font-medium text-gray-400 mb-2">Export Quality Mode</label>
              <select
                value={exportMode}
                onChange={(e) => setExportMode(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded p-2 text-sm text-gray-300 outline-none focus:border-blue-500"
              >
                <option value="fast">Fast (Keyframe Snap)</option>
                <option value="accurate">Accurate (Re-encode)</option>
              </select>
            </div>

            <div className="space-y-4">
              <div><label className="block text-sm text-gray-400 mb-1">Threshold: {(threshold * 100).toFixed(0)}%</label><input type="range" min="0.1" max="0.99" step="0.01" value={threshold} onChange={(e) => setThreshold(e.target.value)} className="w-full accent-blue-500" /></div>
              <div><label className="block text-sm text-gray-400 mb-1">Padding: {padding}s</label><input type="range" min="0.0" max="5.0" step="0.5" value={padding} onChange={(e) => setPadding(e.target.value)} className="w-full accent-blue-500" /></div>
              <div><label className="block text-sm text-gray-400 mb-1">Extraction FPS: {fps}</label><input type="range" min="0.1" max="2.0" step="0.1" value={fps} onChange={(e) => setFps(e.target.value)} className="w-full accent-blue-500" /></div>
            </div>
          </div>

          <button onClick={startAnalysis} disabled={!selectedVideo} className={`w-full font-bold py-3 px-4 rounded mb-6 transition ${selectedVideo ? 'bg-blue-600 hover:bg-blue-500' : 'bg-gray-600 cursor-not-allowed text-gray-400'}`}>
            Analyze Video
          </button>

          <div className="mt-auto">
            <div className="mb-2 text-sm text-gray-300 flex justify-between">
              <span>{status}</span><span>{progress}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-4">
              <div className="bg-green-500 h-4 rounded-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        </div>
      </div>

      {cuts && (
        <div className="max-w-6xl mx-auto">
          <VideoPlayer
            videoPath={selectedVideo}
            initialCuts={cuts}
            onExport={handleExport}
          />
        </div>
      )}
    </div>
  );
}

export default App;