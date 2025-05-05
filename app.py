import os
import shutil
import mimetypes
import datetime
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'development-key'  # Change this for production!

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions for file upload
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_creation_date(file_path):
    try:
        timestamp = os.path.getctime(file_path)
        return datetime.datetime.fromtimestamp(timestamp)
    except Exception:
        return datetime.datetime.now()

def suggest_category_by_extension(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    extension = os.path.splitext(file_path)[1].lower()
    
    extension_categories = {
        '.pdf': 'Documents', '.doc': 'Documents', '.docx': 'Documents',
        '.txt': 'Documents', '.rtf': 'Documents', '.odt': 'Documents',
        '.ppt': 'Presentations', '.pptx': 'Presentations',
        '.xls': 'Spreadsheets', '.xlsx': 'Spreadsheets', '.csv': 'Spreadsheets',
        '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images',
        '.gif': 'Images', '.bmp': 'Images', '.svg': 'Images',
        '.mp4': 'Videos', '.mov': 'Videos', '.avi': 'Videos',
        '.mp3': 'Audio', '.wav': 'Audio', '.ogg': 'Audio',
        '.zip': 'Archives', '.rar': 'Archives', '.7z': 'Archives',
        '.py': 'Code', '.js': 'Code', '.html': 'Code',
        '.exe': 'Executables', '.msi': 'Executables'
    }
    
    if extension in extension_categories:
        return extension_categories[extension]
    
    if mime_type:
        if mime_type.startswith('image/'):
            return 'Images'
        elif mime_type.startswith('video/'):
            return 'Videos'
        elif mime_type.startswith('audio/'):
            return 'Audio'
        elif mime_type.startswith('text/'):
            return 'Documents'
    
    return 'Other'

def suggest_category_by_date(file_path):
    creation_date = get_creation_date(file_path)
    year = creation_date.strftime('%Y')
    month = creation_date.strftime('%B')
    return f"{year}/{month}"

def suggest_category_by_content_pattern(filename):
    patterns = {
        r'invoice|receipt|bill|payment': 'Finance',
        r'resume|cv|cover.letter': 'Job Applications',
        r'screenshot|capture': 'Screenshots',
        r'backup|bak': 'Backups'
    }
    
    filename_lower = filename.lower()
    for pattern, category in patterns.items():
        if re.search(pattern, filename_lower):
            return category
    return None

def get_files_with_sorting_info(directory, sort_order):
    files_info = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            file_info = {
                'name': item,
                'path': item_path,
                'creation_time': os.path.getctime(item_path),
                'modified_time': os.path.getmtime(item_path),
                'size': os.path.getsize(item_path),
                'size_mb': round(os.path.getsize(item_path) / (1024 * 1024), 2)
            }
            files_info.append(file_info)
    
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

def generate_directory_tree(files):
    tree = []
    for i, file in enumerate(files):
        prefix = "└── " if i == len(files) - 1 else "├── "
        tree.append(f"{prefix}{file['name']}")
    return tree

def generate_proposed_tree(file_categories):
    categories_dict = {}
    for file, category in file_categories.items():
        if category not in categories_dict:
            categories_dict[category] = []
        categories_dict[category].append(file)
    
    sorted_categories = sorted(categories_dict.keys())
    tree = []
    
    for i, category in enumerate(sorted_categories):
        files = sorted(categories_dict[category])
        cat_prefix = "└── " if i == len(sorted_categories) - 1 else "├── "
        tree.append(f"{cat_prefix}{category}")
        
        for j, file in enumerate(files):
            indent = "    " if i == len(sorted_categories) - 1 else "│   "
            file_prefix = "└── " if j == len(files) - 1 else "├── "
            tree.append(f"{indent}{file_prefix}{file}")
    
    return tree

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if files were uploaded
        if 'files' not in request.files:
            flash('No files selected', 'error')
            return redirect(request.url)
        
        files = request.files.getlist('files')
        
        # Check if any files were actually selected
        if not files or all(file.filename == '' for file in files):
            flash('No files selected', 'error')
            return redirect(request.url)
        
        # Create a unique folder for this upload
        upload_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], upload_id)
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save all uploaded files
        for file in files:
            if file and file.filename:  # Check if file exists and has a filename
                filename = secure_filename(file.filename)
                file.save(os.path.join(upload_folder, filename))
        
        # Store in session
        session['upload_folder'] = upload_folder
        session['mode'] = request.form.get('mode', '1')
        session['sort_order'] = request.form.get('sort_order', '1')
        
        return redirect(url_for('analyze'))
    
    return render_template('index.html')


@app.route('/analyze')
def analyze():
    upload_folder = session.get('upload_folder')
    if not upload_folder or not os.path.exists(upload_folder):
        flash('Upload folder not found', 'error')
        return redirect(url_for('index'))
    
    mode = session.get('mode', '1')
    sort_order = session.get('sort_order', '1')
    
    # Get files with sorting info
    files_info = get_files_with_sorting_info(upload_folder, sort_order)
    
    # Generate current directory tree
    current_tree = generate_directory_tree(files_info)
    
    # Categorize files
    file_categories = {}
    for file_info in files_info:
        file_path = file_info['path']
        
        if mode == "1":
            category = suggest_category_by_extension(file_path)
        elif mode == "2":
            category = suggest_category_by_date(file_path)
        elif mode == "3":
            category = suggest_category_by_content_pattern(file_info['name']) or suggest_category_by_extension(file_path)
        else:
            category = suggest_category_by_extension(file_path)
        
        file_categories[file_info['name']] = category
    
    # Generate proposed directory tree
    proposed_tree = generate_proposed_tree(file_categories)
    
    # Prepare categories list
    categories = {}
    for file, category in file_categories.items():
        if category not in categories:
            categories[category] = 0
        categories[category] += 1
    
    # Save to session for organization step
    session['file_categories'] = file_categories
    
    return render_template('analyze.html', 
                         current_tree=current_tree,
                         proposed_tree=proposed_tree,
                         files=files_info,
                         categories=categories,
                         folder_path=upload_folder)

@app.route('/organize', methods=['POST'])
def organize():
    upload_folder = session.get('upload_folder')
    if not upload_folder or not os.path.exists(upload_folder):
        flash('Upload folder not found', 'error')
        return redirect(url_for('index'))
    
    file_categories = session.get('file_categories', {})
    results = []
    
    # Create category directories and move files
    categories = set(file_categories.values())
    for category in categories:
        category_path = os.path.join(upload_folder, category)
        if "/" in category:
            parts = category.split("/")
            current_path = upload_folder
            for part in parts:
                current_path = os.path.join(current_path, part)
                os.makedirs(current_path, exist_ok=True)
        else:
            os.makedirs(category_path, exist_ok=True)
    
    # Move files to appropriate categories
    for file, category in file_categories.items():
        source_path = os.path.join(upload_folder, file)
        dest_path = os.path.join(upload_folder, category, file)
        
        try:
            shutil.move(source_path, dest_path)
            results.append(f"Moved '{file}' to '{category}'")
        except Exception as e:
            results.append(f"Error moving '{file}': {str(e)}")
    
    # Generate results tree
    organized_tree = []
    categories = {}
    for item in os.listdir(upload_folder):
        item_path = os.path.join(upload_folder, item)
        if os.path.isdir(item_path):
            categories[item] = []
            for file in os.listdir(item_path):
                if os.path.isfile(os.path.join(item_path, file)):
                    categories[item].append(file)
    
    sorted_categories = sorted(categories.keys())
    for i, category in enumerate(sorted_categories):
        files = sorted(categories[category])
        cat_prefix = "└── " if i == len(sorted_categories) - 1 else "├── "
        organized_tree.append(f"{cat_prefix}{category}")
        
        for j, file in enumerate(files):
            indent = "    " if i == len(sorted_categories) - 1 else "│   "
            file_prefix = "└── " if j == len(files) - 1 else "├── "
            organized_tree.append(f"{indent}{file_prefix}{file}")
    
    return render_template('results.html', 
                         results=results,
                         organized_tree=organized_tree,
                         folder_path=upload_folder)

if __name__ == '__main__':
    app.run(debug=True)