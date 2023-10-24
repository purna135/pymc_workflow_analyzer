from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        report = ''
        return render_template('index.html' , report = report)

if __name__ == '__main__':
    app.run(debug=True)
