# jukebox-tools

A Windows utility for DJs, audiophiles, and music enthusiasts who want consistency in their file formats. I built this to standardize my music library on AIFF — the lossless format that commonly works with professional DJ software and hardware like Serato, Rekordbox, and Pioneer CDJs. Drop files in a folder, right-click them in Explorer, or run a batch pass over your whole library — all metadata, tags, and album art are preserved.

## Why AIFF?

AIFF is my preferred format for DJing (it may not be yours, if you want to fork this to make tweaks, feel free!):

- **Lossless audio** — no quality degradation
- **DJ software compatibility** — natively supported by Serato DJ, Rekordbox, Traktor, and Virtual DJ
- **CDJ compatibility** — Pioneer CDJs read AIFF reliably; compressed formats can cause issues
- **Preserved metadata** — artist, title, album, BPM, key, genre, album art, and all other tags carry over from the source file

## Features

- **Right-click context menu** — transcode files directly from Windows Explorer, works on single files or multi-selections
- **Continuous folder watcher** — monitors a folder in real-time and transcodes new files as they arrive
- **Batch processor** — one-shot processing of an entire folder, suitable for scheduled runs
- **Full metadata preservation** — all ID3/Vorbis tags and album art are copied to the output file
- **Smart skipping** — files already in AIFF at the target sample rate are left untouched
- **Recursive** — processes all subdirectories automatically

## Prerequisites

1. **Python 3.7+** — [Download Python](https://www.python.org/downloads/)
   - During installation, check **"Add Python to PATH"**
2. **FFmpeg** — required for audio conversion
   - Install via winget: `winget install ffmpeg`
   - Or via Chocolatey: `choco install ffmpeg`
   - Or [download manually](https://ffmpeg.org/download.html) and add to PATH
   - Verify: `ffmpeg -version`

## Installation

1. Clone or download this repository
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Choose how you want to use it (see Usage below)

## Configuration

1. Copy the example config file:
   ```
   copy config.json.example config.json
   ```

2. Edit `config.json`:
   ```json
   {
     "watch_folder": "C:/Users/yourname/Music/ToTranscode",
     "ffmpeg_path": null
   }
   ```
   - `watch_folder` — folder to watch or batch-process (use forward slashes or double backslashes)
   - `ffmpeg_path` — full path to `ffmpeg.exe` if it is not in your PATH, otherwise leave as `null`

## Usage

### Option 1: Right-Click Context Menu (Recommended)

Adds a "Transcode to AIFF 48kHz" option to the Windows Explorer right-click menu for all supported audio file types.

**One-time setup (requires Administrator):**

1. Right-click `install_context_menu.bat` → **Run as administrator**
2. Right-click any audio file in Explorer → **Transcode to AIFF 48kHz**

To remove the context menu entry:

1. Right-click `uninstall_context_menu.bat` → **Run as administrator**

**Pros:** Easiest to use, works on individual files or multiple selections
**Cons:** One-time admin setup required

### Option 2: Continuous Folder Watcher

Runs in the background and transcodes files as soon as they appear in the watched folder:

```
python transcoder_watch.py "C:/Users/yourname/Music/ToTranscode"
```

Or using a config file:

```
python transcoder_watch.py --config config.json
```

**Pros:** Files are processed immediately on arrival
**Cons:** Process must stay running

### Option 3: Batch Processing

Processes all audio files in a folder on demand:

```
python transcoder_batch.py "C:/Users/yourname/Music/ToTranscode"
```

Or using a config file:

```
python transcoder_batch.py --config config.json
```

**Pros:** Only runs when needed, no persistent process
**Cons:** New files are not processed until the script is run again

### Custom FFmpeg Path

If FFmpeg is installed somewhere other than your PATH:

```
python transcoder_watch.py "C:/Music/ToTranscode" --ffmpeg "C:/ffmpeg/bin/ffmpeg.exe"
```

### Running as a Background Service (Windows)

**Continuous watcher via Task Scheduler:**

1. Open Task Scheduler → Create Task
2. Trigger: At log on
3. Action: Start a program
   - Program: `pythonw.exe` (runs without a console window)
   - Arguments: `"C:\path\to\transcoder_watch.py" "C:\path\to\watch\folder"`
   - Start in: `C:\path\to\jukebox-tools`

**Batch processor on a schedule via Task Scheduler:**

Same as above but set the trigger to a schedule (e.g. daily, hourly) and use `python.exe` with `transcoder_batch.py`.

## How It Works

1. An audio file is detected (via right-click, folder watcher, or batch scan)
2. If the file is already AIFF at 48 kHz it is skipped
3. FFmpeg converts the audio to AIFF 24-bit PCM at 48 kHz
4. All metadata is copied to the output file:
   - For FLAC files: mutagen reads Vorbis comments and PICTURE blocks and writes them as ID3 tags directly into the AIFF
   - For all other formats: FFmpeg carries metadata through natively
5. The original file is replaced with the transcoded AIFF

## Supported Formats

| Input | Output |
|-------|--------|
| FLAC, MP3, WAV, M4A, AAC, OGG, WMA, AIFF, AIF | AIFF (24-bit PCM, 48 kHz, stereo) |

## Troubleshooting

**FFmpeg not found**
- Verify it is installed and on your PATH: `ffmpeg -version`
- Or specify the path with `--ffmpeg` or in `config.json`

**Metadata or album art missing after conversion**
- Make sure `mutagen` is installed for the same Python that runs the scripts:
  ```
  python -m pip install mutagen
  ```
- If using the context menu, check which Python it points to:
  ```
  reg query "HKEY_CLASSES_ROOT\SystemFileAssociations\.flac\Shell\TranscodeToAIFF\command"
  ```
  Then install mutagen for that specific executable:
  ```
  & "C:\path\to\that\python.exe" -m pip install mutagen
  ```

**Files not being transcoded**
- Check that the file extension is in the supported list
- Check `transcoder.log` for error details

**Permission errors**
- Ensure the script has read/write access to the watch folder
- Check that the file is not open in another application

## Notes

- Original files are replaced in-place by the transcoded AIFF
- Large files may take a moment to convert (10-minute timeout per file)
- The folder watcher waits 1 second after a file appears before processing it, to ensure it is fully written to disk
