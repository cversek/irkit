import time
from collections import OrderedDict
import cv, cv2
from SimpleCV.Camera import FrameSource
#monkey patch the SimpleCV class to fix homography calculation in 
#Image.findKeypointMatch
from ImageClass2 import Image2 as Image 

class CaptureContainer:
    """
    The CaptureContainer class wraps a opencv2 VideoCapture object
    so that it can easily be loaded and unloaded in order to deal
    with USB bandwidth overflows. Note, the reloading step will
    introduce a latency of on the order of 0.5s for each image 
    into the capture process. 

    """
    #human readable to CV constant property mapping
    prop_map = {"width": cv.CV_CAP_PROP_FRAME_WIDTH,
                "height": cv.CV_CAP_PROP_FRAME_HEIGHT,
                "brightness": cv.CV_CAP_PROP_BRIGHTNESS,
                "contrast": cv.CV_CAP_PROP_CONTRAST,
                "saturation": cv.CV_CAP_PROP_SATURATION,
                "hue": cv.CV_CAP_PROP_HUE,
                "gain": cv.CV_CAP_PROP_GAIN,
                "exposure": cv.CV_CAP_PROP_EXPOSURE}
    
    def __init__(self, dev_index, prop_set = None):
        self.dev_index = dev_index
        self.capture = None
        if prop_set is None:
            prop_set = {}
        self.prop_set = prop_set
        
    def read(self):
        if self.capture is None:
            self.load_capture()
        return self.capture.read()
     
    def load_capture(self):
        self.capture = cv2.VideoCapture(self.dev_index)   
        #set any properties which were passed in the constructor
        for p in self.prop_set.keys():
            if p in self.prop_map:
                self.capture.set(self.prop_map[p], self.prop_set[p])
    
    def release_capture(self):
        if not self.capture is None:
            self.capture.release()
            self.capture = None
    
    def __hash__(self):
        return self.dev_index

class DualCamera:
    """
    The DualCamera class is the class for managing input two webcams.
    
    !!!! FIXME !!!! 
    Because of limitations in the underlying v4l2 drivers, the bandwidth
    needed by some USB capture devices might be too high to support two
    devices at full resolution.  If this bandwidth saturation is present
    the getImage method tries to unload the other capture device before
    acquiring the second image.  This may introduce a latency of on the order
    of 0.5s for each image into the capture process. 
    """
    
    
    def __init__(self, camera_index1 = 0, camera_index2 = 1, prop_set = None):
        if prop_set is None:
            prop_set = {}
        self.prop_set = prop_set
        self._capture_containers = OrderedDict()
        self._capture_containers[1] = CaptureContainer(camera_index1, prop_set = prop_set)
        self._capture_containers[2] = CaptureContainer(camera_index2, prop_set = prop_set)
        for key,cc in self._capture_containers.items():
            cc.load_capture()
        
    def _safeCapture(self, camera_num):
        cc = self._capture_containers[camera_num]
        success, img_array = cc.read()
        if not success: #if it failed try unloading the other capture device
            other_cc = None
            if camera_num == 1:
                other_cc = self._capture_containers[2]
            elif camera_num == 2:
                other_cc = self._capture_containers[1]
            else:
                raise ValueError, "'camera_num' must be either 1 or 2"
            #reset the capture objects and try again
            other_cc.release_capture()
            cc.release_capture()       #must also reset this capture after error
            success, img_array = cc.read()
            if not success:
                raise RuntimeError, "safeCapture failed for camera%d, video device %d" % (camera_num,cc.dev_index)
        img = cv.fromarray(img_array)
        return Image(img)
            
    def capture(self, camera_num):
        t0 = time.time()
        img = self._safeCapture(camera_num)
        t1 = time.time() #record capture time
        img.capture_time    = t1
        img.capture_latency = t1 - t0
        return img
        
    def capture_both(self):
        t0 = time.time()
        img1 = self._safeCapture(1)
        t1 = time.time() #record capture time
        img1.capture_time    = t1
        img1.capture_latency = t1 - t0
        img2 = self._safeCapture(2)
        t2 = time.time() #record capture time
        img2.capture_time    = t2
        img2.capture_latency = t2 - t0
        return img1,img2
        
        
################################################################################
#  TEST CODE
################################################################################
if __name__ == "__main__":
    PROP_SET = {'height': 1024,
                'width':  768,
               }
    DC = DualCamera(prop_set = PROP_SET)
   
    try:
        while True:
            img1, img2 = DC.getImage()
            print "img1.capture_latency: %0.3f" % img1.capture_latency
            print "img2.capture_latency: %0.3f" % img2.capture_latency
            dual_img = img1.sideBySide(img2)
            dual_img.show()
            time.sleep(5)
    except KeyboardInterrupt:
        pass
