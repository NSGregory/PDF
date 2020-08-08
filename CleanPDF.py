from PDF_manipulator import RenamePDF
import os
import shutil
from configparser import ConfigParser

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
    print(file)
    if file.endswith(".pdf"):
        if True:
        # try:
            pdf = RenamePDF(source_path + file, destination_path, fail_path)
            pdf.rename()
            if os.path.exists(source_path + file):
                print(f"{file} failed to move.")

                if os.path.exists(fail_path + file):
                    shutil.move(source_path + file, fail_path + file + "1")
                else:
                    shutil.move(source_path + file, fail_path)
        # except:
        #    print("Error renaming the PDF")
    else:
        print(f"File '{file}' does not appear to be a PDF")
