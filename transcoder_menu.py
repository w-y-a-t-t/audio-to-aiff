#!/usr/bin/env python3
"""
Transcode Selected Files
Transcodes selected audio files to AIFF 48kHz from Windows context menu.
"""

import sys
import logging
from pathlib import Path

# Import transcoder from main script
from transcoder_watch import AudioTranscoder, AUDIO_EXTENSIONS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to transcode selected files."""
    if len(sys.argv) < 2:
        logger.error("No files specified. Usage: transcoder_menu.py <file1> [file2] ...")
        sys.exit(1)
    
    # Get file paths from command line arguments
    file_paths = [Path(arg) for arg in sys.argv[1:]]
    
    # Initialize transcoder
    try:
        transcoder = AudioTranscoder()
    except Exception as e:
        logger.error(f"Failed to initialize transcoder: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Process each file
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for file_path in file_paths:
        # Resolve the path
        try:
            file_path = file_path.resolve()
        except Exception as e:
            logger.error(f"Invalid path: {file_path} - {e}")
            error_count += 1
            continue
        
        # Check if file exists
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            error_count += 1
            continue
        
        # Check if it's an audio file
        if file_path.suffix.lower() not in AUDIO_EXTENSIONS:
            logger.warning(f"Skipping non-audio file: {file_path.name}")
            skip_count += 1
            continue
        
        # Check if transcoding is needed
        if not transcoder.needs_transcoding(file_path):
            logger.info(f"Skipping {file_path.name} (already in target format)")
            skip_count += 1
            continue
        
        # Transcode the file
        logger.info(f"Processing: {file_path.name}")
        if transcoder.transcode(file_path):
            success_count += 1
        else:
            error_count += 1
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info(f"Processing complete:")
    logger.info(f"  Successfully transcoded: {success_count}")
    logger.info(f"  Skipped (already correct): {skip_count}")
    logger.info(f"  Errors: {error_count}")
    logger.info(f"{'='*50}")
    
    # Keep window open if there were errors or if run from context menu
    if error_count > 0:
        input("\nPress Enter to exit...")

if __name__ == '__main__':
    main()
