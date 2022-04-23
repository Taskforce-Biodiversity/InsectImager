#!/bin/bash

# does not work currently due to bug in cv2 config handling
#https://github.com/Nuitka/Nuitka/issues/1275

# Nuitka docs
#https://nuitka.net/doc/user-manual.html

python -m nuitka --onefile --enable-plugin=tk-inter --enable-plugin=numpy --include-data-dir=../assets/=assets ../InsectImager.py
