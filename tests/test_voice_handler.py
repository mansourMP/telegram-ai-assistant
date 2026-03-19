import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Ensure src is in the import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from mansur_bot import bot

def test_handle_voice_success():
    # Mock Message
    message = MagicMock()
    message.voice.file_id = "test_file_id"
    
    # Mock bot and client
    with patch('mansur_bot.bot.bot') as mock_bot, \
         patch('mansur_bot.bot.client') as mock_client:
        
        mock_bot.get_file.return_value = MagicMock(file_path="mock_path")
        mock_bot.download_file.return_value = b"fake_audio_data"
        
        # Mock transcription response
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="hello world")
        
        # Run handler
        bot.handle_voice(message)
        
        # Verify
        mock_bot.reply_to.assert_called_with(message, "🎙️ hello world")
        assert not os.path.exists("temp_test_file_id.ogg")

def test_handle_voice_failure():
    # Mock Message
    message = MagicMock()
    message.voice.file_id = "test_file_id"
    
    with patch('mansur_bot.bot.bot') as mock_bot, \
         patch('mansur_bot.bot.client') as mock_client:
        
        mock_bot.get_file.return_value = MagicMock(file_path="mock_path")
        mock_bot.download_file.return_value = b"fake_audio_data"
        
        # Simulate Whisper failure
        mock_client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        # Run handler
        bot.handle_voice(message)
        
        # Verify
        mock_bot.reply_to.assert_called_with(message, "Could not transcribe. Please try again.")
        assert not os.path.exists("temp_test_file_id.ogg")
