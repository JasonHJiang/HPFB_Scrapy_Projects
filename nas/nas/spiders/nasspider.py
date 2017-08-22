# -*- coding: utf-8 -*-
from PIL import Image
import sys
import codecs
import pyocr
import pyocr.builders
import csv
import io
import scrapy
from scrapy import Selector
import datetime
import urlparse
import socket
import os
from os.path import splitext, basename
from nas.items import NasItem, NasItemLoader
from scrapy.http import Request
from scrapy.loader.processors import MapCompose, Join
from scrapy.item import Item
from scrapy.loader import ItemLoader
import layout_scanner
from cStringIO import StringIO
import pypdf_to_image
from os.path import basename
import re
import socket
from elasticsearch import Elasticsearch
import base64
from pdfminer.converter import TextConverter
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTChar
from binascii import b2a_hex
import urllib
from urllib2 import Request, urlopen
from pyPdf import PdfFileWriter, PdfFileReader
from StringIO import StringIO
from tika import language
import itertools
import string
import re
from openpyxl import load_workbook
import pandas as pd
import math
import numpy
import requests


### system setting ###
es = Elasticsearch('http://elastic-gate.hc.local:80')
reload(sys)  
sys.setdefaultencoding('utf8')
csv.field_size_limit(sys.maxsize)
os.chdir('nas')

### function to find index of a list of list ###
def findItem(theList, item):
   return [(ind, theList[ind].index(item)) for ind in xrange(len(theList)) if item in theList[ind]]

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split('(\d+)', text) ]

def OCRtest(file_name):
    ### pyocr ###
    final_text = []
    builder = pyocr.builders.TextBuilder()
    tools = pyocr.get_available_tools()
    if len(tools) == 0:
        print("No OCR tool found")
        sys.exit(1)
    # The tools are returned in the recommended order of usage
    tool = tools[0]
    print("Will use tool '%s'" % (tool.get_name()))
    # 
    # 
    langs = tool.get_available_languages()
    print("Available languages: %s" % ", ".join(langs))
    lang = langs[3]
    print("Will use lang '%s'" % (lang))
    # 
    # 
    txt = tool.image_to_string(
        Image.open(file_name),
        lang=lang,
        builder=pyocr.builders.TextBuilder()
    )
    # 
    # with codecs.open(txt_file_name, 'a', encoding='utf-8') as file_descriptor:
    # for text in final_text:
    #   builder.write_file(file_descriptor, text)
    return txt
        
def convert(fname, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)
    
    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)
    
    fname = 'pdf_folder/' + fname
    infile = open(fname, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue().decode('utf8')
    output.close
    # os.remove(fname)
    return text

def download_pdf(url):
    writer = PdfFileWriter()
    code = requests.get(url, stream=True).status_code
    if code != 404:
        remoteFile = urlopen(Request(url)).read()
    
        memoryFile = StringIO(remoteFile)
        pdfFile = PdfFileReader(memoryFile)
        
        for pageNum in xrange(pdfFile.getNumPages()):
                currentPage = pdfFile.getPage(pageNum)
                #currentPage.mergePage(watermark.getPage(0))
                writer.addPage(currentPage)
        
        outputStream = open('pdf_folder/%s'%basename(url),"wb")
        writer.write(outputStream)
        outputStream.close()
        return (True)
    else:
        return (False)

### Open the latest superlist

class nasspider(scrapy.Spider):
    name = "nasspider"
    # allowed_domains = [""]
    start_urls = ['file:///home/hjiang/nas/Superlist_Rebuild_Aug_10_2017.xlsx']

    def parse(self, response):
        xl = pd.ExcelFile('Superlist_Rebuild_Aug_10_2017.xlsx')
        sheet_list = xl.sheet_names
        df = xl.parse('Masterlist July')
        df = df.drop_duplicates()
        df = df[['Drug Code','Drug Product (DIN name)','DIN','PM ENG','PM FR', 'ATC Code']]
        colnames = list(df.columns[0:len(df.columns)])
        # df = df.reset_index(drop=True)
        
        atc_df = pd.read_csv('updated_atc.csv', delimiter=',')
        atc_list = []
        for i in range(0,len(atc_df)):
            atc_code_short = atc_df['atc_code5'][i]
            atc_code_long = atc_df['atc_code1'][i] + '/'+atc_df['atc_code2'][i] + '/'+atc_df['atc_code3'][i] + '/'+atc_df['atc_code4'][i] + '/'+atc_df['atc_code5'][i]
            atc_code_desc = atc_df['atc_desc1'][i] + '/' + atc_df['atc_desc2'][i] + '/' + atc_df['atc_desc3'][i] + '/' + atc_df['atc_desc4'][i] + '/' + atc_df['atc_desc5'][i]
            atc_list.append([atc_code_short,atc_code_long,atc_code_desc])
            
        row_list = [4499,4500,7204,7205,7206,7207,4881,4882,4883,6135,6136,6137,6138,9007,10435,6141,6142]
        for element in row_list:
            item = NasItem()
            for ele in colnames:
                if (ele == u'ATC Code'):
                     try:
                         atc_index = findItem(atc_list,df['ATC Code'][element])[0][0]
                         item['atc_code'] = atc_list[atc_index][1]
                         item['atc_code_desc'] = atc_list[atc_index][2]
                     except IndexError:
                         item['atc_code'] = df['ATC Code'][element]
                         item['atc_code_desc'] = ''
                elif (ele == u'Drug Product (DIN name)'):
                     item['drug_product'] = df['Drug Product (DIN name)'][element]
                elif (ele == u'Drug Code'):
                     item['drug_code'] = df['Drug Code'][element]
                elif (ele == u'DIN'):
                     item['DIN'] = str('{0:08}'.format(int(df['DIN'][element])))
                elif ((ele == u'PM ENG') or (ele == u'PM FR')):
                    if (ele == u'PM ENG'):
                          if (math.isnan(df['PM ENG'][element])):
                              item['pm_eng'] = ''
                              item['pm_page_one_eng'] = ''
                              item['content_eng'] =''
                          else:
                              item['pm_eng'] = str('{0:08}'.format(int(df['PM ENG'][element])))
                              pm_eng_number = str('{0:08}'.format(int(df['PM ENG'][element])))
                              pdf_eng_link = 'https://pdf.hres.ca/dpd_pm/' + pm_eng_number + '.PDF'
                              print(pdf_eng_link)
                              if download_pdf(pdf_eng_link):
                                  file = basename(pdf_eng_link)
                                  if ' '.join(convert(file, pages=[0]).split()) == '':
                                      pypdf_to_image.convert(('file:///home/hjiang/nas/pdf_folder/' + file))
                                      os.chdir('nas/pdftoimage/%s'%pm_eng_number)
                                      file_dir = 'nas/pdftoimage/%s/'%pm_eng_number
                                      folder_length = len([name for name in os.listdir('.') if os.path.isfile(name)])
                                      # file_obj = codecs.open("nas/pdftoimage_text/%s.txt"%(pm_eng_number), 'a',encoding='utf-8')
                                      file_obj = codecs.open("nas/pdftoimage_text/%s.txt"%(pm_eng_number), 'a')
                                      for i in range(0,folder_length):
                                          filedata = OCRtest(file_dir + '%s-%s.jpeg'%(pm_eng_number,i))
                                          file_obj.write(filedata + '\n\n\n' + 'Page:%s'%i)
                                          if i == 0:
                                                item['pm_page_one_eng'] = filedata
                                      file_obj.close()
                                      f = open("nas/pdftoimage_text/%s.txt"%(pm_eng_number))
                                      item['content_eng'] = f.read()
                                  else:
                                      item['pm_page_one_eng'] = ' '.join(convert(file, pages=[0]).split())
                                      item['content_eng'] = ' '.join(convert(file).split())
                                  os.remove('nas/pdf_folder/%s'%file)
                    elif (ele == u'PM FR'):
                         if (math.isnan(df['PM FR'][element])):
                              item['pm_fr'] = ''
                              item['pm_page_one_fr'] = ''
                              item['content_fr'] =''
                         else:
                              item['pm_fr'] = str('{0:08}'.format(int(df['PM FR'][element])))
                              pm_fr_number = str('{0:08}'.format(int(df['PM FR'][element])))
                              pdf_fr_link = 'https://pdf.hres.ca/dpd_pm/' + pm_fr_number + '.PDF'
                              print(pdf_fr_link)
                              if  download_pdf(pdf_fr_link):
                                  file = basename(pdf_fr_link)
                                  if ' '.join(convert(file, pages=[0]).split()) == '':
                                      pypdf_to_image.convert(('file:///home/hjiang/nas/pdf_folder/' + file))
                                      os.chdir('nas/pdftoimage/%s'%pm_fr_number)
                                      file_dir = 'nas/pdftoimage/%s/'%pm_fr_number
                                      folder_length = len([name for name in os.listdir('.') if os.path.isfile(name)])
                                      file_obj = codecs.open("nas/pdftoimage_text/%s.txt"%(pm_fr_number), 'a',encoding='utf-8')
                                      for i in range(0,folder_length):
                                          filedata = OCRtest(file_dir + '%s-%s.jpeg'%(pm_fr_number,i))
                                          file_obj.write(filedata + '\n\n\n' + 'Page:%s'%i)
                                          if i == 0:
                                                item['pm_page_one_fr'] = filedata
                                      file_obj.close()
                                      f = open("nas/pdftoimage_text/%s.txt"%(pm_fr_number))
                                      item['content_fr'] = f.read()
                                  else:
                                      item['pm_page_one_fr'] = ' '.join(convert(file, pages=[0]).split())
                                      item['content_fr'] = ' '.join(convert(file).split())
                                  os.remove('nas/pdf_folder/%s'%file)
                # else:
                #     ele = ele.encode('utf-8')
                #     if isinstance(df[ele][element], numpy.float64):
                #         if math.isnan(df[ele][element]):
                #             item[ele] = ''
                #         else:
                #             item[ele] = df[ele][element]
                #     elif (type(df[ele][element]) == float):
                #         if numpy.isnan(df[ele][element]):
                #             item[ele] = ''
                #         else:
                #             item[ele] = df[ele][element]
                #     else:
                #         item[ele] = df[ele][element]
            yield item
