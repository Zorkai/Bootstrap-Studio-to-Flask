# Bootstrap-Studio-to-Flask
Converts an exported Bootstrap Studio project into a Flask-ready structure

## 🚀 Usage
- In Bootstrap Studio, use the `export.bat` file as your export script.
<img src="https://github.com/user-attachments/assets/5cb5305b-7e9f-4517-abaa-6e08e928e8d9" width="500" height="328">

- **Export your project from Bootstrap Studio.** ✅
 
## ✨ Features
- Copies the original project into a new folder for Flask conversion
- Moves HTML files to a templates/ folder
- Renames the assets/ folder to static/
- Converts internal links (href, src, background-image URLs) to url_for()
- Adds Jinja {% block content %} for templating
- Generates a template_main.py file with Flask routes
- Uses a config.toml file for easy customization

## 📂 Folder Structure After Conversion
```php
project-Flask/
│── templates/      # All HTML files moved here (converted to Jinja)
│── static/         # Assets (CSS, JS, images) moved here
│── template_main.py # Flask app with auto-generated routes
└── python_log.txt  # Log file for debuggin
```

## ⚙️ Configuration (config.toml)
Before running the script, set your project path in config.toml:
```toml
flask_folder_suffix = "-Flask"
export_template_code = false
```
