import hashlib
import os
from app import app
from flask import render_template, request, redirect, url_for, make_response, send_file, jsonify
from .utils import analyze_file

@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html', nma = 'asd')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        f = request.files.get('data')

        if True or f.content_type == 'text/csv':
            result_filename = 'result%s.xlsx' % hashlib.md5(f.filename.encode('utf-8')).hexdigest()
            result_filename = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)

            try: results = analyze_file(f, result_filename)
            except:
                return make_response(jsonify({
                    'error' : True,
                    'msg'    : 'При обработке файла произошла ошибка, убедитесь в корректности данных'
                }))

            if not 'error' in results:

                return make_response(jsonify({
                    'success' : True,
                    'html'    : render_template('result.html', **results)
                }))
            else:
                return make_response(jsonify({
                    'error' : True,
                    'msg'    : results["msg"]
                }))

        else:
            return make_response(jsonify({
                'error' : True,
                'msg'    : 'Неверный тип файла'
            }))


    return redirect(url_for('index'))

@app.route('/download/<filename>')
def downloadFile (filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(path, as_attachment=True)
