import image as Img
from wand.image import Image
import uuid
import numpy as np
import glob
import os
import sys
import os.path
from os.path import basename

def convert(filepdf):
    #used to generate temp file name. so we will not duplicate or replace anything
    uuid_set = str(uuid.uuid4().fields[-1])[:5]
    try:
        #now lets convert the PDF to Image
        #this is good resolution As far as I know
        with Image(filename=filepdf, resolution=400) as img:
            #keep good quality
            img.compression_quality = 1000
            #save it to tmp name
            new_folder_name = (os.path.basename(filepdf)).split('.PDF')[0]
            new_folder_path = "/home/hjiang/superlist/pdftoimage/%s" % new_folder_name
            os.makedirs(new_folder_path)
            name = basename(filepdf).split('.')[0]
            img.save(filename=new_folder_path + "/%s.jpeg" % name)
            print(uuid_set)
    except Exception, err:
        #always keep track the error until the code has been clean
        print err
        return False
    else:
        """
        We finally success to convert pdf to image. 
        but image is not join by it self when we convert pdf files to image. 
        now we need to merge all file
        """
        pathsave = []
        print('A')
        try:
            #search all image in temp path. file name ends with uuid_set value
            # new_folder_name = (os.path.basename(filepdf)).split('.PDF')[0]
            # print(new_folder_name)
            # new_folder_path = "/home/hjiang/superlist/pdftoimage/%s" % new_folder_name
            # print(new_folder_path)
            # os.makedirs(new_folder_path)
            list_im = glob.glob(new_folder_path + "/%s*.jpeg" % uuid_set)
            print('B')
            list_im.sort() #sort the file before joining it
            print('C')
            imgs = [Img.open(i) for i in list_im]
            print('D')
            #now lets Combine several images vertically with Python
            min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
            print('E')
            imgs_comb = np.vstack(
                (np.asarray(i.resize(min_shape)) for i in imgs))
            print('F')
            # for horizontally  change the vstack to hstack
            imgs_comb = Img.fromarray(imgs_comb)
            print('G')
            pathsave = new_folder_path + "MyPdf%s.jpeg" % uuid_set
            print('H')
            #now save the image
            imgs_comb.save(pathsave)
            print('I')
            #and then remove all temp image
            for i in list_im:
                os.remove(i)
            print('J')
        except Exception, err:
            print err 
            return False
        return pathsave

if __name__ == "__main__":
     arg = sys.argv[1]
     result = convert(arg)
     if result:
        print "[*] Succces convert %s and save it to %s" % (arg, result)
     else:
        print "[!] Whoops. something wrong dude. enable err var to track it"
