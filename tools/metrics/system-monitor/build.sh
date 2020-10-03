[ ! -d "_release" ] && mkdir _release
cd _release
cmake ..
make -j $(($(nproc) + 1))
