from PyPDF2 import PdfFileReader
import os
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
import bibtexparser
import requests
import re
from pathlib import Path
import shutil


class RenamePDF:
    def __init__(self, path, destination, fail):
        self.path = path
        self.destination = destination
        self.fail_path = fail

    def pdfs(self):
        """
        Goes to the given directory when the PyPDF object is initiated and finds all the PDFS there.
        Returns the values as a full path name.
        :return: full file path and name
        """
        print(f"pdfs called: {self.path}")
        # Determine if path is a single file
        test_path = Path(self.path)
        if test_path.is_file():
            tmp_list = [self.path]
            return tmp_list
            # This supports running individual files through renamer
            # The advantage of this is it allows you to ensure filenames match up
            # Convert to list type for later iterating so it doesn't go by chars in string
        else:
            if not os.path.exists(self.path):
                tmp_list = [self.path]
                return tmp_list

            file_list = os.listdir(self.path)
            pdfs = [self.path + x for x in file_list if x.endswith(".pdf")]
            return pdfs

    def info(self, filename):
        """
        Uses P2PDF2's PdfFileReader function, which is very limited and heavily flawed.
        The limitation seems to come from the publisher's end who inconsistently use the metadata.
        This was ultimately abandoned in favor of using DOI.

        :param filename: filname as full path
        :return: basic info derived from PyPDF2's PdfFileReader function.
        """
        try:
            with open(filename, 'rb') as f:
                pdf = PdfFileReader(f)
                info = pdf.getDocumentInfo()
                number_of_pages = pdf.getNumPages()
            author = info.author
            creator = info.creator
            producer = info.producer
            subject = info.subject
            title = info.title
            return info
        except:
            # input(f"Could not open {path}.  Press any key to continue.")
            f = open("../../SortedFiles/text/pdf/2020/07/PDF_error_log.txt", "a")
            f.write(filename + "\n")
            f.close()

    def get_first_page(self, path):
        """
        Pulls the first page from the PDF.  This is useful for parsing the
        text later as the needed information for pulling the metadata is
        contained there.

        This function was based on the incorrect assumption that DOI
        is printed on the first page.  It in fact can be found anywhere
        in the document.  So this isn't that helpful.

        :param path: filename given as the full file path
        :return:
        """
        try:
            with open(path, 'rb') as f:
                pdf = PdfFileReader(f)
                page1 = pdf.getPage(1)
                text = page1.extractText()
                return page1, text
        except:
            print("error getting page1")

    def extract_all_text(self, path, doi_only=False):
        """
        Uses the PyPDF2 library to pull all of the text out of a PDF and
        returns it as a single string.

        :param path: path to pdf being evaluated
        :param doi_only: If true, will only include pages containing "doi"
        in the text. This is likely going away, not that helpful.
        :return: entire text of a pdf as a string
        """
        # print(doi_only)
        text = []
        try:
            with open(path, 'rb') as f:
                pdf = PdfFileReader(f)
                if doi_only == True:
                    for page in pdf.pages:
                        x = page.extractText()
                        if "doi" in x:
                            text.append(x)
                else:
                    for page in pdf.pages:
                        text.append(page.extractText())
                    string_text = "".join(text)
                return string_text
        except:
            print("error getting the file open or something")

    def get_doi(self, path):
        #TODO: alter structure so that each doi match then tries crossref
        #TODO: if match is successful, ultimately return the title
        #TODO: if match is unsuccessful, try the next strategy
        #TODO: add searching metadata info for doi tag

        print(path)
        initial_test_string = ["doi", "DOI", "doi:", "DOI:"]
        exclude_doi_source = ["zenodo"]  # alternative doi publishers that don't work with crossref
        text = self.extract_all_text(path)
        if text == None:
            return None

        doi = None
        m = False
        # single_pattern =["(?:https?://.{0,5})" +  # Look for possible https and "doi" versus "dx.doi"
        #                 "?doi(?!ng\b)(?:\.org)/" + #Look for "doi" but not "doing" and possible ".org"
        #                 "?(?:(?:\S|\n)" + # The actual unique identifier for the paper
        #                 "(?!Article|Download|Wiley|1Department|Department|$))*" + # Exclude specific strings
        #                 "(?:[a-z0-9]|-\n+?\S+)"] # Wrap around detection if there's a -\n combination
        # preserve this single_pattern = ["(?:https?://.{0,5})?doi(?!ng\b)(:?\n)?(?:\.org)?(?:(?:\S)(?!Article|Download|Wiley|$))*(?:[a-z0-9]|-\n+?\S+)"]
        # single_pattern =["(?:https?://.{0,5})?doi(?!ng\b)(:?\n)?(?:\.org)?(?:(\S)(?!Article|Download|Wiley|1Department|Department|$))*(?:[a-z0-9]|-\n+?(?:(\S)(?!Division|$))+)"]

        # rp is "regex pattern"
        # This is the master regex that is meant to catch the vast majority.
        # Some journals are particularly wonky and will require alternative.
        rp = ["(?:https?://.{0,5})?" +  # Https and up to 5 character
              "doi(?!ng\b)" +  # "doi" but not "doing"
              "(:?\n)?" +  # possible ":" and/or newline
              "(?:\.org)?" +  # possible ".org"
              "(?:(\S)(?!Article|Download|Wiley|1Department|Department|$))*" +
              # all non-whitespace characters
              # but not key words after "?!"
              # the keywords approach is probably not sustainable
              # as they can fail in unique ways for each PDF encountered
              "(?:[a-z0-9]|-\n+?" +  # newlines preceded by hyphen
              "(?:(\S)(?!Division|$))+)"  # characters after a "-\n"
              # but not keywords after "?!
              # this seems to consume an extra char
              ]

        # Specialized patterns for particular journals
        spec_pattern_list = ["\S+sciadv.\d+", "\S+nature+\d+", "\S+/science\.\S+", "DOI: \S+/science\.\S+"]

        for pattern in rp:
            result = re.search(pattern, text, re.IGNORECASE)
            if result != None:
                doi = result[0]
                if any(n in doi for n in exclude_doi_source):
                    doi = None

        if doi == None:
            for pattern in spec_pattern_list:
                result = re.search(pattern, text, re.IGNORECASE)
                if result != None:
                    doi = result[0]

        return doi

    def get_crossref_metadata(self, doi):
        """
        Retrieves metadata from Crossref database using the Requests module.
        Doi must be formatted as a valid URL before being sent via Requests.
        First part of the function handles the URL formatting, which is then
        sent on to Crossref.org.

        Crossref.org supports multiple header formats which will return a
        range of values.  See Crossref.org for more examples.  Changing the
        header will break this function.

        :param doi: Document object identifier number
        :return: Metadata from the Crossref database
        """
        if doi == None:
            return None
        # print(doi)
        doi = doi.replace("\n", "")  # get rid of new lines stored in the doi
        doi = doi.replace(" ", "")  # get rid of whitespace
        if "DOI:http://" in doi:
            url = "https://" + doi[11:]
        elif any(n in doi for n in ["https://dx.doi.org", "http://dx.doi.org"]):
            url = doi
        elif "https://doi.org" in doi:
            url = doi
        elif any(n in doi for n in ["doi.org/", "DOI.org/"]):
            print(doi)
            url = "https://" + doi
        elif any(n in doi for n in ["DOI:", "doi:"]):
            url = "https://doi.org/" + doi[4:]
        elif any(n in doi for n in ["DOI ", "doi "]):
            url = "https://doi.org/" + doi[4:]
        elif any(n in doi for n in ["DOI", "doi"]):
            url = "https://doi.org/" + doi[3:]
        elif any(n in doi for n in ["sciadv"]):
            # this elif block is for special patterns that return only the unique DOI
            url = "https://doi.org/" + doi
        else:
            print("maybe the doi is malformed?")
            return None
        # print(url)
        # the headers here determine what kind of output you get from Crossref.org
        # this method ultimately requires that you be online and depend on
        # crossref.org to continue to provide the service
        # Given the longevity of Crossref.org, I think this is a reasonable bet
        headers = {
            'accept': 'text/bibliography; style=bibtex',
        }
        print(f"url: {url}")
        crossref_request = requests.get(url, headers=headers)
        return crossref_request.text

    def make_bibtex_entries(self, meta_data):
        """
        Converts the metadata from crossref.org into a formated bibliography
        entry.  This is returned.  It also saves the entry into two
        bibliographic repositiories.  Temp.bib is overwritten with each run of
        this function.  Repository.bib accumulates over time.  The idea is to
        automatically build a bibliography reference as papers get imported.

        :param meta_data: Raw metadata from Crossref.org
        :return: formatted bibliography
        """
        #TODO:base location of temp.bib and repository.bib on destination path

        if meta_data == None:
            return None
        # print(meta_data)
        db = BibDatabase()
        db.entries = meta_data
        # print(db.entries)
        writer = BibTexWriter()
        with open("../Scratch/temp.bib", 'w', encoding='utf-8') as bibfile:
            bibfile.write(meta_data)
        with open("../Scratch/repository.bib", 'a', encoding='utf-8') as bibfile:
            bibfile.write(meta_data)
        with open("../Scratch/temp.bib", encoding='utf-8') as bibtexfile:
            bib_database = bibtexparser.load(bibtexfile)

        return bib_database

    def make_titles(self, bib_database):
        """
        Converts bibliographic data into a simplified title.

        Author Year - <5 words of title>

        This also strips out simple words/prepositions and certain characters.

        :param bib_database: bibliographic formatted metadata
        :return: title in above format (str)
        """

        if bib_database == None:
            return None
        if not len(bib_database.entries) > 0:
            print("File not readable")
            return None

        # print(bib_database.entries)
        author = bib_database.entries[0]['author'].split(',')[0]
        year = bib_database.entries[0]['year']
        title = bib_database.entries[0]['title']

        prune_words = ["of", "and", "the", "The", "with", "at", "by",
                       "in", "for", "after", "by", "against", "instead",
                       "to", "between", "over"]
        prune_punctuation = ["&", "!", "@", ":", ",", "$", "#",
                             "%", "*", "?", ";", "/", "\\", "'", '"',
                             "\x80", "\x99"
                             ]
        base_title = title
        title_as_list = base_title.split(' ')
        temp_title = []
        for word in prune_words:
            if word in title_as_list:
                title_as_list.remove(word)
        if len(title_as_list) > 4:
            title_as_list = title_as_list[0:4]
        title_as_string = ' '.join(title_as_list)
        for character in prune_punctuation:
            title_as_string = title_as_string.replace(character, "")

        return f"{author} {year} - {title_as_string}.pdf"

    def rename(self):
        """
        Helper function that renames file to reflect new path. If a file of the same
        name already exists in the destination folder, the file name is numbered and
        incremented until the filename is unique (prevents overwriting files).
        :param Path source: source of file to be moved
        :param Path destination_path: path to destination directory
        """
        #TODO: Determine best location of these self.variables
        self.pdf_list_as_path = self.pdfs()
        self.doi_list = [self.get_doi(x) for x in self.pdf_list_as_path]
        self.pdf_info = [self.info(x) for x in self.pdf_list_as_path]
        self.meta_list = [self.get_crossref_metadata(x) for x in self.doi_list]
        self.bibtex_entries = [self.make_bibtex_entries(x) for x in self.meta_list]
        self.final_titles = [self.make_titles(x) for x in self.bibtex_entries]

        if None in self.final_titles:
            return None

        x = 0
        print("rename called")
        for file in self.pdf_list_as_path:
            final_name = Path(self.final_titles[x])
            destination_path = Path(self.destination)
            source = Path(file)
            x += 1

            new_name = Path(destination_path / final_name)
            if new_name.exists():
                increment = 0

                while new_name.exists():
                    increment += 1
                    new_name = destination_path / f'{final_name.stem}_{increment}{final_name.suffix}'

                    # if not new_name.exists():
                    #    return new_name

                # return self.destination / final_name
            shutil.move(file, new_name)





class GetImages:
    #TODO: A function that pulls out all the images from a PDF
    #TODO: Put all those images in a .pptx
    #TODO: Determine if this should be a separate library?

    #Tried: minecart - got Attribute errors, may need reinstall?
    #Tried: PyMuPDF - didn't export all images

    pass

# if __name__ == '__main__':
#
#     path="C:/Users/gregoryn/test/"
#     destination="C:/Users/gregoryn/test2/"
#     pdf=RenamePDF(path, destination)
#     pdf.rename()
#     #doi_page=pdf.extract_all_text(pdf.pdf_list_as_path[0], doi_only=True)

# url="https://doi.org/10.1186/s12984-019-0535-7"
# headers={
#     'accept':'text/bibliography; style=bibtex',
# }
# r=requests.get(url, headers=headers)
# print(r.text)
# headers={
#     'accept':'application/citeproc+json'
# }
#
# r=requests.get(url, headers=headers)
# print(r.text)
#
# # file_list=PyPDF.pdfs(".")
# r=requests.get(url, headers=headers)

# for x in file_list:
#     PyPDF.info(x)

# file_list = get_pdfs(".")
# for x in file_list:
#     PyPDF2_info(x)
#     print(x)
#
#
# remote_list=get_pdfs(path)
# print(remote_list)
# for x in remote_list:
#     PyPDF2_info(x)
#     print(x)
# data=bibtex(path)
# data.info()
