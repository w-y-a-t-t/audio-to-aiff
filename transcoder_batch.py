#!/usr/bin/env python3
"""
Batch Audio File Transcoder
Processes all audio files in a folder (and subdirectories) that need transcoding.
Run this script on a schedule instead of keeping a watcher running continuously.
"""

import os
import sys
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

# Import transcoder from main script
from transcoder_watch import AudioTranscoder, AUDIO_EXTENSIONS

def process_folder(folder_path: Path, transcoder: AudioTranscoder, processed_files: set = None):
    """
    Recursively process all audio files in a folder.
    
    Args:
        folder_path: Folder to process
        transcoder: AudioTranscoder instance
        processed_files: Set to track already processed files (to avoid duplicates)
    """
    if processed_files is None:
        processed_files = set()
    
    logger.info(f"Scanning folder: {folder_path}")
    
    # Get all audio files
    audio_files = []
    for ext in AUDIO_EXTENSIONS:
        audio_files.extend(folder_path.rglob(f'*{ext}'))
        audio_files.extend(folder_path.rglob(f'*{ext.upper()}'))
    
    logger.info(f"Found {len(audio_files)} audio file(s)")
    
    # Process each file
    transcoded_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in audio_files:
        file_id = str(file_path.resolve())
        
        # Skip if already processed
        if file_id in processed_files:
            continue
        
        processed_files.add(file_id)
        
        try:
            # Check if transcoding is needed
            if transcoder.needs_transcoding(file_path):
                logger.info(f"Processing: {file_path.relative_to(folder_path)}")
                if transcoder.transcode(file_path):
                    transcoded_count += 1
                else:
                    error_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            error_count += 1
    
    logger.info(f"Processing complete: {transcoded_count} transcoded, {skipped_count} skipped, {error_count} errors")
    return transcoded_count, skipped_count, error_count


def main():
    """Main function for batch processing."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Batch transcode audio files to AIFF 48kHz'
    )
    parser.add_argument(
        'folder',
        type=str,
        nargs='?',
        help='Folder to process (default: from config.json)'
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
    
    # Get folder from config or args
    if args.folder:
        folder_path = Path(args.folder).expanduser().resolve()
    elif 'watch_folder' in config:
        folder_path = Path(config['watch_folder']).expanduser().resolve()
    else:
        logger.error("No folder specified. Provide folder as argument or in config.json")
        sys.exit(1)
    
    if not folder_path.exists():
        logger.error(f"Folder does not exist: {folder_path}")
        sys.exit(1)
    
    if not folder_path.is_dir():
        logger.error(f"Path is not a directory: {folder_path}")
        sys.exit(1)
    
    logger.info(f"Processing folder: {folder_path}")
    
    # Initialize transcoder
    try:
        ffmpeg_path = args.ffmpeg or config.get('ffmpeg_path')
        transcoder = AudioTranscoder(ffmpeg_path=ffmpeg_path)
    except Exception as e:
        logger.error(f"Failed to initialize transcoder: {e}")
        sys.exit(1)
    
    # Process folder
    process_folder(folder_path, transcoder)
    logger.info("Batch processing complete")


if __name__ == '__main__':
    main()
