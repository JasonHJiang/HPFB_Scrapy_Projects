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
from pmscrapy.items import pmScrapeItem, pmScrapeItemLoader
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

### system setting ###
es = Elasticsearch('http://elastic-gate.hc.local:80')
reload(sys)  
sys.setdefaultencoding('utf8')
csv.field_size_limit(sys.maxsize)

### open drug-bank database ###
f = open('xmltest.csv', 'rb')
reader = csv.reader(f)
content_list = []
for row in reader:
    content_list.append(row)    
for ele in content_list:
    if ele[2] == 'Fica':
          content_list.remove(ele)
          
def append_exception(list,before, after):
    for i in range(len(list)):
        if list[i][2] == before:
            new_content = list[i]
            new_content[2] = after
    list.append(new_content)

append_exception(content_list,'Ursodeoxycholic acid','Ursodiol')
append_exception(content_list,'Alendronic acid','alendronate')
append_exception(content_list,'Somatotropin','Somatropin')
append_exception(content_list,'Amiodarone','Amiodorone')
append_exception(content_list,'Etidronic acid','Etidronate')
append_exception(content_list,'Estrone sulfate','Estropipate')
append_exception(content_list,'Verapamil','Veramapil')
append_exception(content_list,'Gadobenic acid','Gadobenate')
append_exception(content_list,'Antithymocyte immunoglobulin (rabbit)','Anti-thymocyte Globulin [Rabbit]')
append_exception(content_list,'Etacrynic acid','Ethacrynic')
append_exception(content_list,'Nitroglycerin','Nitroglycérine')
append_exception(content_list,'Antihemophilic factor human','Antihemophilic factor')
append_exception(content_list,'Valaciclovir','Valacyclovir')
append_exception(content_list,'Agalsidase beta','Agalsidase alfa')
name_list = []
synonyms_list = []
for ele in range(1,len(content_list)):
    name_list.append(content_list[ele][2])
    synonyms_content = content_list[ele][1].split('\n')
    synonyms_list.append(synonyms_content)

### open PTterm pmNumber list ###
f = open('PTterm_pmNumber.csv', 'rb')
reader = csv.reader(f)
ptpm_list = []
for row in reader:
    ptpm_list.append(row)
pmnumber_list = []
for ele in range(1,len(ptpm_list)):
    pmnumber_list.append(ptpm_list[ele][1])

def extract_key(v):
    return v[1]
    
data = sorted(ptpm_list[0:], key=extract_key)
newlist = [['PT_term','pm_number']]
tem = [
    [k,[x[0] for x in g]]
    for k, g in itertools.groupby(data, extract_key)
]
for i in range(len(tem)):
    tem[i][1] = ','.join(tem[i][1])
for ele in tem:
    newlist.append(ele)
ptpm_list = newlist

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
    
    fname = '/home/hjiang/pmscrapy/pdf_folder/' + fname
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
    
    remoteFile = urlopen(Request(url)).read()
    memoryFile = StringIO(remoteFile)
    pdfFile = PdfFileReader(memoryFile)
    
    if pdfFile.isEncrypted:
        pdfFile.decrypt('')
    
    for pageNum in xrange(pdfFile.getNumPages()):
            currentPage = pdfFile.getPage(pageNum)
            #currentPage.mergePage(watermark.getPage(0))
            writer.addPage(currentPage)
    
    outputStream = open('/home/hjiang/pmscrapy/pdf_folder/%s'%basename(url),"wb")
    writer.write(outputStream)
    outputStream.close()
    
class pmspider(scrapy.Spider):
    name = 'pmspider'
    # allowed_domains = ['pdf.hres.ca']
    allowed_domains = ['']
    
    def start_requests(self):
        # check duplications
        with open('list.txt', 'r+') as myfile:
            data=myfile.read()
        list = data.split('\n')
        list = filter(None, list)
        while True:
            count = 0
            for file in list:
                file_name = file.split('.PDF')[0]
                res=es.search(index="test_pm", body={"query": {"match": {"pm_number": file_name}}})
                if (res['hits']['total'] != 0):
                    list.remove(file)
                    print('remove' + file)
                    count = count + 1
            if count == 0:
                break
        list = filter(None, list)
        with open('list.txt', 'w') as myfile:
            for ele in list:
                myfile.write(ele + '\n')
        
        ### Check whether the pdf file consists of scanned images or full texts
        list.sort(key=natural_keys)
        file_directory = []
        file_directory = ['https://pdf.hres.ca/dpd_pm/' + file_dir for file_dir in list]
        print(file_directory)
        for file_dir in file_directory:
            download_pdf(file_dir)
            local_file = basename(file_dir)
            print('local file is ' + local_file)
            # local_file = basename(file_dir)
            if ' '.join(convert(local_file, pages=[0]).split()) == '':
                pypdf_to_image.convert(('file:///home/hjiang/pmscrapy/pdf_folder/' + local_file))
            else:
                yield scrapy.Request(('file:///home/hjiang/pmscrapy/pdf_folder/' + local_file), self.txtparser)
                
        ### OCRtest on images
        spath = r"/home/hjiang/pmscrapy/pdftoimage"
        directorylist = []
        dir_list = []
        file_name_list = []
        root_name = []
        file_dir_list = []
        file_directory = []
        for roots, dirs, file in os.walk(spath,topdown = True):
            root_name.append(roots)
            for dir in dirs:
                dir_list.append(dir)
            for file in file:
                file_dir_list.append(roots + '/' + file)
                file_name_list.append(file)

        file_dir_list.sort(key=natural_keys)
        dir_list.sort(key=natural_keys)
        file_name_list.sort(key=natural_keys)
        root_name.sort(key=natural_keys)
        directorylist = [dir_list,file_name_list,root_name]
        file_directory = [file_dir for file_dir in file_dir_list]
        file_directory.sort(key=natural_keys)
        
        for i in range(1,(len(directorylist[2]))):
            file_obj = codecs.open("/home/hjiang/pmscrapy/pdftoimage_text/%s.txt"%(basename(directorylist[2][i])), 'a',encoding='utf-8')
            count = 0
            for file in file_directory:
                if (file.find(directorylist[2][i]) != (-1)):
                    if file.endswith('.jpeg'):
                        print(file)
                        filedata = OCRtest(file)
                        count = count + 1
                        file_obj.write(filedata + '\n\n\n' + 'Page:%s'%count)

        ### Start scraping
        spath = r"/home/hjiang/pmscrapy/pdftoimage_text"
        file_list = []
        for roots, dirs, file in os.walk(spath,topdown = True):
            for file in file:
                file = 'file://' + roots + '/' + file
                yield scrapy.Request(file, self.imageparser)

    def txtparser(self, response):
        pmspiderItem = pmScrapeItem()
        pdf_file = basename(response.url)
        
        ### clean pm_page_one ###
        pmspiderItem['pm_page_one'] = ' '.join(convert(pdf_file, pages=[0]).split())
        pm_page_one=' '.join(convert(pdf_file, pages=[0]).split()).encode('utf-8').lower()
        pm_page_one = pm_page_one.replace('classification','')
        replace_punctuation = string.maketrans(string.punctuation, ' '*len(string.punctuation))
        pm_page_one = pm_page_one.translate(replace_punctuation)
        pm_page_one = re.sub(' +',' ',pm_page_one.lower())
        ### typo correction ###
        # pm_page_one = pm_page_one.replace('somatropin','somatotropin')
        pm_page_one = pm_page_one.replace('p r o d u c t m o n o g r a p h','')
        pm_page_one = pm_page_one.replace('product monograph','')
        f = open('pmpageone.txt','w')
        f.write(pm_page_one)
        f.close()
        
        pmspiderItem['content'] = ' '.join(convert(pdf_file).split())
        content = ' '.join(convert(pdf_file).split())
        f = open('/home/hjiang/pmscrapy/pdf_text/pdftext.txt','w')
        f.write(content)
        lang = language.from_file('/home/hjiang/pmscrapy/pdf_text/pdftext.txt')
        pmspiderItem['language'] = lang
        f.close()
        temp = (response.url).split('file://')[1]
        fp = open(temp)
        parser = PDFParser(fp)
        doc = PDFDocument(parser)
        parser.set_document(doc)
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pages = layout_scanner.get_pages(response.url)
        
        pmspiderItem['file_type']='PDF'
        pmspiderItem['pm_number']=splitext(basename(response.url))[0].decode('utf-8')
        pm_number = splitext(basename(response.url))[0].decode('utf-8')
        pmspiderItem['file_path']='https://pdf.hres.ca/dpd_pm/%s.PDF'%pm_number
        file_path='https://pdf.hres.ca/dpd_pm/%s.PDF'%pm_number
        pmspiderItem['file_name']=basename(file_path).decode('utf-8')
        pmspiderItem['date_scraped']=datetime.datetime.now()
        pmspiderItem['server']=socket.gethostname()
        pmspiderItem['project']=self.settings.get('BOT_NAME')
        pmspiderItem['spider']=self.name
        pmspiderItem['content_length']=len(content)
        # pmspiderItem['pt_term_index']=findItem(ptpm_list,pm_number)[0][0]
        # pt_term_index=findItem(ptpm_list,pm_number)[0][0]
        # pmspiderItem['pt_term']=ptpm_list[pt_term_index][1]
      
        
        pt_term_index = []
        pt_term_index=findItem(ptpm_list,pm_number)
        if pt_term_index == []:
            pmspiderItem['pt_term'] = 'NA'
            pmspiderItem['pt_term_index'] = 'NA'
        else:
            pmspiderItem['pt_term'] = ptpm_list[pt_term_index[0][0]][1]
            pmspiderItem['pt_term_index'] = pt_term_index[0][0]
        
        count = 0
        for k in range(len(name_list)):
            if count >= 1:
                break
            text = name_list[k].translate(replace_punctuation)
            ele_list = text.split(' ')
            if len(ele_list) <= 4:
                ele_list = list(itertools.permutations(ele_list))
            else:
                ele_list = [' '.join(ele_list)]
            for i in range(len(ele_list)):
                ele_list[i] = ' '.join(ele_list[i])
                if ele_list[i].lower() in pm_page_one.lower():
                    content_index = k + 1
                    pmspiderItem['atc_code']=content_list[content_index][0]
                    pmspiderItem['synonyms']=content_list[content_index][1]
                    pmspiderItem['categories']=content_list[content_index][3]
                    pmspiderItem['dosages']=content_list[content_index][4]
                    pmspiderItem['matchiterm'] = name_list[k]
                    pmspiderItem['contentindex'] = content_index
                    count = count + 1
                    print('yes')
                    break
            # if count == 0:
            #     if synonyms_list[k] == '':
            #         print('empty list')
            #         break
            #     else:
            #         for synonyms in synonyms_list[k]:
            #             if synonyms == '':
            #                 print('missing value')
            #                 break
            #             if synonyms.lower() in pm_page_one.lower():
            #                 print("This is synonyms blablabla:%s"%synonyms)
            #                 content_index = k + 1
            #                 pmspiderItem['atc_code']=content_list[content_index][0]
            #                 pmspiderItem['synonyms']=content_list[content_index][1]
            #                 pmspiderItem['categories']=content_list[content_index][3]
            #                 pmspiderItem['dosages']=content_list[content_index][4]
            #                 pmspiderItem['matchiterm'] = synonyms
            #                 pmspiderItem['contentindex'] = content_index
            #                 count = count + 1
            #                 print('yes1')
            #                 break
        if count == 0:
            pmspiderItem['atc_code']= 'NA'
            pmspiderItem['synonyms']= 'NA'
            pmspiderItem['categories']= 'NA'
            pmspiderItem['dosages']= 'NA'
            pmspiderItem['matchiterm'] = 'NA'
            pmspiderItem['contentindex'] = 'NA'
            print('no')
        os.remove(temp) 
        return pmspiderItem

    def imageparser(self, response):
        pmspiderItem = pmScrapeItem()
        temp = (response.url).split('file://')[1]
        pdf_file = basename(response.url)
        pmspiderItem['pm_page_one']=((response.body).split('Page:1')[0]).decode('utf-8').replace("\n", "")
        pm_page_one=((response.body).split('Page:1')[0]).replace("\n", "")
        replace_punctuation = string.maketrans(string.punctuation, ' '*len(string.punctuation))
        pm_page_one = pm_page_one.translate(replace_punctuation)
        pm_page_one = re.sub(' +',' ',pm_page_one.lower())
        pm_page_one.replace('somatropin','somatotropin')
        f = open('pmpageone.txt','w')
        f.write(pm_page_one)
        f.close()
        
        pmspiderItem['content']=response.body
        content = response.body
        pmspiderItem['file_type']='PDF'
        pmspiderItem['pm_number']=splitext(basename(response.url))[0].decode('utf-8')
        pm_number = splitext(basename(response.url))[0].decode('utf-8')
        pmspiderItem['id']=pm_number
        pmspiderItem['file_path']='https://pdf.hres.ca/dpd_pm/%s.PDF'%pm_number
        file_path='https://pdf.hres.ca/dpd_pm/%s.PDF'%pm_number
        pmspiderItem['file_name']=''.join(splitext(basename(file_path))).decode('utf-8')
        pmspiderItem['date_scraped']=datetime.datetime.now()
        pmspiderItem['server']=socket.gethostname()
        pmspiderItem['project']=self.settings.get('BOT_NAME')
        pmspiderItem['spider']=self.name
        pmspiderItem['content_length']=len(response.body)
        
        f = open('/home/hjiang/pmscrapy/pdf_text/pdftext.txt','w')
        f.write(content)
        lang = language.from_file('/home/hjiang/pmscrapy/pdf_text/pdftext.txt')
        pmspiderItem['language'] = lang
        f.close()

        if pm_number in pmnumber_list:
            pt_term_index=pmnumber_list.index(pm_number)
            pmspiderItem['pt_term'] = ptpm_list[pt_term_index][0]
            pmspiderItem['pt_term_index'] = pt_term_index
        else:
            pmspiderItem['pt_term'] = 'NA'
            pmspiderItem['pt_term_index'] = 'NA'


        count = 0
        for k in range(len(name_list)):
            if count >= 1:
                break
            text = name_list[k].translate(replace_punctuation)
            ele_list = text.split(' ')
            if len(ele_list) <= 4:
                ele_list = list(itertools.permutations(ele_list))
            else:
                ele_list = [' '.join(ele_list)]
            for i in range(len(ele_list)):
                ele_list[i] = ' '.join(ele_list[i])
                if ele_list[i].lower() in pm_page_one.lower():
                    content_index = k + 1
                    pmspiderItem['atc_code']=content_list[content_index][0]
                    pmspiderItem['synonyms']=content_list[content_index][1]
                    pmspiderItem['categories']=content_list[content_index][3]
                    pmspiderItem['dosages']=content_list[content_index][4]
                    pmspiderItem['matchiterm'] = name_list[k]
                    pmspiderItem['contentindex'] = content_index
                    count = count + 1
                    break
            # if count == 0:
            #     for synonyms in synonyms_list[k]:
            #         if synonyms == '':
            #             break
            #         elif synonyms.lower() in pm_page_one.lower():
            #             content_index = k + 1
            #             pmspiderItem['atc_code']=content_list[content_index][0]
            #             pmspiderItem['synonyms']=content_list[content_index][1]
            #             pmspiderItem['categories']=content_list[content_index][3]
            #             pmspiderItem['dosages']=content_list[content_index][4]
            #             pmspiderItem['matchiterm'] = name_list[k]
            #             pmspiderItem['contentindex'] = content_index
            #             count = count + 1
            #             break
        if count == 0:
            pmspiderItem['atc_code']= 'NA'
            pmspiderItem['synonyms']= 'NA'
            pmspiderItem['categories']= 'NA'
            pmspiderItem['dosages']= 'NA'
            pmspiderItem['matchiterm'] = 'NA'
            pmspiderItem['contentindex'] = 'NA'
        os.remove(temp) 
        return pmspiderItem
     
