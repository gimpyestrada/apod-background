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

import json
import logging
import logging.handlers
import ssl
import sys
import argparse
import urllib.request
import urllib.error
from typing import Optional
from pathlib import Path
from ctypes import windll, WinError
import winreg

NASA_APOD_API = 'https://science.nasa.gov/wp-json/wp/v2/apod-basic?per_page=1'
STORAGE_FOLDER = Path(__file__).resolve().parent / 'NASA-APOD'
WALLPAPER_FILENAME = 'apod.png'

logger = logging.getLogger(__name__)


def install_https_opener() -> None:
    """Use certifi's CA bundle for HTTPS requests when available.

    Falls back to the system default trust store otherwise. This guards
    against Windows machines whose OS certificate store hasn't yet picked
    up a newly rotated CA chain on the NASA site.
    """
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return

    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
    urllib.request.install_opener(opener)


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
    """Return text content for the given URL or None on failure."""
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


def get_latest_apod(api_content: Optional[str]) -> Optional[dict]:
    """Parse the APOD Basic JSON API response and return the latest entry."""
    if not api_content:
        return None

    try:
        entries = json.loads(api_content)
    except json.JSONDecodeError as exc:
        logger.error("Error parsing APOD API response: %s", exc)
        return None

    if not entries:
        logger.warning("APOD API returned no entries")
        return None

    return entries[0]


def extract_image_url(apod: Optional[dict]) -> Optional[str]:
    """Extract the full-size image URL from an APOD Basic JSON entry."""
    if not apod:
        return None

    if apod.get('media_type') != 'image':
        logger.warning("Latest APOD is not an image (media_type=%s); skipping", apod.get('media_type'))
        return None

    image_url = apod.get('hdurl')
    if not image_url:
        logger.warning("No hdurl found in APOD entry")
        return None

    return image_url


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

        result = windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            image_path,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        if not result:
            raise WinError()

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

    install_https_opener()
    STORAGE_FOLDER.mkdir(parents=True, exist_ok=True)
    
    api_content = download_site(NASA_APOD_API)
    if not api_content:
        logger.error("Could not fetch APOD API")
        return 1

    apod = get_latest_apod(api_content)
    if not apod:
        logger.error("Could not retrieve latest APOD entry")
        return 1

    logger.info("Latest APOD: %s (%s)", apod.get('title'), apod.get('date'))

    image_url = extract_image_url(apod)
    if not image_url:
        logger.error("Could not extract image URL from APOD entry")
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

