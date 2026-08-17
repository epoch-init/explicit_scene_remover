import { useRef, useState, useEffect } from 'react';
import { Play, Pause, Trash2, CheckCircle2 } from 'lucide-react';

export default function VideoPlayer({ videoPath, initialCuts, onExport }) {
  const videoRef = useRef(null);
  const [cuts, setCuts] = useState(initialCuts);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // Load backend stream URL
  const videoSrc = `http://localhost:5000/api/stream?path=${encodeURIComponent(videoPath)}`;

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const updateTime = () => setCurrentTime(video.currentTime);
    const updateDuration = () => setDuration(video.duration);

    video.addEventListener('timeupdate', updateTime);
    video.addEventListener('loadedmetadata', updateDuration);

    return () => {
      video.removeEventListener('timeupdate', updateTime);
      video.removeEventListener('loadedmetadata', updateDuration);
    };
  }, []);

  const togglePlay = () => {
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  };

  const jumpTo = (time) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  };

  const removeCut = (indexToRemove) => {
    setCuts(cuts.filter((_, i) => i !== indexToRemove));
  };

  // Convert time to HH:MM:SS
  const formatTime = (seconds) => new Date(seconds * 1000).toISOString().slice(11, 19);

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg border border-gray-700 mt-8">
      <h2 className="text-xl font-semibold mb-4 text-green-400">Review Detected Scenes</h2>

      {/* Video Player */}
      <div className="relative bg-black rounded overflow-hidden aspect-video mb-4 flex items-center justify-center">
        <video
          ref={videoRef}
          src={videoSrc}
          className="max-h-full w-full object-contain"
          controls={false}
        />
      </div>

      {/* Controls & Custom Timeline */}
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <button onClick={togglePlay} className="bg-gray-700 p-2 rounded hover:bg-gray-600">
            {isPlaying ? <Pause size={20} /> : <Play size={20} />}
          </button>
          <span className="text-sm font-mono">{formatTime(currentTime)} / {formatTime(duration)}</span>
        </div>

        {/* Timeline Bar */}
        <div className="relative h-6 bg-gray-700 rounded cursor-pointer overflow-hidden"
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const percentage = (e.clientX - rect.left) / rect.width;
            jumpTo(percentage * duration);
          }}>

          {/* Progress Indicator */}
          <div
            className="absolute top-0 bottom-0 bg-blue-500 opacity-50 pointer-events-none"
            style={{ width: `${(currentTime / duration) * 100}%` }}
          />

          {/* Red Cut Zones */}
          {duration > 0 && cuts.map((cut, idx) => {
            const leftPct = (cut.start / duration) * 100;
            const widthPct = ((cut.end - cut.start) / duration) * 100;
            return (
              <div
                key={idx}
                className="absolute top-0 bottom-0 bg-red-500 opacity-70 hover:opacity-100 transition-opacity border-x border-red-700"
                style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
                title={`Detected: ${cut.label}`}
                onClick={(e) => {
                  e.stopPropagation();
                  jumpTo(cut.start);
                }}
              />
            );
          })}
        </div>
      </div>

      {/* Cut List Review */}
      <div className="mt-6 space-y-2 max-h-48 overflow-y-auto custom-scrollbar pr-2">
        {cuts.length === 0 ? (
          <p className="text-gray-400 text-sm">No scenes to cut! Video is clean.</p>
        ) : (
          cuts.map((cut, idx) => (
            <div key={idx} className="flex items-center justify-between bg-gray-900 p-3 rounded text-sm">
              <div>
                <span className="text-red-400 font-bold mr-2">[{formatTime(cut.start)} - {formatTime(cut.end)}]</span>
                <span className="text-gray-300">Label: {cut.label}</span>
              </div>
              <div className="flex gap-2">
                <button onClick={() => jumpTo(cut.start)} className="text-blue-400 hover:underline px-2">Play</button>
                <button onClick={() => removeCut(idx)} className="flex items-center gap-1 text-green-400 hover:bg-gray-800 p-1 rounded" title="Keep this scene (Ignore detection)">
                  <CheckCircle2 size={16} /> Keep
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="mt-6 border-t border-gray-700 pt-6 flex justify-end">
        <button
          onClick={() => onExport(cuts)}
          className="bg-green-600 hover:bg-green-500 text-white font-bold py-3 px-6 rounded shadow-lg transition"
        >
          Export Cleaned Video ({cuts.length} cuts)
        </button>
      </div>
    </div>
  );
}