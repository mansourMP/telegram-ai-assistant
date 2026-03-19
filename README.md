# Mansur Bot 🤖

A Telegram-based study assistant for quiz delivery, math normalization, and AI-powered explanations.

## Features

- **Quiz Mode**: Interactive multiple-choice questions from Markdown files.
- **Study Mode**: Delivers study notes and flashcards.
- **Math Support**: Normalizes LaTeX and mathematical notation for clean Telegram display.
- **AI Chat**: Optional integration with DeepSeek (or OpenAI compatible) API for explaining answers.
- **OCR Support**: Extracts text from images using Tesseract (optional).
- **PDF Generation**: Tools to export quizzes to PDF.

## Project Structure

```
├── src/mansur_bot/       # Core bot logic
├── scripts/              # Helper scripts (PDF gen, stats)
├── examples/content/     # Sample quiz content
├── tests/                # Unit tests
└── requirements.txt      # Dependencies
```

## Getting Started

### Prerequisites

- Python 3.9+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (optional, for image text extraction)

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/mansur-bot.git
    cd mansur-bot
    ```

2.  Create a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Configure environment:
    Copy `.env.example` to `.env` and fill in your credentials.
    ```bash
    cp .env.example .env
    ```

### Configuration (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram Bot Token (from @BotFather) | Yes |
| `DEEPSEEK_API_KEY` | API Key for AI explanations (DeepSeek/OpenAI) | No |
| `UNIVERSITY_DIR` | Path to your custom content folder (defaults to `examples/content`) | No |

### Usage

Run the bot:

```bash
python3 src/mansur_bot/bot.py
```

Or install as a package and run:

```bash
pip install -e .
mansur-bot
```

### Adding Content

Place Markdown files in your content directory (e.g., `University/Subject/Questions.md`).
The bot expects a specific format:

```markdown
## Assignment 1

### Question 1
**Question text...**
A. Option 1
B. Option 2...

**Correct Answer:** A
```

See `examples/content` for more details.

## Development

Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
python3 tests/test_bot_logic.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)
