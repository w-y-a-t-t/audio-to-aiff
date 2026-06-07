#!/usr/bin/env python3
"""
Audio File Transcoder
Automatically transcodes audio files to .aiff format at 48 kHz
when files are added to a watched folder.
"""

import sys
import time
import subprocess
import json
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transcoder.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Supported audio extensions
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma', '.aiff', '.aif'}

# Target format
TARGET_EXTENSION = '.aiff'
TARGET_SAMPLE_RATE = 48000


class AudioTranscoder:
    """Handles audio file transcoding using FFmpeg."""
    
    def __init__(self, ffmpeg_path: Optional[str] = None):
        """
        Initialize the transcoder.
        
        Args:
            ffmpeg_path: Optional path to ffmpeg executable. If None, uses 'ffmpeg' from PATH.
        """
        self.ffmpeg_path = ffmpeg_path or 'ffmpeg'
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Verify that FFmpeg is available."""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise RuntimeError("FFmpeg check failed")
            logger.info(f"FFmpeg found: {result.stdout.split()[2]}")
        except (FileNotFoundError, subprocess.TimeoutExpired, RuntimeError) as e:
            logger.error(f"FFmpeg not found or not working. Please install FFmpeg.")
            logger.error(f"Download from: https://ffmpeg.org/download.html")
            raise
    
    def get_audio_info(self, file_path: Path) -> Optional[dict]:
        """
        Get audio file information using FFprobe.
        
        Returns:
            Dictionary with 'format', 'sample_rate', 'codec' or None if error.
        """
        try:
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
            cmd = [
                ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"Could not probe {file_path}: {result.stderr}")
                return None
            
            data = json.loads(result.stdout)
            
            # Find audio stream
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                return None
            
            return {
                'format': data['format'].get('format_name', '').lower(),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'codec': audio_stream.get('codec_name', '').lower(),
                'extension': file_path.suffix.lower()
            }
        except Exception as e:
            logger.error(f"Error probing {file_path}: {e}")
            return None
    
    def needs_transcoding(self, file_path: Path) -> bool:
        """
        Check if file needs transcoding.
        
        Returns:
            True if file needs transcoding, False otherwise.
        """
        if file_path.suffix.lower() not in AUDIO_EXTENSIONS:
            return False
        
        # Check if already .aiff
        if file_path.suffix.lower() == TARGET_EXTENSION:
            info = self.get_audio_info(file_path)
            if info:
                # Check if sample rate is already 48kHz
                if info['sample_rate'] == TARGET_SAMPLE_RATE:
                    logger.info(f"{file_path.name} is already in target format (AIFF 48kHz)")
                    return False
        
        return True
    
    def _copy_flac_metadata(self, input_path: Path, output_path: Path):
        """Copy all metadata (tags + artwork) from a FLAC file into an AIFF using mutagen."""
        try:
            from mutagen.flac import FLAC
            from mutagen.aiff import AIFF
            from mutagen.id3 import (
                TIT2, TPE1, TALB, TDRC, TRCK, TCON, COMM,
                TPE2, TCOM, TPOS, TBPM, APIC
            )

            flac = FLAC(str(input_path))
            aiff = AIFF(str(output_path))
            if aiff.tags is None:
                aiff.add_tags()

            # Vorbis comment key → ID3 frame mapping
            tag_map = {
                'title':       lambda v: TIT2(encoding=3, text=v),
                'artist':      lambda v: TPE1(encoding=3, text=v),
                'album':       lambda v: TALB(encoding=3, text=v),
                'date':        lambda v: TDRC(encoding=3, text=v),
                'tracknumber': lambda v: TRCK(encoding=3, text=v),
                'genre':       lambda v: TCON(encoding=3, text=v),
                'albumartist': lambda v: TPE2(encoding=3, text=v),
                'composer':    lambda v: TCOM(encoding=3, text=v),
                'discnumber':  lambda v: TPOS(encoding=3, text=v),
                'bpm':         lambda v: TBPM(encoding=3, text=v),
            }

            for key, make_tag in tag_map.items():
                values = flac.get(key)
                if values:
                    aiff.tags.add(make_tag(values))

            # Comments need a language field in ID3
            comment_values = flac.get('comment')
            if comment_values:
                aiff.tags.add(COMM(encoding=3, lang='eng', desc='', text=comment_values))

            # Artwork (FLAC stores these as stream-level PICTURE blocks)
            for pic in flac.pictures:
                aiff.tags.add(APIC(
                    encoding=3,
                    mime=pic.mime,
                    type=pic.type,
                    desc=pic.desc,
                    data=pic.data
                ))

            aiff.save()
            logger.info(f"Copied metadata to {output_path.name}")

        except ImportError:
            logger.warning("mutagen not installed - metadata from FLAC will not be preserved. Install with: pip install mutagen")
        except Exception as e:
            logger.warning(f"Could not copy metadata to {output_path.name}: {e}")

    def transcode(self, input_path: Path, output_path: Optional[Path] = None) -> bool:
        """
        Transcode audio file to .aiff at 48 kHz.
        
        Args:
            input_path: Path to input audio file
            output_path: Optional output path. If None, replaces input file.
        
        Returns:
            True if successful, False otherwise.
        """
        if output_path is None:
            # Replace input file
            output_path = input_path.with_suffix(TARGET_EXTENSION)
            temp_output = input_path.with_suffix(TARGET_EXTENSION + '.tmp')
        else:
            temp_output = output_path.with_suffix(output_path.suffix + '.tmp')
        
        is_flac = input_path.suffix.lower() == '.flac'

        try:
            logger.info(f"Transcoding {input_path.name} to AIFF 48kHz...")

            cmd = [
                self.ffmpeg_path,
                '-i', str(input_path),
            ]

            if is_flac:
                # Mutagen will handle all metadata — tell FFmpeg to strip it to avoid conflicts
                cmd += ['-map_metadata', '-1']
            else:
                cmd += ['-map_metadata', '0']

            cmd += [
                '-map', '0:a',           # Audio stream only
                '-f', 'aiff',            # Explicitly specify AIFF format
                '-acodec', 'pcm_s16be',  # 16-bit PCM (AIFF standard)
                '-ar', str(TARGET_SAMPLE_RATE),  # Sample rate
                '-ac', '2',              # Stereo
                '-y',                    # Overwrite output file
                str(temp_output)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Transcoding failed for {input_path.name}: {result.stderr}")
                if temp_output.exists():
                    temp_output.unlink()
                return False
            
            # Move temp file to final location
            if temp_output.exists():
                if output_path.exists() and output_path != input_path:
                    output_path.unlink()
                temp_output.replace(output_path)
                
                # Copy all FLAC metadata (tags + artwork) via mutagen before deleting the original
                if is_flac:
                    self._copy_flac_metadata(input_path, output_path)

                # If replacing input, remove original
                if output_path == input_path.with_suffix(TARGET_EXTENSION) and input_path != output_path:
                    input_path.unlink()

                logger.info(f"Successfully transcoded {input_path.name} -> {output_path.name}")
                return True
            else:
                logger.error(f"Transcoding completed but output file not found: {temp_output}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Transcoding timeout for {input_path.name}")
            if temp_output.exists():
                temp_output.unlink()
            return False
        except Exception as e:
            logger.error(f"Error transcoding {input_path.name}: {e}")
            if temp_output.exists():
                temp_output.unlink()
            return False


def main():
    """Main function to start the file watcher."""
    # Import watchdog only when needed for the file watcher
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        logger.error("watchdog module not installed. Install with: pip install watchdog")
        sys.exit(1)
    
    # Make AudioFileHandler inherit from FileSystemEventHandler
    class AudioFileHandler(FileSystemEventHandler):
        """Handles file system events for audio transcoding."""
        
        def __init__(self, transcoder: AudioTranscoder, watch_path: Path):
            super().__init__()
            self.transcoder = transcoder
            self.watch_path = watch_path
            self.processing = set()  # Track files being processed to avoid duplicates
        
        def on_created(self, event):
            """Handle file creation events."""
            if event.is_directory:
                return
            
            file_path = Path(event.src_path)
            self._process_file(file_path)
        
        def on_moved(self, event):
            """Handle file move/rename events."""
            if event.is_directory:
                return
            
            file_path = Path(event.dest_path)
            self._process_file(file_path)
        
        def _process_file(self, file_path: Path):
            """Process a file for transcoding."""
            # Normalize path
            try:
                file_path = file_path.resolve()
            except (OSError, RuntimeError):
                return
            
            # Check if file is in watched directory
            try:
                if not file_path.is_relative_to(self.watch_path):
                    return
            except ValueError:
                return
            
            # Check if it's an audio file
            if file_path.suffix.lower() not in AUDIO_EXTENSIONS:
                return
            
            # Avoid processing the same file multiple times
            file_id = str(file_path)
            if file_id in self.processing:
                return
            
            # Wait a bit for file to be fully written (especially for large files)
            time.sleep(1)
            
            # Check if file exists and is readable
            if not file_path.exists() or not file_path.is_file():
                return
            
            # Check file size (skip empty files)
            try:
                if file_path.stat().st_size == 0:
                    logger.warning(f"Skipping empty file: {file_path.name}")
                    return
            except OSError:
                return
            
            self.processing.add(file_id)
            
            try:
                # Check if transcoding is needed
                if self.transcoder.needs_transcoding(file_path):
                    # Transcode the file
                    success = self.transcoder.transcode(file_path)
                    if not success:
                        logger.error(f"Failed to transcode {file_path.name}")
                else:
                    logger.debug(f"Skipping {file_path.name} (already in target format)")
            finally:
                self.processing.discard(file_id)
    
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Watch folder and transcode audio files to AIFF 48kHz'
    )
    parser.add_argument(
        'watch_folder',
        type=str,
        nargs='?',
        help='Folder to watch for audio files (default: from config.json)'
    )
    parser.add_argument(
        '--ffmpeg',
        type=str,
        default=None,
        help='Path to ffmpeg executable (default: use from PATH)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.json',
        help='Path to config file (default: config.json)'
    )
    
    args = parser.parse_args()
    
    # Load config if exists
    config = {}
    config_path = Path(args.config)
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded config from {config_path}")
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
    
    # Get watch folder from args or config
    if args.watch_folder:
        watch_folder = args.watch_folder
    elif 'watch_folder' in config:
        watch_folder = config['watch_folder']
    else:
        logger.error("No folder specified. Provide folder as argument or in config.json")
        sys.exit(1)

    watch_path = Path(watch_folder).expanduser().resolve()

    if not watch_path.exists():
        logger.error(f"Watch folder does not exist: {watch_path}")
        sys.exit(1)
    
    if not watch_path.is_dir():
        logger.error(f"Watch path is not a directory: {watch_path}")
        sys.exit(1)
    
    logger.info(f"Watching folder: {watch_path}")
    
    # Initialize transcoder
    try:
        ffmpeg_path = args.ffmpeg or config.get('ffmpeg_path')
        transcoder = AudioTranscoder(ffmpeg_path=ffmpeg_path)
    except Exception as e:
        logger.error(f"Failed to initialize transcoder: {e}")
        sys.exit(1)
    
    # Set up file watcher
    event_handler = AudioFileHandler(transcoder, watch_path)
    observer = Observer()
    observer.schedule(event_handler, str(watch_path), recursive=True)
    
    logger.info("Starting file watcher...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping file watcher...")
        observer.stop()
    
    observer.join()
    logger.info("File watcher stopped")


if __name__ == '__main__':
    main()
