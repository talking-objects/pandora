# pan.do/ra - open media archive

  for more information on pan.do/ra visit our website at https://pan.do/ra

## SETUP

  pan.do/ra is known to work with Ubuntu 14.04,
  but other distributions should also work.
  The instructions below are for Ubuntu 14.04.
  All commans given expect that you are root.

  To run pan.do/ra you need to install and setup:

    python
    postgres
    nginx (or apache2)
    additinal video packages


## Installing required packages

1) add pandora ppa to get all packages in the required version

    apt-get install software-properties-common
    add-apt-repository ppa:j/pandora
    apt-get update

2) install all required packages

    apt-get install git subversion mercurial \
            python-setuptools python-pip python-virtualenv ipython \
            python-dev python-pil python-numpy python-psycopg2 \
            python-geoip python-html5lib python-lxml \
            postgresql postgresql-contrib rabbitmq-server \
            poppler-utils mkvtoolnix gpac imagemagick \
            python-ox oxframe ffmpeg


## Prepare Environment

1) add pandora user and set permissions

    adduser pandora --disabled-login --disabled-password

2) Setup Database

    su postgres
    createuser pandora
    createdb  -T template0 --locale=C --encoding=UTF8 -O pandora pandora
    echo "CREATE EXTENSION pg_trgm;" | psql pandora
    exit

3) Setup RabbitMQ

  You have to use the same password here and in BROKER_URL in local_settings.py

    rabbitmqctl add_user pandora PASSWORD
    rabbitmqctl add_vhost /pandora
    rabbitmqctl set_permissions -p /pandora pandora ".*" ".*" ".*"


## Install Pan.do/ra

1) Get code from git

    cd /srv/
    git clone https://git.0x2620.org/pandora.git pandora
    cd pandora
    ./ctl init

    cd /srv
    chown -R pandora.pandora pandora

2) create local_settings.py and config.jsonc

2.1) create file /srv/pandora/pandora/local_settings.py with the following content:

    DATABASES = {
        'default': {
            'NAME': 'pandora',
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'USER': 'pandora',
            'PASSWORD': '',
        }
    }
    DB_GIN_TRGM = True
    BROKER_URL = 'amqp://pandora:PASSWORD@localhost:5672//pandora'

    #with apache x-sendfile or lighttpd set this to True
    XSENDFILE = False

    #with nginx X-Accel-Redirect set this to True
    XACCELREDIRECT = True

2.2) create config.jsonc

  config.jsonc holds the configuration for your site.
  To start you can copy /srv/pandora/pandora/config.pandora.jsonc
  to /srv/pandora/pandora/config.jsonc but have a look at 
  https://wiki.0x2620.org/wiki/pandora/configuration and
  config.0xdb.jsonc config.padma.jsonc for configuration options.

3) initialize database

    su pandora
    cd /srv/pandora/pandora
    ./manage.py init_db

4) install init scripts and start daemons

    /srv/pandora/ctl install
    /srv/pandora/ctl start

5) Setup Webserver
a) nginx (recommended)

    apt-get install nginx
    cp /srv/pandora/etc/nginx/pandora /etc/nginx/sites-available/pandora
    cd /etc/nginx/sites-enabled
    ln -s ../sites-available/pandora

    #read comments in /etc/nginx/sites-available/pandora for setting
    #your hostname and other required settings
    #make sure XACCELREDIRECT = True in /srv/pandora/pandora/local_settings.py
    
    service nginx reload

b) apache2 (if you need it for other sites on the same server)

    apt-get install apache2-mpm-prefork libapache2-mod-xsendfile
    a2enmod xsendfile
    a2enmod proxy_http
    a2enmod proxy_wstunnel
    cp /srv/pandora/etc/apache2/pandora.conf /etc/apache2/sites-available/pandora.conf
    a2ensite pandora

    #read comments in /etc/apache2/sites-available/pandora.conf for setting
    #your hostname and other required settings
    #make sure XSENDFILE = True in /srv/pandora/pandora/local_settings.py
    
    service apache2 reload

  Now you can open pandora in your browser, the first user to sign up will become admin.

##  Updating

  To update pandora to the latest version run this:

    su pandora
    cd /srv/pandora
    ./update.py

  this will update pandora/oxjs/python-ox and list possible upgrades to the db

  to update your database run:

    su pandora
    cd /srv/pandora
    ./update.py db

## Development

  in one terminal:

    ./manage.py runserver 2620

  and background task in another:

    ./manage.py celeryd -B -Q celery,default,encoding -l INFO

  now you can access your local pandora instace at http://127.0.0.1:8000/

  we use virtual machines/lxc for development, you can get a vm from our site
  or use the script in vm/build.sh to create one.
