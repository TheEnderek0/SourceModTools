@echo off


echo Building ContentBuilder

python -m PyInstaller --distpath ./dist/ContentBuilder/ --workpath ./build/ -y ./ContentBuilder/ContentBuilder.spec
robocopy ContentBuilder\bundle\ dist\ContentBuilder\ /S



echo Building DuplicateChecker

python -m PyInstaller --distpath ./dist/DuplicateChecker/ --workpath ./build/ -y ./DuplicateChecker/DuplicateChecker.spec
robocopy DuplicateChecker\bundle\ dist\DuplicateChecker\ /S


echo Building MapCompiler

python -m PyInstaller --distpath ./dist/MapCompiler/ --workpath ./build/ -y ./MapCompiler/MapCompiler.spec
robocopy MapCompiler\bundle\ dist\MapCompiler\ /S

pause

