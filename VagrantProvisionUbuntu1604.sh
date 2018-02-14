#!/usr/bin/env bash

# Set environment variables
BUILDS="/opt"
HOME="/home/vagrant"
PRJ="/home/vagrant/REPAiR-Web"

echo "Downloading and installing conda..."
wget http://repo.continuum.io/miniconda/Miniconda3-3.7.0-Linux-x86_64.sh -O $BUILDS/miniconda.sh
bash $BUILDS/miniconda.sh -b -p $BUILDS/miniconda
# need to put it to .profile
sed -i 's@:$PATH@:'"$BUILDS"'/miniconda/bin:$PATH@' $HOME/.profile

#echo PATH="$BUILDS/miniconda/bin:$PATH" >> $HOME/.profile
#echo PATH="$BUILDS/miniconda/bin:$PATH" >> $HOME/.basharc
#echo \nexport PATH >> $HOME/.basharc
rm $BUILDS/Miniconda3-latest-Linux-x86_64.sh $BUILDS/miniconda.sh

echo "Installing pip3"
apt-get install -y python3-pip
pip3 install --upgrade pip3

echo "Set up conda environment..."
conda create --yes -n repair-web -c conda-forge python=3.6 gdal=2.1
source activate repair

echo "Conda installing sqlite..."
conda install --yes -c maxbo sqlite

echo "Downloading and installing Node.js 8.9.4 LTS, Yarn..."
source deactivate
curl -sL https://deb.nodesource.com/setup_8.x | bash -
apt-get install -y nodejs

curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
apt-get update && apt-get install -y yarn

echo "Installing Python and JS requirements..."
cd $PRJ
source activate repair
pip3 install -r requirements-dev.txt

echo PYTHONPATH="${PYTHONPATH}:/home/vagrant/.local/lib/python3.5/site-packages" >> $HOME/.bashrc
echo export PYTHONPATH >> $HOME/.bashrc

yarn install

echo "Setting up database..."
DJANGO_SETTINGS_MODULE=repair.settings_staged
python manage.py migrate --run-syncdb


