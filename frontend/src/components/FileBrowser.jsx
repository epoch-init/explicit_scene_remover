import { useState, useEffect } from 'react';
import { Folder, FileVideo, FileText, CornerLeftUp } from 'lucide-react';

export default function FileBrowser({ onSelectVideo, onSelectSubtitle }) {
  const [currentPath, setCurrentPath] = useState('/');
  const [parentPath, setParentPath] = useState('/');
  const [directories, setDirectories] = useState([]);
  const [files, setFiles] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchDirectory = async (path) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:5000/api/files/browse?path=${encodeURIComponent(path)}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch directory');
      }

      setCurrentPath(data.current_path);
      setParentPath(data.parent_path);
      setDirectories(data.directories);
      setFiles(data.files);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDirectory(currentPath);
  }, []);

  const handleFileClick = (file) => {
    // Treat both mp4 and avi as valid video selections
    if (file.extension === '.mp4' || file.extension === '.avi') {
      onSelectVideo(file.path);
    } else if (file.extension === '.srt') {
      onSelectSubtitle(file.path);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 shadow-lg border border-gray-700 h-96 flex flex-col">
      <h2 className="text-lg font-semibold text-gray-200 mb-2">Local File Browser</h2>

      <div className="flex items-center gap-2 mb-4 bg-gray-900 p-2 rounded text-sm text-gray-300 overflow-x-hidden">
        <span className="truncate flex-1">{currentPath}</span>
      </div>

      {error && <div className="text-red-400 text-sm mb-2">{error}</div>}

      <div className="flex-1 overflow-y-auto space-y-1 pr-2 custom-scrollbar">
        {loading ? (
          <div className="text-gray-400 text-sm p-2">Loading...</div>
        ) : (
          <>
            {currentPath !== parentPath && (
              <button
                onClick={() => fetchDirectory(parentPath)}
                className="w-full flex items-center gap-2 p-2 hover:bg-gray-700 rounded text-gray-400 hover:text-gray-200 transition text-sm text-left"
              >
                <CornerLeftUp size={16} />
                <span>.. (Go Up)</span>
              </button>
            )}

            {directories.map((dir) => (
              <button
                key={dir.path}
                onClick={() => fetchDirectory(dir.path)}
                className="w-full flex items-center gap-2 p-2 hover:bg-gray-700 rounded text-blue-400 transition text-sm text-left"
              >
                <Folder size={16} className="shrink-0" />
                <span className="truncate">{dir.name}</span>
              </button>
            ))}

            {files.map((file) => (
              <button
                key={file.path}
                onClick={() => handleFileClick(file)}
                className="w-full flex items-center gap-2 p-2 hover:bg-gray-700 rounded text-gray-300 transition text-sm text-left group"
              >
                {/* Apply the video icon to both MP4 and AVI files */}
                {file.extension === '.mp4' || file.extension === '.avi' ? (
                  <FileVideo size={16} className="text-green-400 shrink-0" />
                ) : (
                  <FileText size={16} className="text-yellow-400 shrink-0" />
                )}
                <span className="truncate flex-1">{file.name}</span>
                <span className="opacity-0 group-hover:opacity-100 text-xs bg-gray-900 px-2 py-1 rounded text-gray-400">
                  Select
                </span>
              </button>
            ))}
          </>
        )}
      </div>
    </div>
  );
}