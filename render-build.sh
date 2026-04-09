#!/usr/bin/env bash
set -o errexit

STORAGE_DIR=/opt/render/project/.render
mkdir -p $STORAGE_DIR/chrome

if [[ ! -d $STORAGE_DIR/chrome/opt/google/chrome ]]; then
  echo "...Downloading Chrome 114"
  cd $STORAGE_DIR
  wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/114.0.5735.90/linux64/chrome-linux64.zip
  unzip chrome-linux64.zip
  mv chrome-linux64/* chrome/
  rm chrome-linux64.zip
fi

if [[ ! -f $STORAGE_DIR/chromedriver ]]; then
  echo "...Downloading ChromeDriver 114"
  cd $STORAGE_DIR
  wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/114.0.5735.90/linux64/chromedriver-linux64.zip
  unzip chromedriver-linux64.zip
  mv chromedriver-linux64/chromedriver .
  rm chromedriver-linux64.zip
  chmod +x chromedriver
fi
