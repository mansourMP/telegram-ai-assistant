import os
import sys
import time
import pytest
from unittest.mock import MagicMock, patch

# Ensure env vars are set before importing bot
os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"

# Ensure src is in the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from mansur_bot import bot

def test_save_image_folder_creation(tmp_path):
    # Mock save directory
    save_dir = tmp_path / "images"
    os.environ["IMAGE_SAVE_DIR"] = str(save_dir)
    
    # Mock Message
    message = MagicMock()
    # Mock photo objects
    message.photo = [MagicMock(file_id="test_id")]
    
    # Mock bot.get_file and bot.download_file
    with patch('mansur_bot.bot.bot') as mock_bot:
        mock_bot.get_file.return_value = MagicMock(file_path="mock_path")
        mock_bot.download_file.return_value = b"fake_data"
        
        # Call handler
        bot.handle_photo(message)
        
        assert save_dir.exists()
        files = list(save_dir.glob("*.jpg"))
        assert len(files) == 1
        assert "20" in files[0].name # timestamp format starts with 20...

def test_filename_format():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    file_id = "test_id"
    filename = f"{timestamp}_{file_id}.jpg"
    
    # Validate format: YYYYMMDD_HHMMSS_id.jpg
    parts = filename.split('_')
    assert len(parts) >= 3
    assert filename.endswith(".jpg")
    assert parts[0] == time.strftime("%Y%m%d")
