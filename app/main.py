from flask import Flask, request
from pymongo import MongoClient
from functools import wraps
import jwt
import requests
from hashlib import sha256
from os import urandom
from time import time
import json
from bs4 import BeautifulSoup
from bs4.element import Comment
from collections import defaultdict

client = MongoClient(host='mongo')
db = client.wordcount
app = Flask(__name__)
recaptcha_secret = '<recaptcha_secret_key>'
hostname = '<example.com>'
jwt_secret = '<jwt_secret>'


def validate_recaptcha(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.json.get('token', None)
        if not token:
            return 'Invalid token', 400
        res = requests.post('https://www.google.com/recaptcha/api/siteverify',
                            data=dict(secret=recaptcha_secret, response=token)).json()
        if res['success'] and res['hostname'] == hostname and res['score'] >= 0.5:
            return func(*args, **kwargs)
        else:
            return 'Invalid token', 400

    return wrapper


def get_jwt_payload(token):
    try:
        return jwt.decode(token, jwt_secret, algorithms='HS256')
    except (jwt.exceptions.InvalidTokenError,
            jwt.exceptions.DecodeError,
            jwt.exceptions.InvalidSignatureError,
            jwt.exceptions.ExpiredSignatureError,
            jwt.exceptions.InvalidKeyError,
            AttributeError, KeyError):
        return None


def authorized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'Authorization' not in request.headers:
            return '', 401
        jwt_payload = get_jwt_payload(request.headers['Authorization'])
        if jwt_payload:
            kwargs['user_email'] = jwt_payload['email']
            return func(*args, **kwargs)
        else:
            return '', 401

    return wrapper


def throttling(amount=20, time_frame=60, success_key=None):
    """
(Denial-of-Service protection)
Blocks an ip from accessing a method if it reaches the amount of requests in a given time frame.
The counter resets if the success key is inside the returned value from the method.
The info is kept in an in-memory dictionary, so it resets between lambda instances.
    :param amount: the maximum amount of requests allowed for an ip per time_frame.
    :param time_frame: the time frame for the amount of requests (in seconds).
    :param success_key: a value that is returned inside successful requests to the method.
    :return: 429 TOO_MANY_REQUESTS if ip is blocked or the value of the method if not.
    """
    access_cache = defaultdict(list)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            time_now = time()
            access_data = access_cache[request.remote_addr]
            if len(access_data) == amount:
                if time_now - access_data[0] <= time_frame:
                    return '', 429
                else:
                    access_data.append(time_now)
                    access_data.remove(access_data[0])
            else:
                access_data.append(time_now)
            result = func(*args, **kwargs)
            try:
                if success_key and success_key in result:
                    access_cache.pop(request.remote_addr, None)
            except TypeError:
                pass
            return result

        return wrapper

    return decorator


@app.route('/register', methods=['POST'])
@validate_recaptcha
def register():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    if not (email and password) or not (isinstance(email, str) and isinstance(password, str)):  # empty str or not str
        return '', 400

    if not db.users.find_one({'email': email}):
        salt = urandom(16)
        db.users.insert_one({
            'email': email,
            'salt': salt,
            'password_hash': sha256(password.encode() + salt).hexdigest()
        })
        return jwt.encode({'email': email}, jwt_secret, algorithm='HS256').decode()
    else:
        return 'User exists', 400


@app.route('/login', methods=['POST'])
@validate_recaptcha
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    if not (email and password) or not (isinstance(email, str) and isinstance(password, str)):  # empty str or not str
        return '', 400

    user = db.users.find_one({'email': email})
    if user and user['password_hash'] == sha256(password.encode() + user['salt']).hexdigest():
        return jwt.encode({'email': email}, jwt_secret, algorithm='HS256').decode()
    else:
        return '', 401


def is_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True


def get_visible_texts(body):
    soup = BeautifulSoup(body, 'html.parser')
    texts = soup.findAll(text=True)
    return (tag.strip().lower() for tag in texts if is_visible(tag))


@app.route('/word_count', methods=['POST'])
@authorized
@throttling()
def word_count(user_email=None):
    url = request.json.get('url', None)
    words = request.json.get('words', None)
    if not (isinstance(url, str) and isinstance(words, list)):
        return '', 400
    if not url.startswith('http'):
        url = 'http://' + url
    words_count = dict(zip((word.lower() for word in words), [0] * len(words)))
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return 'Bad url', 400
        html_page = response.content
        for text in get_visible_texts(html_page):
            for word in text.split():
                if word in words_count:
                    words_count[word] += 1
        db.history.insert_one({
            'user': user_email,
            'timestamp': int(time()),
            'url': url,
            'results': words_count
        })
        return json.dumps(words_count)

    except requests.exceptions.RequestException:
        return 'Bad url', 400


if __name__ == '__main__':
    app.run()
