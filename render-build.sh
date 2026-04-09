#!/usr/bin/env bash
set -o errexit

STORAGE_DIR=/opt/render/project/.render
mkdir -p $STORAGE_DIR/chrome

if [[ ! -d $STORAGE_DIR/chrome/opt/google/chrome ]]; then
  echo "...Downloading Chrome"
  cd $STORAGE_DIR
  # লেটেস্ট স্ট্যাবল ক্রোম ডাউনলোড
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x google-chrome-stable_current_amd64.deb chrome/
  rm google-chrome-stable_current_amd64.deb
fi

export PATH=$PATH:$STORAGE_DIR/chrome/opt/google/chrome
