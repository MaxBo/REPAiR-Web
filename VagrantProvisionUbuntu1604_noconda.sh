#!/usr/bin/env bash

# Set environment variables
BUILDS="/opt"
HOME="/home/vagrant"
PRJ="/home/vagrant/REPAiR-Web"

echo "Updating Ubuntu..."
apt-get update
apt-get upgrade -y

echo "Installing Python3.6..."
add-apt-repository ppa:fkrull/deadsnakes -y
#add-apt-repository ppa:jonathonf/python-3.6 -y
apt-get update
apt-get install -y --allow-unauthenticated python3.6
#printf "\nalias python=python3.6" >> $HOME/.bashrc

echo "Installing SQLite 3.11.0..."
apt-get install -y sqlite3 libsqlite3-mod-spatialite spatialite-bin
apt-get update
apt-get upgrade -y

echo "Installing pip for Python3.6..."
curl https://bootstrap.pypa.io/get-pip.py | python3.6
#printf "\nalias pip=pip3.6" >> $HOME/.bashrc

echo "Installing GDAL 2.1.3..."
add-apt-repository ppa:ubuntugis/ppa -y
apt-get update
apt-get install -y --allow-unauthenticated binutils libproj-dev gdal-bin libgdal-dev libgeos-dev

echo "Downloading and installing Node.js 8.9.4 LTS, Yarn..."
curl -sL https://deb.nodesource.com/setup_8.x | bash -
apt-get install -y nodejs

curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
apt-get update && apt-get install -y --allow-unauthenticated yarn

echo "Installing Python and JS requirements..."
cd $PRJ
pip install -r requirements-dev.txt

#echo PYTHONPATH="${PYTHONPATH}:/home/vagrant/.local/lib/python3.5/site-packages" >> $HOME/.bashrc
#echo export PYTHONPATH >> $HOME/.bashrc

yarn install

#echo "Setting up database..."
#DJANGO_SETTINGS_MODULE="repair.settings_staged"
python3.6 manage.py migrate --run-syncdb --settings=repair.settings_staged_vagrant
python3.6 manage.py loaddata sandbox_data --settings=repair.settings_staged_vagrant

echo "Compiling JS files and starting the server..."
# Run servers in the background: https://stackoverflow.com/a/11856575
#nohup node server-dev.js > /dev/null 2>&1 &
#nohup python3.6 manage.py runserver localhost:8002 --settings=repair.settings_dev_vagrant > /dev/null 2>&1 &
node server-dev.js
python3.6 manage.py runserver localhost:8002 --settings=repair.settings_dev_vagrant



