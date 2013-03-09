################################################################################
import datetime, os, time, argparse
from dual_camera import DualCamera
#monkey patch the SimpleCV class to fix homography calculation in 
#Image.findKeypointMatch
from ImageClass2 import Image2 as Image 

DEFAULT_NUM         = 5
DEFAULT_DELAY       = 5
DEFAULT_RESOLUTION  = "1280x1024"
DEFAULT_PNG_COMPRESSION = 9 # (-1,0-10)
DEFAULT_OUTPUT_PATH = "raw_images"
DEFAULT_VERBOSE     = True
################################################################################

################################################################################
class Application:
    def __init__(self,
                 vis_camera_index  = 0,
                 ir_camera_index   = 1,
                 resolution        = DEFAULT_RESOLUTION,
                 png_compression   = DEFAULT_PNG_COMPRESSION,
                 output_path       = DEFAULT_OUTPUT_PATH,
                 verbose           = DEFAULT_VERBOSE,
                ):
        #setup image output directory
        self.output_path = output_path
        if not os.path.isdir(output_path):
            os.mkdir(output_path)
        #make noise?
        self.verbose = verbose
        self.dual_camera = DualCamera(camera_index1 = vis_camera_index,
                                      camera_index2 = ir_camera_index,
                                     )
    
    def capture(self, 
                filename_prefix = None, 
                filename_suffix = "",
               ):
        #capture the images
        img_vis, img_ir = self.dual_camera.capture_both() 
        #format filenames
        if filename_prefix is None:
            dt    = datetime.datetime.now()
            filename_prefix = dt.strftime("%Y-%m-%d_%H_%M_%S")
        #update prefix to include the output path
        filename_prefix = os.sep.join((self.output_path,filename_prefix))
        #construct the filepaths
        fn_vis = "%s_VISimg%s.png" % (filename_prefix, filename_suffix)
        fn_ir = "%s_IRimg%s.png"  % (filename_prefix, filename_suffix)
        #save the images
        if self.verbose:
            print '-'*40
            print "saving VIS image:"
            print "\tfilename:", fn_vis
            print "\tlatency: %0.2f" % img_vis.capture_latency
        img_vis.save(fn_vis)
        if self.verbose:
            print "saving IR image:"
            print "\tfilename:", fn_ir
            print "\tlatency: %0.2f" % img_ir.capture_latency   
        img_ir.save(fn_ir)

        
    def capture_sequence(self,
                         num, 
                         delay, 
                        ):                                            
        for i in range(num):
            dt = datetime.datetime.now()
            filename_prefix = dt.strftime("%Y-%m-%d_%H_%M_%S")
            filename_suffix = "%03d" % i
            self.capture(filename_prefix = filename_prefix, 
                         filename_suffix = filename_suffix,
                        )
            if not (i == num-1):
                time.sleep(delay)
################################################################################
# MAIN
################################################################################
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    #capture sequence arguments
    parser.add_argument("-n", "--num", 
                        help = "number of images in sequence",
                        type = int,
                        default = DEFAULT_NUM,
                       )
    parser.add_argument("-d", "--delay", 
                        help = "post capture delay for sequence",
                        type = int,
                        default = DEFAULT_DELAY,
                       )
    #optional arguments
    parser.add_argument("-r", "--resolution", 
                        help = "set the resolution of the camera",
                        default = DEFAULT_RESOLUTION,
                       )
    parser.add_argument("-c", "--png_compression", 
                        help = "level of PNG compression (-1,0-10)",
                        type = int,
                        choices = (-1,0,1,2,3,4,5,6,7,8,9,10),
                        default = DEFAULT_PNG_COMPRESSION,
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
    app = Application(resolution        = args.resolution,
                      png_compression   = args.png_compression,
                      output_path       = args.output_path,
                      verbose           = args.verbose,
                     )
    #run the capture_sequence
    app.capture_sequence(num = args.num, delay = args.delay)  

