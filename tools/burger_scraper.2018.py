from urllib.request import Request, urlopen
from urllib.parse import urlparse
import json
from bs4 import BeautifulSoup
import os
import sys
import sqlite3
from pprint import PrettyPrinter

def validate():
    if len(sys.argv) < 2:
        print('Not enough arguments. Usage: python3 burger_scraper_2018.py destination.db')
        exit(1)


def grab_from_generator(generator, place):
  for n in range(0, place):
      generator.next()
      return generator.next()


def extract_coords_from_url(url):
    parsed_url = urlparse(url)
    url_parts = parsed_url.path.split('/')
    coords = url_parts[4]
    coords = coords[1:-1].split(',')
    return { 'latitude': coords[0], 'longitude': coords[1] }


def save_burger_image(url, suffix):
    parsed_url = urlparse(url)
    url_parts = parsed_url.path.split('/')
    image_name = suffix + ".png"
    local_path = 'burger_images/' + image_name
    local_image = open(local_path, 'wb')
    local_image.write(spoofed_read(url))
    local_image.close()
    return { 'image_path': local_path, 'id': url_parts[2] }


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


def spoofed_read(url):
    # Listen, guys - if you block my user agent, I'll spoof it. If you block my
    # IP, I'll run the scraper from AWS. Heck, I'll manually cURL down each page
    # one at a time and run the scraper against the cached copy. There isn't
    # much use in blocking this tool; you've got a website up to the public-
    # facing internet.
    header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
    request = Request(url, data=None, headers=header)
    url = urlopen(request)
    return url.read()


def scrape():
    validate()
    pp = PrettyPrinter(indent=4)
    burger_path = os.path.realpath(os.curdir) + '/burger_images'
    if not os.path.exists(burger_path):
        os.makedirs(burger_path)
    base_url = "https://peiburgerlove.ca/"
    conn = sqlite3.connect(os.getcwd() + '/' + sys.argv[1])
    cur = conn.cursor()
    try:
        main = spoofed_read(base_url)
    except Exception as e:
        print(str(e))
        return
    parsed_main = BeautifulSoup(main, 'html.parser')
    restaurants = parsed_main.find_all('li')
    for restaurant in restaurants:
      page_href = restaurant.find('a')['href'].replace(' ', '%20')
      url_suffix = page_href.rsplit('/', 1)[-1]
      burgerpage = BeautifulSoup(spoofed_read(base_url + page_href), 'html.parser')
      image = burgerpage.find('img', class_="burger-image")
      save_burger_image(base_url + image['src'], url_suffix)

      title_bit = burgerpage.find('div', id="Burger-Title").text.split('\n')

      burgerinfo = {
          'name': title_bit[0].strip(),
          'quote': burgerpage.find('blockquote', id="Burger-Quote").text[2:-2].strip(),
          'ingredients': burgerpage.find('div', id="Ingredients").string.strip(),
          'url_suffix': url_suffix,
      }

      cur.execute('insert into burgers (name, quote, ingredients, url_suffix) values (?,?,?,?)', [burgerinfo['name'], burgerinfo['quote'], burgerinfo['ingredients'], burgerinfo['url_suffix']])
      burger_id = cur.lastrowid

      restaurant_divs = []
      restaurant_ids = []
      restaurant_divs.append(burgerpage.find('div', class_="location-address"))
      maybe_also = burgerpage.find('div', id="Location2")
      if (maybe_also is not None):
        restaurant_divs.append(maybe_also)

      for restaurant_div in restaurant_divs:
        map_url = burgerpage.find(class_="map-img")
        coords = extract_coords_from_url(map_url['href'])

        restaurantinfo = {
          'name': title_bit[1].strip(),
          'phone_number': restaurant_div.find('div', class_='profile-contact').text[5:18],
          'site_id': url_suffix,
          'website': restaurant_div.find('a', class_='website-link')['href'],
          'latitude': coords['latitude'],
          'longitude': coords['longitude'],
          'address': json.dumps(get_address_bits(burgerpage.find(class_="location-address").strong.next_sibling.text)),
          'hours_of_operation': json.dumps([line.strip() for line in burgerpage.find(class_="profile-hours").text.splitlines()]),
        }

        cur.execute('insert into restaurants (name, phone_number, address, hours_of_operation, latitude, longitude, website) values (?,?,?,?,?,?,?)', [restaurantinfo['name'], restaurantinfo['phone_number'], restaurantinfo['address'], restaurantinfo['hours_of_operation'], restaurantinfo['latitude'], restaurantinfo['longitude'], restaurantinfo['website']])
        restaurant_ids.append(cur.lastrowid)

      for restaurant_id in restaurant_ids:
        cur.execute('insert into restaurant_burgers (burger_id, restaurant_id) values (?,?)', [burger_id, restaurant_id])

    conn.commit()
    conn.close()


if __name__ == '__main__':
    scrape()
