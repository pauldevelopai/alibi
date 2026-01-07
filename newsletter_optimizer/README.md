# Newsletter Optimizer

AI-powered newsletter generation and optimization tool trained on your writing style.

Built for [Develop AI](https://developai.substack.com) by Paul McNally.

## Features

- **📊 Archive & Patterns**: Analyze your past newsletters for patterns
- **💡 Idea Generator**: Generate newsletter ideas from collected AI news
- **📥 Content Inbox**: Collect and organize AI news for inspiration
- **🚀 Generate Newsletter**: Multi-step newsletter generation with your style
- **📚 Library**: Save, version, and manage your newsletters
- **📖 Newsletter Bible**: Your personalized writing guide
- **🎚️ Style Controls**: Adjust 22 metrics like doom level, humor, Africa focus

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up your OpenAI API key
echo "OPENAI_API_KEY=your-key-here" > .env

# Run the app
./start_app.sh

# Or run directly
streamlit run app.py
```

Visit: http://localhost:8501

## Run as Permanent Service (macOS)

To have the app start automatically when you log in:

```bash
./install_service.sh
```

To uninstall the service:

```bash
./uninstall_service.sh
```

## Project Structure

```
newsletter_optimizer/
├── app.py                  # Main Streamlit app
├── newsletter_generator.py # AI generation logic
├── style_analyzer.py       # Newsletter pattern analysis
├── content_inbox.py        # Content collection for ideas
├── newsletter_database.py  # Save/version newsletters
├── learning_system.py      # Learn from your edits
├── data/
│   ├── newsletter_bible.json    # Your writing patterns
│   ├── advanced_metrics.json    # Style metric analysis
│   └── newsletters_raw.jsonl    # Your past newsletters
└── email_automation/
    └── gmail_apps_script.js # Auto-collect newsletters
```

## Setup Your Data

1. **Import your Substack export**:
   ```bash
   python import_substack_export.py /path/to/substack/export
   ```

2. **Analyze your style**:
   ```bash
   python style_analyzer.py
   ```

3. **Analyze advanced metrics**:
   ```bash
   python advanced_metrics.py
   ```

## Environment Variables

Create a `.env` file:

```
OPENAI_API_KEY=sk-...
UNSPLASH_ACCESS_KEY=...  # Optional, for image search
PEXELS_API_KEY=...       # Optional, for image search
```

## License

Private - Paul McNally / Develop AI
