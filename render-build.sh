#!/usr/bin/env bash
set -o errexit

STORAGE_DIR=/opt/render/project/.render
mkdir -p $STORAGE_DIR

if [[ ! -d $STORAGE_DIR/chrome ]]; then
  cd $STORAGE_DIR
  wget -q https://storage.googleapis.com/chrome-for-testing-public/123.0.6312.122/linux64/chrome-linux64.zip
  unzip -q chrome-linux64.zip
  mv chrome-linux64 chrome
  
  wget -q https://storage.googleapis.com/chrome-for-testing-public/123.0.6312.122/linux64/chromedriver-linux64.zip
  unzip -q chromedriver-linux64.zip
  mv chromedriver-linux64/chromedriver .
  
  rm chrome-linux64.zip chromedriver-linux64.zip
  chmod +x $STORAGE_DIR/chromedriver
fi
