#!/bin/bash

#Prerequisites, on a ubuntu* distribution.
#sudo apt-get install -y git virtualenv ruby libffi-dev python-dev graphviz gcc libssl-dev python-pip
git submodule init metasm # or clone github.com/jjyg/metasm
git submodule update metasm

#Create & activate the virtual environment
virtualenv flask
source flask/bin/activate

#Install packages
pip install -r requirements.txt 

#Modify the conf.py file
sed -i '/SQLALCHEMY_DATABASE_URI/c\SQLALCHEMY_DATABASE_URI = "sqlite:////opt/data/app.db"' polichombr/config.py
sed -i '/STORAGE_PATH/c\STORAGE_PATH = "/opt/data/storage"' polichombr/config.py

mkdir /opt/data

mv ./examples/db_create.py .
./db_create.py



