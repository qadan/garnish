import sqlite3
import os
from functools import wraps
from json import loads
from flask import Flask, request, g, jsonify
from datetime import datetime, timedelta
from yaml import load

'''
Configuration options. Change these later (environment variables?).
'''
config_file = os.environ.get('GARNISH_CONFIG', os.path.dirname(os.path.realpath(__file__)) + '/garnish_config.yaml')
if not os.path.isfile(config_file):
    print('Failed to load config file; there should be a garnish_config.yaml paired with garnish.py, or one should be provided at GARNISH_CONFIG.')
    exit(1)
with open(config_file, 'r') as loaded_config:
    config = load(loaded_config)

DATABASE = config['database']
DEBUG = config['debug']

garnish = Flask(__name__)
garnish.config.from_object(__name__)


'''
Invalid things exceptions.
'''
class InvalidRequestException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload


    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


'''
Database connection/utils
'''
def make_dicts(cursor, row):
    json_indices = [
        'address',
        'hours_of_operation',
    ]
    return dict((cursor.description[idx][0], loads(value) if cursor.description[idx][0] in json_indices else value) for idx, value in enumerate(row))


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(garnish.config['DATABASE'])
        db.row_factory = make_dicts
    return db


def query_db(query, args=(), one=True):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@garnish.before_request
def before_request():
    g.db = get_db()


@garnish.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


'''
Helpers.
'''
@garnish.errorhandler(InvalidRequestException)
def handle_invalid_request(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def jsonp(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            data = str(func(*args, **kwargs).data)
            content = str(callback) + '(' + data + ')'
            mimetype = 'application/javascript'
            return garnish.response_class(content, mimetype=mimetype)
        else:
            return func(*args, **kwargs)
    return decorated_function


def now_is_within_time_ranges(weekday_times, offset):
    if weekday_times is None:
      return False

    try:
      offset = int(offset)
    except ValueError:
      offset = 0
    now = datetime.now() + timedelta(hours=offset)
    for weekday_time in weekday_times:
      start_time = datetime.now().replace(hour=weekday_time['start_time']['h'], minute=weekday_time['start_time']['m'], second=0, microsecond=0)
      if weekday_time['end_time']['h'] < weekday_time['start_time']['h']:
        end_day = start_time.day + 1
      else:
        end_day = start_time.day
      end_time = datetime.now().replace(day=end_day, hour=weekday_time['end_time']['h'], minute=weekday_time['end_time']['m'], second=0, microsecond=0)
      if now > start_time and now < end_time:
        return True

    return False


'''
Main routes.
'''
@garnish.route('/')
@jsonp
def rest_info():
    with open(os.path.dirname(os.path.realpath(__file__)), 'r') as rest_info:
        return jsonify(rest_info.read())


@garnish.route('/burgers')
@jsonp
def get_all_burgers():
    burgers = query_db('select * from burgers', one=False)
    burgers = {
        'burgers': burgers
    }
    return jsonify(burgers)


@garnish.route('/burger/<int:id>')
@jsonp
def get_burger_info(id):
    properties = query_db('select * from burgers where id = ?', [id])
    if properties is not None:
        restaurants = query_db('select restaurant_id from restaurant_burgers where burger_id = ?', [id], one=False)
        properties['restaurants'] = [r['restaurant_id'] for r in restaurants]
        return jsonify(properties)
    else:
        raise InvalidRequestException('The given ID does not exist.')


@garnish.route('/burger/<int:id>/restaurants')
@jsonp
def get_restaurants_for_burger(id):
    restaurants = query_db('select restaurant_id from restaurant_burgers where burger_id = ?', [id], one=False)
    if restaurants is not None:
        restaurants = {
            'restaurants': restaurants
        }
        return jsonify(restaurants)
    else:
        raise InvalidRequestException('No restaurants found for this burger.')


@garnish.route('/restaurants')
@jsonp
def get_all_restaurants():
    restaurants = query_db('select * from restaurants', one=False)
    restaurants = {
        'restaurants': restaurants
    }
    return jsonify(restaurants)


@garnish.route('/restaurant/<int:id>')
@jsonp
def get_restaurant_info(id):
    properties = query_db('select * from restaurants where id = ?', [id])
    if properties is not None:
        burgers = query_db('select burger_id from restaurant_burgers where restaurant_id = ?', [id], one=False)
        properties['burgers'] = [b['burger_id'] for b in burgers]
        return jsonify(properties)
    else:
        raise InvalidRequestException('The given ID does not exist.')


@garnish.route('/restaurant/<int:id>/partners')
@jsonp
def get_restaurant_partners(id):
    ''' Some restaurants may team up to create the same burger; handle that.'''
    burger = query_db('select burger_id from restaurant_burgers where restaurant_id = ?', [id])
    if burger is not None:
        partners = query_db('select restaurant_id from restaurant_burgers where burger_id = ? and restaurant_id != ?', [burger['burger_id'], id], one=False)
        partners = {
            'partners': partners
        }
        return jsonify(partners)
    else:
        raise InvalidRequestException('The given ID does not exist.')


@garnish.route('/coordinates')
@jsonp
def get_all_restaurant_coordinates():
    coordinates = query_db('select id, name, latitude, longitude from restaurants', one=False)
    coordinates = {
        'coordinates': coordinates,
    }
    return jsonify(coordinates)


@garnish.route('/coordinates/open')
@jsonp
def get_all_open_restaurant_coordinates():
    offset = request.args.get('offset', default=0)
    coordinates = query_db('select id, name, latitude, longitude, hours_table from restaurants', one=False)
    coordinates_to_return = {
        'coordinates': [],
    }
    weekday = datetime.now().weekday()
    for coordinate in coordinates:
      hours_table = loads(coordinate['hours_table'])
      try:
        if now_is_within_time_ranges(hours_table[str(weekday)], offset):
          coordinates_to_return['coordinates'].append(coordinate)
      except KeyError:
        continue

    return jsonify(coordinates_to_return)


@garnish.route('/search')
@jsonp
def search():
    '''
    TODO: This is just awful but it's like 3 AM.
    '''
    results = {}
    ids = []
    i = 0;
    search_term = "%" + '%'.join(request.args.getlist('term')) + '%'

    from_restaurants = query_db('select id, latitude, longitude from restaurants where name like ? or address like ?', [search_term, search_term], one=False)
    for restaurant in from_restaurants:
        if restaurant['id'] not in ids:
            results[i] = {
                'id': restaurant['id'],
                'latitude': restaurant['latitude'],
                'longitude': restaurant['longitude'],
            }
            ids.append(restaurant['id'])
            i = i + 1

    from_burgers = query_db('select distinct id from burgers where name like ? or quote like ? or ingredients like ?', [search_term, search_term, search_term], one=False)
    for burger in from_burgers:
        burger_restaurants = query_db('select restaurant_id from restaurant_burgers where burger_id = ?', [burger['id']], one=False)
        for new_restaurant in burger_restaurants:
            if new_restaurant['restaurant_id'] not in ids:
                new_info = query_db('select latitude, longitude from restaurants where id = ?', [new_restaurant['restaurant_id']])
                results[i] = {
                    'id': new_restaurant['restaurant_id'],
                    'latitude': new_info['latitude'],
                    'longitude': new_info['longitude'],
                }
                ids.append(new_restaurant['restaurant_id'])
                i = i + 1

    return jsonify(results)


'''
Aaaaaaaand go.
'''
if __name__ == '__main__':
    garnish.run(host='0.0.0.0')
