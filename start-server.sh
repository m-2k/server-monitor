#!/bin/bash
DART=/home/marcelo/Programas/dart
cd ./monitor_webapp

echo "Compiling web app..."
$DART/dart-sdk/bin/pub build
cd ..

echo "Running server..."
python main.py
