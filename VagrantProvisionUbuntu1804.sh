#!/usr/bin/env bash

# Set environment variables
BUILDS="/opt"
HOME="/home/vagrant"
PRJ="/home/vagrant/REPAiR-Web"

sudo add-apt-repository -y "deb http://archive.ubuntu.com/ubuntu $(lsb_release -sc) main universe restricted multiverse"

echo "Installing Python3.6 development packages"
sudo apt-get install -y python3-dev python3-pip

echo "Installing GDAL 2.2..."
sudo apt-get install -y binutils libproj-dev gdal-bin libgdal-dev libgeos-dev

echo "Installing SQLite 3.11.0..."
sudo apt-get install -y sqlite3 libsqlite3-mod-spatialite spatialite-bin

echo "Downloading and installing Node.js 8.10.0, Yarn..."
sudo apt-get install -y nodejs

curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt-get update && sudo apt-get install -y --allow-unauthenticated yarn

echo "Installing graph-tools..."
sudo add-apt-repository -y "deb http://downloads.skewed.de/apt/bionic bionic universe"
sudo apt-key adv --keyserver pgp.skewed.de --recv-key 612DEFB798507F25
sudo apt-get update && sudo apt-get install -y --allow-unauthenticated python3-graph-tool

sudo apt-get install -y libcairo2-dev libjpeg-dev libgif-dev

echo "Installing Python and JS requirements..."
cd $PRJ
pip3 install -r requirements-dev.txt

yarn install

echo "Setting up database..."
python3 manage.py migrate --run-syncdb --settings=repair.settings_staged_vagrant
python3 manage.py loaddata sandbox_data --settings=repair.settings_staged_vagrant

echo "Compiling JS files and starting the Node and Django server..."
# Run servers in the background: https://stackoverflow.com/a/11856575
# Stop server that runs in background: https://stackoverflow.com/a/27070134
nohup node server-dev.js > /dev/null 2>/tmp/node_server-dev.log &
nohup python3 manage.py runserver 0.0.0.0:80 --settings=repair.settings_dev_vagrant > /dev/null 2>/tmp/django_server-dev.log &

printf "\nSee VAGRANT.md for additional configuration instructions and then run 'vagrant ssh' to log into the virtual machine. Listening at http://localhost:8081 (on host)..."


