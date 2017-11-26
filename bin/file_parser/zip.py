"""Parse zip files"""

from .utils import *
import docx
import os
import zipfile


def parse_zip(part, part_name):
    """
    This reads a docx file form a string and outputs just the text from the document
    along with the document's internal structure
    :param part: This is a MIME message part from an email that contains a docx file
    :type part: Union[email.message.Message, basestring]
    :param part_name: This can be either file or email
    :type part_name basestring
    :return: This returns the texts from the word document.
    :rtype: list
    """
    if EMAIL_PART == part_name:
        decoded_payload = part.get_payload(decode=True)
        zip_name = part.get_filename() or ''
    else:
        decoded_payload = part
        zip_name = part_name
    fp = StringIO(decoded_payload)
    try:
        zfp = zipfile.ZipFile(fp)
    except zipfile.BadZipfile:
        return ['#UNSUPPORTED_ATTACHMENT: %s' % zip_name]
    extension = str(os.path.splitext(zip_name)[1]).lower()
    unzip_content = []
    if zfp:
        ziplist = ['#BEGIN_ZIP_FILELIST: %s' % zip_name]
        ziplist.extend(zfp.namelist())
        ziplist.append('#END_ZIP_FILELIST: %s' % zip_name)
        unzip_content.append("\n".join(ziplist))
        if '.docx' == extension:
            unzip_content.extend(docx.parse_docx(part, part_name))
        else:
            for each_compressedfile in zfp.namelist():
                zipped_file = []
                if not each_compressedfile.endswith('/'):
                    zipped_fextension = str(os.path.splitext(each_compressedfile)[1]).lower()
                    zipped_file = ["#BEGIN_ATTACHMENT: %s/%s" % (zip_name, each_compressedfile)]
                    if zipped_fextension in TEXT_FILE_EXTENSIONS:
                        f = zfp.open(each_compressedfile)
                        for line in f:
                            zipped_file.append(line)
                    elif zipped_fextension in ZIP_EXTENSIONS:
                        file_buff = zfp.open(each_compressedfile).read()
                        zipped_file.extend(parse_zip(file_buff, each_compressedfile))
                    else:
                        zipped_file.append("#UNSUPPORTED_CONTENT: file_name = %s" % each_compressedfile)
                    zipped_file.append("#END_ATTACHMENT: %s/%s" % (zip_name, each_compressedfile))
                unzip_content.append("\n".join(zipped_file))
    return unzip_content


def parse_zip_from_mail(message):
    """

    :param message: string representation of docx file
    :type message: email.message.Message
    :return:
    """
    parse_zip(message, EMAIL_PART)


def parse_zip_from_string(file_as_string, file_name):
    """

        :param file_as_string: string representation of docx file
        :type file_as_string: basestring
        :param file_name: docx file name
        :type file_name: basestring
        :return:
        """
    parse_zip(file_as_string, file_name)
