# Installation

## source installation from github on linux 

### requirements
- git (for cloning the repository).
- curl for getting the poetry install script.
- pyenv (for managing and containing the required python version in a virtual environment.)  
  https://github.com/pyenv/pyenv
- poetry (for managing all the libraries in the correct versions, that the app depends on.)  
  https://python-poetry.org/

### installation steps
Using the commandline:
1) Install git anc curl, using your distributions package manager.  
   e.g. on debian/ubuntu:
   > apt install git curl
2) Install pyenv using the documentation on the site:  
   https://github.com/pyenv/pyenv#installation
  

3) Install poetry (read the documentation on the site)  
   shortcut: 
   > curl -sSL https://install.python-poetry.org | python3 -
4) clone the InsectImager source in a folder of your choice:
   > git clone https://github.com/Taskforce-Biodiversity/InsectImager.git
5) Add the correct python version (3.10.1) with pyenv.
   > pyenv install 3.10.1
6) Go to the InsectImager source folder and make 3.10.1 the python version for the project folder
   > python local 3.10.1  
   > pyenv rehash  

   check if you are using the correct python version in the project folder:
   > python --version
7) install all the dependencies with poetry, based on the included pyproject.toml file
   > poetry update
8) run the application from the InsectImager folder with:
   > poetry run python InsectImager.py

### troubleshooting
- The usb Vendor:product id (1A86:7523) from the usb serial converter in the xy-table clashes with the id from an e-reader.  
This makes newer versions of the brltty package disconnect it.  
see: https://bbs.archlinux.org/viewtopic.php?id=269975 for the solution. (on ubuntu 22.04 the file = 85-brltty.rules)
- The user needs to be able to write to /dev/ttyUSB(x). Add the user to the dialout group and logout / login for settings to take effect.
  > sudo adduser *your-username* dialout
