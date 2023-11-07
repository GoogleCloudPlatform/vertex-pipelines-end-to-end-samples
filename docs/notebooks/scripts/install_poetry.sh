#!/bin/bash
# install poetry
curl -sSL https://install.python-poetry.org | POETRY_HOME=$HOME/.poetry python3 -
# add poetry to PATH
echo "export PATH=$HOME/.poetry/bin:PATH" >> $HOME/.bashrc
poetry --version
