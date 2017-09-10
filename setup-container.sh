#!/bin/bash

cp -rp /usr/git-src/* /usr/src/app/
unlink /usr/git-src/${VIRTUAL_HOST}-botlog.json
touch /usr/git-src/${VIRTUAL_HOST}-botlog.json
rm /usr/src/app/www/botlog.json
ln -s /usr/git-src/${VIRTUAL_HOST}-botlog.json /usr/src/app/www/botlog.json 

rm -rf /usr/src/app/market_data/
ln -s /usr/git-src/market_data/ /usr/src/app/market_data
