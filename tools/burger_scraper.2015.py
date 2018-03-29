import urllib2
import json
from bs4 import BeautifulSoup
import os
import urlparse

burger_path = os.path.realpath(os.curdir) + '/burger_images'
if not os.path.exists(burger_path):
    os.makedirs(burger_path)

base_url = "http://peiburgerlove.ca/"

def grab_from_generator(generator, place):
    for n in range(0, place):
        generator.next()
    return generator.next()

def extract_coords_from_url(url):
    parsed_url = urlparse.urlparse(url)
    if parsed_url.query:
        parsed_qs = urlparse.parse_qs(parsed_url.query)
        coords = parsed_qs['sll'][0].split(',')
    else:
        url_parts = parsed_url.path.split('/')
        coords = url_parts[4]
        coords = coords[1:-1].split(',')
    return { 'latitude': coords[0], 'longitude': coords[1] }

def save_burger_image(url):
    image = urllib2.urlopen(url)
    parsed_url = urlparse.urlparse(url)
    url_parts = parsed_url.path.split('/')
    image_name = url_parts[2] + ".png"
    local_path = 'burger_images/' + image_name
    local_image = open(local_path, 'w')
    local_image.write(image.read())
    local_image.close()
    return { 'image_path': local_path, 'id': url_parts[2] }

def use_witchcraft_to_messily_divine_an_ingredient_list(ingredient_string):
    if ' on a ' in ingredient_string:
        separated_ingredients = ingredient_string.split(' on a ')
        messy_ingredient_list = separated_ingredients[0].split(', ')
        not_messy_ingredient_list = []
        for ingredient in messy_ingredient_list:
            if ingredient.startswith("and "):
                not_messy_ingredient_list.append(ingredient[4:])
            elif " and " in ingredient:
                not_messy_ingredient_list.extend(ingredient.split(" and "))
            else:
                not_messy_ingredient_list.append(ingredient)
        return { 'ingredients': not_messy_ingredient_list, 'bun': separated_ingredients[1] }
    elif ' nestled between ' in ingredient_string:
        '''
        This takes care of an edge case with the Frosty Treat entry (damn you and your weird ice cream sandwich burger!)
        '''
        return { 'ingredients': ['5oz. Island Beef Patty', 'Bacon', 'Maple Syrup', 'Marshmallow', 'Maraschino Cherry'], 'bun': 'two Ice Cream Sandwiches' }

def split_string_on_one_of_several_strings(string, split_types):
    '''
    Because OS-X vs. Windows weirdness
    '''
    for split_type in split_types:
        if split_type in string:
            new_list = map(unicode.strip, string.split(split_type))
            return new_list
    return [string]

urls = [
    'http://peiburgerlove.ca/burger/21-Breakwater-Restaurant',
    'http://peiburgerlove.ca/burger/Ansons-Restaurant',
    'http://peiburgerlove.ca/burger/Big-Burger',
    'http://peiburgerlove.ca/burger/BOOMburger',
    'http://peiburgerlove.ca/burger/Brits-Fish-And-Chips',
    'http://peiburgerlove.ca/burger/Brothers-2',
    'http://peiburgerlove.ca/burger/Budleys',
    'http://peiburgerlove.ca/burger/Casa-Mia-Cafe',
    'http://peiburgerlove.ca/burger/Cedars-Eatery',
    'http://peiburgerlove.ca/burger/Chambers',
    'http://peiburgerlove.ca/burger/Claddagh-Oyster-House',
    'http://peiburgerlove.ca/burger/Cornwall-Pizza-Delight',
    'http://peiburgerlove.ca/burger/Downtown-Deli',
    'http://peiburgerlove.ca/burger/Dundee-Arms-Inn',
    'http://peiburgerlove.ca/burger/East-Side-Marios',
    'http://peiburgerlove.ca/burger/Edens-Gate',
    'http://peiburgerlove.ca/burger/Five-Eleven-West',
    'http://peiburgerlove.ca/burger/Frosty-Treat',
    'http://peiburgerlove.ca/burger/Gahan-House',
    'http://peiburgerlove.ca/burger/Gentleman-Jims',
    'http://peiburgerlove.ca/burger/Hunters-Ale-House',
    'http://peiburgerlove.ca/burger/Ladys-Slipper-Cafe',
    'http://peiburgerlove.ca/burger/Main-Street-Pub',
    'http://peiburgerlove.ca/burger/Mavors',
    'http://peiburgerlove.ca/burger/The-Merchantman-Pub',
    'http://peiburgerlove.ca/burger/Nightcap',
    'http://peiburgerlove.ca/burger/Osheas-Pub-Eatery',
    'http://peiburgerlove.ca/burger/Olde-Dublin-Pub',
    'http://peiburgerlove.ca/burger/Outriders-Cookhouse',
    'http://peiburgerlove.ca/burger/Papa-Joes',
    'http://peiburgerlove.ca/burger/Peakes-Tee',
    'http://peiburgerlove.ca/burger/PEI-Brewing-Company',
    'http://peiburgerlove.ca/burger/Phinleys-Diner',
    'http://peiburgerlove.ca/burger/Piatto',
    'http://peiburgerlove.ca/burger/Pizza-Delight-1911-Jail',
    'http://peiburgerlove.ca/burger/Pizza-Delight-Summerside',
    'http://peiburgerlove.ca/burger/The-Prince-Edward-Restaurant',
    'http://peiburgerlove.ca/burger/Quality-Inn-On-The-Hill',
    'http://peiburgerlove.ca/burger/Razzys-Roadhouse',
    'http://peiburgerlove.ca/burger/Reds-Corner',
    'http://peiburgerlove.ca/burger/Redwater-Rustic-Grille',
    'http://peiburgerlove.ca/burger/Riverside-Diner',
    'http://peiburgerlove.ca/burger/Row-House',
    'http://peiburgerlove.ca/burger/Sams-Restaurant',
    'http://peiburgerlove.ca/burger/Sims-Corner',
    'http://peiburgerlove.ca/burger/Smittys',
    'http://peiburgerlove.ca/burger/Terre-Rouge',
    'http://peiburgerlove.ca/burger/The-Bay-Restaurant',
    'http://peiburgerlove.ca/burger/The-Brickhouse',
    'http://peiburgerlove.ca/burger/The%20Factory%20Cookhouse',
    'http://peiburgerlove.ca/burger/The-Home-Place',
    'http://peiburgerlove.ca/burger/The-Landing-Oyster-House',
    'http://peiburgerlove.ca/burger/The-Loyalist-Country-Inn',
    'http://peiburgerlove.ca/burger/Maple-Grille',
    'http://peiburgerlove.ca/burger/The-Old-Triangle',
    'http://peiburgerlove.ca/burger/The-Pilot-House',
    'http://peiburgerlove.ca/burger/The-Whiskey-Pub-Kitchen',
    'http://peiburgerlove.ca/burger/Turfs-Bar-And-Grill',
    'http://peiburgerlove.ca/burger/Water-St-Fish-And-Chips',
    'http://peiburgerlove.ca/burger/Waters-Edge'
]

completed_list = []
for url in urls:
    list_item = {}
    urls = {}
    page = urllib2.urlopen(url).read()
    parsed_page = BeautifulSoup(page)
    urls['burger_page'] = url
    urls['vote_page'] = base_url + parsed_page.find(id="Rate-Button")['href']
    company_website = parsed_page.find(class_="website-link")
    if company_website:
        urls['company_website'] = company_website['href']
    else:
        urls['company_website'] = False
    list_item['urls'] = urls
    list_item['burger_name'] = grab_from_generator(parsed_page.find(id="Burger-Title").stripped_strings, 0)
    list_item['restaurant_name'] = parsed_page.find(id="Restaurant-Name").string
    list_item['burger_quote'] = grab_from_generator(parsed_page.find(id="Burger-Quote").stripped_strings, 1)
    burger_map_url = parsed_page.find(class_="burger-map")
    list_item['coordinates'] = extract_coords_from_url(burger_map_url['href'])
    burger_image = save_burger_image(base_url + parsed_page.find(id="Burger-Img").img['src'])
    list_item['id'] = burger_image['id']
    list_item['image_path'] = burger_image['image_path']
    list_item['ingredients'] = use_witchcraft_to_messily_divine_an_ingredient_list(grab_from_generator(parsed_page.find(id="Ingredients").stripped_strings, 0))
    address_parts = unicode(parsed_page.find(class_="burger-address"))
    address_parts = address_parts[36:-7]
    address_parts = split_string_on_one_of_several_strings(address_parts, ['<br/>\n<br/>\r\n', '<br/>\n<br/>\n'])
    list_item['address'] = split_string_on_one_of_several_strings(address_parts[0], ['<br/>\r\n', '<br/>\n'])
    '''
    I don't even know which restaurant needs this fix, just don't worry about it.
    '''
    if "Opening April 3rd!" in address_parts[1]:
        list_item['hours_of_operation'] = split_string_on_one_of_several_strings(address_parts[2], ['<br/>\r\n', '<br/>\n'])
        list_item['phone_number'] = address_parts[3][:18]
    else:
        list_item['hours_of_operation'] = split_string_on_one_of_several_strings(address_parts[1], ['<br/>\r\n', '<br/>\n'])
        list_item['phone_number'] = address_parts[2][5:18]
    completed_list.append(list_item)
    print "Added " + list_item['restaurant_name']

f = open('2015.json', 'w')
json.dump(completed_list, f)
