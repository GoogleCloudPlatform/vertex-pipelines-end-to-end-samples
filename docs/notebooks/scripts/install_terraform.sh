#!/bin/bash
# create temporary folder
mkdir tmp && cd tmp || exit
# download terraform and unzip
curl -so terraform.zip https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_amd64.zip && unzip terraform.zip > /dev/null
# move binaries to ~/.bin
mkdir $HOME/.bin && mv terraform $HOME/.bin > /dev/null
# clean up temporary folder
cd .. && rm -r tmp || exit
