#!/bin/bash

source ~/PythonTest/bin/activate

exit_code=1

while [ $exit_code -eq 1 ]; do
    # Wyczyść ekran
    clear
    # Uruchom skrypt Python w środowisku wirtualnym
    python ~/Desktop/ControlPad2.py
    # Pobierz kod wyjścia
    exit_code=$?
    sleep 5
done
