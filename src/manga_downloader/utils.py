"""Utility functions for manga downloading and processing."""

import queue
import re
import shutil
import threading
import time
from pathlib import Path

import cloudscraper
import img2pdf
import requests
from bs4 import BeautifulSoup
from loguru import logger
from requests.sessions import RequestsCookieJar
from tqdm import tqdm

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def easy_slug(string: str, repl: str = "-", directory: bool = False) -> str:
    """Clean a string to make it suitable for file/directory names.

    Args:
        string: String to clean
        repl: Replacement character for invalid characters
        directory: Whether this is for a directory name

    Returns:
        Cleaned string

    """
    if directory:
        return re.sub(r"^\.|\.+$", "", easy_slug(string, repl, directory=False))
    return re.sub(r'[\\/:*?"<>|]|\s$', repl, string)


def download_page(
    manga_url: str,
    scrapper_delay: int = 5,
    additional_headers: dict[str, str] | None = None,
    cookies: RequestsCookieJar | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[BeautifulSoup, RequestsCookieJar]:
    """Download a web page and return parsed content with cookies.

    Args:
        manga_url: URL to download
        scrapper_delay: Delay for cloudscraper
        additional_headers: Additional headers to merge with default headers
        cookies: Cookies to include in the request
        headers: Custom headers to use instead of default headers

    Returns:
        Tuple of (BeautifulSoup object, cookies)

    """
    headers = headers or DEFAULT_HEADERS.copy()

    if additional_headers:
        headers = headers | additional_headers

    sess = requests.session()
    sess = cloudscraper.create_scraper(sess, delay=scrapper_delay)

    connection = sess.get(manga_url, headers=headers, cookies=cookies)

    if connection.status_code != 200:
        logger.error(
            f"Failed to download page: {manga_url} with status code {connection.status_code}"
        )
        connection.raise_for_status()

    page_source = BeautifulSoup(connection.text.encode("utf-8"), "html.parser")
    return page_source, sess.cookies


def downloader(
    image_and_name: tuple[str, str],
    referer: str,
    directory_path: str | Path,
    pbar: tqdm | None = None,
    append_headers: dict[str, str] | None = None,
    cookies: RequestsCookieJar | None = None,
) -> bool:
    """Download a single image file.

    Args:
        image_and_name: Tuple of (image_url, filename)
        referer: Referer URL for the request
        directory_path: Directory to save the image
        pbar: Optional tqdm progress bar to update
        append_headers: Additional headers to merge with default headers
        cookies: Cookies to include in the request

    Returns:
        True if download was successful, False otherwise

    """
    image_url, file_name = image_and_name
    file_check_path = Path(directory_path) / file_name

    logger.debug(f"File Check Path: {file_check_path}")
    logger.debug(f"Download File Name: {file_name}")

    # Skip if file already exists
    if file_check_path.exists():
        if pbar:
            pbar.write(f"File exists! Skipping: {file_name}")
        return True

    # Prepare headers
    headers = DEFAULT_HEADERS.copy()
    headers["Referer"] = referer

    # Merge additional headers if provided
    if append_headers:
        headers = headers | append_headers

    try:
        sess = requests.session()
        sess = cloudscraper.create_scraper(sess)

        # Download with retry logic
        max_retries = 3
        for download_attempt in range(max_retries):
            try:
                response = sess.get(
                    image_url,
                    stream=True,
                    headers=headers,
                    cookies=cookies,
                    timeout=30,
                )
                response.raise_for_status()

                # Ensure directory exists
                Path(directory_path).mkdir(parents=True, exist_ok=True)

                # Write file directly to destination
                with Path.open(file_check_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                if pbar:
                    pbar.update()

                return True

            except (
                requests.RequestException,
                cloudscraper.exceptions.CloudflareChallengeError,
            ) as e:
                if download_attempt >= max_retries - 1:
                    if pbar:
                        pbar.write(
                            f"Failed to download {file_name} after {max_retries} attempts: {e}"
                        )
                    logger.error(f"Failed to download {file_name}: {e}")
                    return False
                time.sleep(2**download_attempt)  # Exponential backoff

    except Exception as e:
        if pbar:
            pbar.write(f"Error downloading {file_name}: {e}")
        logger.error(f"Unexpected error downloading {file_name}: {e}")
        return False

    if pbar:
        pbar.update()
    return False


def conversion(
    directory_path: str | Path,
    conversion: str,
    keep_files: bool,
    manga_name: str,
    chapter_number: str,
) -> bool:
    """Convert downloaded images to PDF.

    Args:
        directory_path: Path to directory containing images
        conversion: Conversion format ("pdf" or "none")
        keep_files: Whether to keep original image files
        manga_name: Name of the comic/manga
        chapter_number: Chapter number

    Returns:
        True if conversion was successful, False otherwise

    """
    directory_path = Path(directory_path)
    parent_directory = directory_path.parent
    conversion_lower = conversion.lower().strip()

    try:
        if conversion_lower not in ["pdf", "none", "skip"]:
            logger.warning(f"Unsupported conversion format: {conversion}")
            return False

        if conversion_lower in ["none", "skip"]:
            return True

        if conversion_lower == "pdf":
            # Find all image files and sort them properly
            image_patterns = ["*.jpg", "*.jpeg", "*.png", "*.webp"]
            image_files = []
            for pattern in image_patterns:
                image_files.extend(directory_path.glob(pattern))

            image_files = sorted(image_files, key=lambda x: x.stem)

            if not image_files:
                logger.warning(f"No image files found in {directory_path}")
                return False

            pdf_file_name = (
                parent_directory / f"{easy_slug(manga_name)}_c{chapter_number}.pdf"
            )

            if pdf_file_name.exists():
                logger.info(f"PDF file exists! Skipping: {pdf_file_name}")
                return True

            # Convert to PDF
            with Path(pdf_file_name).open("wb") as f:
                pdf_bytes = img2pdf.convert([str(img) for img in image_files])
                if pdf_bytes is None:
                    error_msg = "img2pdf.convert() returned None"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                f.write(pdf_bytes)

            return True

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        keep_files = True  # Don't delete files if conversion failed
        return False

    finally:
        # Clean up files if requested and conversion was successful
        if not keep_files and conversion_lower != "none":
            try:
                shutil.rmtree(directory_path, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Could not clean up directory {directory_path}: {e}")
                raise e

    return True


def multithread_download(
    chapter_number: str,
    manga_name: str,
    manga_url: str,
    directory_path: str | Path,
    file_names: list[str],
    links: list[str],
    pool_size: int = 4,
    cookies: RequestsCookieJar | None = None,
    additional_headers: dict[str, str] | None = None,
) -> bool:
    """Download multiple images using multithreading.

    Args:
        chapter_number: Chapter number for progress display
        manga_name: Comic name for progress display
        manga_url: Comic URL used as referer
        directory_path: Directory to save images
        file_names: list of filenames
        links: list of image URLs
        pool_size: Number of threads to use
        cookies: Cookies to include in requests
        additional_headers: Additional headers to merge with default headers

    Returns:
        True if all downloads completed successfully, False otherwise

    """
    if not links or not file_names:
        logger.warning("No links or filenames provided for download")
        return False

    if len(links) != len(file_names):
        logger.error("Mismatch between links and filenames count")
        return False

    def worker() -> None:
        """Worker function for downloading images."""
        while True:
            try:
                worker_item = in_queue.get(timeout=1)
                success = downloader(
                    image_and_name=worker_item,
                    referer=manga_url,
                    directory_path=directory_path,
                    pbar=pbar,
                    cookies=cookies,
                    append_headers=additional_headers,
                )
                if not success:
                    err_queue.put(f"Failed to download {worker_item[1]}")
                in_queue.task_done()
            except queue.Empty:
                return
            except Exception as ex:
                err_queue.put(ex)
                in_queue.task_done()

    in_queue = queue.Queue()
    err_queue = queue.Queue()

    # Ensure directory exists
    Path(directory_path).mkdir(parents=True, exist_ok=True)

    # Create progress bar
    pbar = tqdm(
        total=len(links),
        leave=True,
        unit="image(s)",
        position=0,
        desc=f"{manga_name} [{chapter_number}]",
    )

    # Start worker threads
    threads = []
    for _ in range(min(pool_size, len(links))):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)

    # Queue all downloads
    for item in zip(links, file_names, strict=False):
        in_queue.put(item)

    # Wait for all downloads to complete
    in_queue.join()

    # Wait for all threads to finish
    for t in threads:
        t.join(timeout=1)

    pbar.close()

    # Check for errors
    errors = []
    try:
        while True:
            error = err_queue.get_nowait()
            errors.append(str(error))
    except queue.Empty:
        pass

    if errors:
        logger.error(
            f"Download errors for {manga_name} [{chapter_number}]: {'; '.join(errors[:5])}"
        )
        logger.warning(f"Some downloads failed for {manga_name} [{chapter_number}]")
        return False

    logger.success(f"Completed: {manga_name} [{chapter_number}]")
    return True
