# NASA APOD Desktop Wallpaper for Windows

Download the latest NASA Astronomy Picture of the Day and set it as your Windows desktop background daily.

## Overview

This Python script fetches the latest image from NASA's [Astronomy Picture of the Day](http://apod.nasa.gov/apod/) and automatically sets it as your Windows desktop background with center fit (no stretching or resizing).

## Requirements

- **Python 3.9 or later**
- Windows 7, 8, 10, or 11
- No external dependencies (uses only Python standard library)

## Installation

1. Download or clone this repository
2. Verify Python 3.9+ is installed:
   ```bash
   python --version
   ```

## Usage

### Manual Execution

Run the script directly:
```bash
python nasa_apod_desktop.py
```

For detailed logging output:
```bash
python nasa_apod_desktop.py --verbose
```

### Automatic Daily Execution

Set up Windows Task Scheduler to run the script daily:

1. Open **Task Scheduler** (`Win+R` → type `taskschd.msc` → Enter)
2. Click **Create Basic Task** (right sidebar)
3. **Name**: `NASA APOD Daily Wallpaper`
4. **Description**: `Download and set NASA APOD as desktop background`
5. **Trigger**: Choose daily schedule (e.g., 8:00 AM)
6. **Action**: Start a program
   - **Program**: Full path to `python.exe`
     - Example: `C:\Users\YourName\AppData\Local\Programs\Python\Python310\python.exe`
   - **Arguments**: `"C:\path\to\nasa_apod_desktop.py"`
   - (Use quotes around the script path if it contains spaces)
7. Click **Finish**

**To find your Python executable:**
```bash
python -c "import sys; print(sys.executable)"
```

## Configuration

Edit these constants in `nasa_apod_desktop.py` to customize behavior:

| Constant | Default | Purpose |
|----------|---------|---------|
| `NASA_APOD_SITE` | `http://apod.nasa.gov/apod/` | APOD website URL |
| `STORAGE_FOLDER` | `%APPDATA%\NASA-APOD\` | Where images are saved |
| `WALLPAPER_FILENAME` | `apod.png` | Filename for the wallpaper image |

## How It Works

1. Downloads the APOD webpage
2. Extracts the image URL using HTML parsing
3. Downloads the full-resolution image
4. Sets it as Windows desktop background (center fit)
5. Logs all activity to `%APPDATA%\NASA-APOD\logs\nasa_apod_desktop.log`

## Logging

Activity logs are saved to: `%APPDATA%\NASA-APOD\logs\nasa_apod_desktop.log`

- **Default**: Info-level messages printed to console
- **With `--verbose`**: Debug-level details shown and logged

## Storage

Images are stored in: `%APPDATA%\NASA-APOD\`

- Previous day's image is automatically overwritten
- Safe to manually delete the folder and images at any time
- Logs are kept in a `logs` subfolder

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Image not updating | Run manually with `--verbose` to check for errors |
| Wallpaper not setting | Verify write permissions to storage folder |
| Task Scheduler fails | Check Python path is correct and script path is in quotes |
| Network timeout | Ensure internet connection; APOD must be reachable |

## Notes

- Based on the original [nasa-apod-desktop](https://github.com/randomdrake/nasa-apod-desktop) by David Drake
- Completely rewritten for Windows 10/11 with modern Python 3.9+
- No external dependencies required
- Images are downloaded fresh each day; old images are replaced
