import os
import shutil
import re

def consolidate_files():
    source_root = r'd:\benchmark\data\test'
    dest_dir = r'd:\benchmark\data\all_together'

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f"Created directory: {dest_dir}")

    # Regex to match set directory name and capture the set number
    set_dir_pattern = re.compile(r'set (\d+)', re.IGNORECASE)

    for item in os.listdir(source_root):
        source_item_path = os.path.join(source_root, item)
        
        if os.path.isdir(source_item_path):
            match = set_dir_pattern.match(item)
            if match:
                set_no = match.group(1)
                print(f"Processing Set {set_no}...")
                
                for filename in os.listdir(source_item_path):
                    if filename.endswith('.json') or filename.endswith('.pdf'):
                        # capture the file number/name from the filename (e.g., '1.json' -> '1')
                        name_base, ext = os.path.splitext(filename)
                        
                        new_filename = f"set_{set_no}_{name_base}{ext}"
                        dest_file_path = os.path.join(dest_dir, new_filename)
                        source_file_path = os.path.join(source_item_path, filename)
                        
                        shutil.copy2(source_file_path, dest_file_path)
                        print(f"  Copied: {filename} -> {new_filename}")

if __name__ == "__main__":
    consolidate_files()
