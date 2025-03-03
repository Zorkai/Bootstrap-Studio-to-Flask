import sys
import os
import shutil
import re
import toml
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.parse

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.toml")
log_path = os.path.join(script_dir, "python_log.txt")

def log_message(message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_path, "a", encoding='utf-8') as log_file:
        log_file.write(f"[{timestamp}] {message}\n")
    print(message)

def load_config():
    if not os.path.exists(config_path):
        log_message("Config file not found. Please create a config.toml file.")
        sys.exit(1)
    return toml.load(config_path)

config = load_config()

def copy_source_to_flask(source_path):
    flask_path = f"{source_path}{config['flask_folder_suffix']}"
    os.makedirs(flask_path, exist_ok=True)

    for item in os.listdir(source_path):
        src_item = os.path.join(source_path, item)
        dest_item = os.path.join(flask_path, item)
        
        if os.path.isdir(src_item):
            if os.path.exists(dest_item):
                shutil.rmtree(dest_item)
            shutil.copytree(src_item, dest_item)
        else:
            shutil.copy2(src_item, dest_item)
    
    log_message(f"Copied source folder '{source_path}' to '{flask_path}'")
    return flask_path

def move_html_files_and_rename_assets(directory_path):
    log_message(f"Processing directory: {directory_path}")
    templates_folder = os.path.join(directory_path, 'templates')
    assets_folder = os.path.join(directory_path, 'assets')
    static_folder = os.path.join(directory_path, 'static')
    assets_in_static_folder = os.path.join(static_folder, 'assets')
    
    if not os.path.exists(templates_folder):
        os.makedirs(templates_folder)
        log_message(f"Created 'templates' folder at: {templates_folder}")
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                shutil.move(file_path, os.path.join(templates_folder, file))
                log_message(f"Moved HTML file: {file_path} to {templates_folder}")

    if os.path.exists(assets_folder):
        shutil.move(assets_folder, static_folder)
        log_message(f"Renamed 'assets' folder to 'static' at: {static_folder}")
    else:
        log_message("No 'assets' folder found.")

    if os.path.exists(assets_in_static_folder):
        shutil.rmtree(assets_in_static_folder)
        log_message(f"Deleted 'static/assets' folder at: {assets_in_static_folder}")
    else:
        log_message("No 'static/assets' folder found to delete.")

def check_path_type(path):
    if path.startswith("#") or path in ["true", "false"]:
        return None
    result = urllib.parse.urlparse(path)
    if result.scheme:
        return "online"
    elif re.match(r"^(\/|\w:)", path):
        return "absolute"
    elif re.match(r"^(?!\/)(?!([A-Za-z]:\\)).*", path):
        return "relative"
    else:
        return "no_path"

def make_valid_function(s):
    s = re.sub(r'[^0-9a-zA-Z_]+', '_', s)
    s = re.sub(r'^_+', '', s)
    if not s or s[0].isdigit():
        s = '_' + s
    return s

def href_changer(tag):
    if 'href' in tag.attrs and check_path_type(tag['href']) != "online":
        if "#" in tag['href']:
            return
        if tag['href'].startswith("/") and tag['href'].endswith(".html"):
            name = make_valid_function(tag['href'].replace(".html", ""))
            tag['href'] = f"{{{{ url_for('{name}') }}}}"
        elif tag['href'].endswith(".html"):
            name = make_valid_function(tag['href'].replace(".html", ""))
            tag['href'] = f"{{{{ url_for('{name}') }}}}"
        else:
            tag['href'] = f"{{{{ url_for('static', filename='{tag['href']}') }}}}"

def src_changer(tag):
    if 'src' in tag.attrs and check_path_type(tag['src']) != "online" and not "{{" in tag['src']:
        tag['src'] = f"{{{{ url_for('static', filename='{tag['src']}') }}}}"

def convert_links(soup):
    for tag in soup.find_all(href=True):
        href_changer(tag)
    for tag in soup.find_all(src=True):
        src_changer(tag)

def convert_background_urls(soup):
    for tag in soup.find_all(style=True):
        tag['style'] = re.sub(r'url\(["\']?([^"\')]+)["\']?\)',
                               r'url("{{ url_for("static", filename="\1") }}")',
                               tag['style'])

def convert_to_jinja(folder):
    log_message(f"Starting Jinja conversion in folder: {folder}")
    for root, _, files in os.walk(folder):
        for file in files:
            if not file.endswith('.html'):
                continue
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            convert_links(soup)
            convert_background_urls(soup)
            body = soup.find("body")
            if body:
                body.insert_before("{% block content %}")
                body.insert_after("{% endblock content %}")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(soup.prettify().replace("/assets/", "").replace("{{ url_for('static', filename='/') }}", "{{ url_for('index') }}"))
    if not config['export_template_code']:
        return
    main_py_content = """from flask import Flask, render_template
app = Flask(__name__)
"""
    for file in files:
        if file.endswith('.html'):
            route_name = file.replace('.html', '')
            function_name = make_valid_function(route_name)
            if route_name == "index-app" or route_name == "index":
                main_py_content += "\n@app.route('/')"
                function_name = "index"
            else:
                main_py_content += f"\n@app.route('/{route_name}')"
            main_py_content += f"""
def {function_name}():
    return render_template('{file}')
"""
    main_py_content += """
if __name__ == '__main__':
    app.run(debug=True)
"""
    with open(os.path.join(folder, 'template_main.py'), 'w', encoding='utf-8') as f:
        f.write(main_py_content)
    log_message("Generated Flask main file: template_main.py")

def convert_flask(source_path):
    flask_path = copy_source_to_flask(source_path)
    move_html_files_and_rename_assets(flask_path)
    convert_to_jinja(flask_path)
    log_message("Flask conversion completed.")

def main():
    if len(sys.argv) < 2:
        log_message("No parameter provided.")
    else:
        convert_flask(sys.argv[1])

if __name__ == "__main__":
    main()
