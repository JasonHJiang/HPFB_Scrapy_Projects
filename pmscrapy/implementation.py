import layout_scanner
from cStringIO import StringIO

file_and_name = '/home/hjiang/pmscrapy/pdf_folder/00000001.PDF'
folder = '/home/hjiang/scrapy/'
images_folder = '/homne/hjiang/scrapy/tmp/'
file_name = '00002207.PDF'
output_name = 'test2.txt'
pwd = ''

toc=layout_scanner.get_toc(file_and_name, pwd)
len(toc)


pages=layout_scanner.get_pages(file_and_name)
# len(pages)

for page in pages:
  layout_scanner.write_file(folder,output_name,page)
