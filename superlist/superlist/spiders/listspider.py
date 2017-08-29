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
from superlist.items import SuperlistItem, SuperlistItemLoader
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

### open drug-bank database ###
# f = open('xmltest.csv', 'rb')
# reader = csv.reader(f)
# content_list = []
# for row in reader:
#     content_list.append(row)    
# for ele in content_list:
#     if ele[2] == 'Fica':
#           content_list.remove(ele)
#           
# def append_exception(list,before, after):
#     for i in range(len(list)):
#         if list[i][2] == before:
#             new_content = list[i]
#             new_content[2] = after
#     list.append(new_content)

# name_list = []
# synonyms_list = []
# for ele in range(1,len(content_list)):
#     name_list.append(content_list[ele][2])
#     synonyms_content = content_list[ele][1].split('\n')
#     synonyms_list.append(synonyms_content)

### open PTterm pmNumber list ###
# f = open('PTterm_pmNumber.csv', 'rb')
# reader = csv.reader(f)
# ptpm_list = []
# for row in reader:
#     ptpm_list.append(row)
# pmnumber_list = []
# for ele in range(1,len(ptpm_list)):
#     pmnumber_list.append(ptpm_list[ele][1])
# 
# def extract_key(v):
#     return v[1]
#     
# data = sorted(ptpm_list[0:], key=extract_key)
# newlist = [['PT_term','pm_number']]
# tem = [
#     [k,[x[0] for x in g]]
#     for k, g in itertools.groupby(data, extract_key)
# ]
# for i in range(len(tem)):
#     tem[i][1] = ','.join(tem[i][1])
# for ele in tem:
#     newlist.append(ele)
# ptpm_list = newlist

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
    
    fname = '/home/hjiang/superlist/pdf_folder/' + fname
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
        
        outputStream = open('/home/hjiang/superlist/pdf_folder/%s'%basename(url),"wb")
        writer.write(outputStream)
        outputStream.close()
        return (True)
    else:
        return (False)

### Open the latest superlist

class ListspiderSpider(scrapy.Spider):
    name = "listspider"
    # allowed_domains = [""]
    start_urls = ['file:///home/hjiang/superlist/Superlist_Rebuild_Aug_10_2017.xlsx']

    def parse(self, response):
        xl = pd.ExcelFile('Superlist_Rebuild_Aug_10_2017.xlsx')
        sheet_list = xl.sheet_names
        df = xl.parse('Masterlist July')
        df = df[['Drug Code','DIN','PM ENG','PM FR','ATC Code']]
        colnames = list(df.columns[0:(len(df.columns)-1)])
        df = df.drop_duplicates()
        df = df.reset_index(drop=True)
        
        atc_df = pd.read_csv('updated_atc.csv', delimiter=',')
        atc_list = []
        for i in range(0,len(atc_df)):
            atc_code_short = atc_df['atc_code5'][i]
            atc_code_long = atc_df['atc_code1'][i] + '/'+atc_df['atc_code2'][i] + '/'+atc_df['atc_code3'][i] + '/'+atc_df['atc_code4'][i] + '/'+atc_df['atc_code5'][i]
            atc_code_desc = atc_df['atc_desc1'][i] + '/' + atc_df['atc_desc2'][i] + '/' + atc_df['atc_desc3'][i] + '/' + atc_df['atc_desc4'][i] + '/' + atc_df['atc_desc5'][i]
            atc_list.append([atc_code_short,atc_code_long,atc_code_desc])
            
        for i in range(0,len(df)):
            din_number = str('{0:08}'.format(int(df['DIN'][i])))
            res=es.search(index="test_pm*", doc_type="raw_pm", body={"query": {"match": {"DIN": din_number}}})
            if (res['hits']['total'] != 0):
                item = SuperlistItem()
                for ele in colnames:
                    if (ele == u'DIN'):
                         item['DIN'] = str('{0:08}'.format(int(df['DIN'][i])))
                    elif (ele == u'ATC Code'):
                         try:
                             atc_index = findItem(atc_list,df['ATC Code'][i])[0][0]
                             item['atc_code'] = atc_list[atc_index][1]
                             item['atc_code_desc'] = atc_list[atc_index][2]
                         except IndexError:
                             item['atc_code'] = df['ATC Code'][i]
                             item['atc_code_desc'] = ''
                    elif ((ele == u'PM ENG') or (ele == u'PM FR')):
                        if (ele == u'PM ENG'):
                              if (math.isnan(df['PM ENG'][i])):
                                  item['PM_ENG'] = ''
                                  item['pm_page_one_eng'] = ''
                                  item['content_eng'] =''
                              else:
                                  item['PM_ENG'] = str('{0:08}'.format(int(df['PM ENG'][i])))
                                  pm_eng_number = str('{0:08}'.format(int(df['PM ENG'][i])))
                                  pdf_eng_link = 'https://pdf.hres.ca/dpd_pm/' + pm_eng_number + '.PDF'
                                  print(pdf_eng_link)
                                  if download_pdf(pdf_eng_link):
                                      file = basename(pdf_eng_link)
                                      if ' '.join(convert(file, pages=[0]).split()) == '':
                                          pypdf_to_image.convert(('file:///home/hjiang/superlist/pdf_folder/' + file))
                                          os.chdir('/home/hjiang/superlist/pdftoimage/%s'%pm_eng_number)
                                          file_dir = '/home/hjiang/superlist/pdftoimage/%s/'%pm_eng_number
                                          folder_length = len([name for name in os.listdir('.') if os.path.isfile(name)])
                                          # file_obj = codecs.open("/home/hjiang/superlist/pdftoimage_text/%s.txt"%(pm_eng_number), 'a',encoding='utf-8')
                                          file_obj = codecs.open("/home/hjiang/superlist/pdftoimage_text/%s.txt"%(pm_eng_number), 'a')
                                          for i in range(0,folder_length):
                                              filedata = OCRtest(file_dir + '%s-%s.jpeg'%(pm_eng_number,i))
                                              file_obj.write(filedata + '\n\n\n' + 'Page:%s'%i)
                                              if i == 0:
                                                    item['pm_page_one_eng'] = filedata
                                          file_obj.close()
                                          f = open("/home/hjiang/superlist/pdftoimage_text/%s.txt"%(pm_eng_number))
                                          item['content_eng'] = f.read()
                                      else:
                                          item['pm_page_one_eng'] = ' '.join(convert(file, pages=[0]).split())
                                          item['content_eng'] = ' '.join(convert(file).split())
                                      os.remove('/home/hjiang/superlist/pdf_folder/%s'%file)
                        elif (ele == u'PM FR'):
                             if (math.isnan(df['PM FR'][i])):
                                  item['PM_FR'] = ''
                                  item['pm_page_one_fr'] = ''
                                  item['content_fr'] =''
                             else:
                                  item['PM_FR'] = str('{0:08}'.format(int(df['PM FR'][i])))
                                  pm_fr_number = str('{0:08}'.format(int(df['PM FR'][i])))
                                  pdf_fr_link = 'https://pdf.hres.ca/dpd_pm/' + pm_fr_number + '.PDF'
                                  print(pdf_fr_link)
                                  if  download_pdf(pdf_fr_link):
                                      file = basename(pdf_fr_link)
                                      if ' '.join(convert(file, pages=[0]).split()) == '':
                                          pypdf_to_image.convert(('file:///home/hjiang/superlist/pdf_folder/' + file))
                                          os.chdir('/home/hjiang/superlist/pdftoimage/%s'%pm_fr_number)
                                          file_dir = '/home/hjiang/superlist/pdftoimage/%s/'%pm_fr_number
                                          folder_length = len([name for name in os.listdir('.') if os.path.isfile(name)])
                                          file_obj = codecs.open("/home/hjiang/superlist/pdftoimage_text/%s.txt"%(pm_fr_number), 'a',encoding='utf-8')
                                          for i in range(0,folder_length):
                                              filedata = OCRtest(file_dir + '%s-%s.jpeg'%(pm_fr_number,i))
                                              file_obj.write(filedata + '\n\n\n' + 'Page:%s'%i)
                                              if i == 0:
                                                    item['pm_page_one_fr'] = filedata
                                          file_obj.close()
                                          f = open("/home/hjiang/superlist/pdftoimage_text/%s.txt"%(pm_fr_number))
                                          item['content_fr'] = f.read()
                                      else:
                                          item['pm_page_one_fr'] = ' '.join(convert(file, pages=[0]).split())
                                          item['content_fr'] = ' '.join(convert(file).split())
                                      os.remove('/home/hjiang/superlist/pdf_folder/%s'%file)
                    else:
                        ele = ele.encode('utf-8')
                        if isinstance(df[ele][i], numpy.float64):
                            if math.isnan(df[ele][i]):
                                item[ele] = ''
                            else:
                                item[ele] = df[ele][i]
                        elif (type(df[ele][i]) == float):
                            if numpy.isnan(df[ele][i]):
                                item[ele] = ''
                            else:
                                item[ele] = df[ele][i]
                        else:
                            item[ele] = df[ele][i]
                yield item
