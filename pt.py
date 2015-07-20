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

def get_online_users():
    try:
        current = int(time.time()) // 60
        minutes = xrange(6)
        sv = ('{}'.format([(current - x) for x in minutes]))
        print('sv: {}'.format(sv))
        #svalue = redis.sunion('online-users/{}'.format((current)))
        svalue = redis.sunion('online-users/*')
        #svalue = redis.sunion('online-users/{}'.format([(current - x) for x in xrange(6)]))
        print('debug : online_users {}'.format(svalue))
        return svalue
    except Exception as ret:
        print('exception : {}'.format(redis.keys()))
        keys = redis.keys('*')
        for key in keys:
            if redis.type(key) is 'KV':
                print(redis.get(key))
        return('poop')

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

@app.route('/activity')
def active():
    '''
    get last users
    '''
    return 'activity {}'.format(get_user_last_activity(request.remote_addr))
