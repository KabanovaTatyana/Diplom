import os
from flask import Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.dirname(os.path.abspath(__file__)) + '/tmp'

from . import views
