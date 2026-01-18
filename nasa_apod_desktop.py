#!/usr/bin/env python3
"""
NASA APOD Desktop Wallpaper Setter for Windows

Downloads the latest Astronomy Picture of the Day from NASA and sets it as the
Windows desktop background with fit style. Runs daily via Windows Task Scheduler.

Usage:
    python nasa_apod_desktop.py [--verbose]

Requirements:
    Python 3.9+
    No external dependencies (uses built-in libraries only)
"""

import logging
import logging.handlers
import sys
import argparse
import urllib.request
import urllib.error
from typing import Optional
from html.parser import HTMLParser
from pathlib import Path
from ctypes import windll
import winreg

NASA_APOD_SITE = 'http://apod.nasa.gov/apod/'
STORAGE_FOLDER = Path.home() / 'AppData' / 'Roaming' / 'NASA-APOD'
WALLPAPER_FILENAME = 'apod.png'

logger = logging.getLogger(__name__)



class APODImageParser(HTMLParser):
    """Parse the APOD page to locate the first image link."""

    def __init__(self):
        super().__init__()
        self.image_url: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag == 'a' and not self.image_url:
            for attr, value in attrs:
                if attr == 'href' and value and 'image' in value:
                    self.image_url = value
                    break


def setup_logging(verbose: bool) -> None:
    """Configure console and rotating file logging."""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    log_folder = STORAGE_FOLDER / 'logs'
    log_folder.mkdir(parents=True, exist_ok=True)
    log_file = log_folder / 'nasa_apod_desktop.log'
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=1048576,
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def download_site(url: str) -> Optional[str]:
    """Return HTML content for the given URL or None on failure."""
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read().decode('utf-8')
    except urllib.error.URLError as exc:
        logger.error("Failed to download %s: %s", url, exc)
    except UnicodeDecodeError as exc:
        logger.error("Failed to decode response from %s: %s", url, exc)
    except OSError as exc:
        logger.error("Unexpected OS error downloading %s: %s", url, exc)
    return None


def extract_image_url(html_content: Optional[str]) -> Optional[str]:
    """Extract the APOD image URL from the page HTML."""
    if not html_content:
        return None

    parser = APODImageParser()
    try:
        parser.feed(html_content)
    except (ValueError, TypeError) as exc:
        logger.error("Error parsing HTML: %s", exc)
        return None

    if parser.image_url:
        if 'http' in parser.image_url:
            return parser.image_url
        return NASA_APOD_SITE + parser.image_url

    logger.warning("No image URL found in APOD HTML")
    return None


def download_image(image_url: str, save_path: str) -> bool:
    """Download the APOD image to the target path."""
    try:
        logger.info("Downloading image from %s", image_url)
        urllib.request.urlretrieve(image_url, save_path)
        logger.info("Image saved to %s", save_path)
        return True
    except urllib.error.URLError as exc:
        logger.error("Failed to download image from %s: %s", image_url, exc)
    except OSError as exc:
        logger.error("File error while saving %s: %s", save_path, exc)
    return False


def set_windows_wallpaper(image_path: str) -> bool:
    """Set the Windows desktop wallpaper to the given file."""
    try:
        logger.info("Setting wallpaper to %s", image_path)

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r'Control Panel\Desktop',
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, 'WallpaperStyle', 0, winreg.REG_SZ, '6')
        winreg.SetValueEx(key, 'TileWallpaper', 0, winreg.REG_SZ, '0')
        winreg.CloseKey(key)

        SPI_SETDESKWALLPAPER = 0x0014
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02

        windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            image_path,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )

        logger.info("Wallpaper set successfully")
        return True
    except OSError as exc:
        logger.error("Failed to set wallpaper %s: %s", image_path, exc)
        return False


def main() -> int:
    """Download today's APOD image and set it as the wallpaper."""
    parser = argparse.ArgumentParser(description='Set Windows desktop to NASA APOD image')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger.info("Starting APOD wallpaper setter")
    
    STORAGE_FOLDER.mkdir(parents=True, exist_ok=True)
    
    html_content = download_site(NASA_APOD_SITE)
    if not html_content:
        logger.error("Could not fetch APOD website")
        return 1
    
    image_url = extract_image_url(html_content)
    if not image_url:
        logger.error("Could not extract image URL from APOD")
        return 1
    
    wallpaper_path = STORAGE_FOLDER / WALLPAPER_FILENAME
    if not download_image(image_url, str(wallpaper_path)):
        return 1
    
    if not set_windows_wallpaper(str(wallpaper_path)):
        return 1
    
    logger.info("APOD wallpaper setter completed successfully")
    return 0


if __name__ == '__main__':
    sys.exit(main())

