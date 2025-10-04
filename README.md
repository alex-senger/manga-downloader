# 📚 Manga Downloader

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A powerful and efficient CLI tool to download manga from MangaFox/FanFox websites and convert them to PDF format. Built with Python 3.12+ and featuring multithreaded downloads, automatic retry logic, and comprehensive logging.

## 🚀 Installation

### Using uv
```bash
git clone https://github.com/alex-senger/manga-downloader.git
cd manga-downloader
uv sync
```

## 📖 Usage

### Basic Usage

Download a single chapter:
```bash
manga-downloader https://fanfox.net/manga/slam_dunk/v01/c001/1.html
```

Download an entire series:
```bash
manga-downloader https://fanfox.net/manga/slam_dunk/
```

### Advanced Usage

Download specific chapter range:
```bash
manga-downloader https://fanfox.net/manga/slam_dunk/ --chapters 1-10
```

Download with custom directory and keep images:
```bash
manga-downloader https://fanfox.net/manga/slam_dunk/ \
  --download-dir ./my-manga \
  --keep-images \
  --verbose
```

Download in ascending order (oldest first):
```bash
manga-downloader https://fanfox.net/manga/slam_dunk/ --sort asc
```

## 🔧 Configuration

### Logging

Logs are automatically saved to `manga_downloader.log` with:
- 📁 **Rotation**: 10MB file size limit
- 🕐 **Retention**: 7 days
- 📊 **Levels**: DEBUG (file) and INFO (console)

## 🏗️ Development

### Setup Development Environment

```bash
git clone https://github.com/alex-senger/manga-downloader.git
cd manga-downloader
uv sync --dev
```

### Code Quality

This project uses:
- **Ruff**: For linting and formatting
- **Pyright**: For type checking  
- **Pytest**: For testing

Run quality checks:
```bash
uv run ruff check
uv run pyright
uv run pytest
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Requirements

- Python 3.12+
- Dependencies automatically installed via `uv`

## ⚠️ Disclaimer

This tool is for educational and personal use only. Please respect the terms of service of the websites you scrape and consider supporting manga creators by purchasing official releases.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/alex-senger/manga-downloader/issues) page
2. Create a new issue with detailed information
3. Include the log file (`manga_downloader.log`) if applicable

## 📊 Supported Sites

Currently supported:
- ✅ **MangaFox/FanFox** (fanfox.net)

---

Made with ❤️ by [Alex Senger](https://github.com/alex-senger)
