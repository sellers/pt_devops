from datetime import datetime
import time
from flask import Flask, request
from flask_redis import Redis

ONLINE_LAST_MIN = 6

app = Flask(__name__)
app.debug = True

app.config['REDIS_HOST'] = 'localhost'
app.config['REDIS_PORT'] = 6379
app.config['REDIS_DB'] = 0

redis = Redis(app)

def mark_online(addr='null'):
    now = int(time.time())
    expires = now + (360)
    all_users_key = 'online-users/{}'.format(now)
    print('debug {}'.format(all_users_key))
    user_key = 'user-activity/{}'.format(request.remote_addr)
    p = redis
    p.sadd(all_users_key, request.remote_addr)
    p.set(user_key, now)
    p.expireate(all_users_key, expires)
    p.expireat(user_key, expires)
    p.execute()

def get_user_last_activity(user_id):
    last_active = redis.get('user-activity/{}'.format(request.remote_addr))
    if last_active is None:
        return None
    return datetime.utcfromtimestamp(int(last_active))

def get_online_users():
    current = int(time.time()) // 60
    minutes = xrange(6)
    return redis.sunion([('online-users/{}'.format(current -x)) for x in minutes])


@app.route('/')
def index():
    '''
    let's show something
    '''
    mark_online(request.remote_addr)
    return 'Hello from Flask! {}+{}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                            request.remote_addr)

@app.route('/users')
def users():
    '''
    list the visitors
    '''
    return 'online {}'.format(get_online_users())
