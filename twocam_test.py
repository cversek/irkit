import time
from SimpleCV import *

#RESOLUTION = (640,480)
#CAM0_PROPS = {'width':RESOLUTION[0],'height':RESOLUTION[1]}
#CAM1_PROPS = CAM0_PROPS.copy()

c0 = cv.CaptureFromCAM(0)
cv.GrabFrame(c0)
frame = cv.RetrieveFrame(c0)
newimg = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U, 3)
cv.Copy(frame, newimg)
img0 = Image(newimg)

#FIXME - delete the first capture buffer to prevent 
# the error "libv4l2: error turning on stream: No space left on device"
del(c0)

c1 = cv.CaptureFromCAM(1)
cv.GrabFrame(c1)
frame = cv.RetrieveFrame(c1)
newimg = cv.CreateImage(cv.GetSize(frame), cv.IPL_DEPTH_8U, 3)
cv.Copy(frame, newimg)
img1 = Image(newimg)

dual_img = img0.sideBySide(img1)
dual_img.show()

time.sleep(5)
