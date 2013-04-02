################################################################################
import datetime, os, glob, time, argparse
import numpy as np
from matplotlib import pyplot as plt
import cv, cv2
from SimpleCV import Color, ColorMap, Image
DEFAULT_INPUT_PATH  = "."
DEFAULT_OUTPUT_PATH = "processed_images"
DEFAULT_MINDIST     = 0.10
DEFAULT_VERBOSE     = True
IMAGE_PATTERN_VIS   = "*VISimg*.png"
IMAGE_PATTERN_NIR   = "*NIRimg*.png"
################################################################################

def findHomographyNIR_VIS(img1,img2,minDist=DEFAULT_MINDIST):
    r1,g1,b1 = img1.splitChannels()
    r2,g2,b2 = img2.splitChannels()
    m = r2.findKeypointMatch(r1, minDist=minDist)
    H = m[0].getHomography()
    return H

def align(img1, img2, H = None, minDist=DEFAULT_MINDIST):
    """align img1 against img2 by applying a perspective warp transform"""
    if H is None:
        H = findHomographyNIR_VIS(img1,img2, minDist=minDist)
    aligned_img = img1.transformPerspective(H)
    return aligned_img
        
def overlay(img1,img2, H = None, minDist=DEFAULT_MINDIST):
    a1_2 = align(img1,img2, H = H)
    if a1_2 is None:
        return None
    oimg = img2.blit(a1_2,alpha=0.5)
    return oimg
     
def cropped_match(img1,img2, H = None, minDist=DEFAULT_MINDIST):
    a1_2 = align(img1,img2, H = H)
    if a1_2 is None:
        return None
    nonblack = a1_2.colorDistance(Color.BLACK)
    nonblack_blob = nonblack.findBlobs(1)[-1]
    img_mask = nonblack_blob.hullMask()               #get the central image region
    c1 = a1_2.crop(nonblack_blob)                     #crops to bounding rectangle
    c2 = img2.crop(nonblack_blob) - img_mask.invert() #cuts of non overlaping edges
    return (c1,c2)
        

        

################################################################################
class Application:
    def __init__(self,
                 input_path  = DEFAULT_INPUT_PATH,
                 output_path = DEFAULT_OUTPUT_PATH,
                 verbose     = DEFAULT_VERBOSE,
                ):
        self.input_path = input_path
        #setup image output directory
        self.output_path = output_path
        if not os.path.isdir(output_path):
            os.mkdir(output_path)
        #make noise?
        self.verbose = verbose
        
    def lazy_load_all(self):
        fns_vis = glob.glob(os.sep.join((self.input_path,IMAGE_PATTERN_VIS)))
        fns_nir = glob.glob(os.sep.join((self.input_path,IMAGE_PATTERN_NIR)))
        for fn_vis, fn_nir in zip(sorted(fns_vis), sorted(fns_nir)):
            img_vis  = Image(fn_vis).toRGB()  #FIXME toRGB is a workaround for a bug in SimpleCV
            img_nir  = Image(fn_nir).toBGR()
            yield (img_vis, img_nir)
    
    def lazy_match_all(self, 
                       H = None, 
                       minDist = DEFAULT_MINDIST, 
                       save = False
                      ):
        for i, imgs in enumerate(self.lazy_load_all()):
            img1, img2 = imgs
            img1 = align(img1,img2, H=H, minDist=minDist)
            m12vis, m12nir = (img1, img2)
            #m12vis, m12nir = cropped_match(img1, img2, H=H, minDist=minDist)
            #m21nir, m21vis = cropped_match(img2, img1, H=H, minDist=minDist)
            #rescale images
            m12vis = m12vis.adaptiveScale((800,600))
            m12nir = m12nir.adaptiveScale((800,600))
            if save:
                opath = os.sep.join((self.output_path,'vis'))
                if not os.path.isdir(opath):
                    os.mkdir(opath)
                m12vis.save(os.sep.join((opath,'img%03d.png' % i)))
                opath = os.sep.join((self.output_path,'nir'))
                if not os.path.isdir(opath):
                    os.mkdir(opath)
                m12nir.save(os.sep.join((opath,'img%03d.png' % i)))
                #m21vis.save(os.sep.join((opath,'m2-1_VISimg%03d.png' % i)))
                #m21nir.save(os.sep.join((opath,'m2-1_NIRimg%03d.png' % i)))
            yield (m12vis, m12nir)#, m21vis, m21nir)
            
    def lazy_NRG_all(self,
                      H = None, 
                      minDist = DEFAULT_MINDIST,  
                      save = False
                     ):
        
        gen_matches = self.lazy_match_all(H=H,minDist=minDist,save=save)   
        for i, imgs in enumerate(gen_matches):
            m12vis, m12nir = imgs#, m21vis, m21nir = imgs
            r,g,b = m12vis.splitChannels()  #extract all color channels
            nir = m12nir.splitChannels()[0] #extract red channel only
            #filter the NIR images
            nir = nir.smooth('median',(5,5))#Filter((3,3))
            nrg = m12vis.mergeChannels(r=nir*2,g=r,b=g) #amplify the NIR channel
            #filter
            #nrg = nrg.smooth('median',(5,5))#Filter((3,3))
            if save:
                opath = os.sep.join((self.output_path,'nrg'))
                if not os.path.isdir(opath):
                    os.mkdir(opath)
                nrg.save(os.sep.join((opath,'img%03d.png' % i)))
                opath = os.sep.join((self.output_path,'red'))
                if not os.path.isdir(opath):
                    os.mkdir(opath)
                r.save(os.sep.join((opath,'img%03d.png' % i)))
                opath = os.sep.join((self.output_path,'nir_red'))
                if not os.path.isdir(opath):
                    os.mkdir(opath)
                nir.save(os.sep.join((opath,'img%03d.png' % i)))
#                Image(arr12nir).save(os.sep.join((opath,'nir_avg1-2_plot%03d.png' % i)))
#                pylab.imsave(os.sep.join((opath,'ndvi2-1_img%03d.png' % i)), ndvi21, pylab.cm.jet)
            yield nrg#(ndvi12, ndvi21)
                    
    def lazy_NDVI_all(self,
                      gen_matches,
                      save = False
                     ):
        
        for i, imgs in enumerate(gen_matches):
            m12vis, m12nir = imgs#, m21vis, m21nir = imgs
            #downsample inputs to improve overlap
            # down-scale and upscale the image to filter out the noise
            w, h = m12vis.size()
            #pyr1 = cv.CreateImage( (w/2, h/2), 8, 3)
            #pyr2 = cv.CreateImage( (w/2, h/2), 8, 3)
            #cv.PyrDown( m12vis.getMatrix(), pyr1)
            #cv.PyrDown( m12nir.getMatrix(), pyr2)
            #m12vis = Image(pyr1)
            #m12nir = Image(pyr2)
            #m12vis = m12vis.gaussianBlur((9,9)).scale(0.5)
            #m12nir = m12nir.gaussianBlur((9,9)).scale(0.5)
            arr12red = m12vis.splitChannels()[0].getNumpy()[:,:,0].astype(np.float64) #extract red channel only
            arr12nir = m12nir.getGrayNumpy().astype(np.float64)#m12nir.splitChannels()[0].getNumpy()[:,:,0].astype(np.float64) #extract red channel only
            #arr21red = m21vis.getNumpy()[:,:,0].astype(np.float64) #extract red channel only
            #arr21nir = m21nir.getNumpy()[:,:,0].astype(np.float64) #extract red channel only
            
            #arr12nir /= arr12nir.max()
            #arr12red /= arr12red.max()
            #arr12nir *= 2.0
            num   = (arr12nir - arr12red)
            num   = np.where(num > 0, num, 0) #zero out negatives
            denom = (arr12nir + arr12red)
            ndvi12 = num/denom
            #ndvi21 = (arr21nir - arr21red)/(arr21nir + arr21red)
            f12 = plt.figure()
            f12.set_frameon(False)
            ax12 = f12.add_subplot(111)
            ax12.set_axis_off()
            ax12.patch.set_alpha(0.0) 
            ndvi12_plot = ax12.imshow(ndvi12.transpose(), cmap=plt.cm.hot, interpolation="nearest")
            #cbar12 = f12.colorbar(ndvi12_plot)
            #ndvi12_plot = pylab.imshow(ndvi12, cmap=pylab.cm.hot, interpolation="nearest")
            if save:
                opath = os.sep.join((self.output_path,'ndvi'))
                if not os.path.isdir(opath):
                    os.mkdir(opath)
                f12.savefig(os.sep.join((opath,'img%03d.png' % i)))
                opath = os.sep.join((self.output_path,'red'))
                if not os.path.isdir(opath):
                    os.mkdir(opath)
                Image(arr12red).save(os.sep.join((opath,'img%03d.png' % i)))
                opath = os.sep.join((self.output_path,'nir_red'))
                if not os.path.isdir(opath):
                    os.mkdir(opath)
                Image(arr12nir).save(os.sep.join((opath,'img%03d.png' % i)))
#                pylab.imsave(os.sep.join((opath,'ndvi2-1_img%03d.png' % i)), ndvi21, pylab.cm.jet)
            yield ndvi12#(ndvi12, ndvi21)
################################################################################
# MAIN
################################################################################
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_path", 
                        help = "path for img output",
                        default = DEFAULT_INPUT_PATH,
                       ) 
    parser.add_argument("-o", "--output_path", 
                        help = "path for img output",
                        default = DEFAULT_OUTPUT_PATH,
                       )                      
    parser.add_argument("-v", "--verbose", 
                        help="increase output verbosity",
                        action="store_true",
                        default = DEFAULT_VERBOSE,
                       )
    args = parser.parse_args()
    #apply configuration arguments to constructor
    app = Application(input_path        = args.input_path,
                      output_path       = args.output_path,
                      verbose           = args.verbose,
                     )
    ###########################################################
    # for processing timelapse
    ###########################################################
    import shelve
    config = shelve.open("config.db")
    H = config['H']
    gen_matches = app.lazy_match_all(H=H,save=True)
    #list(gen_matches)
    gen_nrg = app.lazy_NRG_all(H=H,save=True)
    #nrg_img = gen_nrg.next()
    #pull all images through processing pipe
    NRGs = list(gen_nrg)
    gen_ndvi = app.lazy_NDVI_all(gen_matches,save=True)
    #ndvi_img = gen_ndvi.next()
    #pull all images through processing pipe
    #NDVIs = list(gen_ndvi)
    
    
    
    

