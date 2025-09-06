# WoT AI Assistant (Lite)

This repository contains tools for capturing your World of Tanks gameplay and training a self‑supervised model (RotNet) on your footage.

## Features

* **Window capture**: record the game window directly in windowed (borderless) mode on Windows.
* **Flexible matching**: match the window by process name, PID or window title.
* **Session recording**: save MP4 video and/or individual frames with metadata for each recording session.
* **Self‑supervised training**: train a RotNet model on your recorded frames to learn robust visual features for downstream tasks.

## Quick start

### Installation

```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Recording gameplay

Use `record.py` to capture your gameplay. The following example matches the game window by process name and records both video and frames:

```bash
python record.py --source window --match-by process_name --process-name WorldOfTanks.exe --video --frames --fps 30 --frame-step 15 --preview
```

Options:

- `--match-by process_name --process-name WorldOfTanks.exe` matches the World of Tanks process.
- `--match-by pid --pid 9404` matches a specific PID (useful when multiple clients are running).
- `--match-by title --window-title "WoT Client"` matches by window title.
- `--video` saves an MP4 file under the session directory.
- `--frames` saves individual JPEG frames every `--frame-step` frames.
- `--preview` shows a live preview window; press **Q** or **Esc** to stop recording.

Sessions are saved under `data/sessions/` with a timestamped folder containing a `video/capture.mp4` file, a `frames` directory, and a `meta.json` describing the session parameters.

Ensure your game is running in **Windowed (Borderless)** mode and that the window remains visible during recording.

### Training a RotNet model

After recording gameplay, you can train a RotNet model on your frames to learn a useful feature representation without any manual labels:

```bash
python train_rotnet.py --data data/sessions/session_YYYYMMDD_HHMMSS/frames --epochs 5 --batch-size 64
```

This will save a model checkpoint to `models/rotnet_resnet18.pth`. You can later use this encoder for downstream tasks such as event detection, minimap classification or clustering.

## Notes

* This lite version focuses on data collection and self‑supervised learning. It does not include in‑game overlays or tactical advice.
* On Windows, you may need to install the CPU-only versions of PyTorch:
  ```bash
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
  ```
* The `record.py` script relies on `pywin32` and `psutil` for window management.
* Always ensure the game window is not minimized; otherwise no frames will be captured.
