#!/bin/bash
# install poetry
curl -sSL https://install.python-poetry.org | POETRY_HOME=$HOME/.poetry python3 -
# add poetry to PATH
echo "export PATH=$HOME/.poetry/bin:$PATH" >> $HOME/.bash_profile
source $HOME/.bash_profile
poetry --version
