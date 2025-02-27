#!/usr/bin/bash

if [ -z "$1" ]; then
    executable="python3"
else
    executable="$1"
fi

echo Building ContentBuilder

$executable -m PyInstaller --distpath ./dist/ContentBuilder/ --workpath ./build/ -y ./ContentBuilder/ContentBuilder.spec
cp -r ContentBuilder/bundle/* dist/ContentBuilder/
chmod +x dist/ContentBuilder/ContentBuilder

echo Building DuplicateChecker

$executable -m PyInstaller --distpath ./dist/DuplicateChecker/ --workpath ./build/ -y ./DuplicateChecker/DuplicateChecker.spec
cp -r DuplicateChecker/bundle/* dist/DuplicateChecker/
chmod +x dist/DuplicateChecker/DuplicateChecker

$executable -m PyInstaller --distpath ./dist/MapCompiler/ --workpath ./build/ -y ./MapCompiler/MapCompiler.spec
cp -r MapCompiler/bundle/* dist/MapCompiler/
chmod +x dist/MapCompiler/MapCompiler

echo Build done!