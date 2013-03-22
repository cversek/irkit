################################################################################
import datetime, os, time, argparse, multiprocessing, subprocess

DEFAULT_NUM = 1
DEFAULT_DELAY = 5
DEFAULT_RESOLUTION = "1280x1024"
#DEFAULT_RESOLUTION = "320x240"
DEFAULT_PNG_COMPRESSION = 9 # (-1,0-10)
DEFAULT_PRE_CAPTURE_DELAY = 1 #seconds
DEFAULT_FRAME_SKIP = 3
USERHOME_PATH       = os.path.expanduser("~")  #should be portable
DEFAULT_OUTPUT_PATH = os.sep.join((USERHOME_PATH,"snap_images"))
DEFAULT_VERBOSE = True
################################################################################

def run_cmd(cmd):
        return subprocess.call(cmd, shell=False)
################################################################################
class Application:
    def __init__(self,
                 resolution        = DEFAULT_RESOLUTION,
                 png_compression   = DEFAULT_PNG_COMPRESSION,
                 pre_capture_delay = DEFAULT_PRE_CAPTURE_DELAY, #seconds
                 frame_skip        = DEFAULT_FRAME_SKIP,
                 output_path       = DEFAULT_OUTPUT_PATH,
                 verbose           = DEFAULT_VERBOSE,
                ):
        #setup capture options
        self.resolution = resolution
        self.png_compression = int(png_compression)
        self.pre_capture_delay = int(pre_capture_delay)
        self.frame_skip = int(frame_skip)
        #setup image output directory
        self.output_path = output_path
        if not os.path.isdir(output_path):
            os.mkdir(output_path)
        #make noise?
        self.verbose = verbose
        #setup asynchronous process launching
        count = multiprocessing.cpu_count() #get num of multiprocessors
        self._pool = multiprocessing.Pool(processes=count)
        #configure camera devices
        #FIXME how to tell which is IR and which is VIS when device number
        # depends on USB initialization order?! Get serial number??
        self._cam0 = "/dev/video0" #IR
        self._cam1 = "/dev/video1" #VIS
    
    def capture(self,
                filename_prefix = None,
                filename_suffix = "",
                async  = False, 
               ):
        if filename_prefix is None:
            dt = datetime.datetime.now()
            filename_prefix = dt.strftime("%Y-%m-%d_%H_%M_%S")
        #build the common capture command options
        base_cmd = ["fswebcam"]
        base_cmd.append("-r %s" % self.resolution)
        base_cmd.append("--png %d" % self.png_compression)
        base_cmd.append("-D %d" % self.pre_capture_delay)
        base_cmd.append("-S %d" % self.frame_skip)
        #update prefix to include the output path
        filename_prefix = os.sep.join((self.output_path,filename_prefix))
        #construct the filepaths
        fn0 = "%s_IRimg%s.png" % (filename_prefix, filename_suffix)
        fn1 = "%s_VISimg%s.png" % (filename_prefix, filename_suffix)
        #construct the full capture commands
        cmd0 = base_cmd[:] #copy list
        cmd0.append("--save %s" % fn0)
        cmd0.append("-d %s" % self._cam0)
        cmd0 = " ".join(cmd0)
        cmd1 = base_cmd[:] #copy list
        cmd1.append("--save %s" % fn1)
        cmd1.append("-d %s" % self._cam1)
        cmd1 = " ".join(cmd1)
        #run the commands asynchronously
        if async:
            if self.verbose:
                print "running following commands asynchronously:"
                print cmd0
                print cmd1
                print '-'*40
            self._pool.map(run_cmd,[cmd0.split(), cmd1.split()])
        else: #or in sequence
            if self.verbose:
                print "running following command:"
                print cmd0
                print '-'*40
            run_cmd(cmd0.split())
            if self.verbose:
                print "now, running following command:"
                print cmd1
                print '-'*40
            run_cmd(cmd1.split())
        
    def capture_sequence(self,
                         num,
                         delay,
                         **kwargs
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
                             **kwargs
                            )
                if not (i == num-1):
                    time.sleep(delay)
                i += 1
        except KeyboardInterrupt:
            if self.verbose:
                print "user aborted capture...goodbye"
   
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
    parser.add_argument("-a", "--async",
                        help = "run both captures in parallel processes",
                        action = "store_true",
                        default = False,
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
    parser.add_argument("-p", "--pre_capture_delay",
                        help = "pre capture delay (seconds)",
                        type = float,
                        default = DEFAULT_PRE_CAPTURE_DELAY,
                       )
    parser.add_argument("-f", "--frame_skip",
                        help = "skip number of frames",
                        type = int,
                        default = DEFAULT_FRAME_SKIP,
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
    app = Application(resolution = args.resolution,
                      png_compression = args.png_compression,
                      pre_capture_delay = args.pre_capture_delay, #seconds
                      frame_skip = args.frame_skip,
                      output_path = args.output_path,
                      verbose = args.verbose,
                     )
    #run the capture_sequence
    app.capture_sequence(num   = args.num, 
                         delay = args.delay,
                         async = args.async,
                         )
    
    


