from PDF_manipulator import RenamePDF
import os
import shutil

#configs
source_path = "c:/Users/gregoryn/Downloads/"
#source_path = "c:/Users/gregoryn/SortedFiles/text/pdf/2020/07/"
destination_path ="c:/Users/gregoryn/PDFs/"
fail_path="c:/Users/gregoryn/PDFs/Unreadable/"
#batch rename has a risk of misnaming the files
batch_rename = False


if not os.path.exists(fail_path):
    os.makedirs(fail_path)
if not os.path.exists(destination_path):
    os.makedirs(destination_path)

if batch_rename == True:
    pdf=RenamePDF(source_path, destination_path, fail_path)
    pdf.rename()

if batch_rename == False:
    for file in os.listdir(source_path):
        print(file)
        if file.endswith(".pdf"):
            if True:
            #try:
                pdf=RenamePDF(source_path+file, destination_path, fail_path)
                pdf.rename()
                if os.path.exists(source_path+file):
                    print(f"{file} failed to move.")
                    if os.path.exists(fail_path+file):
                        shutil.move(source_path+file, fail_path+file+"1")
                    else:
                        shutil.move(source_path+file, fail_path)
            #except:
            #    print("Error renaming the PDF")
        else:
            print(f"File '{file}' does not appear to be a PDF")
