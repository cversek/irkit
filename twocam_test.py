import time
from SimpleCV import *

RESOLUTION = (640,480)
CAM0_PROPS = {'width':RESOLUTION[0],'height':RESOLUTION[1]}
CAM1_PROPS = CAM0_PROPS.copy()

cam0 = Camera(0,CAM0_PROPS)
cam1 = Camera(1,CAM1_PROPS)

img0 = cam0.getImage()
img1 = cam1.getImage()

dual_img = img0.sideBySide(img1)
dual_img.show()

time.sleep(5)
