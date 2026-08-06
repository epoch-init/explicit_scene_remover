This is an excellent addition. Giving the user granular control over *what* constitutes an explicit scene makes the tool infinitely more useful. Some users might want a family-friendly "PG" cut (removing swearing and violence), while others might only want to remove nudity.

To support this, the ML models will return their predictions *with labels* (e.g., NudeNet returns specific labels like `EXPOSED_BREAST_F` or `EXPOSED_GENITALIA_M`, and YAMNet returns classes like `moan` or `breathing`). The backend will then filter these against the user's selected checkboxes.

Here is the updated System Design Document reflecting these changes.

---

# System Design Document: AutoCleanse (Local Movie Sanitizer)

## 1. System Overview
A locally-hosted web application designed to automatically detect and remove explicit video scenes and audio from movies. The system provides an interactive timeline for users to review detected scenes based on their specific label preferences (e.g., nudity vs. makeouts, moaning vs. profanity) before performing a lossless, fast export using FFmpeg. It simultaneously synchronizes external `.srt` subtitle files with the newly cut video.

## 2. Architecture Diagram

```text
+-------------------+       HTTP / WebSockets       +------------------------+
|                   | <---------------------------> |                        |
| React Frontend    |                               | Flask API (Backend)    |
| (UI, Video Player,|       File Path & Config      | (Routing, File Access, |
| Timeline, Sliders,| ----------------------------> |  WebSocket Server)     |
| Label Checkboxes) |                               |                        |
+-------------------+                               +------------------------+
                                                              |   ^
                                                  Queue Job   |   | Job Status / Result
                                                              v   |
                                                    +--------------------+
                                                    | Redis              |
                                                    | (Message Broker)   |
                                                    +--------------------+
                                                              |   ^
                                                  Fetch Job   |   | Update Progress
                                                              v   |
+----------------------------------------------------------------------------------+
| Celery Worker (Background Processing Engine)                                     |
|                                                                                  |
|   +---------------+      +----------------+      +---------------------------+   |
|   | 1. FFmpeg     | ---> | 2. Vision AI   | ---> | 3. Audio AI               |   |
|   | (Extraction)  |      | (Outputs Labels|      | (Outputs Audio/Word       |   |
|   |               |      | & Timestamps)  |      |  Labels & Timestamps)     |   |
|   +---------------+      +----------------+      +---------------------------+   |
|           |                      |                             |                 |
|           v                      v                             v                 |
|   +--------------------------------------------------------------------------+   |
|   | 4. Aggregator (Filters by User-Selected Labels, Applies Threshold/Padding|   |
|   +--------------------------------------------------------------------------+   |
|           |                                                                      |
|           v                                                                      |
|   +--------------------------------------------------------------------------+   |
|   | 5. FFmpeg (Stream Copy Video Cut) & Subtitle Parser (Shift SRT)          |   |
|   +--------------------------------------------------------------------------+   |
+----------------------------------------------------------------------------------+
```

---

## 3. Component Breakdown

### 3.1. Frontend (React)
*   **Local File Browser UI:** A custom file browser component that calls a backend API to list local `.mp4` and `.srt` files (bypassing browser path security constraints).
*   **Settings Panel:**
    *   **Detection Class Filters (Checkboxes):** 
        *   *Video:* Nudity, Makeouts/Kissing, Gore (if supported by model), etc.
        *   *Audio:* Profanity/Cursing, Explicit Sounds (Moaning, Heavy Breathing).
    *   **FPS Slider:** Configurable extraction rate (0.01 fps to 1.0 fps).
    *   **Confidence Threshold Slider:** 0% to 100% (Filters out low-confidence AI predictions).
    *   **Padding Slider:** 0 to 10 seconds (Adds buffer time before and after an explicit scene).
*   **Progress Dashboard:** Connects via WebSockets to display real-time text and a progress bar (e.g., *"Analyzing Audio: 65%"*).
*   **Interactive Preview Player:** A standard HTML5 `<video>` player overlayed with a custom timeline. 
    *   Renders red clickable blocks on the timeline. Hovering over a block displays the detected label (e.g., *"Detected: Moaning (92%)"*).
    *   Allows users to preview the timestamp and click "Keep Scene" (ignore) or "Cut Scene".

### 3.2. Backend (Flask + Redis + Celery)
*   **Flask:** Serves the API, handles WebSocket connections via `Flask-SocketIO`, and manages local file system traversal.
*   **Redis:** Acts as the message broker passing tasks between Flask and Celery.
*   **Celery:** A background task queue that runs the heavy, time-consuming FFmpeg and ML operations without freezing the web server.

### 3.3. Machine Learning Pipeline (Strict 2GB VRAM Strategy)
To adhere to the 2GB NVIDIA VRAM limit, the pipeline operates strictly **sequentially**.
1.  **Load Vision Model (NudeNet/Action Model):** Load into GPU. Process all extracted frames. Generates list of `[timestamp, label, confidence]`.
2.  **Unload Vision Model:** Run `del model` and `torch.cuda.empty_cache()` to clear VRAM.
3.  **Load Audio Models (Whisper Tiny for Words / YAMNet for Sounds):** Load into GPU. Process audio. Generates list of `[timestamp, label, confidence]`.
4.  **Unload Audio Models:** Clear VRAM.

### 3.4. Processing Utilities
*   **Aggregator & Filter Engine:** Before returning cuts to the UI, this Python module cross-references the AI outputs with the user's selected classes. If a scene is tagged `Makeout` but the user only checked `Nudity`, that timestamp is discarded. It then applies the confidence threshold and padding to the remaining valid timestamps.
*   **Subtitle Manager:** A pure Python script using the `pysrt` library. It reads the final cut timestamps, deletes subtitle blocks falling within those times, and subtracts the duration of the cut from all subsequent subtitle blocks.

---

## 4. API Endpoints & Data Models

### REST APIs
| Endpoint | Method | Payload | Description |
| :--- | :--- | :--- | :--- |
| `/api/files/browse` | GET | `?path=C:/Movies` | Returns list of folders and `.mp4`/`.srt` files in the given directory. |
| `/api/analyze` | POST | `{ video_path, srt_path, fps, threshold, padding, target_video_labels: ["nudity"], target_audio_labels: ["profanity", "moaning"] }` | Triggers the Celery analysis task. Returns a `task_id`. |
| `/api/task/<task_id>` | GET | None | Backup polling endpoint for task status/results. |
| `/api/export` | POST | `{ video_path, srt_path, final_cuts: [...] }` | Triggers the final FFmpeg cut and SRT modification. |

### WebSocket Events
| Event Name | Direction | Payload | Description |
| :--- | :--- | :--- | :--- |
| `task_progress` | Backend -> Client | `{ status: "Analyzing Audio", progress: 65 }` | Real-time UI updates. |
| `task_complete` | Backend -> Client | `{ cuts: [ { start: 10, end: 25, label: "Profanity" }, ... ] }` | Sends final JSON of red zones to UI. |

---

## 5. System Data Flow (Step-by-Step)

1.  **Selection:** User selects `movie.mp4` and `movie.srt` via the React local file browser.
2.  **Configuration:** User sets FPS to 0.5, Threshold to 85%, Padding to 2s. **User checks "Nudity" and "Moaning", but unchecks "Profanity" and "Makeouts".** Clicks "Start".
3.  **Initialization:** React sends `POST /api/analyze` with the config payload. Flask pushes job to Redis, returns `task_id`.
4.  **Extraction (Celery):** 
    *   FFmpeg extracts video frames at 0.5 FPS to a `temp/frames/` folder.
    *   FFmpeg extracts audio to `temp/audio.wav`.
5.  **ML Analysis (Celery):**
    *   Vision AI analyzes frames and outputs raw data (e.g., `01:10:05 - Nudity`, `01:15:00 - Makeout`). Unloads from VRAM.
    *   Audio AI analyzes `.wav` and outputs raw data (e.g., `01:10:05 - Moaning`, `01:20:10 - Profanity`). Unloads from VRAM.
6.  **Filtering & Aggregation:** 
    *   Celery checks the user payload. It *discards* the `Makeout` and `Profanity` timestamps. 
    *   It keeps the `Nudity` and `Moaning` timestamps.
    *   It applies the 85% threshold, adds the 2-second padding, and merges overlapping cuts.
7.  **Preview:** WebSockets notify React that processing is done. React fetches the `cuts.json`. The user scrubs through the timeline, reviewing only the nudty/moaning scenes, and removes any false positives.
8.  **Export:** User clicks "Export". React sends the final confirmed array of cuts to `POST /api/export`.
9.  **Splicing & Shifting:**
    *   FFmpeg uses `concat` demuxer or `-ss` / `-to` commands with stream copy (`-c copy`) to join the safe parts of the video into `movie_clean.mp4`.
    *   Python parses `movie.srt`, deletes the cut blocks, shifts remaining blocks, and saves as `movie_clean.srt`.
10. **Cleanup:** Backend deletes the `temp/` folder (frames and wav file).

---

## 6. MVP Constraints & Known Limitations

1.  **Format Restriction:** Only `.mp4` video files will be supported initially for native browser playback during the Preview phase.
2.  **Keyframe Snapping:** Because export uses FFmpeg Stream Copy (`-c copy`) for speed, cuts will snap to the nearest Keyframe (I-Frame). This means a cut might happen 1 to 3 seconds off from the exact AI-detected timestamp. The UI must display a tooltip explaining this.
3.  **Label Availability Dependence:** The available checkboxes in the UI are strictly limited to the classes the chosen ML models were trained on. (e.g., If NudeNet cannot differentiate between a "kiss" and a "hug", "Makeout" filtering may require implementing a secondary action-recognition model in the future).
4.  **Local Environment Only:** The app allows backend APIs to read/write arbitrary paths on the host machine; it must never be exposed to the public internet.