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
from scrapexml.items import ScrapexmlItem, ScrapexmlItemLoader
from scrapy.http import Request
#from scrapy.loader.processors import MapCompose, Join
from scrapy.item import Item
from scrapy.loader import ItemLoader



class xmlspider(scrapy.Spider):
    name = "xmlspider"
    allowed_domains = ['']

    def start_requests(self):
        os.chdir('scrapexml')
        # start_urls = ['file:///home/hjiang/scrapexml/full_database.xml']
        with open('full_database.xml', 'r') as myfile:
            data=myfile.read()
        myfile.close()
        lists = data.split('<drug type=')
        for i in range(1,len(lists)):
            temp = ['<drug type=',lists[i]]
            lists[i] = ''.join(temp)
        for i in range(1,len(lists)):
            file = open('/home/hjiang/scrapexml/xmlfolder/%s.xml'%i, 'w+')
            file.write(lists[i])
            file.close()
            yield scrapy.Request('file:///home/hjiang/scrapexml/xmlfolder/%s.xml'%i, self.parse)
            os.remove('/home/hjiang/scrapexml/xmlfolder/%s.xml'%i)
    def parse(self, response):
            XmlspiderItem = ScrapexmlItem()
            print(response.url)
            sel = Selector(text = response.body)
            XmlspiderItem['name'] = sel.xpath('//body/drug/name/text()').extract()[0]
            name = sel.xpath('//body/drug/name/text()').extract()[0]
            XmlspiderItem['synonyms'] = '\n'.join(sel.xpath('//body/drug/synonyms/synonym/text()').extract())
            atc_codes = []
            atc_codes = sel.xpath('//body/drug/atc-codes/atc-code/@code').extract()
            if atc_codes == []:
                XmlspiderItem['atc_code'] = 'NA'
            else:
                atc_sub_codes = sel.xpath('//body/drug/atc-codes/atc-code/level').extract()
                atc_sub_codes_list = []
                for ele in atc_sub_codes:
                    sel1 = Selector(text = ele)
                    atcsubcodes = sel1.xpath('//body/level/@code').extract()
                    if atcsubcodes == []:
                        atcsubcodes = ['NA']
                    atc_sub_codes_list.append(atcsubcodes[0])
                
                atc_sub_names = sel.xpath('//body/drug/atc-codes/atc-code/level').extract()
                atc_sub_names_list = []
                for ele in atc_sub_names:
                    sel1 = Selector(text = ele)
                    atcsubnames = sel1.xpath('//body/level/text()').extract()
                    if atcsubnames == []:
                        atcsubnames = ['NA']
                    atc_sub_names_list.append(atcsubnames[0])
                
                new_list = []
                i = 0
                while i<len(atc_sub_names_list):
                    new_list.append(atc_sub_names_list[i:i+4])
                    i+=4
                for i in range(len(new_list)):
                    new_list[i] = list(reversed(new_list[i]))
                atc_sub_names_list = []
                atc_sub_names_list = new_list
                
                new_list = []
                i = 0
                while i<len(atc_sub_codes_list):
                    new_list.append(atc_sub_codes_list[i:i+4])
                    i+=4
                for i in range(len(new_list)):
                    new_list[i] = list(reversed(new_list[i]))
                atc_sub_codes_list = []
                atc_sub_codes_list = new_list    
                
                atc_code_list = []
                atc_code_sub_list = []
                for i in range(0,len(atc_codes)):
                    for j in range(0,len(atc_sub_codes_list[i])):
                        print(i + j)
                        atc_code_sub_list.append(atc_sub_names_list[i][j] + '(' + atc_sub_codes_list[i][j] + ')/')
                    atc_code_list.append(''.join(atc_code_sub_list) + name + '(' + atc_codes[i] + ')')
                XmlspiderItem['atc_code'] = '\n'.join(atc_code_list)
            
            dosages_form = sel.xpath('//body/drug/dosages/dosage/form').extract()
            dosageform_list = []
            for ele in dosages_form:
                sel1 = Selector(text = ele)
                dosageform = sel1.xpath('//body/form/text()').extract()
                if dosageform == []:
                    dosageform = ['NA']
                dosageform_list.append(dosageform[0])

            dosages_route = sel.xpath('//body/drug/dosages/dosage/route').extract()
            dosageroute_list = []
            for ele in dosages_route:
              sel1 = Selector(text = ele)
              dosageroute = sel1.xpath('//body/route/text()').extract()
              if dosageroute == []:
                  dosageroute = ['NA']
              dosageroute_list.append(dosageroute[0])

            dosages_strength = sel.xpath('//body/drug/dosages/dosage/strength').extract()
            dosagestrength_list = []
            for ele in dosages_strength:
                sel1 = Selector(text = ele)
                dosagestrength = sel1.xpath('//body/strength/text()').extract()
                if dosagestrength == []:
                    dosagestrength = ['NA']
                dosagestrength_list.append(dosagestrength[0])

            dosages_list = []
            for i in range(0,len(dosages_form)):
                dosages_list.append('form:' + dosageform_list[i] + ' route: ' + dosageroute_list[i] + ' strength: ' + dosagestrength_list[i])
            XmlspiderItem['dosages'] = '\n'.join(dosages_list)
            
            categories_list = []
            category = sel.xpath('//body/drug/categories/category/category').extract()
            caetegory_list = []
            for ele in category:
                sel1 = Selector(text = ele)
                category1 = sel1.xpath('//body/category/text()').extract()
                if category1 == []:
                    category1 = ['NA']
                caetegory_list.append(category1[0])
            
            
            mesh_id = sel.xpath('//body/drug/categories/category/mesh-id').extract()
            meshid_list = []
            for ele in mesh_id:
                sel1 = Selector(text = ele)
                meshid = sel1.xpath('//body/mesh-id/text()').extract()
                if meshid == []:
                    meshid = ['NA']
                meshid_list.append(meshid[0])
                
            for i in range(0,len(category)):
                categories_list.append('category:' + caetegory_list[i] + ' mesh-id: ' + meshid_list[i])
            XmlspiderItem['categories'] = '\n'.join(categories_list)
            
            return XmlspiderItem
