from SimpleCV import *
#monkey patch the SimpleCV class to fix homography calculation in 
#Image.findKeypointMatch
from ImageClass2 import Image2 as Image 
import cv2
import cv
import numpy as np

def align(img1, img2):
    """align img1 against img2 by applying a perspective warp transform"""
    w1,h1 = img1.size()
    w2,h2 = img2.size()
    print "(w1, h1)=", (w1,h1)
    w = min(w1,w2)
    h = min(h1,h2)
    
    #extract the homography matrix using keypoint matching
    #print "Finding matching features ..."
    res = img2.findHomography(img1)

    if not res is None:
        homo, mask = res
        H = np.matrix(homo)
        o0 = np.matrix((0,0,1)).T #upper left corner of img1 
        o1 = np.matrix((w,h,1)).T #lower right corner of img1 
        t0 = H*o0
        t1 = H*o1
        p0 = (int(np.round(t0[0]/t0[2])),int(np.round(t0[1]/t0[2])))
        p1 = (int(np.round(t1[0]/t1[2])),int(np.round(t1[1]/t1[2])))
        print p0,p1
        b0 = (max(p0[1],0),max(p0[0],0))
        b1 = (min(p1[1],w2),min(p1[0],h2))
        #transform the first image to match the second
        img1_array = np.array(img1.getMatrix())
        aligned_array = cv2.warpPerspective(src = img1_array,
                                            M = homo,
                                            dsize = (h,w),
                                            flags = cv2.INTER_CUBIC,
                                           )  
                                   
        aligned_img = Image(aligned_array)
        #aligned_img = aligned_img.blit(img2,alpha=0.5)  #overlay
        #aligned_img = aligned_img.crop(b0[0],b0[1],b1[0]-b0[0],b1[1]-b0[1])
        return aligned_img
    else:
        return None
        
     
def cropped_match(img1,img2):
    a1_2 = align(img1,img2)
    nonblack = a1_2.colorDistance(Color.BLACK)
    nonblack_blob = nonblack.findBlobs(1)[-1]
    img_mask = nonblack_blob.hullMask()               #get the central image region
    c1 = a1_2.crop(nonblack_blob)                     #crops to bounding rectangle
    c2 = img2.crop(nonblack_blob) - img_mask.invert() #cuts of non overlaping edges
    return (c1,c2)
    
    
    
    
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
    

    
    
