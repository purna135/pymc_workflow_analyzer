from flask import Flask, render_template, request
import json
import os
from pymc_workflow_analyzer.analyzer import static_analyzer
from pymc_workflow_analyzer.report import generate_static_report
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-upload limit

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])  # create folder for uploaded files

ALLOWED_EXTENSIONS = {'py', 'ipynb'}
        
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    report = None
    error = None
    url = request.args.get('url')  # Get the URL parameter from the query string
    code = None
    
    if url:
        try:
            analysis_data = static_analyzer(url, source_type="url")
            report = generate_static_report(analysis_data)
        except Exception as e:
            error = str(e)
            
    elif request.method == 'POST':
        code = request.form['code']
        url = request.form['url']
        file = request.files['file']
        filepath = None

        try:
            if file:
                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    analysis_data = static_analyzer(filepath, source_type="file")
                    report = generate_static_report(analysis_data)
                else:
                    error = "Please upload .py or .ipynb file only"
            elif code:
                analysis_data = static_analyzer(code, source_type="code")
                report = generate_static_report(analysis_data)
            elif url:
                analysis_data = static_analyzer(url, source_type="url")
                report = generate_static_report(analysis_data)
            else:
                error = "Please provide a valid input!"
        except Exception as e:
            error = str(e)  # Display the error message to the user
        finally:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)  # Ensure file is deleted if an error occurs.
    
    return render_template('index.html', report=report, error=error, code=code, url=url)


if __name__ == "__main__":
    app.run(debug=True)
