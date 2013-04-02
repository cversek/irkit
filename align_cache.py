################################################################################
import datetime, os, glob, time, argparse
import numpy as np
from matplotlib import pyplot as plt
import cv, cv2
from SimpleCV import Color, ColorMap, Image
from process import align, overlay, findHomographyNIR_VIS
DEFAULT_INPUT_PATH  = "."
DEFAULT_OUTPUT_PATH = "processed_images"
DEFAULT_MINDIST     = 0.10
DEFAULT_VERBOSE     = True
IMAGE_PATTERN_VIS   = "*VISimg*.png"
IMAGE_PATTERN_NIR   = "*NIRimg*.png"
################################################################################

def show_overlay(img1,im2):
    overlay(img1,img2, H = x).show()

    def lazy_load_all(self):
        fns_vis = glob.glob(os.sep.join((self.input_path,IMAGE_PATTERN_VIS)))
        
        for fn_vis, fn_nir in zip(sorted(fns_vis), sorted(fns_nir)):
            img_vis  = Image(fn_vis)
            img_nir  = Image(fn_nir)
            yield (img_vis, img_nir)
    

################################################################################
# MAIN
################################################################################
if __name__ == "__main__":
    import argparse, shelve
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_path", 
                        help = "path of files",
                        default = DEFAULT_INPUT_PATH,
                       )
    parser.add_argument("-a", "--align", 
                        help = "image to align",
                        default = None,
                       ) 
    parser.add_argument("-t", "--template", 
                        help = "image template to align to",
                        default = None,
                       )  
    args = parser.parse_args()
    ###########################################################
    input_path = args.input_path
    if args.align is None:
        args.align    = sorted(glob.glob(os.sep.join((input_path,IMAGE_PATTERN_VIS))))[-1] #choose latest
    if args.template is None:
        args.template = sorted(glob.glob(os.sep.join((input_path,IMAGE_PATTERN_NIR))))[-1] #choose latest
    print args.align
    print args.template
    img1 = Image(args.align)
    img2 = Image(args.template)
    res = ""
    H = None
    while not res in ["y","Y"]:
        H = findHomographyNIR_VIS(img1,img2)
        overlay(img1,img2,H=H).show()
        res = raw_input("Keep [y/N]? ")


    config = shelve.open("config.db")
    config['H'] = H
    config.close()


