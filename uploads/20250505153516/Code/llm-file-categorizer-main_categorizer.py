import os
import shutil
import time
import mimetypes
import datetime
import re
from termcolor import colored

# Try to import Gemini API, but don't fail if not available
try:
    import google.generativeai as genai  # type: ignore
    from dotenv import load_dotenv
    # Load environment variables from .env file
    load_dotenv()
    GEMINI_AVAILABLE = True
    print(colored("Gemini API module detected.", "green"))
    
    # Check if API key is available
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        print(colored("Gemini API key found and configured.", "green"))
        GEMINI_CONFIGURED = True
    else:
        print(colored("No Gemini API key found in environment variables.", "yellow"))
        print(colored("Local categorization will be used as fallback.", "yellow"))
        GEMINI_CONFIGURED = False
        
except ImportError:
    GEMINI_AVAILABLE = False
    GEMINI_CONFIGURED = False
    print(colored("Gemini API not available. Using local categorization only.", "yellow"))

def print_directory_tree(directory):
    """
    Print a directory tree structure.
    """
    print(f"Directory tree before organizing:")
    print(f"{directory}")
    
    # Get all files in the directory
    files = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            files.append(item)
    
    # Sort files for clean display (now sorting alphabetically)
    files.sort()
    
    # Print files as a tree structure
    for file in files:
        print(f"├── {file}")
    
    print("*" * 60)
        
def print_organized_directory_tree(directory, file_categories):
    """
    Print the proposed organized directory tree structure with categories.
    """
    print(f"Proposed directory structure:")
    print(f"{directory}")
    
    # Group files by category
    categories_dict = {}
    for file, category in file_categories.items():
        if category not in categories_dict:
            categories_dict[category] = []
        categories_dict[category].append(file)
    
    # Sort categories for consistent display
    sorted_categories = sorted(categories_dict.keys())
    
    # Print each category and its files
    for i, category in enumerate(sorted_categories):
        files = sorted(categories_dict[category])
        
        # Print category
        cat_prefix = "└── " if i == len(sorted_categories) - 1 else "├── "
        print(f"{cat_prefix}{category}")
        
        # Print files
        for j, file in enumerate(files):
            indent = "    " if i == len(sorted_categories) - 1 else "│   "
            file_prefix = "└── " if j == len(files) - 1 else "├── "
            print(f"{indent}{file_prefix}{file}")

def get_creation_date(file_path):
    """Get file creation date."""
    try:
        # Get file creation time (or last modified time if creation is not available)
        timestamp = os.path.getctime(file_path)
        return datetime.datetime.fromtimestamp(timestamp)
    except Exception:
        # If error, return current date
        return datetime.datetime.now()

def get_files_with_sorting_info(directory, sort_order):
    """
    Get files with their sorting information based on the specified order.
    """
    files_info = []
    
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            file_info = {
                'name': item,
                'path': item_path,
                'creation_time': os.path.getctime(item_path),
                'modified_time': os.path.getmtime(item_path),
                'size': os.path.getsize(item_path)
            }
            files_info.append(file_info)
    
    # Sort based on the selected order
    if sort_order == "1":  # Alphabetical
        files_info.sort(key=lambda x: x['name'].lower())
    elif sort_order == "2":  # Creation time
        files_info.sort(key=lambda x: x['creation_time'])
    elif sort_order == "3":  # Modified time
        files_info.sort(key=lambda x: x['modified_time'])
    elif sort_order == "4":  # Size
        files_info.sort(key=lambda x: x['size'])
    elif sort_order == "5":  # Size (descending)
        files_info.sort(key=lambda x: x['size'], reverse=True)
    
    return files_info

def suggest_category_by_extension(file_path):
    """
    Suggest a category based on file extension and mime type.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    extension = os.path.splitext(file_path)[1].lower()
    
    # Define category mappings
    extension_categories = {
        # Documents
        '.pdf': 'Documents',
        '.doc': 'Documents',
        '.docx': 'Documents',
        '.txt': 'Documents',
        '.rtf': 'Documents',
        '.odt': 'Documents',
        '.ppt': 'Presentations',
        '.pptx': 'Presentations',
        '.xls': 'Spreadsheets',
        '.xlsx': 'Spreadsheets',
        '.csv': 'Spreadsheets',
        
        # Images
        '.jpg': 'Images',
        '.jpeg': 'Images',
        '.png': 'Images',
        '.gif': 'Images',
        '.bmp': 'Images',
        '.svg': 'Images',
        '.tiff': 'Images',
        '.webp': 'Images',
        
        # Videos
        '.mp4': 'Videos',
        '.mov': 'Videos',
        '.avi': 'Videos',
        '.mkv': 'Videos',
        '.flv': 'Videos',
        '.wmv': 'Videos',
        '.webm': 'Videos',
        
        # Audio
        '.mp3': 'Audio',
        '.wav': 'Audio',
        '.ogg': 'Audio',
        '.flac': 'Audio',
        '.aac': 'Audio',
        '.wma': 'Audio',
        
        # Archives
        '.zip': 'Archives',
        '.rar': 'Archives',
        '.7z': 'Archives',
        '.tar': 'Archives',
        '.gz': 'Archives',
        '.bz2': 'Archives',
        
        # Code
        '.py': 'Code',
        '.js': 'Code',
        '.html': 'Code',
        '.css': 'Code',
        '.java': 'Code',
        '.cpp': 'Code',
        '.c': 'Code',
        '.php': 'Code',
        '.rb': 'Code',
        '.go': 'Code',
        '.swift': 'Code',
        '.json': 'Code',
        '.xml': 'Code',
        
        # Executables
        '.exe': 'Executables',
        '.msi': 'Executables',
        '.app': 'Executables',
        '.bat': 'Executables',
        '.sh': 'Executables',
        '.apk': 'Executables',
        
        # Other types
        '.torrent': 'Downloads',
        '.iso': 'Disk Images',
        '.dmg': 'Disk Images'
    }
    
    # Return category based on extension
    if extension in extension_categories:
        return extension_categories[extension]
    
    # If extension not found but mime type is available
    if mime_type:
        if mime_type.startswith('image/'):
            return 'Images'
        elif mime_type.startswith('video/'):
            return 'Videos'
        elif mime_type.startswith('audio/'):
            return 'Audio'
        elif mime_type.startswith('text/'):
            return 'Documents'
        elif mime_type.startswith('application/pdf'):
            return 'Documents'
        elif mime_type.startswith('application/msword') or mime_type.startswith('application/vnd.openxmlformats-officedocument.wordprocessingml'):
            return 'Documents'
        elif mime_type.startswith('application/vnd.ms-excel') or mime_type.startswith('application/vnd.openxmlformats-officedocument.spreadsheetml'):
            return 'Spreadsheets'
        elif mime_type.startswith('application/vnd.ms-powerpoint') or mime_type.startswith('application/vnd.openxmlformats-officedocument.presentationml'):
            return 'Presentations'
        elif mime_type.startswith('application/zip') or mime_type.startswith('application/x-rar') or mime_type.startswith('application/x-7z'):
            return 'Archives'
    
    # Default category
    return 'Other'

def suggest_category_by_date(file_path):
    """Suggest category by date (Year/Month)."""
    creation_date = get_creation_date(file_path)
    year = creation_date.strftime('%Y')
    month = creation_date.strftime('%B')  # Full month name
    return f"{year}/{month}"

def suggest_category_by_content_pattern(filename):
    """
    Suggest category based on filename patterns.
    """
    patterns = {
        r'invoice|receipt|bill|payment': 'Finance',
        r'resume|cv|cover.letter': 'Job_Applications',
        r'certificate|diploma|degree': 'Certificates',
        r'project|proposal|plan': 'Projects',
        r'report|analysis|research': 'Research',
        r'manual|guide|tutorial|howto': 'Guides',
        r'screenshot|capture': 'Screenshots',
        r'backup|bak': 'Backups',
        r'template|form': 'Templates',
        r'letter|email': 'Correspondence',
        r'meeting|agenda|minutes': 'Meetings',
        r'contract|agreement|legal': 'Legal',
        r'wallpaper|background': 'Wallpapers',
        r'profile|avatar|photo': 'Profile_Pictures',
        r'log|debug|error': 'Logs',
        r'setup|install|config': 'Configuration',
        r'dataset|data': 'Datasets',
        r'icon|logo': 'Icons_Logos',
        r'banner|header|ad': 'Marketing',
        r'social|facebook|instagram|linkedin|twitter': 'Social_Media'
    }
    
    # Check if the filename matches any pattern
    filename_lower = filename.lower()
    for pattern, category in patterns.items():
        if re.search(pattern, filename_lower):
            return category
    
    # No pattern matched
    return None

def get_file_description_gemini(file_path):
    """
    Get the description of a file using the Gemini Pro model.
    """
    if not GEMINI_AVAILABLE or not GEMINI_CONFIGURED:
        return None
        
    mime_type, _ = mimetypes.guess_type(file_path)
    print(colored(f"Processing file: {file_path}", "blue"))
    print(colored(f"MIME type: {mime_type}", "yellow"))
    
    try:
        if mime_type and mime_type.startswith('text/'):
            with open(file_path, 'r', errors='ignore') as f:
                file_content = f.read().strip()[:10000]  # Get first 10,000 characters of file content
            
            # Text-only mode
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(
                f"""
                Describe this text file. This is the name of the file: <name>{os.path.basename(file_path)}</name>.
                Here is a portion of the file:
                <contents>
                {file_content}
                </contents>
                Wrap the description in <description></description> tags. Keep your response concise and to the point - no more than 30 words.
                """
            )
        
        elif mime_type and mime_type.startswith('image/'):
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                # Check if image API is supported in this version
                if hasattr(genai.types, 'Part'):
                    # Multimodal mode for image processing
                    model = genai.GenerativeModel('gemini-pro-vision')
                    response = model.generate_content(
                        [
                            genai.types.Part.from_data(file_data, mime_type=mime_type),
                            genai.types.Part.from_text(
                                f"""
                                Describe the contents of the image file. This is the name of the file: {os.path.basename(file_path)}.
                                Wrap the description in <description></description> tags. Keep your response concise and to the point - Maximum of 30 words.
                                """
                            )
                        ]
                    )
                else:
                    # Fall back to just the filename if Part is not available
                    raise AttributeError("Module 'google.generativeai.types' has no attribute 'Part'")
            
            except (AttributeError, TypeError) as e:
                # Fall back for image files if Part is not supported
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(
                    f"""
                    This is an image file: {os.path.basename(file_path)} with mime type {mime_type}.
                    Based just on the filename, suggest what this image might contain.
                    Wrap the description in <description></description> tags. Keep your response concise.
                    """
                )
        
        else:
            # For other file types, just use the filename
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(
                f"""
                Describe the contents of this file. This is the name of the file: <name>{os.path.basename(file_path)}</name>.
                Wrap the description in <description></description> tags. Keep your response concise and to the point - 5-10 words should be enough.
                """
            )
        
        # Extract description from response
        description_text = response.text
        try:
            description = description_text.split('<description>')[1].split('</description>')[0].strip()
        except IndexError:
            # Fallback if tags aren't properly included
            description = description_text.strip()
            print(colored("Warning: Description tags not found in response. Using full response.", "yellow"))
        
        print(colored(f"File description: {description}", "green"))
        return description
        
    except Exception as e:
        print(colored(f"Error getting file description from Gemini: {str(e)}", "red"))
        print(colored("Falling back to local categorization.", "yellow"))
        return None

def get_category_suggestion_gemini(file_descriptions):
    """
    Get category suggestions for the given file descriptions using Gemini Pro model.
    """
    if not GEMINI_AVAILABLE or not GEMINI_CONFIGURED:
        return []
        
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"""
            You are given a list of file descriptions. You need to categorize these files into different categories. Here are the file descriptions:
            <file_descriptions>
            {', '.join(file_descriptions)}
            </file_descriptions>
            You need to suggest up to 10 categories for these files. Wrap the categories in <categories></categories> tags, and separate them with commas, like `, `. Keep your response concise and to the point - they should be valid folder names, like example, or example-category. No restricted characters, please.
            """
        )
        
        response_text = response.text
        try:
            categories_text = response_text.split('<categories>')[1].split('</categories>')[0].strip()
            categories = [cat.strip() for cat in categories_text.split(', ')]
        except IndexError:
            # Fallback if tags aren't properly included
            categories = [cat.strip() for cat in response_text.strip().split(', ')]
            print(colored("Warning: Category tags not found in response. Using full response split by commas.", "yellow"))
        
        print(colored(f"Suggested categories: {categories}", "green"))
        return categories
        
    except Exception as e:
        print(colored(f"Error getting category suggestions from Gemini: {str(e)}", "red"))
        print(colored("Falling back to local categorization.", "yellow"))
        return []

def get_file_category_gemini(file_description, categories):
    """
    Get the category for a file based on its description using Gemini Pro model.
    """
    if not GEMINI_AVAILABLE or not GEMINI_CONFIGURED:
        return None
        
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"""
            You are given a file description. You need to suggest a category for this file. Here is the file description:
            <file_description>
            {file_description}
            </file_description>
            You need to suggest a category for this file. Wrap the category in <category></category> tags. Here is a list of the categories you can choose from:
            <categories>
            {str(categories)}
            </categories>
            ONLY USE these categories!!!! Nothing else!!!!!
            """
        )
        
        response_text = response.text
        try:
            category = response_text.split('<category>')[1].split('</category>')[0].strip()
        except IndexError:
            # Fallback if tags aren't properly included
            # Find the closest match from categories
            for cat in categories:
                if cat.lower() in response_text.lower():
                    category = cat
                    break
            else:
                category = categories[0]  # Default to first category if no match
            print(colored(f"Warning: Category tags not found in response. Selected category: {category}", "yellow"))
        
        # Validate that the category is in our list
        if category not in categories:
            closest_match = min(categories, key=lambda x: abs(len(x) - len(category)))
            print(colored(f"Warning: Category '{category}' not in provided list. Using '{closest_match}' instead.", "yellow"))
            category = closest_match
        
        print(colored(f"File category: {category}", "green"))
        return category
        
    except Exception as e:
        print(colored(f"Error getting file category from Gemini: {str(e)}", "red"))
        print(colored("Falling back to local categorization.", "yellow"))
        return None

def main():
    """
    Main function to categorize files in a folder.
    """
    print("=" * 60)
    print(colored("Hybrid File Categorizer", "cyan"))
    print(colored("Supports both Gemini AI and local categorization", "cyan"))
    print("=" * 60)
    
    folder_path = input("Enter the folder path: ")
    
    if not os.path.exists(folder_path):
        print(colored(f"Error: Folder path '{folder_path}' does not exist.", "red"))
        return
    
    print("Choose the mode to organize your files:")
    print("1. By file type (Documents, Images, Videos, etc.)")
    print("2. By date (Year/Month)")
    print("3. By content pattern (detect patterns in filenames)")
    print("4. Custom categorization (you'll be asked to review each file)")
    if GEMINI_AVAILABLE and GEMINI_CONFIGURED:
        print("5. Using Gemini AI (intelligent categorization based on content)")
    
    mode = input("Enter your choice: ")
    
    print("Choose the sorting order for files:")
    print("1. Alphabetical (A-Z)")
    print("2. Creation time (oldest first)")
    print("3. Modified time (oldest first)")
    print("4. Size (smallest first)")
    print("5. Size (largest first)")
    
    sort_order = input("Enter your sorting choice (default: 1): ") or "1"
    
    start_time = time.time()
    
    # Get files with sorting information
    files_info = get_files_with_sorting_info(folder_path, sort_order)
    files = [file_info['name'] for file_info in files_info]
    
    load_time = time.time() - start_time
    
    print("-" * 60)
    print(colored(f"Time taken to load and sort file paths: {load_time:.2f} seconds", "cyan"))
    print("-" * 60)
    
    # Print directory tree before organizing
    print_directory_tree(folder_path)
    
    if not files:
        print(colored(f"No files found in {folder_path}", "yellow"))
        return
    
    # Dictionary to store file -> category mappings
    file_categories = {}
    
    # Use Gemini API mode
    if mode == "5" and GEMINI_AVAILABLE and GEMINI_CONFIGURED:
        file_descriptions = []
        file_desc_map = {}  # Map filenames to descriptions
        
        # Get descriptions for all files
        for file in files:
            file_path = os.path.join(folder_path, file)
            try:
                description = get_file_description_gemini(file_path)
                if description:
                    file_descriptions.append(f"{file}: {description}")
                    file_desc_map[file] = description
                else:
                    # If Gemini fails, use local categorization
                    file_desc_map[file] = f"File with extension {os.path.splitext(file)[1]}"
                    file_descriptions.append(f"{file}: {file_desc_map[file]}")
            except Exception as e:
                print(colored(f"Error processing file {file}: {str(e)}", "red"))
                file_desc_map[file] = f"File with extension {os.path.splitext(file)[1]}"
                file_descriptions.append(f"{file}: {file_desc_map[file]}")
        
        # Get category suggestions
        try:
            categories = get_category_suggestion_gemini(file_descriptions)
            if not categories:
                # If Gemini fails, use local categories
                categories = ["Documents", "Images", "Videos", "Audio", "Archives", "Code", "Other"]
        except Exception as e:
            print(colored(f"Error getting category suggestions: {str(e)}", "red"))
            categories = ["Documents", "Images", "Videos", "Audio", "Archives", "Code", "Other"]
        
        # Assign categories to files
        for file in files:
            try:
                if file in file_desc_map:
                    category = get_file_category_gemini(file_desc_map[file], categories)
                    if not category:
                        # If Gemini fails, use local categorization
                        category = suggest_category_by_extension(os.path.join(folder_path, file))
                else:
                    category = suggest_category_by_extension(os.path.join(folder_path, file))
                
                file_categories[file] = category
            except Exception as e:
                print(colored(f"Error categorizing file {file}: {str(e)}", "red"))
                # Default to extension-based category on error
                file_categories[file] = suggest_category_by_extension(os.path.join(folder_path, file))
    
    # Local categorization modes
    else:
        for file in files:
            file_path = os.path.join(folder_path, file)
            
            if mode == "1":
                # Categorize by file type
                category = suggest_category_by_extension(file_path)
            elif mode == "2":
                # Categorize by date
                category = suggest_category_by_date(file_path)
            elif mode == "3":
                # Categorize by content pattern
                category = suggest_category_by_content_pattern(file) or suggest_category_by_extension(file_path)
            elif mode == "4":
                # Custom categorization
                print(f"\nFile: {file}")
                suggested = suggest_category_by_extension(file_path)
                category = input(f"Enter category for this file (suggested: {suggested}): ").strip()
                if not category:
                    category = suggested
            else:
                print(colored("Invalid choice. Using file type categorization.", "yellow"))
                category = suggest_category_by_extension(file_path)
            
            file_categories[file] = category
    
    # Print proposed directory structure
    print("*" * 60)
    print_organized_directory_tree(folder_path, file_categories)
    
    # Ask for confirmation
    print("*" * 60)
    confirm = input("Do you want to proceed with this organization? (yes/no): ")
    if confirm.lower() not in ["yes", "y"]:
        print(colored("Operation canceled by user.", "yellow"))
        return
    
    # Create category directories
    categories = set(file_categories.values())
    for category in categories:
        category_path = os.path.join(folder_path, category)
        
        # Handle nested categories (e.g., "2023/January")
        if "/" in category:
            parts = category.split("/")
            current_path = folder_path
            for part in parts:
                current_path = os.path.join(current_path, part)
                os.makedirs(current_path, exist_ok=True)
        else:
            os.makedirs(category_path, exist_ok=True)
    
    # Move files to appropriate categories
    for file, category in file_categories.items():
        source_path = os.path.join(folder_path, file)
        dest_path = os.path.join(folder_path, category, file)
        
        try:
            shutil.move(source_path, dest_path)
            print(colored(f"Moved '{file}' to category '{category}'", "green"))
        except Exception as e:
            print(colored(f"Error moving file {file}: {str(e)}", "red"))
    
    print("*" * 60)
    print(colored("The files have been organized successfully.", "green"))
    print("*" * 60)
    
    # Save log of organization
    log_file = os.path.join(folder_path, "organization_log.txt")
    with open(log_file, 'w') as f:
        f.write(f"File Organization Log - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Folder: {folder_path}\n")
        f.write(f"Organization mode: {mode}\n")
        f.write(f"Sorting order: {sort_order}\n\n")
        f.write("Files organized:\n")
        for file, category in file_categories.items():
            f.write(f"{file} → {category}\n")
    
    print(colored(f"Organization log saved to: {log_file}", "green"))
    
    # Ask to organize another directory
    another = input("Would you like to organize another directory? (yes/no): ")
    if another.lower() in ["yes", "y"]:
        main()  # Recursive call to start again

if __name__ == "__main__":
    main()