################################################################################
import datetime, os, glob, time, argparse
import numpy, cv, cv2
from dual_camera import DualCamera
#monkey patch the SimpleCV class to fix homography calculation in 
#Image.findKeypointMatch
from ImageClass2 import Image2 as Image 

DEFAULT_INPUT_PATH  = "raw_images"
DEFAULT_OUTPUT_PATH = "processed_images"
DEFAULT_VERBOSE     = True
IMAGE_PATTERN_VIS   = "*VISimg*.png"
IMAGE_PATTERN_IR    = "*IRimg*.png"
################################################################################

def align(img1, img2, crop_intersection = True):
    """align img1 against img2 by applying a perspective warp transform"""
    h1,w1 = img1.size()
    h2,w2 = img2.size()
    h = min(h1,h2)
    w = min(w1,w2)
    
    #extract the homography matrix using keypoint matching
    #print "Finding matching features ..."
    res = img2.findHomography(img1)

    if not res is None:
        homo, mask = res

        img1_array = numpy.array(img1.getMatrix())
        aligned_array = cv2.warpPerspective(src = img1_array,
                                            M = homo,
                                            dsize = (h,w),
                                            flags = cv2.INTER_CUBIC,
                                           )  
                                   
        aligned_img = Image(aligned_array)
        if crop_intersection:
            cropped_img = aligned_img
            return cropped_img
        else:
            return aligned_img
    else:
        return None
        

        

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
        fns_ir = glob.glob(os.sep.join((self.input_path,IMAGE_PATTERN_IR)))
        for fn_vis, fn_ir in zip(sorted(fns_vis), sorted(fns_ir)):
            img_vis = Image(fn_vis)
            img_ir = Image(fn_ir)
            yield (img_vis, img_ir)
    
    def lazy_align_all(self, save = False):
        if save:
            opath = os.sep.join((self.output_path,'tmp_aligned'))
            if not os.path.isdir(opath):
                os.mkdir(opath)
        for i, imgs in enumerate(self.lazy_load_all()):
            img1, img2 = imgs
            a1_2 = align(img1, img2)
            a2_1 = align(img2, img1)
            if save:
                if not a1_2 is None:
                    a1_2.save(os.sep.join((opath,'a1-2_%03d.png' % i)))
                if not a2_1 is None:
                    a2_1.save(os.sep.join((opath,'a2-1_%03d.png' % i)))
            yield (a1_2, a2_1)
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


