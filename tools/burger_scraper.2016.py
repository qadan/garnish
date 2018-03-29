import urllib2
import json
from bs4 import BeautifulSoup
import os
import urlparse
import sqlite3
from pprint import PrettyPrinter

pp = PrettyPrinter(indent=4)

burger_path = os.path.realpath(os.curdir) + '../burger_images'
if not os.path.exists(burger_path):
    os.makedirs(burger_path)

base_url = "http://peiburgerlove.ca/"

def grab_from_generator(generator, place):
  for n in range(0, place):
      generator.next()
      return generator.next()

def extract_coords_from_url(url):
    parsed_url = urlparse.urlparse(url)
    url_parts = parsed_url.path.split('/')
    coords = url_parts[4]
    coords = coords[1:-1].split(',')
    return { 'latitude': coords[0], 'longitude': coords[1] }

def save_burger_image(url, suffix):
    try:
        image = urllib2.urlopen(url)
    except:
        print url + " should be " + suffix + ".png"
        return None
    parsed_url = urlparse.urlparse(url)
    url_parts = parsed_url.path.split('/')
    image_name = suffix + ".png"
    local_path = '../burger_images/' + image_name
    local_image = open(local_path, 'w')
    local_image.write(image.read())
    local_image.close()
    return { 'image_path': local_path, 'id': url_parts[2] }

def split_string_on_one_of_several_strings(string, split_types):
    '''
    Because OS-X vs. Windows weirdness
    '''
    for split_type in split_types:
        if split_type in string:
            new_list = map(unicode.strip, string.split(split_type))
            return new_list
    return [string]

def get_address_bits(address):
  address_bits = []
  address = address.split('\n')
  address.pop(0)
  for line in address:
    if line[:4] == '    ':
      address_bits.append(line.strip())
    else:
      break
  return address_bits

conn = sqlite3.connect('/Users/DTM-2/gits/qadan.github.io/pytools/garnish/garnish.db')
cur = conn.cursor()
main = urllib2.urlopen('http://www.peiburgerlove.ca/restaurants').read()
parsed_main = BeautifulSoup(main, 'html.parser')
restaurants = parsed_main.find_all('li', class_="rl-row")
restaurants.pop(0)
for restaurant in restaurants:
  page_href = restaurant.find('a')['href'].replace(' ', '%20')
  url_suffix = page_href.rsplit('/', 1)[-1]
  burgerpage = BeautifulSoup(urllib2.urlopen('http://www.peiburgerlove.ca/' + page_href).read(), 'html.parser')
  image = burgerpage.find('div', class_="burger-img").img
  burger_image = save_burger_image(image['src'], url_suffix)

  burgerinfo = {
      'name': burgerpage.find('div', id="Burger-Title").text.split('  ')[1].strip(),
      'quote': burgerpage.find('blockquote', id="Burger-Quote").text[2:-2].strip(),
      'ingredients': burgerpage.find('div', id="Ingredients").string.strip(),
      'url_suffix': url_suffix,
  }

  cur.execute('insert into burgers values (?, ?, ?, ?, ?)', [None, burgerinfo['name'], burgerinfo['quote'], burgerinfo['ingredients'], burgerinfo['url_suffix']])
  burger_id = cur.lastrowid

  restaurant_divs = []
  restaurant_ids = []
  restaurant_divs.append(burgerpage.find('div', id="Location"))
  maybe_also = burgerpage.find('div', id="Location2")
  if (maybe_also is not None):
    restaurant_divs.append(maybe_also)

  for restaurant_div in restaurant_divs:
    map_url = burgerpage.find(class_="map-img")
    coords = extract_coords_from_url(map_url['href'])

    restaurantinfo = {
      'name': restaurant_div.find('strong').text,
      'phone_number': restaurant_div.find('div', class_='profile-contact').text[5:18],
      'site_id': url_suffix,
      'website': restaurant_div.find('a', class_='website-link')['href'],
      'latitude': coords['latitude'],
      'longitude': coords['longitude'],
      'address': json.dumps(get_address_bits(burgerpage.find(class_="location-address").strong.next_sibling.text)),
      'hours_of_operation': json.dumps([line.strip() for line in burgerpage.find(class_="profile-hours").text.splitlines()]),
    }

    cur.execute('insert into restaurants values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [None, restaurantinfo['name'], restaurantinfo['phone_number'], restaurantinfo['address'], restaurantinfo['hours_of_operation'], None, restaurantinfo['latitude'], restaurantinfo['longitude'], restaurantinfo['website'], restaurantinfo['site_id']])
    restaurant_ids.append(cur.lastrowid)

  for restaurant_id in restaurant_ids:
    cur.execute('insert into restaurant_burgers values (?, ?, ?)', [None, burger_id, restaurant_id])

conn.commit()
conn.close()
