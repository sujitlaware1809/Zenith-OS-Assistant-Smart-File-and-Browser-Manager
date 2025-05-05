from flask import Flask, render_template, request, jsonify, send_from_directory
import datetime
import webbrowser
import os
import shutil
import time
import re
import glob
import subprocess
import sys
from pathlib import Path
import platform
import psutil
import socket
import uuid
import json

# For browser tab management
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.common.by import By
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not installed. Browser tab management will be limited.")

app = Flask(__name__, static_folder='static')

# Browser driver
browser = None

def initialize_browser():
    """Initialize the browser if not already done"""
    global browser
    if browser is None and SELENIUM_AVAILABLE:
        try:
            print("Initializing browser...")
            service = Service(ChromeDriverManager().install())
            browser = webdriver.Chrome(service=service)
            return True
        except Exception as e:
            print(f"Failed to initialize browser: {str(e)}")
            return False
    return browser is not None and SELENIUM_AVAILABLE

# File operations
def list_drives():
    """List all available drives on the system"""
    if os.name == 'nt':
        drives = [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:\\")]
    else:
        drives = ['/']
    
    if not drives:
        return {"status": "error", "message": "No drives found."}
    
    result = {"status": "success", "message": "Available drives:", "drives": drives}
    return result

def navigate_directory(path):
    """Navigate through a directory and its contents"""
    try:
        items = os.listdir(path)
        folders = []
        files = []
        
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folders.append({
                    "name": item,
                    "type": "folder",
                    "path": item_path,
                    "size": get_folder_size(item_path)
                })
            else:
                files.append({
                    "name": item,
                    "type": "file",
                    "path": item_path,
                    "size": os.path.getsize(item_path),
                    "extension": os.path.splitext(item)[1].lower(),
                    "modified": os.path.getmtime(item_path)
                })
        
        result = {
            "status": "success",
            "path": path,
            "folders": folders[:50],  # Limit to 50 for UI performance
            "files": files[:50],      # Limit to 50 for UI performance
            "total_folders": len(folders),
            "total_files": len(files)
        }
        return result
    except Exception as e:
        return {"status": "error", "message": f"Error navigating directory: {str(e)}"}

def get_folder_size(path):
    """Calculate total size of a folder"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except:
                continue
    return total

def open_file(file_path):
    """Open a file with the default application"""
    try:
        if os.name == 'nt':
            os.startfile(file_path)
        elif os.name == 'posix':
            subprocess.run(['open', file_path] if sys.platform == 'darwin' else ['xdg-open', file_path])
        return {"status": "success", "message": f"Opened {os.path.basename(file_path)}"}
    except Exception as e:
        return {"status": "error", "message": f"Could not open file: {str(e)}"}

def search_for_file(file_name, path=None):
    """Search all drives for a specific file"""
    try:
        search_path = path if path else os.getcwd()
        matches = []
        
        for root, _, files in os.walk(search_path):
            for file in files:
                if re.search(file_name.replace('*', '.*'), file, re.IGNORECASE):
                    matches.append({
                        "name": file,
                        "path": os.path.join(root, file),
                        "size": os.path.getsize(os.path.join(root, file))
                    })
                    # Limit results to prevent excessive processing
                    if len(matches) >= 50:
                        break
            if len(matches) >= 50:
                break
        
        if not matches:
            return {"status": "error", "message": f"No files found matching '{file_name}'."}
        
        return {"status": "success", "message": f"Found {len(matches)} files matching '{file_name}'.", "files": matches}
    except Exception as e:
        return {"status": "error", "message": f"Error searching for files: {str(e)}"}

def create_file(filename, directory=None, content=None):
    """Create a new file"""
    try:
        if '.' not in filename:
            filename += '.txt'
        
        filepath = os.path.join(directory, filename) if directory else filename
        
        with open(filepath, 'w') as f:
            if content:
                f.write(content)
        
        return {"status": "success", "message": f"File {filename} has been created successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Error creating file: {str(e)}"}

def delete_file(filename, directory=None):
    """Delete a file"""
    try:
        filepath = os.path.join(directory, filename) if directory else filename
        
        if '*' in filepath:
            matching_files = glob.glob(filepath)
            if not matching_files:
                return {"status": "error", "message": f"No files found matching {filepath}"}
            
            for file in matching_files:
                os.remove(file)
            return {"status": "success", "message": f"Deleted {len(matching_files)} files matching {filepath}"}
        else:
            if os.path.exists(filepath):
                os.remove(filepath)
                return {"status": "success", "message": f"File {filename} has been deleted."}
            else:
                return {"status": "error", "message": f"File {filename} was not found."}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting file: {str(e)}"}

def list_files(directory=".", pattern="*"):
    """List files in a directory"""
    try:
        files = glob.glob(os.path.join(directory, pattern))
        
        if files:
            return {"status": "success", "message": f"Found {len(files)} files.", "files": files}
        else:
            return {"status": "error", "message": f"No files found in {directory} matching pattern {pattern}."}
    except Exception as e:
        return {"status": "error", "message": f"Error listing files: {str(e)}"}

def create_folder(folder_name, directory=None):
    """Create a new folder/directory"""
    try:
        folderpath = os.path.join(directory, folder_name) if directory else folder_name
        
        os.makedirs(folderpath, exist_ok=True)
        return {"status": "success", "message": f"Folder {folder_name} has been created successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Error creating folder: {str(e)}"}

def delete_folder(folder_name, directory=None):
    """Delete a folder"""
    try:
        folderpath = os.path.join(directory, folder_name) if directory else folder_name
        
        if not os.path.exists(folderpath):
            return {"status": "error", "message": f"Folder {folder_name} was not found."}
        
        shutil.rmtree(folderpath)
        return {"status": "success", "message": f"Folder {folder_name} has been deleted."}
    except Exception as e:
        return {"status": "error", "message": f"Error deleting folder: {str(e)}"}

def organize_files(directory="."):
    """Organize files in a directory based on extension"""
    try:
        if not os.path.exists(directory):
            return {"status": "error", "message": f"Directory {directory} was not found."}
        
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        
        if not files:
            return {"status": "error", "message": f"No files found in {directory}."}
        
        organized = 0
        for file in files:
            _, ext = os.path.splitext(file)
            ext = ext[1:].lower()
            if not ext:
                ext = "no_extension"
            
            ext_folder = os.path.join(directory, ext)
            os.makedirs(ext_folder, exist_ok=True)
            
            src_path = os.path.join(directory, file)
            dst_path = os.path.join(ext_folder, file)
            
            if os.path.dirname(src_path) == ext_folder:
                continue
                
            shutil.move(src_path, dst_path)
            organized += 1
        
        return {"status": "success", "message": f"Organized {organized} files in {directory} by file extension."}
    except Exception as e:
        return {"status": "error", "message": f"Error organizing files: {str(e)}"}

def rename_item(old_name, new_name, directory=None):
    """Rename a file or folder"""
    try:
        old_path = os.path.join(directory, old_name) if directory else old_name
        new_path = os.path.join(directory, new_name) if directory else new_name
        
        if not os.path.exists(old_path):
            return {"status": "error", "message": f"Cannot find {old_name}."}
        
        os.rename(old_path, new_path)
        return {"status": "success", "message": f"Successfully renamed {old_name} to {new_name}."}
    except Exception as e:
        return {"status": "error", "message": f"Error renaming: {str(e)}"}

def move_item(item_name, destination, source=None):
    """Move a file or folder"""
    try:
        src_path = os.path.join(source, item_name) if source else item_name
        
        if not os.path.exists(src_path):
            return {"status": "error", "message": f"Cannot find {item_name}."}
        
        os.makedirs(destination, exist_ok=True)
        
        dst_path = os.path.join(destination, os.path.basename(src_path))
        shutil.move(src_path, dst_path)
        return {"status": "success", "message": f"Successfully moved {item_name} to {destination}."}
    except Exception as e:
        return {"status": "error", "message": f"Error moving: {str(e)}"}

def upload_file(file, destination):
    """Handle file upload"""
    try:
        if not os.path.exists(destination):
            os.makedirs(destination, exist_ok=True)
        
        file_path = os.path.join(destination, file.filename)
        file.save(file_path)
        
        return {"status": "success", "message": f"File {file.filename} uploaded successfully.", "path": file_path}
    except Exception as e:
        return {"status": "error", "message": f"Error uploading file: {str(e)}"}

# Browser operations
def open_browser_func():
    """Open a new browser window"""
    if not SELENIUM_AVAILABLE:
        webbrowser.open("https://www.google.com")
        return {"status": "success", "message": "Opened browser window."}
    
    if initialize_browser():
        return {"status": "success", "message": "Browser opened successfully."}
    else:
        webbrowser.open("https://www.google.com")
        return {"status": "success", "message": "Opened regular browser window."}

def open_website(website):
    """Open a specific website"""
    try:
        if not website.startswith(('http://', 'https://')):
            website = f"https://{website}"
        
        if initialize_browser():
            browser.execute_script(f"window.open('{website}');")
            return {"status": "success", "message": f"Opened {website} in a new tab."}
        else:
            webbrowser.open(website)
            return {"status": "success", "message": f"Opened {website} in your default browser."}
    except Exception as e:
        return {"status": "error", "message": f"Error opening website: {str(e)}"}

def get_browser_history():
    """Get browser history (simulated)"""
    try:
        history = [
            {"url": "https://www.google.com", "title": "Google", "visit_count": 42, "last_visit": time.time()},
            {"url": "https://github.com", "title": "GitHub", "visit_count": 15, "last_visit": time.time() - 3600},
            {"url": "https://stackoverflow.com", "title": "Stack Overflow", "visit_count": 28, "last_visit": time.time() - 7200}
        ]
        return {"status": "success", "history": history}
    except Exception as e:
        return {"status": "error", "message": f"Error getting browser history: {str(e)}"}

# System operations
def show_system_info():
    """Show system information"""
    try:
        system_info = {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "hostname": socket.gethostname(),
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "mac_address": ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        }
        
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_usage = psutil.cpu_percent(interval=1)
            
            system_info.update({
                "memory_total": f"{memory.total / (1024 ** 3):.2f} GB",
                "memory_used": f"{memory.used / (1024 ** 3):.2f} GB",
                "memory_free": f"{memory.available / (1024 ** 3):.2f} GB",
                "memory_used_percent": f"{memory.percent}%",
                "disk_total": f"{disk.total / (1024 ** 3):.2f} GB",
                "disk_used": f"{disk.used / (1024 ** 3):.2f} GB",
                "disk_free": f"{disk.free / (1024 ** 3):.2f} GB",
                "disk_used_percent": f"{disk.percent}%",
                "cpu_cores": psutil.cpu_count(),
                "cpu_usage": f"{cpu_usage}%",
                "boot_time": datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            system_info["note"] = f"Extended system info error: {str(e)}"
        
        return {"status": "success", "message": "System Information retrieved", "info": system_info}
    except Exception as e:
        return {"status": "error", "message": f"Error getting system info: {str(e)}"}

def get_running_processes():
    """Get list of running processes"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            processes.append(proc.info)
        
        return {"status": "success", "processes": processes[:50]}  # Limit to 50 for performance
    except Exception as e:
        return {"status": "error", "message": f"Error getting processes: {str(e)}"}

def cleanup_system():
    """Clean up temporary files"""
    try:
        import tempfile
        
        temp_dir = tempfile.gettempdir()
        total_files = sum(len(files) for _, _, files in os.walk(temp_dir))
        
        # Statistics only, no actual deletion
        return {
            "status": "success", 
            "message": f"Found {total_files} files in temporary directory.",
            "temp_dir": temp_dir,
            "total_files": total_files,
            "note": "Use confirm_cleanup endpoint to actually delete files"
        }
    except Exception as e:
        return {"status": "error", "message": f"Error during system cleanup check: {str(e)}"}

def confirm_cleanup():
    """Actually perform the temporary file cleanup"""
    try:
        import tempfile
        
        temp_dir = tempfile.gettempdir()
        deleted = 0
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        deleted += 1
                except:
                    pass
        
        return {"status": "success", "message": f"Cleanup complete. Deleted {deleted} temporary files."}
    except Exception as e:
        return {"status": "error", "message": f"Error during system cleanup: {str(e)}"}

def execute_command(command):
    """Execute a system command"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return {
            "status": "success",
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"status": "error", "message": f"Error executing command: {str(e)}"}

# Terminal operations
def handle_terminal_command(command):
    """Handle terminal commands"""
    try:
        if command.lower() == 'help':
            return {
                "status": "success",
                "output": "Available commands:\n"
                         "help - Show this help message\n"
                         "clear - Clear the terminal\n"
                         "ls - List files\n"
                         "cd - Change directory\n"
                         "pwd - Show current directory\n"
                         "sysinfo - Show system information\n"
                         "processes - Show running processes\n"
                         "history - Show browser history\n"
            }
        elif command.lower() == 'sysinfo':
            info = show_system_info()
            return {
                "status": "success",
                "output": json.dumps(info["info"], indent=2)
            }
        elif command.lower() == 'processes':
            processes = get_running_processes()
            return {
                "status": "success",
                "output": "\n".join([f"{p['pid']}: {p['name']} (CPU: {p['cpu_percent']}%, MEM: {p['memory_percent']}%)" 
                          for p in processes["processes"]])
            }
        elif command.lower().startswith('cd '):
            new_dir = command[3:].strip()
            try:
                os.chdir(new_dir)
                return {
                    "status": "success",
                    "output": f"Changed directory to {os.getcwd()}"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "output": f"Error changing directory: {str(e)}"
                }
        elif command.lower() == 'pwd':
            return {
                "status": "success",
                "output": os.getcwd()
            }
        elif command.lower() == 'ls':
            files = os.listdir()
            return {
                "status": "success",
                "output": "\n".join(files)
            }
        elif command.lower() == 'history':
            history = get_browser_history()
            return {
                "status": "success",
                "output": "\n".join([f"{h['title']} - {h['url']}" for h in history["history"]])
            }
        else:
            return execute_command(command)
    except Exception as e:
        return {"status": "error", "output": f"Error processing command: {str(e)}"}

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

# File operations API
@app.route('/api/drives', methods=['GET'])
def api_drives():
    return jsonify(list_drives())

@app.route('/api/navigate', methods=['POST'])
def api_navigate():
    data = request.json
    path = data.get('path', '.')
    return jsonify(navigate_directory(path))

@app.route('/api/open_file', methods=['POST'])
def api_open_file():
    data = request.json
    file_path = data.get('file_path')
    if not file_path:
        return jsonify({"status": "error", "message": "No file path provided"})
    return jsonify(open_file(file_path))

@app.route('/api/search_file', methods=['POST'])
def api_search_file():
    data = request.json
    file_name = data.get('file_name')
    path = data.get('path')
    if not file_name:
        return jsonify({"status": "error", "message": "No file name provided"})
    return jsonify(search_for_file(file_name, path))

@app.route('/api/create_file', methods=['POST'])
def api_create_file():
    data = request.json
    filename = data.get('filename')
    directory = data.get('directory')
    content = data.get('content')
    if not filename:
        return jsonify({"status": "error", "message": "No filename provided"})
    return jsonify(create_file(filename, directory, content))

@app.route('/api/delete_file', methods=['POST'])
def api_delete_file():
    data = request.json
    filename = data.get('filename')
    directory = data.get('directory')
    if not filename:
        return jsonify({"status": "error", "message": "No filename provided"})
    return jsonify(delete_file(filename, directory))

@app.route('/api/list_files', methods=['POST'])
def api_list_files():
    data = request.json
    directory = data.get('directory', '.')
    pattern = data.get('pattern', '*')
    return jsonify(list_files(directory, pattern))

@app.route('/api/create_folder', methods=['POST'])
def api_create_folder():
    data = request.json
    folder_name = data.get('folder_name')
    directory = data.get('directory')
    if not folder_name:
        return jsonify({"status": "error", "message": "No folder name provided"})
    return jsonify(create_folder(folder_name, directory))

@app.route('/api/delete_folder', methods=['POST'])
def api_delete_folder():
    data = request.json
    folder_name = data.get('folder_name')
    directory = data.get('directory')
    if not folder_name:
        return jsonify({"status": "error", "message": "No folder name provided"})
    return jsonify(delete_folder(folder_name, directory))

@app.route('/api/organize_files', methods=['POST'])
def api_organize_files():
    data = request.json
    directory = data.get('directory', '.')
    return jsonify(organize_files(directory))

@app.route('/api/rename_item', methods=['POST'])
def api_rename_item():
    data = request.json
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    directory = data.get('directory')
    if not old_name or not new_name:
        return jsonify({"status": "error", "message": "Old and new names are required"})
    return jsonify(rename_item(old_name, new_name, directory))

@app.route('/api/move_item', methods=['POST'])
def api_move_item():
    data = request.json
    item_name = data.get('item_name')
    destination = data.get('destination')
    source = data.get('source')
    if not item_name or not destination:
        return jsonify({"status": "error", "message": "Item name and destination are required"})
    return jsonify(move_item(item_name, destination, source))

@app.route('/api/upload_file', methods=['POST'])
def api_upload_file():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"})
    
    destination = request.form.get('destination', os.getcwd())
    return jsonify(upload_file(file, destination))

# Browser operations API
@app.route('/api/open_browser', methods=['GET'])
def api_open_browser():
    return jsonify(open_browser_func())

@app.route('/api/open_website', methods=['POST'])
def api_open_website():
    data = request.json
    website = data.get('website')
    if not website:
        return jsonify({"status": "error", "message": "No website URL provided"})
    return jsonify(open_website(website))

@app.route('/api/browser_history', methods=['GET'])
def api_browser_history():
    return jsonify(get_browser_history())

# System operations API
@app.route('/api/system_info', methods=['GET'])
def api_system_info():
    return jsonify(show_system_info())

@app.route('/api/running_processes', methods=['GET'])
def api_running_processes():
    return jsonify(get_running_processes())

@app.route('/api/cleanup_check', methods=['GET'])
def api_cleanup_check():
    return jsonify(cleanup_system())

@app.route('/api/confirm_cleanup', methods=['POST'])
def api_confirm_cleanup():
    return jsonify(confirm_cleanup())

@app.route('/api/execute_command', methods=['POST'])
def api_execute_command():
    data = request.json
    command = data.get('command')
    if not command:
        return jsonify({"status": "error", "message": "No command provided"})
    return jsonify(execute_command(command))

# Terminal API
@app.route('/api/terminal_command', methods=['POST'])
def api_terminal_command():
    data = request.json
    command = data.get('command')
    if not command:
        return jsonify({"status": "error", "message": "No command provided"})
    return jsonify(handle_terminal_command(command))

if __name__ == '__main__':
    app.run(debug=True)