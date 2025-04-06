import os
import re
import time
from tqdm import tqdm

def get_size(start_path='.', size_threshold=5 * 1024 ** 3):
    total_size = 0
    folder_sizes = {}
    file_sizes = {}
    file_count = 0
    folder_count = 0
    large_folders = []
    large_files = []
    error_paths = []

    # Count files and folders first to initialize progress bar
    print("Counting files and folders for progress estimation...")
    try:
        for dirpath, dirnames, filenames in os.walk(start_path):
            folder_count += 1
            file_count += len(filenames)
    except PermissionError:
        print(f"Permission denied when accessing some directories. Results may be incomplete.")
    
    print(f"Found {folder_count} folders and {file_count} files to scan.")
    
    # Now scan with progress bar
    with tqdm(total=folder_count + file_count, desc="Scanning", unit="item") as pbar:
        for dirpath, dirnames, filenames in os.walk(start_path):
            folder_size = 0

            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    if os.path.isfile(fp):
                        file_size = os.path.getsize(fp)
                        total_size += file_size
                        folder_size += file_size

                        file_sizes[fp] = file_size

                        if file_size > size_threshold:
                            large_files.append((fp, file_size))
                except (PermissionError, OSError) as e:
                    error_paths.append((fp, str(e)))
                finally:
                    pbar.update(1)

            folder_sizes[dirpath] = folder_size

            if folder_size > size_threshold:
                large_folders.append((dirpath, folder_size))

            pbar.update(1)

    return total_size, folder_count, file_count, folder_sizes, large_folders, large_files, error_paths

def format_size(size_bytes):
    """Format the size in bytes to a human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0 or unit == 'TB':
            break
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} {unit}"

def display_results(start_path='.', size_threshold=5 * 1024 ** 3, export_to_file=False):
    start_time = time.time()
    total_size, folder_count, file_count, folder_sizes, large_folders, large_files, error_paths = get_size(start_path, size_threshold)
    scan_time = time.time() - start_time

    # Sort large folders by size (largest first)
    large_folders.sort(key=lambda x: x[1], reverse=True)
    
    # Sort large files by size (largest first)
    large_files.sort(key=lambda x: x[1], reverse=True)

    # Prepare results
    results = []
    results.append(f"\nScan completed in {scan_time:.2f} seconds")
    results.append(f"Total storage scanned: {format_size(total_size)}")
    results.append(f"Total Folders: {folder_count}")
    results.append(f"Total Files: {file_count}")
    
    results.append(f"\nListing Folders over {format_size(size_threshold)}:")
    if large_folders:
        for folder, size in large_folders:
            results.append(f" - {folder}: {format_size(size)}")
    else:
        results.append(f" - No folders over {format_size(size_threshold)}")

    results.append(f"\nListing Files over {format_size(size_threshold)}:")
    if large_files:
        for file, size in large_files:
            results.append(f" - {file}: {format_size(size)}")
    else:
        results.append(f" - No files over {format_size(size_threshold)}")
        
    if error_paths:
        results.append("\nErrors encountered during scan:")
        for path, error in error_paths[:10]:  # Show only first 10 errors
            results.append(f" - {path}: {error}")
        if len(error_paths) > 10:
            results.append(f" - ... and {len(error_paths) - 10} more errors")

    # Display results
    for line in results:
        print(line)
        
    # Export results if requested
    if export_to_file:
        export_path = f"file_size_results_{time.strftime('%Y%m%d-%H%M%S')}.txt"
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(f"File Size Check Results - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Directory: {os.path.abspath(start_path)}\n")
                f.write(f"Size threshold: {format_size(size_threshold)}\n\n")
                for line in results:
                    f.write(line + "\n")
            print(f"\nResults exported to {export_path}")
        except Exception as e:
            print(f"\nFailed to export results: {e}")

if __name__ == "__main__":
    print("File Size Checker by Rashik- Find large files and folders")
    print("================================================")
    print("Choose the directory to scan:")
    print("1. Current directory")
    print("2. Different directory")

    while True:
        choice = input("\nEnter your choice (1 or 2): ")

        if choice == '1':
            current_directory = os.getcwd()
            break
        elif choice == '2':
            current_directory = input("Enter the directory location: ")

            if not os.path.isdir(current_directory):
                print("Invalid directory. Please enter a valid path.")
                continue
            break
        else:
            print("Invalid choice. Please enter 1 or 2.")

    print(f"Current Working Directory: {current_directory}")

    while True:
        try:
            size_input = input("\nSize of Files to scan (e.g., 5GB, 500MB, 10TB, 1024B): ")
            
            # Parse the input to extract number and unit
            match = re.match(r"^(\d+\.?\d*)([KMGT]?B)$", size_input.strip().upper())
            if not match:
                print("Invalid input format. Example formats: 5GB, 500MB, 10TB, 1024B")
                continue
                
            value, unit = match.groups()
            value = float(value)
            
            # Convert to bytes based on unit
            unit_multipliers = {
                "B": 1,
                "KB": 1024,
                "MB": 1024 ** 2,
                "GB": 1024 ** 3,
                "TB": 1024 ** 4
            }
            
            # Handle both KB and K, MB and M, etc.
            if unit == "B":
                multiplier = unit_multipliers["B"]
            else:
                # Get the full unit name (e.g., "GB" from "G")
                full_unit = unit if unit in unit_multipliers else unit[0] + "B"
                multiplier = unit_multipliers.get(full_unit)
                
            if not multiplier:
                print("Invalid unit. Please use B, KB, MB, GB, or TB.")
                continue
                
            # Ask if user wants to export results
            export_choice = input("Export results to a text file? (y/n): ").lower()
            export_to_file = export_choice.startswith('y')
                
            size_threshold = value * multiplier
            display_results(current_directory, size_threshold, export_to_file)
            break
        except ValueError as e:
            print(f"Error parsing input: {e}")
            print("Please enter a valid number with a unit (e.g., 5GB, 500MB).")
        except KeyboardInterrupt:
            print("\nScan cancelled.")
            exit(0)

