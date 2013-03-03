##Load required libraries
#from SimpleCV.base import *
#from SimpleCV.Color import *
#from numpy import int32
#from numpy import uint8
##from EXIF import *
#import pygame as pg
#import scipy.ndimage as ndimage
#import scipy.stats.stats as sss #for auto white balance
#import scipy.cluster.vq as scv
#import math # math... who does that
#import copy # for deep copy


from SimpleCV.Features import FeatureSet, KeypointMatch
from SimpleCV import Image
import numpy as np

class Image2(Image):    
    def findKeypointMatch(self,template,quality=500.00,minDist=0.2,minMatch=0.4):
        """
        !!!! FIXME !!!! THIS IS A REPLACEMENT METHOD
        that patches an incorrect construction of the homography matrix 
        original source:
        https://github.com/rishimukherjee/SimpleCV/blob/c8680008406e940ac5cd0814ffe25be8c90acebd/SimpleCV/ImageClass.py
        
        **SUMMARY**

        findKeypointMatch allows you to match a template image with another image using
        SURF keypoints. The method extracts keypoints from each image, uses the Fast Local
        Approximate Nearest Neighbors algorithm to find correspondences between the feature
        points, filters the correspondences based on quality, and then, attempts to calculate
        a homography between the two images. This homography allows us to draw a matching
        bounding box in the source image that corresponds to the template. This method allows
        you to perform matchs the ordinarily fail when using the findTemplate method.
        This method should be able to handle a reasonable changes in camera orientation and
        illumination. Using a template that is close to the target image will yield much
        better results.

        .. Warning::
        This method is only capable of finding one instance of the template in an image.
        If more than one instance is visible the homography calculation and the method will
        fail.

        **PARAMETERS**

        * *template* - A template image.
        * *quality* - The feature quality metric. This can be any value between about 300 and 500. Higher
        values should return fewer, but higher quality features.
        * *minDist* - The value below which the feature correspondence is considered a match. This
        is the distance between two feature vectors. Good values are between 0.05 and 0.3
        * *minMatch* - The percentage of features which must have matches to proceed with homography calculation.
        A value of 0.4 means 40% of features must match. Higher values mean better matches
        are used. Good values are between about 0.3 and 0.7

        **RETURNS**

        If a homography (match) is found this method returns a feature set with a single
        KeypointMatch feature. If no match is found None is returned.
        **EXAMPLE**
        >>> template = Image("template.png")
        >>> img = camera.getImage()
        >>> fs = img.findKeypointMatch(template)
        >>> if( fs is not None ):
        >>> fs[0].draw()
        >>> img.show()
        **NOTES**

        If you would prefer to work with the raw keypoints and descriptors each image keeps
        a local cache of the raw values. These are named:
        | self._mKeyPoints # A Tuple of keypoint objects
        | self._mKPDescriptors # The descriptor as a floating point numpy array
        | self._mKPFlavor = "NONE" # The flavor of the keypoints as a string.
        | `See Documentation <http://opencv.itseez.com/modules/features2d/doc/common_interfaces_of_feature_detectors.html#keypoint-keypoint>`_

        **SEE ALSO**
        :py:meth:`_getRawKeypoints`
        :py:meth:`_getFLANNMatches`
        :py:meth:`drawKeypointMatches`
        :py:meth:`findKeypoints`

        """
        
        try:
            import cv2
        except:
            warnings.warn("Can't Match Keypoints without OpenCV >= 2.3.0")
            return
            
        if template == None:
          return None
        
        skp,sd = self._getRawKeypoints(quality)
        tkp,td = template._getRawKeypoints(quality)
        if( skp == None or tkp == None ):
            warnings.warn("I didn't get any keypoints. Image might be too uniform or blurry." )
            return None

        template_points = float(td.shape[0])
        sample_points = float(sd.shape[0])
        magic_ratio = 1.00
        if( sample_points > template_points ):
            magic_ratio = float(sd.shape[0])/float(td.shape[0])

        idx,dist = self._getFLANNMatches(sd,td) # match our keypoint descriptors
        p = dist[:,0]
        result = p*magic_ratio < minDist #, = np.where( p*magic_ratio < minDist )
        pr = result.shape[0]/float(dist.shape[0])

        if( pr > minMatch and len(result)>4 ): # if more than minMatch % matches we go ahead and get the data
            lhs = []
            rhs = []
            for i in range(0,len(idx)):
                if( result[i] ):
                    lhs.append((tkp[i].pt[1], tkp[i].pt[0]))
                    rhs.append((skp[idx[i]].pt[0], skp[idx[i]].pt[1]))
            
            rhs_pt = np.array(rhs)
            lhs_pt = np.array(lhs)
            if( len(rhs_pt) < 16 or len(lhs_pt) < 16 ):
                return None
            homography = []
            (homography,mask) = cv2.findHomography(lhs_pt,rhs_pt,cv2.RANSAC, ransacReprojThreshold=1.0 )
            w = template.width
            h = template.height
            yo = homography[0][2] # get the x/y offset from the affine transform
            xo = homography[1][2]
            # draw our template
            pt0 = np.array([0,0,1])
            pt1 = np.array([0,h,1])
            pt2 = np.array([w,h,1])
            pt3 = np.array([w,0,1])
            # apply the affine transform to our points
            pt0p = np.array(pt0*np.matrix(homography))
            pt1p = np.array(pt1*np.matrix(homography))
            pt2p = np.array(pt2*np.matrix(homography))
            pt3p = np.array(pt3*np.matrix(homography))
            #update and clamp the corners to get our template in the other image
            pt0i = (abs(pt0p[0][0]+xo),abs(pt0p[0][1]+yo))
            pt1i = (abs(pt1p[0][0]+xo),abs(pt1p[0][1]+yo))
            pt2i = (abs(pt2p[0][0]+xo),abs(pt2p[0][1]+yo))
            pt3i = (abs(pt3p[0][0]+xo),abs(pt3p[0][1]+yo))
            #construct the feature set and return it.
            fs = FeatureSet()
            fs.append(KeypointMatch(self,template,(pt0i,pt1i,pt2i,pt3i),homography))
            #the homography matrix is necessary for many purposes like image stitching.
            fs.append(homography)
            return fs
        else:
            return None 
