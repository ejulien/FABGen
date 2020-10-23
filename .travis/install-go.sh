#!/bin/bash

#force run with bash
if [ -z "$BASH_VERSION" ]
then
    exec bash "$0" "$@"
    return
fi

#create local scope
function install {

echo "Fetching latest Go version..."
typeset VER=`curl -s https://golang.org/dl/ | grep -m 1 -o 'go1\(\.[0-9]\)\+'`
if uname -m | grep 64 > /dev/null; then
	typeset ARCH=amd64
else
	typeset ARCH=386
fi
typeset FILE=$VER.linux-$ARCH
echo "Installing '$FILE'..."

curl -# https://storage.googleapis.com/golang/$FILE.tar.gz |
	tar -C /usr/local -xzf -

echo "
# Go Paths (Added on: `date -u`)
export GOPATH=\$HOME/go
export PATH=\$PATH:/usr/local/go/bin:\$GOPATH/bin
" >> ~/.bash_profile

. ~/.bash_profile

echo "Go is installed and your GOPATH is '$HOME/go'"
echo "Please reload this shell or enter the command '. ~/.bash_profile'"
}
install
