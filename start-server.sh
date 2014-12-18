#!/bin/bash
DART=/home/marcelo/Programas/dart
cd ./monitor_webapp

echo "Compiling web app..."
$DART/dart-sdk/bin/pub build
cd ..

rm monitor/static
ln -s ./monitor_webapp/build/web monitor/static

echo "Running server..."
python main.py
