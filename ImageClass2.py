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
    def findHomography(self,template,quality=500.00,minDist=0.2,minMatch=0.4):
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
        a homography between the two images. This method allows you to perform matchs the ordinarily 
        fail when using the findTemplate method.
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

        If a homography (match) is found, it is returned otherwise None is returned

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
            #FIXME this code computes the correct homography
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
                
            homography,mask = cv2.findHomography(lhs_pt,rhs_pt,cv2.RANSAC, ransacReprojThreshold=1.0 )
            return (homography, mask)
        else:
            return None 
