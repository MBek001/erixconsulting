from flask import Flask, redirect, url_for, render_template, session, request, send_from_directory , jsonify

app = Flask(__name__)


@app.route('/img/icon/<filename>')
def get_image_home(filename):
    return send_from_directory('/static/img/icon', filename)


@app.route('/')
def home():
    return render_template('index_uz.html')


@app.route('/ru')
def home_ru():
    return render_template('index_ru.html')


@app.route('/en')
def home_en():
    return render_template('index_en.html')


if __name__ == '__main__':
    app.run(debug=True)




