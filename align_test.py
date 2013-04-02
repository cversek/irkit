from SimpleCV import *
#monkey patch the SimpleCV class to fix homography calculation in 
#Image.findKeypointMatch
from ImageClass2 import Image2 as Image 
import cv2
import cv
import numpy as np

def findHomography(img,template,quality=500.00,minDist=0.2,minMatch=0.4):
    skp,sd = img._getRawKeypoints(quality)
    tkp,td = template._getRawKeypoints(quality)
    if( skp == None or tkp == None ):
        warnings.warn("I didn't get any keypoints. Image might be too uniform or blurry." )
        return None

    template_points = float(td.shape[0])
    sample_points = float(sd.shape[0])
    magic_ratio = 1.00
    if( sample_points > template_points ):
        magic_ratio = float(sd.shape[0])/float(td.shape[0])

    idx,dist = img._getFLANNMatches(sd,td) # match our keypoint descriptors
    p = dist[:,0]
    result = p*magic_ratio < minDist #, = np.where( p*magic_ratio < minDist )
    pr = result.shape[0]/float(dist.shape[0])

    if( pr > minMatch and len(result)>4 ): # if more than minMatch % matches we go ahead and get the data
        #FIXME this code computes the "correct" homography
        lhs = []
        rhs = []
        for i in range(0,len(idx)):
            if( result[i] ):
                lhs.append((tkp[i].pt[1], tkp[i].pt[0]))             #FIXME note index order
                rhs.append((skp[idx[i]].pt[0], skp[idx[i]].pt[1]))   #FIXME note index order
        
        rhs_pt = np.array(rhs)
        lhs_pt = np.array(lhs)
        if( len(rhs_pt) < 16 or len(lhs_pt) < 16 ):
            return None
            
        homography,mask = cv2.findHomography(lhs_pt,rhs_pt,cv2.RANSAC, ransacReprojThreshold=1.0 )
        return (homography, mask)
    else:
        return None 

def align(img1, img2):
    """align img1 against img2 by applying a perspective warp transform"""
    w1,h1 = img1.size()
    w2,h2 = img2.size()
    print "(w1, h1)=", (w1,h1)
    w = min(w1,w2)
    h = min(h1,h2)
    
    r1,g1,b1 = img1.splitChannels()
    r2,g2,b2 = img2.splitChannels()
    cmp1 = r1.invert()
    cmp2 = r2.invert()
    
    cmp1 = img1
    cmp2 = img2
    
    #
    
    #extract the homography matrix using keypoint matching
    #print "Finding matching features ..."
    H, mask = findHomography(cmp2, cmp1)
    
    img_array = np.array(img1.getMatrix())
    aligned_array = cv2.warpPerspective(src = img_array,
                                        M = H,
                                        dsize = (h,w),
                                        flags = cv2.INTER_CUBIC,
                                       )  
                           
    aligned_img = Image(aligned_array)
    return aligned_img
#    m = cmp2.findKeypointMatch(cmp1)
#    H = m[0].getHomography()
#    aligned_img = img2.transformPerspective(H)
#    return aligned_img

#    if not res is None:
#        m = m[0]
#        homo = m.getHomography()
#        #homo, mask = res
#        H = np.matrix(homo)
#        o0 = np.matrix((0,0,1)).T #upper left corner of img1 
#        o1 = np.matrix((w,h,1)).T #lower right corner of img1 
#        t0 = H*o0
#        t1 = H*o1
#        p0 = (int(np.round(t0[0]/t0[2])),int(np.round(t0[1]/t0[2])))
#        p1 = (int(np.round(t1[0]/t1[2])),int(np.round(t1[1]/t1[2])))
#        print p0,p1
#        b0 = (max(p0[1],0),max(p0[0],0))
#        b1 = (min(p1[1],w2),min(p1[0],h2))
#        #transform the first image to match the second
#        aligned_img = img1.transformPerspective(homo)
#        img1_array = np.array(img1.getMatrix())
#        aligned_array = cv2.warpPerspective(src = img1_array,
#                                            M = homo,
#                                            dsize = (h,w),
#                                            flags = cv2.INTER_CUBIC,
#                                           )  
#                                   
#        aligned_img = Image(aligned_array)
#        #aligned_img = aligned_img.blit(img2,alpha=0.5)  #overlay
#        #aligned_img = aligned_img.crop(b0[0],b0[1],b1[0]-b0[0],b1[1]-b0[1])
#        return aligned_img
#    else:
#        return None
        
     
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
    IM1 = "test_images/plantcam_bumpoutNIR.png"
    IM2 = "test_images/plantcam_bumpoutVIS.png"
    img1 = Image(IM1)
    img2 = Image(IM2)
    
#    eq1 = img1.equalize()
#    eq2 = img2.equalize()
    
    a1_2 = align(img1,img2)           #alignment 
    o1_2 = a1_2.blit(img2,alpha=0.5)  #overlay
    a2_1 = align(img2,img1)           #alignment 
    o2_1 = a2_1.blit(img1,alpha=0.5)  #overlay
    
    o1_2.save("plantcam_bumpoutOVERLAY_VIStoNIR.png")
    o2_1.save("plantcam_bumpoutOVERLAY_NIRtoVIS.png")
    

    
    
