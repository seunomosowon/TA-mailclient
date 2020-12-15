""" Parse .docx files """
from __future__ import unicode_literals

from .utils import *
from xml.dom.minidom import parse as parsexml
from six import text_type, binary_type, BytesIO
from six import ensure_binary, ensure_str
import zipfile


def parse_docx(part, part_name):
    """
    This reads a docx file form a string and outputs just the text from the document
    along with the document's internal structure
    :param part: This is a MIME part from an email that contains a docx file
    :type part: Union[email.message.Message, basestring]
    :param part_name: This can be either a file name or string $EMAIL$
    :type part_name basestring
    :return: This returns the texts from the word document.
    :rtype: list
    """
    if part_name == EMAIL_PART:
        decoded_payload = part.get_payload(decode=True)
        zip_name = part.get_filename() or ''
    else:
        decoded_payload = part
        zip_name = part_name
    fp = BytesIO(decoded_payload)
    try:
        zfp = zipfile.ZipFile(fp)
    except zipfile.BadZipfile:
        return ['#UNSUPPORTED_ATTACHMENT: %s' % zip_name]
    return_doc = []
    if zfp:
        return_doc.append(parsexml(zfp.open('[Content_Types].xml', 'rU')).documentElement.toprettyxml())
        """
        I can check for Macros here
        if zfp.getinfo('word/vbaData.xml'):
        openXML standard supports any name for xml file. Need to check all files.
        Add the contents pages to the top of word file for visual inspection of macros
        """
        if zfp.getinfo('word/document.xml'):
            doc_xml = parsexml(zfp.open('word/document.xml', 'rU'))
            return_doc.append(''.join(ensure_str([node.firstChild.nodeValue) for node in doc_xml.getElementsByTagName('w:t')]))
        else:
            return_doc.append('#UNSUPPORTED_DOCX_FILE: file_name = %s' % zip_name)
    else:
        return_doc.append('#INVALID_DOCX_FILE: file_name = %s' % zip_name)
    return return_doc


def parse_docx_from_mail(message):
    """

    :param message: string representation of docx file
    :type message: email.message.Message
    :return:
    """
    parse_docx(message, EMAIL_PART)


def parse_docx_from_string(docx_as_string, file_name):
    """

    :param docx_as_string: string representation of docx file
    :type docx_as_string: basestring
    :param file_name: docx file name
    :type file_name: basestring
    :return:
    """
    parse_docx(docx_as_string, file_name)
