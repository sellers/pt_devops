'''
adopted from flask+redis example
http://flask.pocoo.org/snippets/71/
'''
from datetime import datetime
import time
from flask import Flask, request
from redis import Redis

app = Flask(__name__)
app.debug = True

app.config['REDIS_HOST'] = '127.0.0.1'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_DB'] = 0

#redis = Redis(app)
redis = Redis()

def mark_online(uid=None):
    '''
    add visitors to redis cache
    '''
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
    '''
    display active users in redis cache
    '''
    last_active = redis.get('user-activity/{}'.format(uid))
    if last_active is None:
        return None
    return datetime.utcfromtimestamp(int(last_active))

@app.route('/')
def index():
    '''
    default page and recorder of visitor
    '''
    mark_online(request.remote_addr)
    return('<a href="/activity">Hello</a> from Flask! {}+{}'
          ).format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                   request.remote_addr)

@app.route('/activity')
def active():
    '''
    get last users
    '''
    return('<a href='/'>activity</a> of visitors {}'
          ).format(get_user_last_activity(request.remote_addr))
