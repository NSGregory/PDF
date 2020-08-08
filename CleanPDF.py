from PDF_manipulator import RenamePDF
import os
import shutil
from configparser import ConfigParser
from pathlib import Path

# configs
parser = ConfigParser()
parser.read('config.ini')
source_path = parser.get('Filepaths', 'source_path')
destination_path = parser.get('Filepaths', 'destination_path')
fail_path = parser.get('Filepaths', 'fail_path')

if not os.path.exists(fail_path):
    os.makedirs(fail_path)
if not os.path.exists(destination_path):
    os.makedirs(destination_path)

for file in os.listdir(source_path):
    if file.endswith(".pdf"):
        print(file)
        if True:
        #try:
            pdf = RenamePDF(source_path + file, destination_path, fail_path)
            pdf.rename()
            if os.path.exists(source_path + file):
                print(f"{file} failed to move.")
                temp_name = Path( fail_path + file)
                source_name = Path( source_path + file)
                if temp_name.exists():
                    print('file exists')
                    increment = 0
                    while temp_name.exists():
                        increment += 1
                        temp_name = fail_path / f"{file.stem()}_{increment}.{file.suffix}"
                    shutil.move(source_path + file, temp_name)
                else:
                    shutil.move(source_path + file, fail_path)
        #except:
        #    print("Error renaming the PDF")
    #else:
    #    print(f"File '{file}' does not appear to be a PDF")
