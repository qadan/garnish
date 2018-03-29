# Garnish

Garnish is a python webserver, written using Flask, that acts as a request API for burger information to be used with BATT.

## Installation

Garnish requires the following modules to run:

* flask
* sqlite3
* pyyaml

Consider installing all of these in a python virtual environment

## Setup

Before running the server for the first time, `garnish.db` has to be generated and populated.

### Generating `garnish.db`

The `garnish.db` file can be generated using `schema.sql`; the easiest way of doing this is probably just:

```bash
schema.sql > sqlite3 garnish.db
```

This will create an empty `garnish.db` ready to be populated with burgers and restaurants.

### Populating `garnish.db`

`garnish.db` can be populated by hand, but it's easier to use one of the burger scrapers in the `tools` folder (corresponding to the year, of course). These won't create a perfect database, but it'll get close enough to be able to do some tweaking.

The date fields can be populated using the `date_mapping_helper.py` in the tools folder. This will largely have to happen by hand using the prompts.

## Usage

Check that the information in `garnish_config.yaml` is correct. You may want to set `debug` to `False` in production.

The path to an alternate configuration yaml can be specified with the `GARNISH_CONFIG` environment variable; however, this gets complicated with any setup more complicated thanything than a command-line WSGI setup.

### Apache's `mod_wsgi` - the easy way

Simplest way to get this set up is probably using Apache with `mod_wsgi`, since Apache is probably where the webserver using Garnish is going to be set up:

```bash
sudo apt-get install libapache2-mod-wsgi
```

Modify the sites file being used in `/etc/apache2/sites-available` to contain references to both servers (expecting Garnish to live in `/usr/bin/garnish` and the webserver to live in `/var/www/html`):

```xml
<VirtualHost *:80>
  # Standard webserver stuffs go in here
  ServerName meatadata.info
  DocumentRoot /var/www/html
</VirtualHost>
<VirtualHost *:5432>
  WSGIDaemonProcess garnish user=ubuntu group=ubuntu threads=5
  WSGIScriptAlias / /usr/bin/garnish/garnish.wsgi
  <Directory /usr/bin/garnish>
      WSGIProcessGroup garnish
      WSGIApplicationGroup %{GLOBAL}
      Order deny,allow
      Allow from all
  </Directory>
</VirtualHost>
```

### Routes

All the routes can be found at the root of the site, which returns a JSON descriptive representation of the API.
