"""CLI interface for manga-downloader."""

import argparse
import sys
from pathlib import Path

from loguru import logger

from manga_downloader import __version__, set_log_level
from manga_downloader.scraper import MangaScraper


def main() -> None:
    """Main entry point for the CLI."""
    parser = init_parser()
    args = parser.parse_args()

    # Set logging level based on verbosity
    set_log_level(args.verbose)

    # Create download directory
    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    try:
        if args.verbose:
            logger.info(f"Manga Downloader v{__version__}")
            logger.info(f"Target URL: {args.url}")
            logger.info(f"Download directory: {download_dir}")
            logger.info(f"Output format: {args.format}")
            logger.info(f"Chapter range: {args.chapters}")
            logger.info(f"Sort order: {args.sort}")
            logger.info(f"Keep images: {args.keep_images}")
            logger.info("-" * 50)

        # Initialize scraper and download
        scraper = MangaScraper(verbose=args.verbose)

        scraper.download_manga(
            url=args.url,
            download_dir=download_dir,
            chapter_range=args.chapters,
            conversion=args.format,
            keep_files=args.keep_images,
            sorting=args.sort,
        )

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Operation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        if args.verbose:
            logger.exception("Full traceback:")
        sys.exit(1)


def init_parser() -> argparse.ArgumentParser:
    """Initialize the argument parser."""
    parser = argparse.ArgumentParser(
        description="Download manga from websites and convert them to PDF/CBZ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download single chapter as PDF
  manga-downloader https://fanfox.net/manga/example/v01/c001/1.html

  # Download entire series as CBZ files
  manga-downloader https://fanfox.net/manga/example/ --format cbz

  # Download specific chapter range
  manga-downloader https://fanfox.net/manga/example/ --chapters 1-10

  # Keep original images after conversion
  manga-downloader https://fanfox.net/manga/example/ --keep-images
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"manga-downloader {__version__}",
    )

    parser.add_argument(
        "url",
        type=str,
        help="URL of the manga website to scrape (single chapter or series)",
    )

    parser.add_argument(
        "-d",
        "--download-dir",
        type=str,
        default="downloads",
        help="Directory to download images to (default: downloads)",
    )

    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["pdf", "cbz", "none"],
        default="pdf",
        help="Output format: pdf, cbz, or none (default: pdf)",
    )

    parser.add_argument(
        "-c",
        "--chapters",
        type=str,
        default="All",
        help="Chapter range to download, e.g., '1-10' or 'All' (default: All)",
    )

    parser.add_argument(
        "-s",
        "--sort",
        type=str,
        choices=["asc", "desc", "ascending", "descending", "old", "new"],
        default="desc",
        help="Download order: asc (oldest first) or desc (newest first) (default: desc)",
    )

    parser.add_argument(
        "--keep-images",
        action="store_true",
        help="Keep downloaded images after creating PDF/CBZ",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    parser.add_argument(
        "--delay",
        type=int,
        default=1,
        help="Delay between requests in seconds (default: 1)",
    )

    return parser


if __name__ == "__main__":
    main()
