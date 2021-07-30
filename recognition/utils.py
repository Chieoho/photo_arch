# -*- coding: utf-8 -*-
import json
import math
import os

from sklearn.manifold import TSNE
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

import cv2
import joblib
import platform
import numpy as np
from PIL import Image
from sklearn.preprocessing import Normalizer, LabelEncoder
from insightface.utils import face_align


# calculate a face embedding for each face in the dataset using facenet.
def get_embedding(model, face_pixels):
    # scale pixel values
    # face_pixels = face_pixels.astype('float32')
    # standardize pixel values across channels (global)
    # mean, std = face_pixels.mean(), face_pixels.std()
    # face_pixels = (face_pixels - mean) / std
    face_pixels = prewhiten(face_pixels)
    # transform face into one sample
    samples = np.expand_dims(face_pixels, axis=0)# samples.shape=(1, 160, 160, 3)
    # make prediction to get embedding
    yhat = model.predict(samples)
    embedding = Normalizer(norm='l2').transform(yhat)
    return embedding[0]

def prewhiten(x):
    mean = np.mean(x)
    std = np.std(x)
    std_adj = np.maximum(std, 1.0/np.sqrt(x.size))
    y = np.multiply(np.subtract(x, mean), 1/std_adj)
    return y

def l2_normalize(x, axis=-1, epsilon=1e-10):
    output = x / np.sqrt(np.maximum(np.sum(np.square(x), axis=axis, keepdims=True), epsilon))
    return output

# 判断名字的数量是否一样多，如果一样多，就找距离最小或者相似度最高的名字.
def findBestName(counts, name):
    for key, value in counts.items():
        if key != name and value == counts[name]:
            return True

    return False

def get_name_by_euclid_distance(unknown_embedding, euclideanDist, data_path):
    # Preparation for calculating Euclidean distance.
    if os.path.exists(data_path):
        data = np.load(data_path, allow_pickle=True)
        faces_embedding = data['faces_embedding']
        faces_name = data['faces_name']

        dist = np.linalg.norm(faces_embedding - unknown_embedding, axis=1)
        min_dist = np.min(dist)
        if min_dist < euclideanDist: #默认euclideanDist<0.74
            min_dist_index = np.argmin(dist)
            who_name = faces_name[min_dist_index]
            print('min_dist: %s, name is %s' % (min_dist, who_name))

            # matchedIdxs = [i for (i, d) in enumerate(dist) if d < 0.74]
            # counts = {}
            # for i in matchedIdxs:
            #     name = faces_name[i]
            #     counts[name] = counts.get(name, 0) + 1
            # who_name = max(counts, key=counts.get)
            # if findBestName(counts, who_name):
            #     min_dist_index = np.argmin(dist)
            #     who_name = faces_name[min_dist_index]
            #     print('min_dist: %s, name is %s' % (min_dist, who_name))
            # else:
            #     print('counts: %s, selected name is %s' % (counts, who_name))
        else:
            who_name = ''
            print('min_dist: %s 已经大于阈值%s了.' % (min_dist, euclideanDist))
    else:
        who_name = ''
        # print('{}文件不存在.'.format(data_path))

    return who_name

def get_name_by_simular(unknown_embedding, simular, data_path):
    # Preparation for calculating Euclidean distance.
    if os.path.exists(data_path):
        data = np.load(data_path, allow_pickle=True)
        faces_embedding = data['faces_embedding']
        faces_name = data['faces_name']

        simL = np.dot(faces_embedding, unknown_embedding)
        simL = simL.reshape(-1)
        simL = list(simL)
        print('#####:',simL)
        max_sim = np.max(simL)
        if max_sim > simular: #simular>0.4
            # max_sim_index = np.argmax(sim)
            # who_name = faces_name[max_sim_index]
            # print('max_sim: %s, name is %s' % (max_sim, who_name))
            matchedIdxs = [i for (i, sim) in enumerate(simL) if sim > simular]
            counts = {}
            for i in matchedIdxs:
                name = faces_name[i]
                counts[name] = counts.get(name, 0) + 1
            who_name = max(counts, key=counts.get)
            if findBestName(counts, who_name): # 人数一样多，就找最大的相似度
                max_sim_index = np.argmax(simL)
                who_name = faces_name[max_sim_index]
                print('max_sim: %s, name is %s' % (max_sim, who_name))
            else:
                print('counts: %s, selected name is %s' % (counts, who_name))
        else:
            who_name = ''
            print('max_sim: %s 已经小于阈值%s了.' % (max_sim, simular))
    else:
        who_name = ''
        # print('{}文件不存在.'.format(data_path))

    return who_name

def get_name_by_embedding(imgPath, unknown_embedding, faceProp, threshold, flag):
    if os.path.exists('data/model/custom_faceRecognize.h5'):
        print('#####:pid=%d, imgPath=%s' % (os.getpid(), imgPath))
        model = joblib.load('data/model/custom_faceRecognize.h5')
        last_data = np.load('data/model/last_data.npz', allow_pickle=True) # 模型上次训练时,使用的数据.
        label_encoder = LabelEncoder()

        emb = unknown_embedding.reshape(1, -1)
        yhat = model.predict(emb)
        yhat_proba = model.predict_proba(emb)
        last_faces_name = last_data['faces_name']
        last_trainy = np.asarray(last_faces_name)
        label_encoder.fit_transform(last_trainy)
        proba = yhat_proba[0][yhat[0]]

        if proba > faceProp: # 默认faceProp=0.9
            who_name = label_encoder.inverse_transform(yhat)[0]
            print('模型预测的proba:%f, predicted name: %s' % (proba, who_name))
        else: # 模型识别的概率低于0.9时,使用欧式距离计算.
            if flag == 1:
                print('模型预测的proba:%f,小于阈值%s,使用欧式距离:' % (proba, faceProp))
                # if os.path.exists('data/last_no_train_data.npz'):
                #     data_path = 'data/last_no_train_data.npz'
                # else:
                #     data_path = 'data/data.npz'
                who_name = get_name_by_euclid_distance(unknown_embedding, threshold, 'data/data.npz')
            else:
                print('模型预测的proba:%f,小于阈值%s,使用相似度计算:' % (proba, faceProp))
                who_name = get_name_by_simular(unknown_embedding, threshold, 'data/data.npz')

    else:
        # 模型不存在时,使用欧式距离计算.
        print('#####:pid=%d, imgPath=%s' % (os.getpid(), imgPath))
        if flag == 1:
            who_name = get_name_by_euclid_distance(unknown_embedding, threshold, 'data/data.npz')
        else:
            who_name = get_name_by_simular(unknown_embedding, threshold, 'data/data.npz')

    return  who_name


# def cvimg_to_qtimg(cvimg):
#
#     height, width, depth = cvimg.shape
#     cvimg = cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB)
#     cvimg = QImage(cvimg.data, width, height, width * depth, QImage.Format_RGB888)
#
#     return cvimg
#
# # PIL格式转QPixmap格式
# def pil2_pixmap(pil_img):
#     pixmap = ImageQt.toqpixmap(pil_img)
#     return pixmap
#
#
# # QPixmap格式转PIL格式
# def pixmap2_pil(pixmap):
#     pil_img = ImageQt.fromqpixmap(pixmap)
#     return pil_img


def cvimg2_pil(cvimg):
    pilimg = Image.fromarray(cv2.cvtColor(cvimg, cv2.COLOR_BGR2RGB))
    return pilimg

# 模型使用的RGB图像,转成BGR会造成某些图片识别不出来
def pil2_cvimg(pil_img):
    cvimg = cv2.cvtColor(np.asarray(pil_img), cv2.COLOR_RGB2BGR)
    return cvimg

def pil2_arrayimg(pil_img):
    arrayimg = np.asarray(pil_img)
    return arrayimg

def arrayimg2_pil(arrayimg):
    pilimg = Image.fromarray(arrayimg)
    return pilimg


def calculate_img_scaling(img_path, canvasH, canvasW):
    (h, w) = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR).shape[0:2]
    # print('original img scale:h=%d, w=%d.' %(h, w))
    # if h > canvasH or w > canvasW:
    if h > 2000 or w > 2000:
        scale = 0.25
    else:  # 图片大小小于画布
        scale = 1

    # print('scaled img: h=%d, w=%d.' %(scaleH, scaleW))
    return scale


# 按照距离顶部最近的人脸框为基准进行排序
def enabel_row_up_by_top(det):
    row_up = []
    row_no = []
    if len(det) >= 1:
        # 以离左上角最近的人脸框为基准,找出同一行的人脸框 or 以离右上角最近的人脸框为基准,找出同一行的人脸框
        # if np.argmin(det[:, 1]) == np.argmin(det[:, 0])

        min_y2 = det[np.argmin(det[:, 1])][3]
        rank_index = np.argsort(det[:, 1])
        for i in range(len(det)):
            if det[rank_index[i]][1] < (min_y2 + 5):
                # ratio = (base_h - abs(base_h - det[rank_index[i]][3]))/base_h
                row_up.append(rank_index[i])  # 成一行
            else:
                row_no.append(rank_index[i])  # 非成行

    return row_up, row_no


def arrange_row_up_by_top(det, row_up):
    det_row = []
    det_arr = []
    length = len(row_up)
    # 取出排成一行的人脸框
    for i in range(length):
        det_row.append(det.tolist().pop(row_up[i]))

    # 对取出的一行人脸框按照左上角坐标x从小到大排序
    det_row = np.asarray(det_row)
    index = np.argsort(det_row[:, 0])
    for i in range(length):
        det_arr.append(det_row[index[i]])

    return det_arr


def remaining_row_no(det, row_no):
    det_row = []
    det_arr = []
    length = len(row_no)
    # 取出剩余未排序的人脸框
    for i in range(length):
        det_row.append(det.tolist().pop(row_no[i]))

    return det_row


def rank_all_faces_by_top(det):
    rank = []
    while True:
        row_up, row_no = enabel_row_up_by_top(det)
        # print('row_up:', row_up)
        # print('row_no:', row_no)
        if len(row_up) >= 1:
            det_row_up = arrange_row_up_by_top(det, row_up)
            for i in range(len(det_row_up)):
                rank.append(det_row_up[i])

        if len(row_no) > 1:
            det_row_no = remaining_row_no(det, row_no)
            det = np.asarray(det_row_no)
        elif len(row_no) == 1:
            det_row_no = remaining_row_no(det, row_no)
            det = np.asarray(det_row_no)
            rank.append(det[0])
            break
        else:
            break

    return rank


# 按照距离底部最近的人脸框为基准进行排序
def enabel_row_up_by_bottom(det):
    row_up = []
    row_no = []
    if len(det) >= 1:
        # 以离左上角最近的人脸框为基准,找出同一行的人脸框 or 以离右上角最近的人脸框为基准,找出同一行的人脸框
        # if np.argmin(det[:, 1]) == np.argmin(det[:, 0])

        max_y1 = det[np.argmax(det[:, 3])][1]
        rank_index = np.argsort(det[:, 3])
        for i in range(len(det)):
            if det[rank_index[i]][3] > (max_y1 + 5):
                # ratio = (base_h - abs(base_h - det[rank_index[i]][3]))/base_h
                row_up.append(rank_index[i])  # 成一行
            else:
                row_no.append(rank_index[i])  # 非成行

    return row_up, row_no


def arrange_row_up_by_bottom(det, row_up):
    det_row = []
    det_arr = []
    length = len(row_up)
    # 取出排成一行的人脸框
    for i in range(length):
        det_row.append(det.tolist().pop(row_up[i]))

    # 对取出的一行人脸框先按照左上角坐标x从小到大排序，然后从中间向两边取.
    det_row = np.asarray(det_row)
    index = np.argsort(det_row[:, 0])

    for i in range(int(length / 2) + 1):
        if i == 0:
            init_pos = int(length / 2)
            det_arr.append(det_row[index[init_pos]])
        else:
            if init_pos - i >= 0:
                det_arr.append(det_row[index[init_pos - i]])
            if init_pos + i <= (length - 1):
                det_arr.append(det_row[index[init_pos + i]])

    return det_arr


def rank_all_faces_by_bottom(det):
    rank = []
    while True:
        row_up, row_no = enabel_row_up_by_bottom(det)
        # print('row_up:', row_up)
        # print('row_no:', row_no)
        if len(row_up) >= 1:
            det_row_up = arrange_row_up_by_bottom(det, row_up)
            for i in range(len(det_row_up)):
                rank.append(det_row_up[i])

        if len(row_no) > 1:
            det_row_no = remaining_row_no(det, row_no)
            det = np.asarray(det_row_no)
        elif len(row_no) == 1:
            det_row_no = remaining_row_no(det, row_no)
            det = np.asarray(det_row_no)
            rank.append(det[0])
            break
        else:
            break

    return rank


# 置信度排序
def rank_confidence(src_det_x1, dst_det, src_cf):
    rank_cf = []
    for i in range(len(src_cf)):
        x1 = np.asarray(dst_det)[:, 0][i]
        index = src_det_x1.index(x1)
        rank_cf.append(src_cf[index])

    return rank_cf


def findCPos(img, det, cf):
    # 找C位
    face_nums = len(det)
    if face_nums > 0:
        det = np.asarray(det)
        img_size = np.asarray(img.shape)[0:2]
        det_arr = []
        cf_arr =[]
        if face_nums > 1:
            bounding_box_size = (det[:, 2] - det[:, 0]) * (det[:, 3] - det[:, 1])
            img_center = img_size / 2
            offset = np.vstack([(det[:, 2] + det[:, 0]) / 2 - img_center[1], (det[:, 3] + det[:, 1]) / 2 - img_center[0]])
            offset_dist_squared = np.sum(np.power(offset, 2), 0)
            result = bounding_box_size - offset_dist_squared * 2.0
            rank_index = np.argsort(result)  # 结果从小到大排序
            for i in range(face_nums):
                idx = (face_nums - 1) - i
                det_arr.append(np.squeeze(det[rank_index[idx]]))
                cf_arr.append(np.squeeze(cf[rank_index[idx]]))
        else:
            det_arr.append(np.squeeze(det))
            cf_arr.append(np.squeeze(cf))

    return det_arr, cf_arr


def saveData(data_path, faces_name, faces_embedding):
    if not os.path.exists(data_path):
        np.savez_compressed(data_path, faces_name=faces_name, faces_embedding=faces_embedding)
    else:
        data = np.load(data_path, allow_pickle=True)
        name, embedding = data['faces_name'], data['faces_embedding']
        name_list = list(name)
        name_list.extend(faces_name)

        embedding_list = list(embedding)
        embedding_list.extend(faces_embedding)

        np.savez_compressed(data_path, faces_name=name_list, faces_embedding=embedding_list)


def caffe_interfece(test_img, caffeNet, default_confidence):
    det = []
    cf = []

    (h, w) = test_img.shape[:2]
    # load the input image and construct an input blob for the image
    # by resizing to a fixed 300x300 pixels and then normalizing it
    blob = cv2.dnn.blobFromImage(cv2.resize(test_img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    # caffe模型检测人脸
    caffeNet.setInput(blob)
    detections = caffeNet.forward()

    # # loop over the detections： (1,1,人脸个数,7), 7:xx, xx, confidence, x1, y1, x2, y2
    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        # if i >= 4:
        #     break

        # filter out weak detections by ensuring the `confidence` is greater than the minimum confidence
        if confidence > default_confidence:
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # 将超出图像边框的检测框过滤掉
            if endX > w or endY > h:
                print('检测框超出了图像边框的.')
                continue

            print('置信度:%f.' % confidence)
            det.append(box)
            cf.append(confidence)

    return det, cf


def fileTreeWidgetData(rootVolumePath, dbDataList):
    fileTreeData = []
    dbListDirName = []

    for ele in dbDataList:
        dbListDirName.append(ele['volume_name'])

    dstListDirName = os.listdir(rootVolumePath)
    targetDirName = [x for x in dstListDirName if x not in dbListDirName]  # #在dstListDirName列表中而不在dbListDirName列表中

    for ele in dbDataList:
        myMap = {}
        myMap[ele['volume_name']] = ele['volume_num']
        fileTreeData.append(myMap)

    for ele in targetDirName:
        myMap = {}
        myMap[ele] = '编辑'
        fileTreeData.append(myMap)

    if len(dbDataList) > 0:
        rootVolumeNum  = dbDataList[0]['root_volume_num']
    else:
        rootVolumeNum = '编辑'

    return rootVolumeNum, fileTreeData


def get_filePath_with_creationDate_as_dict(folder):
    result = {}
    for f in os.listdir(folder):
        if platform.system().lower() == 'windows':
            fullFileName = folder + "\\" + f
        else:
            fullFileName = folder + "/" + f
        if os.path.isfile(fullFileName):
            t = os.stat(fullFileName)
            mtime = np.min([t.st_ctime, t.st_mtime, t.st_atime])
            mtime = str(mtime)
            i = 0
            while mtime+"_"*i in result:
                i += 1
            mtime = mtime+"_"*i
            result[mtime] = fullFileName
    return result


def rank_and_rename_filePath_with_creationDate(filesDict, preName):
    for i,key in enumerate(sorted(filesDict)):
        dummy, extension =  os.path.splitext(filesDict[key])
        parentPath = os.path.abspath(os.path.join(dummy, ".."))
        newName = preName + '-{0:0>4}'.format(i + 1)
        new_file_name = os.path.abspath(os.path.join(parentPath, newName)) + extension
        os.rename(filesDict[key],  new_file_name)
        filesDict[key] = new_file_name

        return filesDict


# 两个眼睛和图片中心旋转实现人脸对齐
def alignment_1(img,landmark):

    if landmark.shape[0]==68:
        x = landmark[36,0] - landmark[45,0]
        y = landmark[36,1] - landmark[45,1]
    elif landmark.shape[0]==5:
        x = landmark[0,0] - landmark[1,0]
        y = landmark[0,1] - landmark[1,1]

    # 眼睛连线相对于水平线的倾斜角，计算arctan
    if x==0:
        angle = 0
    else:
        # 计算弧度值
        angle = math.atan(y/x)*180/math.pi

    # 计算图片的中心
    center = (img.shape[1]//2, img.shape[0]//2)

    # 根据两只眼睛的倾斜角和图片的中心计算整张图片的旋转矩阵
    RotationMatrix = cv2.getRotationMatrix2D(center, angle, 1)
    # 利用仿射函数进行图片的旋转
    new_img = cv2.warpAffine(img,RotationMatrix,(img.shape[1],img.shape[0]))

    # 在旋转后的图片上（即对齐后的人脸图片）计算新的5个人脸特征点的位置
    RotationMatrix = np.array(RotationMatrix)
    new_landmark = []
    for i in range(landmark.shape[0]):
        pts = []
        pts.append(RotationMatrix[0,0]*landmark[i,0]+RotationMatrix[0,1]*landmark[i,1]+RotationMatrix[0,2])
        pts.append(RotationMatrix[1,0]*landmark[i,0]+RotationMatrix[1,1]*landmark[i,1]+RotationMatrix[1,2])
        new_landmark.append(pts)

    new_landmark = np.array(new_landmark)

    # 矫正后的人脸图片和人脸5个关键特征点位置
    return new_img, new_landmark


#-----------------------------#
#   将长方形调整为正方形
#-----------------------------#
def rect2square(rectangles):
    w = rectangles[:,2] - rectangles[:,0]
    h = rectangles[:,3] - rectangles[:,1]
    l = np.maximum(w,h).T
    rectangles[:,0] = rectangles[:,0] + w*0.5 - l*0.5
    rectangles[:,1] = rectangles[:,1] + h*0.5 - l*0.5
    rectangles[:,2:4] = rectangles[:,0:2] + np.repeat([l], 2, axis = 0).T
    return rectangles

# 根据box的坐标返回包含box坐标的矩形索引
def selectedRectIndex(rectangles, box):
    for rect in rectangles:
        flag = [False for elem in box if elem not in rect]
        if not flag:
            return rectangles.index(rect)

# 两个眼睛和图片中心旋转实现人脸对齐
def alignFace(img, rectangles, squareRect, box):
    index = selectedRectIndex(rectangles, box)
    rectangle = squareRect[index]
    landmark = (np.reshape(rectangle[5:15],(5,2)) - np.array([int(rectangle[0]),int(rectangle[1])]))/(rectangle[3]-rectangle[1])*160
    crop_img = img[int(rectangle[1]):int(rectangle[3]), int(rectangle[0]):int(rectangle[2])]
    crop_img = cv2.resize(crop_img,(160,160))
    new_img,_ = alignment_1(crop_img,landmark)
    return new_img


std_160_landmark = [[54.80897114,59.00365493], # 160x160的目标点
               [112.01078961,55.16622207],
               [86.90572522,91.41657571],
               [55.78746897,114.90062758],
               [113.15320624,111.08135986]]

std_112_landmark = [[30.2946+8.0000, 51.6963], # 112x112的目标点
               [65.5318+8.0000, 51.6963],
               [48.0252+8.0000, 71.7366],
               [33.5493+8.0000, 92.3655],
               [62.7299+8.0000, 92.3655]]

def transformation_from_points(points1, points2):
    points1 = points1.astype(np.float64)
    points2 = points2.astype(np.float64)
    c1 = np.mean(points1, axis=0)
    c2 = np.mean(points2, axis=0)
    points1 -= c1
    points2 -= c2
    s1 = np.std(points1)
    s2 = np.std(points2)
    points1 /= s1
    points2 /= s2
    U, S, Vt = np.linalg.svd(points1.T * points2)
    R = (U * Vt).T
    return np.vstack([np.hstack(((s2 / s1) * R,c2.T - (s2 / s1) * R * c1.T)),np.matrix([0., 0., 1.])])


def warp_im(img_im, orgi_landmarks,tar_landmarks):
    pts1 = np.float64(np.matrix([[point[0], point[1]] for point in orgi_landmarks]))
    pts2 = np.float64(np.matrix([[point[0], point[1]] for point in tar_landmarks]))
    M = transformation_from_points(pts1, pts2)
    dst = cv2.warpAffine(img_im, M[:2], (img_im.shape[1], img_im.shape[0]))
    return dst


def alignFace2(img, rectangles, rectanglesExd, squareRect, box):
    index = selectedRectIndex(rectangles, box)
    margin = int((rectanglesExd[index][0] - squareRect[index][0]) / 2)
    # margin = int((rectanglesExd[index][0] - squareRect[index][0]))
    # print('#### alignFace2:', margin)
    imgSize = [160, 160 + margin]
    face_landmarks = np.reshape(rectanglesExd[index][5:15], (5, 2)).tolist()
    warpImg = warp_im(img, face_landmarks, std_160_landmark)
    new_img = warpImg[0:imgSize[0], margin:imgSize[1]]
    return new_img, face_landmarks

def alignFace3(img, rectangles, rectanglesExd, squareRect, box):
    index = selectedRectIndex(rectangles, box)
    margin = int((rectanglesExd[index][0] - squareRect[index][0]) / 2)
    # margin = int((rectanglesExd[index][0] - squareRect[index][0]))
    # print('#### alignFace2:', margin)
    imgSize = [112, 112 + margin]
    face_landmarks = np.reshape(rectanglesExd[index][5:15], (5, 2)).tolist()
    warpImg = warp_im(img, face_landmarks, std_112_landmark)
    new_img = warpImg[0:imgSize[0], margin:imgSize[1]]
    return new_img, face_landmarks

def alignFace4(img, rectangles, box):
    index = selectedRectIndex(rectangles, box)
    face_landmarks = np.reshape(rectangles[index][5:15], (5, 2))
    new_img = face_align.norm_crop(img, face_landmarks)
    return new_img, face_landmarks


def alignFace2WithVerify(img, margin, face_landmarks):
    imgSize = [160, 160 + margin]
    warpImg = warp_im(img, face_landmarks, std_160_landmark)
    new_img = warpImg[0:imgSize[0], margin:imgSize[1]]
    return new_img


def  visualTsne(embeddings, y_train):
    tsne = TSNE(learning_rate=100)

    tsne_features = tsne.fit_transform(embeddings)

    X = tsne_features[:, 0]
    y = tsne_features[:, 1]

    dataset = pd.DataFrame(data=y_train, columns=['label'])
    dataset['X'] = X
    dataset['y'] = y

    plt.figure(figsize=(13, 8))
    sns.scatterplot(data=dataset, x='X', y='y', hue='label', s=120)
    plt.show()


class OperationJson:
    def __init__(self, file_name=None):
        if file_name:
            self.file_name = file_name
        else:
            self.file_name = './config/cfg.json'
        self.data = self.get_data()

    def get_data(self):
        fp = open(self.file_name)
        data = json.load(fp)
        fp.close()
        return data

    def get_value(self, id):
        return self.data[id]













