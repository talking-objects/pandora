#!/bin/sh
#fails in bootstrap
apt-get -y install ipython

#ffmpeg
wget http://firefogg.org/nightly/ffmpeg.linux -O /usr/local/bin/ffmpeg
chmod 755 /usr/local/bin/ffmpeg

wget http://firefogg.org/nightly/ffmpeg2theora.linux -O /usr/local/bin/ffmpeg2theora
chmod 755 /usr/local/bin/ffmpeg2theora

#postgresql
apt-get -y install postgresql
sudo -u postgres createuser -S -D -R pandora
sudo -u postgres createdb  -T template0 --locale=C --encoding=UTF8 -O pandora pandora

#rabbitmq
RABBITPWD=$(pwgen -n 16 -1)
rabbitmqctl add_user pandora $RABBITPWD
rabbitmqctl add_vhost /pandora
rabbitmqctl set_permissions -p /pandora pandora ".*" ".*" ".*"

#pandora
cat > /srv/pandora/pandora/local_settings.py << EOF
DATABASES = {
    'default': {
        'NAME': 'pandora',
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'USER': 'pandora',
        'PASSWORD': '',
    }
}

DATA_SERVICE='http://data.0xdb.org/api/'

BROKER_PASSWORD = "$RABBITPWD"

XACCELREDIRECT = True
EOF

cd /srv/pandora/pandora
sudo -u pandora python manage.py syncdb --noinput 
echo "UPDATE django_site SET domain = 'pandora.local', name = 'pandora.local' WHERE 1=1;" | sudo -u pandora python manage.py dbshell


mkdir /srv/pandora/data
chown -R pandora:pandora /srv/pandora
sudo -u pandora python manage.py update_static

cp /srv/pandora/etc/init/* /etc/init/

service pandora-encoding start
service pandora-tasks start
service pandora start

#nginx
sed "s/__PREFIX__/\/srv\/pandora/g" "/srv/pandora/etc/nginx/vhost.in" > "/etc/nginx/sites-available/default"
service nginx restart

