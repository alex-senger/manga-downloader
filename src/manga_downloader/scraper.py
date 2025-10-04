"""Scraper for MangaFox (fanfox.net) website."""

import re
from pathlib import Path
from urllib.parse import urlparse

import jsbeautifier
from loguru import logger

import manga_downloader.utils as utils


class MangaScraper:
    """Scraper for MangaFox (fanfox.net) website."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the manga scraper.

        Args:
            verbose: Enable verbose output

        """
        self.verbose = verbose

    def download_manga(
        self,
        url: str,
        download_dir: str | Path,
        chapter_range: str = "All",
        conversion: str = "pdf",
        keep_files: bool = False,
        sorting: str = "desc",
    ) -> None:
        """Download manga from MangaFox.

        Args:
            url: Manga or chapter URL
            download_dir: Directory to save downloads
            chapter_range: Range of chapters to download (e.g., "1-10", "10-All" or "All")
            conversion: Output format ("pdf", or "none")
            keep_files: Whether to keep individual image files after conversion
            sorting: Order to download chapters ("asc" or "desc")

        """
        if re.match(r".*fanfox\.net.*", url) is None:
            logger.error("This scraper only supports fanfox.net URLs.")
            return

        if re.match(r".*/v\d+/c\d+/\d+\.html$", url):
            # https://fanfox.net/manga/slam_dunk/v01/c001/1.html
            manga_name = url.split("/")[4]
            logger.info(f"Detected manga name: {manga_name}")

            self._single_chapter(
                manga_url=url,
                manga_name=manga_name,
                download_directory=download_dir,
                conversion=conversion,
                keep_files=keep_files,
            )
        else:
            # https://fanfox.net/manga/slam_dunk/
            manga_name = re.search(r"/manga/(.*?)/?$", url).group(1)
            self._full_series(
                manga_url=url,
                manga_name=manga_name,
                sorting=sorting,
                download_directory=download_dir,
                chapter_range=chapter_range,
                conversion=conversion,
                keep_files=keep_files,
            )

    def _single_chapter(
        self,
        manga_url: str,
        manga_name: str,
        download_directory: str | Path,
        conversion: str,
        keep_files: bool,
    ) -> None:
        # https://fanfox.net/manga/dagashi_kashi/v08/c141/1.html
        url_split = str(manga_url).split("/")
        current_chapter_volume = url_split[-3].replace("v", "")
        chapter_number = url_split[-2].replace("c", "")
        series_code = url_split[-4]

        source, cookies = utils.download_page(manga_url=manga_url)
        chapter_id = int(
            str(re.search(r"chapterid\s?=\s?(.*?);", str(source)).group(1)).strip()
        )
        current_page_number = int(
            str(re.search(r"imagepage\s?=\s?(.*?);", str(source)).group(1)).strip()
        )
        last_page_number = int(
            str(re.search(r"imagecount\s?=\s?(.*?);", str(source)).group(1)).strip()
        )

        # create dir for series
        series_dir = Path(download_directory) / manga_name
        series_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(
            f"Downloading chapter {chapter_number} of volume {current_chapter_volume} to {series_dir}"
        )

        links = {}
        additional_headers = {"referer": manga_url}

        for page_number in range(current_page_number, last_page_number + 1):
            script_url = f"https://fanfox.net/manga/{series_code}/{current_chapter_volume}/{chapter_number}/chapterfun.ashx?cid={chapter_id}&page={page_number}&key="
            logger.debug(f"Fetching script URL: {script_url}")

            (
                script_source,
                cookies,
            ) = utils.download_page(
                manga_url=script_url,
                cookies=cookies,
                additional_headers=additional_headers,
            )

            if not script_source:
                logger.error(f"Failed to fetch script for {page_number}")
                continue

            beautified_script = jsbeautifier.beautify(script_source.text)
            pix_url = str(
                re.search(r'pix\s+=\s+"(.*?)";', str(beautified_script))
                .group(1)
                .strip()
            )
            p_values = (
                re.search(r"pvalue = \[(.*?)\];", str(beautified_script))
                .group(1)
                .strip()
                .replace('"', "")
                .split(",")
            )

            # Construct final image URL
            if len(p_values) > 0:
                custom_image_filename = (
                    f"{page_number:0{len(str(last_page_number))}d}.jpg"
                )
                image_url = f"https:{pix_url}{p_values[0].strip()}"
                links[custom_image_filename] = image_url
                logger.debug(f"Found link for page {page_number} : {image_url}")

        utils.multithread_download(
            chapter_number=chapter_number,
            manga_name=manga_name,
            manga_url=manga_url,
            directory_path=series_dir.resolve(),
            file_names=list(links.keys()),
            links=list(links.values()),
            additional_headers=additional_headers,
        )
        utils.conversion(
            series_dir.resolve(), conversion, keep_files, manga_name, chapter_number
        )

    def _full_series(
        self,
        manga_url: str,
        manga_name: str,
        sorting: str,
        download_directory: str | Path,
        chapter_range: str,
        conversion: str,
        keep_files: bool,
    ) -> None:
        # http://mangafox.la/rss/gentleman_devil.xml
        rss_url = str(manga_url).replace("/manga/", "/rss/") + ".xml"
        source, _ = utils.download_page(manga_url=rss_url)

        all_links = re.findall(r"/manga/(.*?).html", str(source))
        all_links = [f"https://fanfox.net/manga/{link}.html" for link in all_links]

        logger.debug(f"Found {len(all_links)} chapters in series.")

        if chapter_range != "All":
            starting, ending = re.match(r"(\d+)-(\d+|All)", chapter_range).groups()
            starting = int(starting) - 1
            ending = int(ending) if ending.isdigit() else len(all_links)

            all_links = all_links[::-1][starting:ending][::-1]

        if str(sorting).lower() in ["new", "desc", "descending", "latest"]:
            all_links = list(reversed(all_links))

        for chapter_url in all_links:
            url_split = str(chapter_url).split("/")
            current_chapter_volume = url_split[-3]
            chapter_number = url_split[-2].replace("c", "")

            if not chapter_number.isdigit():
                logger.info(
                    f"Skipping chapter {chapter_number} of volume {current_chapter_volume}"
                )
                continue
            logger.info(
                f"Processing chapter {chapter_number} of volume {current_chapter_volume}"
            )

            self._single_chapter(
                manga_url=chapter_url,
                manga_name=manga_name,
                download_directory=download_directory,
                conversion=conversion,
                keep_files=keep_files,
            )
