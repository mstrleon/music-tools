import os

def remove_undefined_prefix(directory='.'):
    # The prefix we want to remove
    prefix = 'undefined - '
    
    # Walk through the directory
    for filename in os.listdir(directory):
        # Check if the file starts with our prefix
        if filename.startswith(prefix):
            # Create the new filename by removing the prefix
            new_filename = filename[len(prefix):]
            
            # Get the full paths
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(directory, new_filename)
            
            try:
                # Rename the file
                os.rename(old_path, new_path)
                print(f'Renamed: {filename} → {new_filename}')
            except OSError as e:
                print(f'Error renaming {filename}: {e}')

if __name__ == '__main__':
    # Get the current directory where the script is running
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f'Processing files in: {current_dir}')
    remove_undefined_prefix(current_dir) 