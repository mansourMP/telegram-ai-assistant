import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Mock environment variables before importing bot
class TestBotLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Patch env vars for the duration of the module
        cls.patcher = patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123:test", "DEEPSEEK_API_KEY": "sk-test"})
        cls.patcher.start()
        
        # Add src to path
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
        
        # Now import the bot
        global bot
        from mansur_bot import bot

    @classmethod
    def tearDownClass(cls):
        cls.patcher.stop()

    def test_normalize_math_text(self):
        # Test basic replacements
        self.assertEqual(bot.normalize_math_text(r"**bold**"), "bold")
        self.assertEqual(bot.normalize_math_text(r"\pi"), "π")
        self.assertEqual(bot.normalize_math_text(r"\cdot"), "·")
        
        # Test fractions
        self.assertEqual(bot.normalize_math_text(r"\frac{1}{2}"), "(1)/(2)")
        
        # Test exponents
        self.assertEqual(bot.normalize_math_text(r"x^2"), "x²")
        self.assertEqual(bot.normalize_math_text(r"x^{-1}"), "x⁻¹")

    def test_is_mcq_text(self):
        # Test valid MCQ
        self.assertTrue(bot.is_mcq_text("A. Option\nB. Option\nC. Option\nD. Option"))
        # Test invalid MCQ
        self.assertFalse(bot.is_mcq_text("Just some text"))
        
        # Test ambiguous case
        self.assertTrue(bot.is_mcq_text("A) One\nB) Two\nC) Three\nD) Four"))

if __name__ == '__main__':
    unittest.main()
