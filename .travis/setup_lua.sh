curl http://www.lua.org/ftp/lua-5.3.2.tar.gz | tar xz
pushd lua-5.3.2

LUA_HOME_DIR=$TRAVIS_BUILD_DIR/install/lua

make linux -j
make INSTALL_TOP="$LUA_HOME_DIR" install

popd
