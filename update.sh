cd `dirname $0`
base=`pwd`
bzr pull http://code.0x2620.org/pandora/
cd static/oxjs
bzr pull http://code.0x2620.org/oxjs/
echo build oxjs
./tools/build/build.py >/dev/null
cd $base
test -e src/python-ox && cd src/python-ox && bzr pull http://code.0x2620.org/python-ox/
