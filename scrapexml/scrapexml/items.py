# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
import dateparser
from scrapy.item import Item, Field
# from scrapy.loader.processors import MapCompose, Join
from scrapy.loader import ItemLoader

class ScrapexmlItemLoader(ItemLoader):
    def add_fallback_css(self, field_name, css, *processors, **kw):
        if not any(self.get_collected_values(field_name)):
            self.add_css(field_name, css, *processors, **kw)


class ScrapexmlItem(scrapy.Item):
    def __setitem__(self, key, value):
        if key not in self.fields:
            self.fields[key] = Field()
        self._values[key] = value
    # define the fields for your item here like:
    # name = scrapy.Field()
        name = Field()
        synonyms = Field()
        atc_code = Field()
        dosage = Field()
        categories = Field()
        synonyms = Field()
        synonyms = Field()
