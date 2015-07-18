from datetime import datetime
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    '''
    let's show something
    '''
    return 'Hello from Flask! (%s)' % datetime.now().strftime('%Y-%m-%d %H:%M:%S')
