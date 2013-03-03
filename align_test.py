from SimpleCV import *
#monkey patch the SimpleCV class to fix homography calculation in 
#Image.findKeypointMatch
from ImageClass2 import Image2 as Image 
import cv2
import cv
import numpy

def align(img1, img2):
    """align img1 against img2 by applying a perspective warp transform"""
    h1,w1 = img1.size()
    h2,w2 = img2.size()
    h = min(h1,h2)
    w = min(w1,w2)
    
    #extract the homography matrix using keypoint matching
    match = img2.findKeypointMatch(img1)
    homo  = match[1]

    #transform img1 via homography matrix
    img1_array = numpy.array(img1.getMatrix())
    res_array = cv2.warpPerspective(src   = img1_array,
                                    M     = homo,
                                    dsize = (h,w),
                                    flags = cv2.INTER_CUBIC,
                                   )
                                   
    #res_img = Image(res_array,colorSpace = ColorSpace.RGB).toBGR()
    res_img = Image(res_array)
    return res_img
    
################################################################################
# TEST CODE
################################################################################    
if __name__ == "__main__":

    #IM1 = "test_images/a0.png"
    #IM2 = "test_images/a1.png"
    IM1 = "test_images/wave1.jpg"
    IM2 = "test_images/wave2.jpg"
    img1 = Image(IM1)
    img2 = Image(IM2)
    
    a1_2 = align(img1,img2)           #alignment 
    o1_2 = a1_2.blit(img2,alpha=0.5)  #overlay
    a2_1 = align(img2,img1)           #alignment 
    o2_1 = a2_1.blit(img1,alpha=0.5)  #overlay
    
    o1_2.save("o1_2.png")
    o2_1.save("o2_1.png")
    

    
    
