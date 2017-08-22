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
from slsascrapy.items import SlsascrapyItem, SlsascrapyItemLoader
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
from pattern.web import URL

### system setting ###
es = Elasticsearch('http://elastic-gate.hc.local:80')
reload(sys)  
sys.setdefaultencoding('utf-8')
csv.field_size_limit(sys.maxsize)
os.chdir('slsascrapy')


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

def download_pdf(url_address):
    url = URL(url_address)
    f = open('pdf_folder/%s'%basename(url_address), 'wb')
    f.write(url.download(cached=False))
    f.close()
    
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
    
def index_pdf_content(item,url,field_name):
    if url.endswith('.pdf'):
        download_pdf(url.replace(' ','%20'))
        pdf_file = basename(url).replace(' ','%20')
        fp = open('slsascrapy/pdf_folder/' + pdf_file)
        parser = PDFParser(fp)
        doc = PDFDocument(parser)
        parser.set_document(doc)
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pages = layout_scanner.get_pages(url)
        content = ' '.join(convert(pdf_file).split())
        item[field_name] += content
        os.remove('slsascrapy/pdf_folder/' + pdf_file)
    else:
        item[field_name] = u'NA'
                
class SlsaspiderSpider(scrapy.Spider):
    name = "slsaspider"
    # allowed_domains = [""]
    start_urls = ['http://publiservice-app.tpsgc-pwgsc.gc.ca/software/index.cfm?fuseaction=slsa.catalogue&lang=e']

    def parse(self, response):
        all_content = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr').extract()
        for i in range(2,(len(all_content)+1)):
        # for i in range(157,158):
            slsaspiderItem = SlsascrapyItem()
            software_publishers = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[1]/text()'%i).extract()[0]
            if 'PDF' in software_publishers:
                k=i
                while 'PDF' in software_publishers:
                    software_publishers = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[1]/text()'%k).extract()[0]
                    k=k-1
                    
                Suppliers_and_Product_and_Price_List = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[1]/a/text()'%i).extract()[0]
                # res=es.search(index="slsa*", doc_type="SLSA_Catalogue", body={"query": {"match": {"Suppliers_and_Product_and_Price_List": Suppliers_and_Product_and_Price_List}}})
                # if (res['hits']['total'] == 0):
                slsaspiderItem['Content_of_SPP_list'] = ''
                slsaspiderItem['Content_of_Software_and_Software_Maintenance_and_Support_Terms_and_Conditions'] = ''
                slsaspiderItem['Content_of_Program_Terms_and_Conditions'] = ''    
                slsaspiderItem['Software_Publishers'] = software_publishers              
                slsaspiderItem['Suppliers_and_Product_and_Price_List'] = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[1]/a/text()'%i).extract()[0]
                slsaspiderItem['Suppliers_and_Product_and_Price_List_Link'] = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[1]/a/@href'%i).extract()[0]
                Suppliers_and_Product_and_Price_List_Link = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[1]/a/@href'%i).extract()[0]
                slsaspiderItem['Sources_of_Supply_link'] = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[2]/a/@href'%i).extract()
                Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Links = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[3]/ul/li/a/@href'%i).extract()
                slsaspiderItem['Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Link'] = ','.join(Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Links)
                Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Link = ','.join(Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Links)
                try:
                    slsaspiderItem['Program_Terms_and_Conditions_Link'] = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[4]/ul/li/a/@href'%i).extract()[0]
                    Program_Terms_and_Conditions_Link = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[4]/ul/li/a/@href'%i).extract()[0]
                    index_pdf_content(slsaspiderItem,Program_Terms_and_Conditions_Link,'Content_of_Program_Terms_and_Conditions')
                except IndexError:
                    slsaspiderItem['Program_Terms_and_Conditions_Link'] = u'NA'
                index_pdf_content(slsaspiderItem,Suppliers_and_Product_and_Price_List_Link,'Content_of_SPP_list')
                for ele in Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Links:
                    index_pdf_content(slsaspiderItem,ele,'Content_of_Software_and_Software_Maintenance_and_Support_Terms_and_Conditions')
                slsaspiderItem['date_scraped']=datetime.datetime.now()
                slsaspiderItem['server']=socket.gethostname()
                slsaspiderItem['project']=self.settings.get('BOT_NAME')
                slsaspiderItem['spider']=self.name
                yield slsaspiderItem
                # else:
                #     print("The link is:%s"%Suppliers_and_Product_and_Price_List)

                        
            else:
                Suppliers_and_Product_and_Price_List = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[2]/a/text()'%i).extract()[0]
                # res=es.search(index="slsa*", doc_type="SLSA_Catalogue", body={"query": {"match": {"Suppliers_and_Product_and_Price_List": Suppliers_and_Product_and_Price_List}}})
                # if (res['hits']['total'] == 0):
                slsaspiderItem['Content_of_SPP_list'] = ''
                slsaspiderItem['Content_of_Software_and_Software_Maintenance_and_Support_Terms_and_Conditions'] = ''
                slsaspiderItem['Content_of_Program_Terms_and_Conditions'] = ''    
                slsaspiderItem['Software_Publishers'] = software_publishers              
                slsaspiderItem['Suppliers_and_Product_and_Price_List'] = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[2]/a/text()'%i).extract()[0]
                slsaspiderItem['Suppliers_and_Product_and_Price_List_Link'] = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[2]/a/@href'%i).extract()[0]
                Suppliers_and_Product_and_Price_List_Link = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[2]/a/@href'%i).extract()[0]
                slsaspiderItem['Sources_of_Supply_link'] = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[3]/a/@href'%i).extract()
                Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Links = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[4]/ul/li/a/@href'%i).extract()
                slsaspiderItem['Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Link'] = ','.join(Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Links)
                Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Link = ','.join(Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Links)
                try:
                    slsaspiderItem['Program_Terms_and_Conditions_Link'] = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[5]/ul/li/a/@href'%i).extract()[0]
                    Program_Terms_and_Conditions_Link = response.xpath('//html/body/table[4]/tr[2]/td[2]/table/tr/td/table/tr[%s]/td[5]/ul/li/a/@href'%i).extract()[0]
                    index_pdf_content(slsaspiderItem,Program_Terms_and_Conditions_Link,'Content_of_Program_Terms_and_Conditions')
                except IndexError:
                    slsaspiderItem['Program_Terms_and_Conditions_Link'] = u'NA'
                    
                index_pdf_content(slsaspiderItem,Suppliers_and_Product_and_Price_List_Link,'Content_of_SPP_list')
                for ele in Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Links:
                    index_pdf_content(slsaspiderItem,ele,'Content_of_Software_and_Software_Maintenance_and_Support_Terms_and_Conditions')
                slsaspiderItem['date_scraped']=datetime.datetime.now()
                slsaspiderItem['server']=socket.gethostname()
                slsaspiderItem['project']=self.settings.get('BOT_NAME')
                slsaspiderItem['spider']=self.name
                yield slsaspiderItem
                # else:
                #     print("The link is:%s"%Suppliers_and_Product_and_Price_List)
            
