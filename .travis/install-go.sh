#!/bin/bash

#force run with bash
if [ -z "$BASH_VERSION" ]
then
    exec bash "$0" "$@"
    return
fi

#create local scope
function install {

echo "Installing https://golang.org/dl/go1.15.3.linux-amd64.tar.gz'..."
curl -# https://golang.org/dl/go1.15.3.linux-amd64.tar.gz |
	tar -xzf

echo "
# Go Paths (Added on: `date -u`)
export GOPATH=\$TRAVIS_BUILD_DIR/go
export PATH=\$PATH:/usr/local/go/bin:\$GOPATH/bin
" >> ~/.bash_profile

. ~/.bash_profile

echo "Go is installed and your GOPATH is '$TRAVIS_BUILD_DIR/go'"
echo "Please reload this shell or enter the command '. ~/.bash_profile'"
}
install
