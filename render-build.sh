#!/usr/bin/env bash
set -o errexit

STORAGE_DIR=/opt/render/project/.render
mkdir -p $STORAGE_DIR

if [[ ! -d $STORAGE_DIR/firefox ]]; then
  echo "...Downloading Firefox"
  cd $STORAGE_DIR
  wget -q "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US" -O firefox.tar.bz2
  tar -xjf firefox.tar.bz2
  rm firefox.tar.bz2
fi

if [[ ! -f $STORAGE_DIR/geckodriver ]]; then
  echo "...Downloading GeckoDriver"
  cd $STORAGE_DIR
  wget -q https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz
  tar -xzf geckodriver-v0.34.0-linux64.tar.gz
  rm geckodriver-v0.34.0-linux64.tar.gz
  chmod +x geckodriver
fi
