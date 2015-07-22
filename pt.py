from datetime import datetime
import time
from flask import Flask, request
from redis import Redis

ONLINE_LAST_MIN = 6

app = Flask(__name__)
app.debug = True

app.config['REDIS_HOST'] = '127.0.0.1'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_DB'] = 0

#redis = Redis(app)
redis = Redis()

def mark_online(uid=None):
    try:
        now = int(time.time())
        expires = now + (360)
        all_users_key = 'online-users/{}'.format(now)
        print('debug all_users_key {}'.format(all_users_key))
        user_key = 'user-activity/{}'.format(uid)
        p = redis.pipeline()
        p.sadd(all_users_key, uid)
        p.set(user_key, now)
        p.expireat(all_users_key, expires)
        p.expireat(user_key, expires)
        print('debug user_key {}'.format(user_key))
        p.execute()
    except Exception as error:
        print('debug: mark_online err {}'.format(error))

def get_user_last_activity(uid):
    last_active = redis.get('user-activity/{}'.format(uid))
    if last_active is None:
        return None
    return datetime.utcfromtimestamp(int(last_active))

@app.route('/')
def index():
    '''
    let's show something
    '''
    mark_online(request.remote_addr)
    return '<a href="/activity">Hello</a> from Flask! {}+{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                            request.remote_addr)

@app.route('/activity')
def active():
    '''
    get last users
    '''
    return '<a href='/'>activity</a> of visitors {}'.format(get_user_last_activity(request.remote_addr))
