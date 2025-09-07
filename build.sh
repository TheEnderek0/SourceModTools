#!/bin/bash

for i in src/*.py; do
    $python_executable -m nuitka --assume-yes-for-downloads --mode=onefile --windows-icon-from-ico=other/Tools.ico --output-dir=build $i
done

mkdir dist

if [ "$RUNNER_OS" == "Linux" ]; then
    cp build/contentbuilder.bin dist/

elif [ "$RUNNER_OS" == "Windows" ]; then
    cp build/contentbuilder.exe dist/
else
    echo "$RUNNER_OS not supported"
    exit 1
fi