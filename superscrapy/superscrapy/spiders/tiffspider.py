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
from superscrapy.items import TiffScrapeItem, TiffScrapeItemLoader
from scrapy.http import Request
#from scrapy.loader.processors import MapCompose, Join
from scrapy.item import Item
from scrapy.loader import ItemLoader
        
class tiffSpider(scrapy.Spider):
    name = 'tiffspider'
    allowed_domains = ['']

    def start_requests(self):
        # spath = r"/home/shared/Supertext/"
        spath = r"/home/hjiang/scrapy/pdf_folder/1"
        # print(os.listdir(spath))
        directorylist = []
        dir_list = []
        file_name_list = []
        root_name = []
        file_dir_list = []

        for roots, dirs, file in os.walk(spath,topdown = True):
            for dir in dirs:
                # print("Dir = %s" % dir)
                dir_list.append(dir)
            for file in file:
                # print("File = %s" % file)
                file_dir_list.append(roots + '/' + file)
                file_name_list.append(file)
            # print (roots)
            root_name.append(roots)

        directorylist = [dir_list,file_name_list,root_name]
        file_directory = ['file://' + file_dir for file_dir in file_dir_list]
        # print (file_directory)
        for file_dir in file_directory:
            print (file_dir)
            yield scrapy.Request(file_dir, self.parse)


    def parse(self, response):
        TiffItem = TiffScrapeItem()
        TiffItem['file_type']='Tiff'
        TiffItem['file_name']=''.join(splitext(basename(response.url)))
        # TiffItem['file_path']=[(response.url).split('Supertext')[1]]
        TiffItem['file_path']=[(response.url).split('scrapy')[1]]
        TiffItem['date_scraped']=datetime.datetime.now()
        
        final_text = []
        builder = pyocr.builders.TextBuilder()
        tools = pyocr.get_available_tools()
        # if len(tools) == 0:
        #     print("No OCR tool found")
        #     sys.exit(1)
        tool = tools[0]
        # print("Will use tool '%s'" % (tool.get_name()))

        langs = tool.get_available_languages()
        # print("Available languages: %s" % ", ".join(langs))
        lang = langs[3]
        # print("Will use lang '%s'" % (lang))

        txt = tool.image_to_string(
            Image.open('/' + response.url.split("///")[1]),
            lang=lang,
            builder=pyocr.builders.TextBuilder()
        )
        TiffItem['tiff_content']=txt

        return TiffItem
