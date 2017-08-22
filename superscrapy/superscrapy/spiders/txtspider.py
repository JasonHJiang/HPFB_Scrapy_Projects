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
from superscrapy.items import TxtScrapeItem, TxtScrapeItemLoader
from scrapy.http import Request
#from scrapy.loader.processors import MapCompose, Join
from scrapy.item import Item
from scrapy.loader import ItemLoader

class txtSpider(scrapy.Spider):
    name = 'txtspider'
    allowed_domains = ['']

    def start_requests(self):
        spath = r"/home/hjiang/SuperText_txt_Files/"
        # spath = r"/home/hjiang/sample/Text/TEXT1/"
        directorylist = []
        dir_list = []
        file_name_list = []
        root_name = []
        file_dir_list = []

        for roots, dirs, file in os.walk(spath,topdown = True):
            for dir in dirs:
                dir_list.append(dir)
            for file in file:
                file_dir_list.append(roots + '/' + file)
                file_name_list.append(file)
            root_name.append(roots)

        directorylist = [dir_list,file_name_list,root_name]
        file_directory = ['file://' + file_dir for file_dir in file_dir_list]
        for file_dir in file_directory:
            yield scrapy.Request(file_dir, self.parse)

    def parse(self, response):
        TxtItem = TxtScrapeItem()
        TxtItem['file_type']='Text'
        TxtItem['file_name']=''.join(splitext(basename(response.url)))
        TxtItem['file_path']=(response.url).split('SuperText_txt_Files')[1]
        TxtItem['date_scraped']=datetime.datetime.now()
        TxtItem['entire_content']=response.body
        thebody = response.body

        split_up = thebody.split('<fields__end>')[0]
        split_down = thebody.split('<fields__end>')[1]
        sel = Selector(text = split_up)
        up_name_lists = sel.xpath('//body/node()').extract()
        up_name_lists = [i.strip() for i in up_name_lists]
        up_name_lists = [i for i in up_name_lists if i != '']
        up_content_lists = sel.xpath('//body/node()/text()').extract()
        for i in range(0,len(up_name_lists)):
            up_name_lists[i] = (up_name_lists[i].split('<')[1]).split('>')[0]
            TxtItem[up_name_lists[i]] = up_content_lists[i]
        TxtItem['other_content']=split_down

        return TxtItem
        
