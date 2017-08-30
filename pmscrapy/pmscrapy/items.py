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

class pmScrapeItemLoader(ItemLoader):
    def add_fallback_css(self, field_name, css, *processors, **kw):
        if not any(self.get_collected_values(field_name)):
            self.add_css(field_name, css, *processors, **kw)

class pmScrapeItem(scrapy.Item):
    def __setitem__(self, key, value):
          if key not in self.fields:
              self.fields[key] = Field()
          self._values[key] = value
          
          file_type = Field()
          file_name = Field()
          file_path = Field()
          date_scraped = Field()
          content = Field()
          pm_page_one = Field()
          pm_number = Field()
          content_length = Field()
          atc_code = Field()
          synonyms=  Field()
          categories = Field()
          dosages = Field()
          pt_term = Field()
          matchiterm = Field()
          contentindex = Field()
          pt_term_index = Field()
