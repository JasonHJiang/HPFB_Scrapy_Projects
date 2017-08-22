# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from cStringIO import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import base64
from scrapyelasticsearch.scrapyelasticsearch import ElasticSearchPipeline
from elasticsearch import Elasticsearch, helpers
from datetime import datetime
from six import string_types
import json
import logging
import hashlib
import types


def json_serial(obj):
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")
    
class NasPipeline(object):
    def __init__(self, es_hosts, index_name, index_type, ingest_pipeline):
        self.es_hosts = es_hosts
        self.index_name = index_name
        self.index_type = index_type
        self.ingest_pipeline = ingest_pipeline

    @classmethod
    def from_crawler(cls, crawler):
        index_name=crawler.settings.get('ELASTICSEARCH_INDEX'),
        index_type=crawler.settings.get('ELASTICSEARCH_TYPE'),
        ingest_pipeline=crawler.settings.get('ELASTICSEARCH_PIPELINE')

        return cls(
            es_hosts=crawler.settings.get('ELASTICSEARCH_SERVERS'),
            index_name=index_name,
            index_type=index_type,
            ingest_pipeline=crawler.settings.get('ELASTICSEARCH_PIPELINE')
        )

    def process_item(self, item, spider):
        es = Elasticsearch(self.es_hosts)
        es.index(index=self.index_name, doc_type=self.index_type, body=json.dumps(dict(item), ensure_ascii=False, default=json_serial).encode("utf-8"))
        # es.index(index=self.index_name, doc_type=self.index_type, pipeline=self.ingest_pipeline, body=json.dumps(dict(item), ensure_ascii=False, default=json_serial).encode("utf-8"))
        return item

