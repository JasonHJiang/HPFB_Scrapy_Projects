# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import dateparser
from scrapy.item import Item, Field
from scrapy.loader.processors import MapCompose, Join
from scrapy.loader import ItemLoader

class SlsascrapyItemLoader(ItemLoader):
    def add_fallback_css(self, field_name, css, *processors, **kw):
        if not any(self.get_collected_values(field_name)):
            self.add_css(field_name, css, *processors, **kw)
            
class SlsascrapyItem(scrapy.Item):
    def __setitem__(self, key, value):
          if key not in self.fields:
              self.fields[key] = Field()
          self._values[key] = value
          
          Software_Publishers	= Field()
          Suppliers_and_Product_and_Price_List = Field()
          Suppliers_and_Product_and_Price_List_Link = Field()
          Content_of_SPP_list = Field()
          Sources_of_Supply_link = Field()
          Software_and_Software_Maintenance_and_Support_Terms_and_Conditions_Link = Field()
          Content_of_Software_and_Software_Maintenance_and_Support_Terms_and_Conditions = Field()
          Program_Terms_and_Conditions_Link = Field()
          Content_of_Program_Terms_and_Conditions = Field()
          date_scraped = Field()
          server = Field()
          project = Field()
          spider = Field()
