## superscrapy
An overview of the scrapy architecture, inputs and outputs.

The tasks of this project:
- [ ] extract text from .txt files using [scrapy](https://doc.scrapy.org/en/latest/).
- [ ] extract text from .tiff files using [Tesseract-OCR](https://github.com/openpaperwork/pyocr) function.
- [ ] record all file paths, data scraped, and file types etc using the [OS.Walk](https://www.tutorialspoint.com/python/os_walk.htm) function.

## txtspider.py
Scrape text from a list of files. Create fields dynamically based on the content, fill pre-defined fields such as file_type, file_name etc. Each field represents an item.

## tiffspider.py
Scrape text from a list of files by using Tesseract-OCR function. Fill pre-defined fields such as file_type, file_name etc. Each field represents an item.

## items.py
Pre-define fields needed for both "txtspider" and "tiffspider", change the setting to allow dynamic items creations.

## pipelines.py
Scraped items are feeded to elasticsearch or output such as .csv files through pipelines. Define the index so items could be feeded to elasticsearch.

## settings.py
Various settings can be determined, in our case, we need to ensure that the pipeline to elasticsearch is enabled.

## tiff.csv & txt.csv
Outputs from scrapy

## Scrapyd
$ curl http://localhost:6800/schedule.json -d project=superscrapy -d spider=txtspider
$ curl http://localhost:6800/schedule.json -d project=superscrapy -d spider=tiffspider
