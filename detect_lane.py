
import numpy as np
import cv2
import glob
import numpy as np
import cv2
import glob
import time
import cv2
import os
import glob
import matplotlib.pyplot as plt


### This function returns the prespective and inverse prespective matrix for a prespective transform
def perspective(spoints,dpoints):
    m= cv2.getPerspectiveTransform(spoints,dpoints)
    minv=cv2.getPerspectiveTransform(dpoints,spoints)
    return m,minv


### This function applies prespective transform to an image and returns the warped image
def apply_perspective(image,m,img_size):
    return cv2.warpPerspective(image,m,img_size,cv2.INTER_LINEAR)
    


#camera_cal takes a set of chessboards and uses it to return the parameters of the camera    
def camera_cal():
    objectpoints=[]
    iamgepoints=[]
    obj=np.zeros((6*9,3),np.float32)
    obj[:,:2]=np.mgrid[0:9,0:6].T.reshape(-1,2)
    images=glob.glob("camera_cal/*.jpg")
    for img in images:
        img=plt.imread(img)
        gimg=cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
        ret, corners = cv2.findChessboardCorners(gimg, (9,6), None)
        if ret :
            iamgepoints.append(corners)
            objectpoints.append(obj)
    gg=cv2.cvtColor(plt.imread(images[0]),cv2.COLOR_RGB2GRAY)        
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objectpoints, iamgepoints, gg.shape[::-1], None, None)
    return mtx,dist
#this finction takes an image and return its undistorted version 
def correct_dist(img,mtx,dist):
    cimg = cv2.undistort(img, mtx, dist, None, mtx)
    return cimg
#this function calculates sobelex or sobely and applies threshold on it    
def sobel(img,s_type):
    gimg=cv2.cvtColor(img,cv2.COLOR_RGB2GRAY)
    if(s_type=='x'):
        sobel = cv2.Sobel(gimg, cv2.CV_64F, 1, 0)
    elif(s_type=='y'):
        sobel = cv2.Sobel(gimg, cv2.CV_64F, 0, 1)
    abs_sobel = np.absolute(sobel)
    scaled_sobel = 255 * ((abs_sobel) / np.max(abs_sobel))
    sbinary = np.zeros_like(scaled_sobel)
    sbinary[(scaled_sobel > 10) & (scaled_sobel < 100)] = 1
    return sbinary 
 #this function to find the s channel and applies threshold on it
def find_s(img):
    hsl=cv2.cvtColor(img,cv2.COLOR_RGB2HLS)
    h=hsl[:,:,0]
    l=hsl[:,:,1]
    s=hsl[:,:,2]
    sbinary = np.zeros_like(s)
    sbinary[(s > 180) & (s < 255)] = 1
    return sbinary
 # this function combines two images
def mix(img1,img2):
    mix_im = np.zeros_like(img1)
    mix_im[(img1 == 1) | (img2 == 1)] = 1
    return mix_im
#to get the approximated source_points and distination_points
def src_dst():
    srcPoints = np.array([[230,691],
                      [1060,681],
                      [600,445],
                      [680,445]]).astype(np.float32)

    dstPoints = np.array([[250, 700],
                      [1000, 700],
                      [200, 0],
                      [1000, 0]]).astype(np.float32)
    return srcPoints,dstPoints
#this function draws the histogram of the binary image and the 2 starting points   
def histogram(img):
    h= np.sum(img[img.shape[0]//2:,:], axis=0)
    mid=int(h.shape[0]//2)
    leftbx = np.argmax(h[:mid])
    rightbx = np.argmax(h[mid:]) + mid
    return leftbx,rightbx  
# sliding window function
def window(img,bl,br):
    oimg=np.dstack((img,img,img))
    no_of_windows=9
    margin=130
    min_pixels=50
    window_height =int(img.shape[0]//no_of_windows)
    nonzero = img.nonzero()
    nonzero_y = np.array(nonzero[0])
    nonzero_x = np.array(nonzero[1])
    cleftx=bl
    crightx=br
    
    leftx, lefty, rightx, righty = [], [], [], []
    for window in range(0,no_of_windows):
        wytop = img.shape[0] - (window+1)*window_height
        wybottom = img.shape[0] - window*window_height
        centerl=(cleftx,wybottom)
        centerr=(crightx,wybottom)
        ltopleft=(centerl[0]-margin,wytop)
        lbottomright=(centerl[0]+margin,wybottom)
        rtopleft=(centerr[0]-margin,wytop)
        
        rbottomright=(centerr[0]+margin,wybottom)
        
        #draw windows
        cv2.rectangle(oimg,ltopleft,lbottomright,(0,255,0), 4) 
        cv2.rectangle(oimg,rtopleft,rbottomright,(0,255,0), 4)
        #calculate pixels in windows
        lcondx = (ltopleft[0] <= nonzero_x) & (nonzero_x <= lbottomright[0])
        lcondy = (ltopleft[1] <= nonzero_y) & (nonzero_y <= lbottomright[1])
        left_x=nonzero_x[lcondx&lcondy]
        left_y=nonzero_y[lcondx&lcondy]
        rcondx = (rtopleft[0] <= nonzero_x) & (nonzero_x <= rbottomright[0])
        rcondy = (rtopleft[1] <= nonzero_y) & (nonzero_y <= rbottomright[1])
        right_x=nonzero_x[rcondx&rcondy]
        right_y=nonzero_y[rcondx&rcondy]
        #append in lists
        leftx.extend(left_x)
        lefty.extend(left_y)
        rightx.extend(right_x)
        righty.extend(right_y)
        # check for update
        if len(left_x) > min_pixels:
                cleftx = np.int32(np.mean(left_x))
        if len(right_x) > min_pixels:
                crightx = np.int32(np.mean(right_x))
    return leftx, lefty, rightx, righty, oimg
#this function finds the equation of both curves of the lane and fills the region between them
def fit_poly(pre,ml,mr):
    leftx, lefty, rightx, righty, oimg =window(pre,ml,mr)
    im=np.zeros_like(pre)
    if len(lefty) > 1500:
        left_fit = np.polyfit(lefty, leftx, 2)
    if len(righty) > 1500:
        right_fit = np.polyfit(righty, rightx, 2)
    ploty = np.linspace(0, pre.shape[0]-1, pre.shape[0] )
    
    try:
        left_fitx = left_fit[0]*ploty**2 + left_fit[1]*ploty + left_fit[2]
        right_fitx = right_fit[0]*ploty**2 + right_fit[1]*ploty + right_fit[2]
    except TypeError:
        left_fitx = 1*ploty**2 + 1*ploty
        right_fitx = 1*ploty**2 + 1*ploty
        
    oimg[lefty, leftx] = [0, 0, 255]
    oimg[righty, rightx] = [0, 0, 255] 
#     plt.plot(left_fitx, ploty, color='red')
#     plt.plot(right_fitx, ploty, color='red')
    
    for i, y in enumerate(ploty):
        l = int(left_fitx[i])
        r = int(right_fitx[i])
        y = int(y)
        cv2.line(im, (l, y), (r, y), 1)
    return im,oimg,left_fit,right_fit
#draw the filled region in the original image
def final(img,fimg):
    ff=np.copy(img)
    r,g,b=cv2.split(ff)
    b[fimg == 1] = 255
    return cv2.merge((r,g,b))
#distance function
def dist_(l,r):   
    xpixel_to_m = 3.7/700
    x_l = np.dot(l, [700**2, 700, 1])
    x_r = np.dot(r, [700**2, 700, 1])
    d = (1280 // 2 - (x_l+x_r)//2)*xpixel_to_m
    dd=int(d*1000)/1000
    return dd 
#combine functions into a single function to create the pipeline
def pipeline(img,mtx,dist):
    im1=correct_dist(img,mtx,dist)
    im2=sobel(im1,'x')
    im3=find_s(im1)
    im4=mix(im2,im3)
    src,dst=src_dst()
    m,miv=perspective(src,dst)
    im5=apply_perspective(im4,m,im4.shape[::-1])
    lx,rx=histogram(im5)
    leftx, lefty, rightx, righty, im6=window(im5,lx,rx)
    im7,im8,l,r=fit_poly(im5,lx,rx)
    d=dist_(l,r)
    im9=apply_perspective(im7,miv,im7.shape[::-1])
    final_out=final(im1,im9)
    s="The offset of the lane center from the center of the image: "
    outputf=cv2.putText(img=final_out, text=s+str(d), org=(50, 150), fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=1, color=(0,0, 255),thickness=1)
    return outputf,im1,im4,im5,im7,im8,im9
def src_bottom_points(img):
    mid_width=(int)((img.shape[1])/2)
    print(mid_width)
    mid_height=(int)((img.shape[0])/2)
    height=(int)(img.shape[0])
    width=(int)(img.shape[1])
    #src bottom left
    b=False
    for j in range(height-1,0,-1):
        for i in range(mid_width,0,-1):            
            if img[j][i]==255:
               b=True
               break
        if b==True:
            break
    
    #src bottom right
    m=False
    for k in range(height-1,0,-1):
        for l in range(mid_width,width,1):            
            if img[k][l]==255:                
                m=True
                break
        
        if m==True:
            break

    return j,i,k,l
    
    
def distance(img):
    #convert image to HSL color space then use s channel
    hsl=cv2.cvtColor(img,cv2.COLOR_RGB2HLS)    
    s=hsl[:,:,2]
    # apply canny to s channel
    edge_image=cv2.Canny(s,200,100)
    #calling a function to find the bottom source points 
    lv,lh,rv,rh=src_bottom_points(edge_image)
    center_of_the_lane=(rh+lh)/2
    print(center_of_the_lane)
    center_of_the_car=(img.shape[1])/2
    print(center_of_the_car)
    s="vehicle is "
    #1pixel = 0.0002645833m
    if (center_of_the_car-center_of_the_lane)>0:
        dist=(int)((center_of_the_car-center_of_the_lane)* 0.0002645833*1000)
        s+=str(dist/1000)+"m right of center"
    else:
        dist=(int)(np.absolute((center_of_the_car-center_of_the_lane))* 0.0002645833*1000)
        s+=str(dist/1000)+"m left of center"
    print(s)    
    return s   
def cars(image):
    weights_path="Yolov3.weights"
    config_path="Yolov3.cfg"
    net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
    #     net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
    #     net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
    #     input_image = cv2.imread(image)
    img = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
    plt.imshow(img)
    (h,w)=img.shape[:2]
    names = list(net.getLayerNames())
    layers_names = [names[i-1] for i in net.getUnconnectedOutLayers()]
    blob = cv2.dnn.blobFromImage(img,1/255.0,(416,416),crop=False,swapRB=False)
    net.setInput(blob)
    #     start_time = time.time()
    layers_output = net.forward(layers_names)
    boxes = []
    confidences = []
    classIDs = []
    for output in layers_output:
        for detection in output:
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            if confidence > 0.85:
                box = detection[:4]*np.array([w,h,w,h])
                bx,by,bw,bh = box.astype("int")
                x = int(bx - (bw/2))
                y = int(by - (bh/2))
                boxes.append([x,y,int(bw),int(bh)])
                confidences.append(float(confidence))
                classIDs.append(classID)
    indexs = cv2.dnn.NMSBoxes(boxes,confidences,0.6,0.6)
    labels_path="coco.names"
    labels = open(labels_path).read().strip().split('\n')
    if len(indexs) > 0:
        for i in indexs.flatten():
            (x,y) = [boxes[i][0],boxes[i][1]]
            (w,h) = [boxes[i][2],boxes[i][3]]
            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,255),2)
            cv2.putText(img,"{}: {}".format(labels[classIDs[i]],confidences[i]),(x,y-5),cv2.FONT_HERSHEY_SIMPLEX,\
                        0.5,(255,0,255),1)
    plt.imshow(img)
    return img


def pipeline_ (img):
  #convert the image read to RGB
  image=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
  #convert the image to HLS to get rid of shadows
  hls_image = cv2.cvtColor(image, cv2.COLOR_RGB2HLS) 
  h_channel = hls_image[:, :, 0]
  l_channel = hls_image[:, :, 1]
  s_channel = hls_image[:, :, 2]
  #using the sobel filter to get the edges
  sobelx = cv2.Sobel(l_channel, cv2.CV_64F, 1, 0)      
  abs_sobel_x = np.absolute(sobelx)
  #scaling the edges image to a range from 0 to 255
  scaled_sobel = (255 * ((abs_sobel_x) / np.max(abs_sobel_x))).astype(np.uint8)
  #thresholding the image to inhance the lane edges
  sx_thresh = [10, 100]
  sx_binary = (np.zeros_like(scaled_sobel)).astype(np.uint8)             
  sx_binary[(scaled_sobel > sx_thresh[0]) & (scaled_sobel < sx_thresh[1])] = 1
  #creating the bird prespective to highlight the lanes
  srcPoints = np.array([[300, 670],
                    [550, 500],
                    [780, 500],
                    [1050, 670]]).astype(np.float32)

  dstPoints = np.array([[200, 700],
                    [200, 50],
                    [1000, 50],
                    [1000, 700]]).astype(np.float32)

  M, Minv = perspectiveTransform(srcPoints, dstPoints)

  warped_image = (warpPerspective(sx_binary, sx_binary.astype(np.float32).shape[1::-1], M)).astype(np.uint8)  #
  cont = np.array([[200, 700],
                    [200, 50],
                    [1000, 50],
                    [1000, 700]])
  cv2.fillPoly(warped_image, pts = [cont], color =(255,0,0))
  original_image = warpPerspective(warped_image, sx_binary.shape[1::-1], Minv).astype(np.uint8) #
  b,g,r = cv2.split(img)
  newArr = np.zeros((720, 1280)).astype(np.uint8)
  for i in range(len(original_image)):
      for j in range(len(original_image[i])):
          if original_image[i][j]>=b[i][j]:
              newArr[i][j]=original_image[i][j]
          else:
              newArr[i][j]=b[i][j]
  #tranforming the image back to the original prespective
  output = (cv2.merge((r,g,newArr))).astype(np.uint8)
  doutput=distance(image)
  # vis = np.concatenate((hls_image,output), axis=0)
  # print("hls",hls_image.shape,"s",s_channel.shape,"sobel",scaled_sobel.shape,"sx_bin",sx_binary.shape,"warped",warped_image.shape,"original",original_image.shape)
  outputf=cv2.putText(img=output, text=doutput, org=(50, 150), fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=1, color=(0,0, 255),thickness=1)
  return [hls_image,s_channel ,scaled_sobel,original_image,outputf]
  
  
  
  
#merging images

def vconcat_resize_min(im_list, interpolation=cv2.INTER_CUBIC):
    w_min = min(im.shape[1] for im in im_list)
    im_list_resize = [cv2.resize(im, (w_min, int(im.shape[0] * w_min / im.shape[1])), interpolation=interpolation)
                      for im in im_list]
    return cv2.vconcat(im_list_resize)


def merge_images(img):
    print(img[1].shape, img[2].shape, img[3].shape, img[4].shape, img[5].shape, img[6].shape)
    gray_three1 = cv2.merge([img[2],img[2],img[2]]).astype('uint8')
    gray_three1*= 255
    gray_three2 = cv2.merge([img[3],img[3],img[3]]).astype('uint8')
    gray_three2*= 255
    m0=np.hstack((img[1], gray_three1, gray_three2))
    #
    gray_three3 = cv2.merge([img[4],img[4],img[4]]).astype('uint8')
    gray_three3*= 255
    gray_three4 = cv2.merge([img[6],img[6],img[6]]).astype('uint8')
    gray_three4*= 255
    m1=np.hstack((gray_three3, img[5].astype('uint8'), gray_three4))
    im_v_resize = vconcat_resize_min([img[0], m0, m1])
    cv2.imwrite('data/dst/opencv_vconcat_resize.jpg', im_v_resize)
    return im_v_resize


#read and write video


import sys
argv = sys.argv
path_in = argv[1]
debug = int(argv[2])
path_out = argv[3]
print(path_in)
print(debug)
print(path_out)

# path_in = "project_video.mp4"
# path_out = "bassantmah.avi"
# debug = 0


col_images=[]
# path="project_video.mp4"
# debug=1 

# Create a VideoCapture object and read from input file
cap = cv2.VideoCapture(path_in)
fps = cap.get(cv2.CAP_PROP_FPS)
print(fps)
print("hi")

 

# Check if camera opened successfully
if (cap.isOpened()== False):
    print("Error opening video file")

 

frame_width = int(cap.get(3))
frame_height = int(cap.get(4))


out = cv2.VideoWriter(path_out,cv2.VideoWriter_fourcc('M','J','P','G'),fps, (frame_width,frame_height))
out2 = cv2.VideoWriter(path_out,cv2.VideoWriter_fourcc('M','J','P','G'),fps, (1280, 1200))

 
mt,ds=camera_cal()

while(cap.isOpened()):
    
    
    # Capture frame-by-frame
    ret, frame = cap.read()
    if ret == True:
        col_images.append(frame)
        mm=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        
        frame_out = pipeline (mm,mt,ds)

        if debug==0:
            frame_out = cars(frame_out[0])
            out.write(frame_out)
        else: 
            pipeline_out = merge_images(frame_out)
#             out2 = cv2.VideoWriter(path_out,cv2.VideoWriter_fourcc('M','J','P','G'),fps - 5, (frame_width,frame_height))
            pipeline_out=cv2.cvtColor(pipeline_out,cv2.COLOR_BGR2RGB)
            out2.write(pipeline_out)
#             plt.figure(figsize=(10,10))
#             image = pipeline_out
#             plt.imshow(image)
#             plt.show()

        # Press Q on keyboard to exit
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

 

    # Break the loop
    else:
        break

 

# When everything done, release
# the video capture object
cap.release()
out.release()
out2.release()

 

# Closes all the frames
cv2.destroyAllWindows()
