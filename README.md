# File Size Checker

A professional tool to find large files and folders on your system. Helps you identify what's consuming your disk space.

## Features

- Easy-to-use graphical interface
- Scan any directory on your system
- Customizable size threshold with multiple units (B, KB, MB, GB, TB)
- Real-time progress tracking
- Export results to text file
- Sort results by size (largest first)
- Graceful error handling

## Screenshots

(Screenshots will be added after the application is built)

## Usage

1. Select a directory to scan
2. Set the size threshold (e.g., 1GB)
3. Click "Start Scan"
4. View results and optionally export them

## Requirements

- Python 3.6 or higher
- Required packages: tkinter, tqdm

## Installation

### Option 1: Run from source

1. Install Python 3.6 or higher
2. Install required packages:
   ```
   pip install tqdm
   ```
3. Run the application:
   ```
   python FileSizeCheckerGUI.py
   ```

### Option 2: Create an executable (Windows)

1. Install PyInstaller:
   ```
   pip install pyinstaller
   ```

2. Create the executable:
   ```
   pyinstaller --onefile --windowed --icon=file_icon.ico --name="File Size Checker" FileSizeCheckerGUI.py
   ```

3. Find the executable in the `dist` folder

4. (Optional) Create an icon for your application:
   - Find a suitable icon and save it as `file_icon.ico` in the same directory as the script
   - Or modify the script to use a different icon path

## Creating a Shortcut (Windows)

1. Right-click on the .exe file
2. Select "Create shortcut"
3. Move the shortcut to your desktop or Start menu

## License

This software is provided as-is, free to use and modify.

## Credits

Developed by Rashik 