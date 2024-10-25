import os
from tqdm import tqdm

def get_size(start_path='.', size_threshold=5 * 1024 ** 3):
    total_size = 0
    folder_sizes = {}
    file_sizes = {}
    file_count = 0
    folder_count = 0
    large_folders = []
    large_files = []

    
    for dirpath, dirnames, filenames in os.walk(start_path):
        folder_count += 1
        file_count += len(filenames)

    
    with tqdm(total=folder_count + file_count, desc="Scanning", unit="item") as pbar:
        for dirpath, dirnames, filenames in os.walk(start_path):
            folder_size = 0

            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    file_size = os.path.getsize(fp)
                    total_size += file_size
                    folder_size += file_size
                    
                    
                    file_sizes[fp] = file_size
                    
                    if file_size > size_threshold:  
                        large_files.append(fp)

                    pbar.update(1)  

            folder_sizes[dirpath] = folder_size
            
            if folder_size > size_threshold:  
                large_folders.append((dirpath, folder_size))

            pbar.update(1)  

    return total_size, folder_count, file_count, folder_sizes, large_folders, large_files

def display_results(start_path='.', size_threshold=5 * 1024 ** 3):
    total_size, folder_count, file_count, folder_sizes, large_folders, large_files = get_size(start_path, size_threshold)

    total_folders_size = sum(folder_sizes.values())
    total_files_size = total_size - total_folders_size

    print(f"\nTotal storage of the PWD: {total_size / (1024 ** 3):.2f} GB")
    print(f"Total Folders: {folder_count}")
    print(f"Total Files: {file_count}")
    print(f"Storage consumed by all Folders: {total_folders_size / (1024 ** 3):.2f} GB")
    print(f"Storage consumed by all Files: {total_files_size / (1024 ** 3):.2f} GB")
    
    print(f"\nListing Folders over {size_threshold / (1024 ** 3):.2f} GB:")
    for folder, size in large_folders:
        print(f" - {folder}: {size / (1024 ** 3):.2f} GB")
    
    print(f"\nListing Files over {size_threshold / (1024 ** 3):.2f} GB:")
    if large_files:
        for file in large_files:
            print(f" - {file}")
    else:
        print(f" - No files over {size_threshold / (1024 ** 3):.2f} GB")

if __name__ == "__main__":
    print("Choose the directory to scan:")
    print("For Same directory: 1")
    print("For Different Directory: 2")
    
    choice = input("Enter your choice (1 or 2): ")
    
    if choice == '1':
        current_directory = os.getcwd()
    elif choice == '2':
        current_directory = input("Enter the directory location: ")
        
        if not os.path.isdir(current_directory):
            print("Invalid directory. Please enter a valid path.")
            exit(1)
    else:
        print("Invalid choice. Please enter 1 or 2.")
        exit(1)

    print(f"Current Working Directory: {current_directory}")
    
    
    try:
        user_input = float(input("Size of Folders and Files to scan (in GB): "))
        size_threshold = user_input * 1024 ** 3  
        display_results(current_directory, size_threshold)
    except ValueError:
        print("Please enter a valid number.")

