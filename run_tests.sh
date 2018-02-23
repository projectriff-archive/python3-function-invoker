#!/usr/bin/env bash

if ! [ $(which python) ]; then
    echo "Python not found."
    exit 1
fi

if ! [ $(which pip) ]; then
   echo "Installing pip"
   wget https://bootstrap.pypa.io/get-pip.py
   sudo python get-pip.py
   sudo pip install -U pip
   rm get-pip.py
fi

if ! [ $(which virtualenv) ]; then
   echo "Installing virtualenv"
   sudo pip install -U virtualenv
fi

virtualenv -q -p "python$1" $2
source $2/bin/activate
pip install -r invoker/requirements.txt

./setup.py test

deactivate

rm -rf $2