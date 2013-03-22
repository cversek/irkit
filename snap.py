################################################################################
import datetime, os, time, argparse, getpass
from dual_camera import DualCamera

DEFAULT_NUM         = 1                        
DEFAULT_DELAY       = 5                        #seconds
DEFAULT_RESOLUTION  = "620x480"                #width x height
USERHOME_PATH       = os.path.expanduser("~")  #should be portable
DEFAULT_OUTPUT_PATH = os.sep.join((USERHOME_PATH,"snap_images"))
DEFAULT_VERBOSE     = True
################################################################################

################################################################################
class Application:
    def __init__(self,
                 vis_camera_index  = 0,
                 nir_camera_index  = 1,
                 resolution        = DEFAULT_RESOLUTION,
                 output_path       = DEFAULT_OUTPUT_PATH,
                 verbose           = DEFAULT_VERBOSE,
                ):
        #setup image output directory
        self.output_path = output_path
        if not os.path.isdir(output_path):
            os.mkdir(output_path)
        #make noise?
        self.verbose = verbose
        
        w, h = map(int,resolution.split('x'))
        self.prop_set_vis = {'width': w, 'height': h}
        self.prop_set_nir = {'width': w, 'height': h}
        
        self.dual_camera = DualCamera(camera_index1 = vis_camera_index,
                                      camera_index2 = nir_camera_index,
                                      prop_set1 = self.prop_set_vis,
                                      prop_set2 = self.prop_set_nir,
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
        fn_ir  = "%s_NIRimg%s.png"  % (filename_prefix, filename_suffix)
        #save the images
        if self.verbose:
            print '-'*40
            print "saving VIS image:"
            print "\tfilename:", fn_vis
            print "\tlatency: %0.2f" % img_vis.capture_latency
        img_vis.save(fn_vis)
        if self.verbose:
            print "saving NIR image:"
            print "\tfilename:", fn_ir
            print "\tlatency: %0.2f" % img_ir.capture_latency   
        img_ir.save(fn_ir)

        
    def capture_sequence(self,
                         num, 
                         delay, 
                        ):
        i = 0  
        try:                                          
            while True:
                if num > 0 and i >= num:  #negative num will never return
                    if self.verbose:
                        print "finished capture...goodbye"
                    return
                dt = datetime.datetime.now()
                filename_prefix = dt.strftime("%Y-%m-%d_%H_%M_%S")
                filename_suffix = "%03d" % i
                self.capture(filename_prefix = filename_prefix, 
                             filename_suffix = filename_suffix,
                            )
                if not (i == num-1):
                    time.sleep(delay)
                i += 1
        except KeyboardInterrupt:
            if self.verbose:
                print "user aborted capture...goodbye"
        finally: #cleanup!
            self.dual_camera.close()

                
    def close(self):
        self.dual_camera.close()
################################################################################
# MAIN
################################################################################
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    #capture sequence arguments
    parser.add_argument("-n", "--num", 
                        help = "number of images in sequence, negative implies infinite",
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
                      output_path       = args.output_path,
                      verbose           = args.verbose,
                     )
    #run the capture_sequence
    app.capture_sequence(num = args.num, delay = args.delay)  

