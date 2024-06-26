# -*- coding: utf-8 -*-
"""
@file: business_recognition.py
@desc:
@author: Jaden Wu
@time: 2020/9/3 10:15
"""
import hashlib
import json
import logging
import os
import shutil
from collections import defaultdict

import cv2
import glob
import time
import threading
import numpy as np
# import tensorflow as tf
# from keras.models import load_model
# from mtcnn import MTCNN

from sklearn.metrics import accuracy_score
from sklearn.svm import SVC
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.model_selection import cross_val_score
from multiprocessing import Process, Event, Queue
import multiprocessing as mp
import recognition.face_model as face_model
import recognition.mtcnn_detector as mtcnn_detector

from recognition.utils import *

from photo_arch.adapters.sql.repo import RepoGeneral
from photo_arch.infrastructures.databases.db_setting import engine, make_session, session
from license.check_license import get_lic_info
from photo_arch.pa_log.log import create_logger

opers = OperationJson()
logLevel = opers.get_value('logLevel')
logger = create_logger()
if logLevel == 'INFO': # 默认debug
    logger.setLevel(logging.INFO)

def get_gpu_state():
    engine.dispose()
    sql_repo = RepoGeneral(make_session(engine))
    license_path_list = sql_repo.query('setting',{'setting_id': [1]})
    if len(license_path_list) == 1:
        license_path = license_path_list[0]['license_path']
        lic_info = get_lic_info(license_path)
        if lic_info != None:
            gpu_state = lic_info.get('enable_gpu')
        else:
            gpu_state = False
    else:
        gpu_state = False
    logger.info('@@@@@@@ gpu state = {}'.format(gpu_state))
    return gpu_state

# 禁用GPU后,下面的config代码也就无效了
gpu_state = get_gpu_state()
# os.environ['CUDA_VISIBLE_DEVICES'] = '0' if gpu_state else '-1'
# if tf.__version__.startswith('1.'):  # tensorflow 1
#     config = tf.ConfigProto()  # allow_soft_placement=True
#     config.gpu_options.allow_growth = True #不全部占满显存, 按需分配
#     sess = tf.Session(config=config)
# else:  # tensorflow 2
#     gpus = tf.config.experimental.list_physical_devices(device_type='GPU')
#     for gpu in gpus:
#         tf.config.experimental.set_memory_growth(gpu, True)


class RecognizeProcess(Process):
    mtcnn_detector = None
    facenet_model = None
    margin = 32

    faceProp = 0.9
    euclideanDist = 0.74
    simular = 0.4
    canvasW = 2000
    canvasH = 2000

    face_rank_rule_by_top = True

    def __init__(self, done_queue, data_queue, param_queue, from_queue):
        super(RecognizeProcess, self).__init__()
        self.event = Event()
        self.event.set() # 设置为True
        self.done_queue = done_queue # 写入返回数据
        self.data_queue = data_queue
        self.param_queue = param_queue
        self.from_queue = from_queue


    def pause(self):
        if self.is_alive():
            logger.info("识别子进程休眠")
            self.event.clear()  # 设置为False, 让进程阻塞
        else:
            logger.info("识别子进程结束")

    def resume(self):
        if self.is_alive():
            self.event.set()  # 设置为True, 进程唤醒
            logger.info("识别子进程唤醒")
        else:
            logger.info("识别子进程结束")


    def run(self):
        if self.mtcnn_detector == None:
            # myKwargs = {'root': 'model'}
            # self.mtcnn_detector = insightface.model_zoo.get_model('retinaface_mnet025_v2', **myKwargs)
            # self.mtcnn_detector.prepare(ctx_id=-1)
            self.mtcnn_detector = mtcnn_detector.MtcnnDetector(model_folder='model/mtcnn-model') # 图像格式bgr
            logger.info('######:识别 mtcnn_detector')
        if self.facenet_model == None:
            gpuDevice = -1
            if gpu_state == True:
                gpuDevice = 0
            self.facenet_model = face_model.FaceModel(gpuDevice, 'model/model-r100-ii/model', 0)
            logger.info('######:识别 load model')


        engine.dispose()
        sql_repo = RepoGeneral(make_session(engine))

        while 1:
            if self.data_queue.empty() == True:
                logger.info('#### 识别:队列空,子进程暂停')
                self.pause()
            else:
                if self.from_queue.empty(): # 如果为空，说明不是通过‘识别’按钮进来的
                    self.pause()
                    logger.info('#### 识别:等待点击识别按钮')
            self.event.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后才立即返回

            imgPath = self.data_queue.get()
            # print('#####:pid=%d, imgPath=%s' %(os.getpid(), imgPath))
            det = []
            lmk = []

            if not self.param_queue.empty():
                try:
                    params = self.param_queue.get_nowait()
                    params = eval(params)
                    self.faceProp = params['threshold']
                except Exception as e:
                    logger.error(repr(e))
                    self.faceProp = 0.9

            scale = calculate_img_scaling(imgPath, self.canvasH, self.canvasW)
            img = cv2.imdecode(np.fromfile(imgPath, dtype=np.uint8), cv2.IMREAD_COLOR)
            (h, w) = img.shape[:2]
            imgCopy = cv2.resize(img, (int(w*scale), int(h*scale)))
            test_img = cv2.cvtColor(imgCopy, cv2.COLOR_BGR2RGB)
            (h, w) = test_img.shape[:2]
            bbox, pts5 = self.mtcnn_detector.detect_face(imgCopy)
            bbox[:, 0] = np.maximum(bbox[:, 0], 0)  # x1
            bbox[:, 1] = np.maximum(bbox[:, 1], 0)  # y1
            bbox[:, 2] = np.minimum(bbox[:, 2], w)  # x2
            bbox[:, 3] = np.minimum(bbox[:, 3], h)  # y2
            for box, pt5 in zip(bbox,pts5):
                confidence = box[4]
                if confidence > 0.98: # 0.93
                    # 将超出图像边框的检测框过滤掉
                    # if endX > w or endY > h:
                    #     print('检测框超出了图像边框的.')
                    #     continue

                    # print('MTCNN置信度:%f.' % confidence)
                    det.append(list(box[0:4].astype('int')))
                    lmk.append(np.array([pt5[0:5], pt5[5:10]]).T)

            face_nums = len(det)
            if face_nums > 0:
                if self.face_rank_rule_by_top:
                    det_arr = rank_all_faces_by_top(np.asarray(det))
                else:
                    det_arr = rank_all_faces_by_bottom(np.asarray(det))

                faces = []
                embeddings = []
                peoples = ''
                curFaceRecNum = 0  # 当前图片里面的人脸数
                faceRecNum = 0
                for j, box in enumerate(det_arr):
                    index = det.index(box.tolist())
                    (startX, startY, endX, endY) = box
                    scaled = face_align.norm_crop(test_img, lmk[index])
                    # cv2.imwrite("zp/reco_align_{}.jpg".format(time.time()), cv2.cvtColor(scaled, cv2.COLOR_RGB2BGR))
                    unknown_embedding = self.facenet_model.get_feature(scaled)
                    # who_name = get_name_by_embedding(imgPath, unknown_embedding, self.faceProp, self.euclideanDist, 1)
                    who_name = get_name_by_embedding(imgPath, unknown_embedding, self.faceProp, self.simular, 0)
                    if who_name != '':
                        faceRecNum += 1
                        curFaceRecNum += 1
                    faces.append({
                        'id': j,
                        'box': str([startX / scale, startY / scale, endX / scale, endY / scale]),
                        'name': who_name
                        # 'landmark': str((lmk[index]/scale).tolist())
                        # 'embedding':str(list(unknown_embedding))
                    })  # box和embedding如果不转换成str,json.dumps就会报错(目前没有找到解决方法)

                    embeddings.append({
                        str(j): str(list(unknown_embedding))
                    })

                    if j < len(det_arr) :
                        if who_name != '':
                            peoples += '{},'.format(who_name)


                if curFaceRecNum == face_nums:
                    face_recog_state = 1  # 全部识别
                else:
                    face_recog_state = 0  # 部分识别

                jsonFaces = json.dumps(faces, ensure_ascii=False)
                jsonEmbeddings = json.dumps(embeddings, ensure_ascii=False)
            else:
                face_recog_state = 2  # 没有检测出脸
                jsonFaces = ''
                jsonEmbeddings = ''
                peoples = ''

            recognizedResultInfo = {'face_nums': face_nums, 'face_recog_state': face_recog_state, 'faceRecNum': faceRecNum, 'img_path': imgPath}
            self.done_queue.put(json.dumps(recognizedResultInfo, ensure_ascii=False))

            # 更新数据库photo_path为imgPath的记录
            sql_repo.update('face', {"photo_path": [imgPath]},
                            new_info={'faces': jsonFaces, 'recog_state': face_recog_state, 'parent_path': os.path.abspath(imgPath + os.path.sep + ".."),
                                      'embeddings': jsonEmbeddings })
            if peoples.endswith(','):
                peoples = peoples[0:-1]
            sql_repo.update('photo', {"photo_path": [imgPath]}, new_info={'peoples': peoples})


class VerifyProcess(Process):
    img_path = ''
    faces_list = []
    table_widget = []


    def __init__(self, verify_queue):
        super(VerifyProcess, self).__init__()
        self.event = Event()
        self.event.set()  # 设置为True
        self.verify_queue = verify_queue


    def pause(self):
        if self.is_alive():
            logger.info("核验子进程休眠")
            self.event.clear()  # 设置为False, 让进程阻塞
        else:
            logger.info("核验子进程结束")

    def resume(self):
        if self.is_alive():
            self.event.set()  # 设置为True, 进程唤醒
            logger.info("核验子进程唤醒")
        else:
            logger.info("核验子进程结束")


    def run(self):
        engine.dispose()
        sql_repo = RepoGeneral(make_session(engine))

        while 1:
            if self.verify_queue.empty() == True:
                logger.info('#### 核验 :队列空,子进程暂停')
                self.pause()
            self.event.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后才立即返回

            checkedInfoDict = self.verify_queue.get()
            checkedInfoDict = eval(checkedInfoDict)

            self.img_path = checkedInfoDict['path']
            self.faces_list = eval(checkedInfoDict['faces'])
            self.table_widget = checkedInfoDict['table_widget']


            faces_name = []
            faces_embedding = []

            new_faces = []
            peoples = ''
            new_faces_name = []
            new_faces_id = []

            orig_faces_id = list(range(len(self.faces_list)))

            for item in self.table_widget:
                if item['id'] == '':
                    continue
                new_faces_id.append(int(item['id']))
                new_faces_name.append(item['name'])

            embeddings_dict = sql_repo.query('face', {"photo_path": [self.img_path]}, ('embeddings'))
            embeddings_dict = eval(embeddings_dict[0]['embeddings'])

            for id in orig_faces_id:
                if id in new_faces_id: # 没有删除
                    index = new_faces_id.index(id)
                    name = new_faces_name[index]
                else:
                    name = ''

                if name != '' :
                    new_faces.append({
                        'id':id,
                        'box':self.faces_list[id]['box'],
                        'name': name
                        # 'landmark': self.faces_list[id]['landmark']
                    })

                    embedding = np.asarray(eval(embeddings_dict[id][str(id)]))
                    faces_embedding.append(embedding)
                    faces_name.append(name)
                    peoples += '{},'.format(name)

            # 只记录有名字的人
            if len(faces_name) > 0 :
                saveData('data/data.npz', faces_name, faces_embedding)
                jsonFaces = json.dumps(new_faces, ensure_ascii=False)
                verifyState = 1
                sql_repo.update('face', {"photo_path": [self.img_path]}, new_info={'faces': jsonFaces, 'verify_state': verifyState})

                if peoples.endswith(','):
                    peoples = peoples[0:-1]
                sql_repo.update('photo', {"photo_path": [self.img_path]}, new_info={'peoples': peoples})


class SearchImagesProcess(Process):
    graph = None
    mtcnn_detector = None
    facenet_model = None
    margin = 32
    canvasH = 0
    canvasW = 0

    search_src_img_path = ''
    src_embedding = None


    def __init__(self, search_queue, retrived_queue, counter_queue, search_faceList_queue, search_filePath_queue, silence_queue, backedWorkIsOver_queue):
        super(SearchImagesProcess, self).__init__()
        self.event = Event()
        self.event.set()  # 设置为True
        self.search_queue = search_queue
        self.retrived_queue = retrived_queue
        self.counter_queue = counter_queue
        self.search_faceList_queue = search_faceList_queue
        self.search_filePath_queue = search_filePath_queue
        self.silence_queue = silence_queue
        self.backedWorkIsOver_queue = backedWorkIsOver_queue


    def pause(self):
        if self.is_alive():
            logger.info("检索子进程休眠")
            self.event.clear()  # 设置为False, 让进程阻塞
        else:
            logger.info("检索子进程结束")

    def resume(self):
        if self.is_alive():
            self.event.set()  # 设置为True, 进程唤醒
            logger.info("检索子进程唤醒")
        else:
            logger.info("检索子进程结束")

    def calculate_euclid_distance(self, sql_repo, parentPath, retrive_src_embedding, flag):
        photo_path = []
        retrive_des_box = []
        retrive_des_embedding = []
        #tsneEmbedding = []
        retriveResultInfo = []
        retriveResultPhotoPath = []
        tmp_photo_path = []
        tmp_box = []
        i= 0
        indexList = []
        if flag == 'searchfaces':
            des_embedding_list = sql_repo.query('searchfaces', {"parent_path": [os.path.abspath(parentPath)]}, ('photo_path', 'face_box', 'embedding'))
            for ele_dict in des_embedding_list:
                # 将每张图片里面人脸的index范围记录下来
                indexDict = {}
                nums = len(eval(ele_dict['face_box']))
                indexDict[i] = i + nums
                i += nums
                indexList.append(indexDict)
                for box in eval(ele_dict['face_box']):
                    retrive_des_box.append(box)
                    photo_path.append(ele_dict['photo_path'])
                for emd in eval(ele_dict['embedding']):
                    retrive_des_embedding.append(emd)
        else:
            des_embedding_list = sql_repo.query('face', {"parent_path": [os.path.abspath(parentPath)]}, ('photo_path', 'faces', 'embeddings'))
            for ele_dict in des_embedding_list:
                # 将每张图片里面人脸的index范围记录下来
                indexDict = {}
                nums = len(eval(ele_dict['face_box']))
                indexDict[i] = i + nums
                i += nums
                indexList.append(indexDict)
                for face in eval(ele_dict['faces']):
                    retrive_des_box.append(eval(face['box']))
                    photo_path.append(ele_dict['photo_path'])
                for i, emd in enumerate(eval(ele_dict['embeddings'])):
                    retrive_des_embedding.append(eval(emd[str(i)]))

        # tsneEmbedding.append(np.asarray(retrive_src_embedding[0]))
        # tsneEmbedding.append(np.asarray(retrive_des_embedding[3]))
        # lable = list(range(len(tsneEmbedding)))
        # visualTsne(tsneEmbedding, lable)
        for emb in retrive_src_embedding:
            # dist = np.linalg.norm(np.asarray(retrive_des_embedding) - np.asarray(emb), axis=1)
            # dist = list(dist)
            sim = np.dot(np.asarray(retrive_des_embedding), np.asarray(emb))
            sim = sim.reshape(-1)
            sim = list(sim)
            # print('###### 相似度(后台):', sim)
            for k in indexList: # indexList的大小就是图片的数量
                f_index = list(k.keys())[0]
                e_index = list(k.values())[0]
                simWithSiglePhoto = sim[f_index:e_index] # 图片里面的人的相似度
                maxV = max(simWithSiglePhoto)
                if maxV >= 0.4:
                    index = sim.index(maxV)
                    tmp_photo_path.append(photo_path[index])
                    tmp_box.append(retrive_des_box[index])
                    # print('图片index和路径:{}-{}, {}, {}'.format(list(k.keys())[0], list(k.values())[0], maxV, photo_path[index]))

        # 将重复图片的box放在同一个list中
        d = defaultdict(list)
        for k, va in [(v, i) for i, v in enumerate(tmp_photo_path)]:
            d[k].append(va)
        for k, v in d.items():
            face_box = []
            for index in v:
                face_box.append(tmp_box[index])
            retriveResultInfo.append({'photo_path': k, 'face_box': face_box})
            retriveResultPhotoPath.append(k)

        return retriveResultInfo, retriveResultPhotoPath



    def run(self):
        if self.mtcnn_detector == None:
            self.mtcnn_detector = mtcnn_detector.MtcnnDetector(model_folder='model/mtcnn-model')  # 图像格式bgr
            logger.info('######:检索 mtcnn_detector')
        if self.facenet_model == None:
            gpuDevice = -1
            if gpu_state == True:
                gpuDevice = 0
            self.facenet_model = face_model.FaceModel(gpuDevice, 'model/model-r100-ii/model', 0)
            logger.info('######:检索 load model')

        engine.dispose()
        sql_repo = RepoGeneral(make_session(engine))

        i = 0
        flag = False
        src_embedding = []
        des_path = ''
        backedSilence_path = ''
        while 1:
            if self.search_queue.empty() == True:
                logger.info('#### 检索:队列空,子进程暂停')
                i = 0
                flag = False
                src_embedding.clear()
                self.pause()
            self.event.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后才立即返回

            imgPath = self.search_queue.get()
            if i == 0 :
                des_path = self.search_filePath_queue.get()
                backedSilence_path = self.search_filePath_queue.get()
                srcPath = imgPath
                face_list = eval(self.search_faceList_queue.get())
                src_embedding_list = sql_repo.query('face', {"photo_path": [os.path.abspath(srcPath)]}, ('embeddings'))
                if len(src_embedding_list) == 0:
                    src_embedding_list = sql_repo.query('searchfaces', {"photo_path": [os.path.abspath(srcPath)]}, ('embedding'))
                    if len(src_embedding_list) == 1: # 已存在searchfaces数据库
                        retrive_src_embedding = eval(src_embedding_list[0]['embedding'])
                        for index in face_list:
                            src_embedding.append(retrive_src_embedding[index])

                        flag = True
                        i += 1
                        self.counter_queue.put(imgPath)
                        continue
                    else:
                        i += 1
                else: # 已存在face数据库
                    retrive_src_embedding = eval(src_embedding_list[0]['embeddings'])
                    retrive_src_embedding = eval(retrive_src_embedding[0]['0'])
                    for index in face_list:
                        src_embedding.append(eval(retrive_src_embedding[index][str(index)]))

                    flag = True
                    i += 1
                    self.counter_queue.put(imgPath)
                    continue
            else:
                if i == 1 :
                    parentPath = des_path # os.path.abspath(os.path.join(imgPath, ".."))
                    parent_path_list = sql_repo.query('face', {"parent_path": [os.path.abspath(parentPath)]}, ('parent_path'))
                    if len(parent_path_list) == 0:
                        parent_path_list = sql_repo.query('searchfaces', {"parent_path": [os.path.abspath(parentPath)]}, ('searchfaces_id','parent_path'))
                        if len(parent_path_list) > 0:
                            retriveResultPhotoPathTmp =[]
                            retriveResultInfoList, retriveResultPhotoPath = self.calculate_euclid_distance(sql_repo, parentPath, src_embedding, 'searchfaces')
                            retriveResultPhotoPathTmp.extend(retriveResultPhotoPath)
                            for ele_dict in retriveResultInfoList:
                                self.retrived_queue.put(json.dumps(ele_dict, ensure_ascii=False))
                            backedRestNums = self.silence_queue.qsize()
                            self.retrived_queue.put('{}'.format(backedRestNums))  # 后台剩余未提取的特征的照片数量

                            if backedRestNums > 0 :
                                self.counter_queue.put(imgPath)
                                initTmpNums = backedRestNums
                                while True:
                                    time.sleep(2)
                                    backedRestNums = self.silence_queue.qsize()
                                    if backedRestNums < initTmpNums:
                                        if backedRestNums == 0:
                                            if self.backedWorkIsOver_queue.empty() == True: # 后台最后一张图片提取的特征还没有写入数据库
                                                continue
                                            else:
                                                flag = self.backedWorkIsOver_queue.get()
                                                logger.info('后台最后一张图片提取的特征已经写入数据库了：',flag)
                                        parent_path_list = sql_repo.query('searchfaces', {"parent_path": [os.path.abspath(parentPath)]}, ('parent_path'))
                                        if len(parent_path_list) > 0:
                                            retriveResultInfoList, retriveResultPhotoPath = self.calculate_euclid_distance(sql_repo, parentPath, src_embedding, 'searchfaces')
                                            if len(retriveResultPhotoPath) > 0:
                                                retriveResultPhotoPathDiff = list(set(retriveResultPhotoPath).difference(set(retriveResultPhotoPathTmp)))
                                                if len(retriveResultPhotoPathDiff) > 0:
                                                    retriveResultPhotoPathTmp.extend(retriveResultPhotoPathDiff)
                                                    for item in retriveResultPhotoPathDiff:
                                                        index = retriveResultPhotoPath.index(item)
                                                        self.retrived_queue.put(json.dumps(retriveResultInfoList[index], ensure_ascii=False))
                                                    self.retrived_queue.put('{}'.format(backedRestNums))  # 后台剩余未提取的特征的照片数量
                                                    imgPath = self.search_queue.get()
                                                    self.counter_queue.put(imgPath)
                                        initTmpNums = backedRestNums
                                    elif backedRestNums == 0:
                                        break

                                for _ in range(self.search_queue.qsize()):
                                    imgPath = self.search_queue.get()
                                    self.counter_queue.put(imgPath)
                                i += 1
                                continue
                            else:
                                self.counter_queue.put(imgPath)
                                for _ in range(self.search_queue.qsize()):
                                    imgPath = self.search_queue.get()
                                    self.counter_queue.put(imgPath)
                                i += 1
                                continue
                        else:
                            if des_path == backedSilence_path:
                                if self.silence_queue.empty() != True: # 后台正在提取图片特征
                                    time.sleep(6) # 等待后台特征入库
                                    self.counter_queue.put(imgPath)
                                    i = 1
                                else: # 在数据库中没有检索到该路径下的数据
                                    self.counter_queue.put(imgPath)
                                    for _ in range(self.search_queue.qsize()):
                                        imgPath = self.search_queue.get()
                                        self.counter_queue.put(imgPath)

                                continue
                            else:
                                i += 1
                    else:
                        retriveResultInfoList = self.calculate_euclid_distance(sql_repo, parentPath, retrive_src_embedding, 'face')
                        for ele_dict in retriveResultInfoList:
                            self.retrived_queue.put(json.dumps(ele_dict, ensure_ascii=False))
                        self.retrived_queue.put('0') # 保持处理的统一性


                        self.counter_queue.put(imgPath)
                        for _ in range(self.search_queue.qsize()):
                            imgPath = self.search_queue.get()
                            self.counter_queue.put(imgPath)

                        continue
                else:
                    i += 1

            det = []
            lmk = []
            rectangles = []
            logger.info('检索: imgPath=%s' % imgPath)

            scale = calculate_img_scaling(imgPath, self.canvasH, self.canvasW)
            img = cv2.imdecode(np.fromfile(imgPath, dtype=np.uint8), cv2.IMREAD_COLOR)
            (h, w) = img.shape[:2]
            imgCopy = cv2.resize(img, (int(w * scale), int(h * scale)))
            test_img = cv2.cvtColor(imgCopy, cv2.COLOR_BGR2RGB)
            (h, w) = test_img.shape[:2]
            bbox, pts5 = self.mtcnn_detector.detect_face(imgCopy)
            bbox[:, 0] = np.maximum(bbox[:, 0], 0)  # x1
            bbox[:, 1] = np.maximum(bbox[:, 1], 0)  # y1
            bbox[:, 2] = np.minimum(bbox[:, 2], w)  # x2
            bbox[:, 3] = np.minimum(bbox[:, 3], h)  # y2

            for box, pt5 in zip(bbox, pts5):
                confidence = box[4]
                if confidence > 0.98:  # 0.93
                    # 将超出图像边框的检测框过滤掉
                    # if endX > w or endY > h:
                    #     print('检测框超出了图像边框的.')
                    #     continue

                    # print('MTCNN置信度:%f.' % confidence)
                    det.append(list(box[0:4].astype('int')))
                    lmk.append(np.array([pt5[0:5], pt5[5:10]]).T)



            face_nums = len(det)
            src_dir = os.path.abspath(os.path.join(imgPath, ".."))
            if face_nums > 0:
                det_arr = rank_all_faces_by_top(np.asarray(det))

                searchface = {}
                box_list = []
                embedding_list = []
                searchfacesDatas = []
                for j, box in enumerate(det_arr):
                    index = det.index(box.tolist())
                    (startX, startY, endX, endY) = box
                    scaled = face_align.norm_crop(test_img, lmk[index])
                    # cv2.imwrite("zpj/reco_align_{}.jpg".format(time.time()), cv2.cvtColor(scaled, cv2.COLOR_RGB2BGR))
                    embedding = self.facenet_model.get_feature(scaled)
                    box_list.append([startX / scale, startY / scale, endX / scale, endY / scale])
                    embedding_list.append(list(embedding))

                searchface['photo_path'] = imgPath
                searchface['face_box'] = str(box_list)
                searchface['embedding'] = str(embedding_list)
                searchface['parent_path'] = src_dir
                searchfacesDatas.append(searchface)
                sql_repo.add('searchfaces', searchfacesDatas)

                if imgPath == srcPath and flag == False:
                    for index in face_list:
                        src_embedding.append(embedding_list[index])
                else:
                    tmp_photo_path = []
                    tmp_box = []
                    for emb in src_embedding:
                        sim = np.dot(np.asarray(embedding_list), np.asarray(emb))
                        sim = sim.reshape(-1)
                        sim = list(sim)
                        # print('###### 相似度(检索):', sim)
                        maxV = max(sim)
                        if maxV >= 0.4:
                            index = sim.index(maxV)
                            tmp_photo_path.append(imgPath)
                            tmp_box.append(box_list[index])
                            # print('图片路径:', imgPath)

                    # 将重复图片的box放在同一个list中
                    d = defaultdict(list)
                    for k, va in [(v, i) for i, v in enumerate(tmp_photo_path)]:
                        d[k].append(va)
                    for k, v in d.items():
                        face_box = []
                        for index in v:
                            face_box.append(tmp_box[index])
                        retriveResultInfo = {'photo_path': k, 'face_box': face_box}
                        self.retrived_queue.put(json.dumps(retriveResultInfo, ensure_ascii=False))
                    if len(d) > 0:
                        self.retrived_queue.put('0') # 再追加一项

            self.counter_queue.put(imgPath)



class BackedSilenceProc(Process):
    graph = None
    mtcnn_detector = None
    facenet_model = None
    margin = 32
    canvasH = 0
    canvasW = 0
    dataQueueFlag = False

    search_src_img_path = ''
    src_embedding = None

    timer = None

    def __init__(self, silence_queue, backedWorkIsOver_queue, data_queue):
        super(BackedSilenceProc, self).__init__()
        self.event = Event()
        self.event.set()  # 设置为True
        # 在添加新照片之前保存的后台静默已检索的照片
        self.last_file_list = []
        self.backedSilenceDir = ''

        self.silence_queue = silence_queue
        self.backedWorkIsOver_queue = backedWorkIsOver_queue
        self.data_queue = data_queue  #用来判断识别进程是否正在进行，如果正在进行识别，则暂停后台静默特征提取


    def pause(self):
        if self.is_alive():
            logger.info("后台静默子进程休眠")
            self.event.clear()  # 设置为False, 让进程阻塞
        else:
            logger.info("后台静默子进程结束")

    def resume(self):
        if self.is_alive():
            self.event.set()  # 设置为True, 进程唤醒
            logger.info("后台静默子进程唤醒")
        else:
            logger.info("后台静默子进程结束")

    def fun_timer(self):
        flag = False # 是否唤醒该进程的标志
        if self.silence_queue.empty() == True:
            flag = True

        if self.dataQueueFlag == True:
            if self.data_queue.empty() == True and flag== False:
                self.dataQueueFlag = False
                logger.info("后台静默子进程唤醒,继续进行特征提取")
                self.resume()
        else:
            # print('检查目标目录是否有添加新照片!')
            if self.backedSilenceDir != '':
                fileData = glob.glob(os.path.abspath(os.path.join(self.backedSilenceDir, '**', '*.*[jpg,png]')), recursive=True)
                if len(fileData) > 0:
                    des_files_list = list(set(fileData).difference(set(self.last_file_list)))
                    self.last_file_list.extend(des_files_list)
                    #print('#####  :', des_files_list)
                    if len(des_files_list) > 0:
                        for file in des_files_list:
                            self.silence_queue.put(file)
                        if flag:
                            self.resume()
            else:
                engine.dispose()
                sql_repo = RepoGeneral(make_session(engine))
                backedSilencePath_list = sql_repo.query('setting', {"setting_id": [1]}, ('photo_path'))
                if len(backedSilencePath_list) > 0:
                    logger.info('###### fun_timer backedSilencePath:', backedSilencePath_list[0]['photo_path'])
                    self.backedSilenceDir = backedSilencePath_list[0]['photo_path']


        # 每隔30s检查一次
        global timer
        timer = threading.Timer(30, self.fun_timer)
        timer.start()


    def run(self):
        # 60s后再执行，防止低配置版本的电脑内存分配不足
        lowCfgComputer = opers.get_value('lowCfgComputer')
        if lowCfgComputer == 'True':
            time.sleep(60)

        engine.dispose()
        sql_repo = RepoGeneral(make_session(engine))
        backedSilencePath_list = sql_repo.query('setting', {"setting_id": [1]}, ('photo_path',))
        if len(backedSilencePath_list) > 0 :
            logger.info('###### backedSilencePath:{}'.format(backedSilencePath_list[0]['photo_path']))
            self.backedSilenceDir = backedSilencePath_list[0]['photo_path']

        # 从数据库读取已存在的路径,赋给self.last_file_list
        photo_path_list = sql_repo.query('searchfaces', {}, ('photo_path',))
        if len(photo_path_list) > 0:
            for item in photo_path_list:
                self.last_file_list.append(item['photo_path'])

        if self.mtcnn_detector == None:
            self.mtcnn_detector = mtcnn_detector.MtcnnDetector(model_folder='model/mtcnn-model')  # 图像格式bgr
            logger.info('######:静默 mtcnn_detector')
        if self.facenet_model == None:
            gpuDevice = -1
            if gpu_state == True:
                gpuDevice = 0
            self.facenet_model = face_model.FaceModel(gpuDevice, 'model/model-r100-ii/model', 0)
            logger.info('######:静默 load model')

        timer = threading.Timer(5, self.fun_timer)
        timer.start()
        while 1:
            if self.silence_queue.empty() == True:
                logger.info('#### 后台静默:队列空,子进程暂停')
                self.pause()
            else:
                if self.data_queue.empty() != True:
                    logger.info('#### 因为识别子进程正在进行识别，后台静默子进程先暂停')
                    self.dataQueueFlag = True
                    self.pause()

            self.event.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后才立即返回

            imgPath = self.silence_queue.get()
            logger.info('后台: imgPath=%s' % imgPath)

            det = []
            lmk = []
            rectangles = []

            scale = calculate_img_scaling(imgPath, self.canvasH, self.canvasW)
            img = cv2.imdecode(np.fromfile(imgPath, dtype=np.uint8), cv2.IMREAD_COLOR)
            (h, w) = img.shape[:2]
            imgCopy = cv2.resize(img, (int(w * scale), int(h * scale)))
            test_img = cv2.cvtColor(imgCopy, cv2.COLOR_BGR2RGB)
            (h, w) = test_img.shape[:2]
            bbox, pts5 = self.mtcnn_detector.detect_face(imgCopy)
            bbox[:, 0] = np.maximum(bbox[:, 0], 0)  # x1
            bbox[:, 1] = np.maximum(bbox[:, 1], 0)  # y1
            bbox[:, 2] = np.minimum(bbox[:, 2], w)  # x2
            bbox[:, 3] = np.minimum(bbox[:, 3], h)  # y2

            for box, pt5 in zip(bbox, pts5):
                confidence = box[4]
                if confidence > 0.98:  # 0.93
                    # 将超出图像边框的检测框过滤掉
                    # if endX > w or endY > h:
                    #     print('检测框超出了图像边框的.')
                    #     continue

                    # print('MTCNN置信度:%f.' % confidence)
                    det.append(list(box[0:4].astype('int')))
                    lmk.append(np.array([pt5[0:5], pt5[5:10]]).T)

            face_nums = len(det)
            src_dir = os.path.abspath(os.path.join(imgPath, ".."))
            if face_nums > 0:
                det_arr = rank_all_faces_by_top(np.asarray(det))

                backedSearchfacesDatas = []
                backedSearchface = {}
                box_list = []
                embedding_list = []
                for j, box in enumerate(det_arr):
                    index = det.index(box.tolist())
                    (startX, startY, endX, endY) = box
                    scaled = face_align.norm_crop(test_img, lmk[index])
                    embedding = self.facenet_model.get_feature(scaled)
                    box_list.append([startX / scale, startY / scale, endX / scale, endY / scale])
                    embedding_list.append(list(embedding))

                backedSearchface['photo_path'] = imgPath
                backedSearchface['face_box'] = str(box_list)
                backedSearchface['embedding'] = str(embedding_list)
                backedSearchface['parent_path'] = src_dir
                backedSearchfacesDatas.append(backedSearchface)
                sql_repo.add('searchfaces', backedSearchfacesDatas)
                if self.silence_queue.empty() == True:
                    self.backedWorkIsOver_queue.put('True')



class Recognition(object):
    def __init__(self):
        os.makedirs('data', exist_ok=True)
        self.pending_dirs_list = []

        # self.opers = OperationJson()
        lowCfgComputer = opers.get_value('lowCfgComputer')

        # # to ake sure multiprocess running on CUDA, you have to set start method as "spawn".解決CUDA error: initialization error.
        mp.set_start_method('spawn') #设置进程启动方式,Windows平台默认使用的也是该启动方式.

        self.data_queue = Queue() # 点击“添加”按钮的时候,用来写入图片路径
        self.param_queue = Queue()
        self.from_queue = Queue()  # 在进行人脸识别的时候，判断是否通过'识别'按钮进行识别操作的
        self.verify_queue = Queue()  # 用来填充核验信息
        self.search_queue = Queue()  # 用来填充以图搜图的图片路径
        self.search_faceList_queue = Queue()  # 用来填充指定的搜索目标的序号
        self.search_filePath_queue = Queue()  # 用来填充路径
        self.silence_queue = Queue()  # 后台静默队列

        self.done_queue = Queue() # 返回识别结果信息
        self.retrived_queue = Queue()  # 返回已检索信息的队列
        self.counter_queue = Queue()  # 返回已检索图片个数的队列
        self.backedWorkIsOver_queue = Queue()  # 后台特征提取的工作是否已经完成的队列(用来存放标志位)

        self.jobs_proc = []   # 将进程对象放进list
        self.pendingTotalImgsNum = 0 #待处理的图片总数量

        # 返回UI层的识别结果信息
        self.noRecFaceImg = 0 # 没有识别出人脸的图片的总数
        self.facesNum = 0  # 总的检测到的所有人脸
        self.recognized_face_num = 0 # 已识别人脸的总数
        self.part_recognized_pic_num = 0 # 部分识别出人脸的图片的总数
        self.all_recognized_pic_num = 0  # 全部识别出人脸的图片的总数
        self.handled_pic_num = 0 # 已处理图片的总数

        # 返回UI层的检索信息
        self.retrived_pic_num = 0  # 已检索的图片数量
        self.pendingRetrieveTotalImgsNum = 0  # 待检索的图片总数量

        # 用于本次识别
        self.part_recog_img_list = []
        self.all_recog_img_list = []

        self.sql_repo = RepoGeneral(session)

        # mtcnn方法检测人脸
        self.mtcnn_detector = mtcnn_detector.MtcnnDetector(model_folder='model/mtcnn-model')  # 图像格式bgr

        # 实例化识别子进程
        logger.info('@@@@@@:lowCfgComputer=%s' % lowCfgComputer)
        if lowCfgComputer == 'True': #低配置的电脑下运行
            cpus = 1
        else:
            cpus = os.cpu_count()
            if cpus > 4:
                cpus = 4
        for i in range(cpus):
            proc = RecognizeProcess(self.done_queue, self.data_queue, self.param_queue, self.from_queue)
            proc.daemon = True
            proc.start()
            logger.info('### pid %d will start' % i)
            self.jobs_proc.append(proc)


        # 开启核验子进程
        self.verifyProc = VerifyProcess(self.verify_queue)
        self.verifyProc.daemon = True
        self.verifyProc.start()


        # 开启以图搜图子进程
        self.searchImagesProc = SearchImagesProcess(self.search_queue, self.retrived_queue, self.counter_queue, self.search_faceList_queue, self.search_filePath_queue, self.silence_queue, self.backedWorkIsOver_queue)
        self.searchImagesProc.daemon = True
        self.searchImagesProc.start()


        # 开启后台静默以图搜图子进程
        self.backedSilenceProc = BackedSilenceProc(self.silence_queue, self.backedWorkIsOver_queue, self.data_queue)
        self.backedSilenceProc.daemon = True
        self.backedSilenceProc.start()


    def initRecognitionInfo(self):
        self.noRecFaceImg = 0
        self.facesNum = 0
        self.recognized_face_num = 0
        self.part_recognized_pic_num = 0
        self.all_recognized_pic_num = 0
        self.handled_pic_num = 0
        self.all_recog_img_list.clear()
        self.part_recog_img_list.clear()


    def recognition(self, params):
        ret = 0
        self.initRecognitionInfo()
        # 再次识别前的数据处理(即预设档号的目录没有变)
        if self.pendingTotalImgsNum != 0 and self.data_queue.qsize() == 0: # 队列已被取空,说明已经识别完了,这里将未核验的图片数据再次取出进行识别
            img_path_list = []
            for dirPath in self.pending_dirs_list:
                img_path_list += self.sql_repo.query('face', {"parent_path": [dirPath], "verify_state":[0]}, ('photo_path'))

            if len(img_path_list) > 0 :
                for elem in img_path_list:
                    self.data_queue.put(elem['photo_path'])
                self.pendingTotalImgsNum = self.data_queue.qsize()
            else: # 所有图片已经核验完了
                ret = 1
                return ret
        elif self.pendingTotalImgsNum == 0 and self.data_queue.qsize() == 0: # 没有进行过‘添加’操作
            ret = 2
            return ret


        for _ in range(self.from_queue.qsize()):
            self.from_queue.get()

        for _ in range(len(self.jobs_proc)):
            self.param_queue.put(json.dumps(params, ensure_ascii=False)) # 为了让每个子进程都能得到这个param参数
            self.from_queue.put('from_recognition_func')

        for job in self.jobs_proc:
            if not self.data_queue.empty():
                job.resume()
                logger.info('### pid will resume')

        return ret


    def pauseRecognition(self):
        for job in self.jobs_proc:
            job.pause()


    def continueRecognition(self):
        for job in self.jobs_proc:
            job.resume()


    def add_folderItem(self, arch_num_info):
        ret = True
        photoDbData = []
        faceDbData = []
        self.pending_dirs_list.clear()
        # 清空队列,py3.9才有clear函数(这里是py3.6版本),故用下面的方法清空队列
        for _ in range(self.data_queue.qsize()):
            self.data_queue.get()

        logger.info('########:{}'.format(arch_num_info))

        if len(arch_num_info['children']) == 0:
            return False

        volume_dict = arch_num_info['children']
        md = hashlib.md5()
        for volume_name, volume_num in volume_dict.items():  # 取绝对路径,数据才会保持一样的形式. 例如 'D:\\深圳市社保局联谊活动\\合影\\0.jpg',否则'D:/深圳市社保局联谊活动\\合影'
            all_files = get_filePath_with_creationDate_as_dict(volume_name)
            # rank_and_rename_filePath_with_creationDate(all_files, volume_num)
            # fileData = glob.glob(os.path.abspath(os.path.join(volume_name, '*.*[jpg,png]')))
            photo_group_info = self.sql_repo.query('photo_group', {'arch_code': [volume_num]}, ('photographer', 'taken_time', 'taken_locations', 'security_classification', 'reference_code'))
            split_arch_code = volume_num.split('-')  # A1-ZP·2020-D10-0001
            for i, key in enumerate(sorted(all_files)):
                photoInfo = {}
                faceInfo = {}
                dummy, extension = os.path.splitext(all_files[key])
                parentPath = os.path.abspath(os.path.join(dummy, ".."))
                arch_code = volume_num + '-{0:0>4}'.format(i + 1)
                newPath = os.path.abspath(os.path.join(parentPath, arch_code)) + extension
                if all_files[key] != newPath :
                    if os.path.exists(newPath): # 如果文件存在,则删除后再重命名
                        os.remove(newPath)
                    os.rename(all_files[key], newPath)
                    # 修改缩略图的路径
                    old0, old1 = os.path.split(all_files[key])
                    new0, new1 = os.path.split(newPath)
                    if os.path.exists(os.path.abspath(os.path.join(new0, 'thumbs', new1))):
                        os.remove(os.path.abspath(os.path.join(new0, 'thumbs', new1)))
                    os.rename(os.path.abspath(os.path.join(old0, 'thumbs', old1)), os.path.abspath(os.path.join(new0, 'thumbs', new1)))

                file = open(newPath, "rb")
                md.update(file.read())
                md5 = md.hexdigest()
                file.close()


                query_result_list = self.sql_repo.query('photo', {"md5": [md5]}, ('arch_code', 'md5'))
                if len(query_result_list) == 1:
                    # 更新件著录信息
                    self.sql_repo.update('photo', {"md5": [md5]}, new_info={'photo_path': newPath, 'arch_code': arch_code, 'fonds_code': split_arch_code[0], 'arch_category_code': split_arch_code[1].split('·')[0],
                                                                            'year': split_arch_code[1].split('·')[1], 'group_code': volume_num, 'photographer': photo_group_info[0]['photographer'], 'taken_time': photo_group_info[0]['taken_time'],
                                                                            'taken_locations': photo_group_info[0]['taken_locations'], 'security_classification': photo_group_info[0]['security_classification'],
                                                                            'reference_code': photo_group_info[0]['reference_code']})
                    self.sql_repo.update('face', {"photo_archival_code": [query_result_list[0]['arch_code']]}, new_info={'photo_path': newPath, 'photo_archival_code': arch_code, 'parent_path': parentPath})

                else:
                    # 新增件著录信息
                    photoInfo['arch_code'] = arch_code  # 件的档号
                    photoInfo['photo_path'] = newPath
                    photoInfo['fonds_code'] = split_arch_code[0]          #全宗号
                    photoInfo['arch_category_code'] =  split_arch_code[1].split('·')[0]  #门类
                    photoInfo['year'] = split_arch_code[1].split('·')[1] #年
                    photoInfo['group_code'] = volume_num  # 组号
                    # 件号,格式 没有在更新字段中
                    photoInfo['photo_code'] = '{0:0>4}'.format(i + 1)  # 件号
                    extName = extension.split('.')[-1].upper() # 格式
                    if extName in ['JPG', 'JPEG']:
                        photoInfo['format'] = 'JPGE'
                    else:
                        photoInfo['format'] = extName
                    photoInfo['photographer'] = photo_group_info[0]['photographer'] # 拍摄者
                    photoInfo['taken_time'] = photo_group_info[0]['taken_time'] # 拍摄时间
                    photoInfo['taken_locations'] = photo_group_info[0]['taken_locations'] # 拍摄地点
                    photoInfo['security_classification'] = photo_group_info[0]['security_classification'] # 密级
                    photoInfo['reference_code'] = photo_group_info[0]['reference_code'] # 参见号
                    photoInfo['md5'] = md5
                    photoDbData.append(photoInfo)

                    # 人脸信息
                    faceInfo['photo_path'] = newPath
                    faceInfo['photo_archival_code'] = arch_code
                    faceInfo['recog_state'] = 0
                    faceInfo['verify_state'] = 0
                    faceInfo['trained_state'] = 0
                    faceInfo['parent_path'] = parentPath
                    faceDbData.append(faceInfo)
                # 图片路径写入队列
                self.data_queue.put(newPath)
            self.pending_dirs_list.append(os.path.abspath(volume_name))

        self.pendingTotalImgsNum = self.data_queue.qsize()
        if len(photoDbData) > 0:
            self.sql_repo.add('photo', photoDbData)
            self.sql_repo.add('face', faceDbData)

        return ret


    def updateRecognitionInfo(self):
        recognizedResultInfo = {}
        self.handled_pic_num += self.done_queue.qsize()  # 已处理图片的数量
        for _ in range(self.done_queue.qsize()):
            subProcRecognizedResultInfo = self.done_queue.get()
            subProcRecognizedResultInfo = eval(subProcRecognizedResultInfo)
            self.facesNum += subProcRecognizedResultInfo['face_nums'] # 总的检测到的所有人脸

            if subProcRecognizedResultInfo['face_recog_state'] == 0:  # 部分识别
                self.part_recognized_pic_num += 1 # 部分识别出人脸的图片的总数
                self.part_recog_img_list.append(subProcRecognizedResultInfo['img_path'])
            elif subProcRecognizedResultInfo['face_recog_state'] == 2:  # 没有识别出来
                self.noRecFaceImg += 1            # 没有识别出人脸的图片的总数
            else:
                self.all_recog_img_list.append(subProcRecognizedResultInfo['img_path'])

            self.recognized_face_num += subProcRecognizedResultInfo['faceRecNum']  # 已识别人脸的总数

        # 全部识别出人脸的图片的总数
        # self.all_recognized_pic_num = (self.handled_pic_num - self.part_recognized_pic_num -self.noRecFaceImg)
        self.all_recognized_pic_num = len(self.all_recog_img_list)
        # print('self.handled_pic_num:', self.handled_pic_num, 'self.part_recognized_pic_num:',
        #       self.part_recognized_pic_num, 'self.noRecFaceImg:', self.noRecFaceImg, 'self.all_recognized_pic_num:',
        #       self.all_recognized_pic_num)
        if self.facesNum > 0 :
            recRatio = round(self.recognized_face_num / self.facesNum, 3)  # 识别出的人脸/总的人脸
        else:
            recRatio = 0.0
        unprocessedImg = self.pendingTotalImgsNum - self.handled_pic_num
        recognizedResultInfo['recognition_rate'] = recRatio  # 识别率
        recognizedResultInfo['recognized_face_num'] = self.recognized_face_num  # 已识别人脸
        recognizedResultInfo['part_recognized_photo_num'] = self.part_recognized_pic_num  # 部分识别出人脸的图片的总数
        recognizedResultInfo['all_recognized_photo_num'] = self.all_recognized_pic_num  # 全部识别出人脸的图片的总数
        recognizedResultInfo['handled_photo_num'] = self.handled_pic_num  # 已处理图片
        recognizedResultInfo['unhandled_photo_num'] = unprocessedImg  # 未处理的图片

        return recognizedResultInfo


    def get_recognized_face_info(self, pic_type, dir_type):
        browse_img_list = []

        if dir_type == 1: # 代表本次识别
            if pic_type == 1: # 所有图片
                total_img_list = self.part_recog_img_list + self.all_recog_img_list
                recog_state = [0, 1]
            elif pic_type == 2: # 代表部分识别图片
                total_img_list = self.part_recog_img_list
                recog_state = [0]
            else:  # 3代表全部识别图片
                total_img_list = self.all_recog_img_list
                recog_state = [1]

            total_img_list = sorted(total_img_list)
            for img in total_img_list:
                face_dict = self.sql_repo.query('face', {"photo_path": [img], "recog_state": recog_state}, ('faces', 'verify_state'))
                photo_dict = self.sql_repo.query('photo', {"photo_path": [img]}, (
                    'photo_path', 'arch_code', 'photo_code', 'peoples', 'format', 'fonds_code',
                    'arch_category_code', 'year', 'group_code', 'photographer', 'taken_time',
                    'taken_locations', 'security_classification', 'reference_code'))
                browse_img_list.append(dict(photo_dict[0], **face_dict[0]))

        else: # 2代表所选目录的识别情况
            for dirPath in self.pending_dirs_list:
                if pic_type == 1 : # 所有图片
                    recog_state = [0, 1]
                elif pic_type == 2: # 代表部分识别图片
                    recog_state = [0]
                else:  # 3代表全部识别图片
                    recog_state = [1]

                photo_path_dict = self.sql_repo.query('face', {"parent_path": [dirPath], "recog_state": recog_state}, ('photo_path'))
                img_list = []
                for item in photo_path_dict:
                    img_list.append(item['photo_path'])
                img_list = sorted(img_list)
                for img in img_list:
                    face_dict = self.sql_repo.query('face', {"photo_path": [img], "recog_state": recog_state},
                                               ('faces', 'verify_state'))
                    photo_dict = self.sql_repo.query('photo', {"photo_path": [img]}, (
                        'photo_path', 'arch_code', 'photo_code', 'peoples', 'format', 'fonds_code',
                        'arch_category_code', 'year', 'group_code', 'photographer', 'taken_time',
                        'taken_locations', 'security_classification', 'reference_code'))
                    browse_img_list.append(dict(photo_dict[0], **face_dict[0]))

        return browse_img_list


    def checke_faces_info(self, checked_info):
        if self.verify_queue.empty() == True:
            self.verifyProc.resume()
        self.verify_queue.put(json.dumps(checked_info, ensure_ascii=False))


    def get_archival_number(self, path):
        arch_num_info = {
            "root": {},
            "children": {}
        }

        dataList = []
        if dataList:
            for ele in dataList:
                arch_num_info["root"].update({path: ele['root_volume_num']})
                arch_num_info["children"].update({ele['volume_path']: ele['volume_num']})
        else:
            arch_num_info = {}

        return  arch_num_info

    # 如果估计器是一个分类器，并且y是二进制或多类，则使用StratifiedKFold，如果是其他情况，就用KFold,
    # 即cv=StratifiedKFold(n_splits=5)其实就等价于cv=5
    def trainModel(self):
        acc = -1.0
        max_acc = 0.9
        if os.path.exists('data/data.npz'):
            data = np.load('data/data.npz', allow_pickle=True)
            faces_name, faces_embedding = data['faces_name'], data['faces_embedding']
            trainX = np.asarray(faces_embedding)
            trainy = np.asarray(faces_name)

            label_encoder = LabelEncoder()
            trainy = label_encoder.fit_transform(trainy)

            model = SVC(kernel='linear', probability=True)
            # try:
            #     model.fit(trainX, trainy)
            # except Exception as e:
            #     print(str(e))
            #     acc = -2.0 # The number of classes has to be greater than one; got 1 class
            #     return {"model_acc": acc}

            # os.makedirs('data/model/', exist_ok=True)
            # joblib.dump(model, 'data/model/custom_faceRecognize.h5')
            # shutil.copy('data/data.npz', 'data/model/last_data.npz') # 当前模型训练时, 使用的数据

            # if os.path.exists('data/last_no_train_data.npz'):
            #     os.remove('data/last_no_train_data.npz')

            # yhat_train = model.predict(trainX)
            # acc = accuracy_score(trainy, yhat_train)
            # print('Accuracy: train=%0.3f' % (acc*100))

            strKFold = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
            try:
                scores = cross_val_score(model, trainX, trainy, cv=strKFold)
            except Exception as e:
                logger.error(str(e))
                acc = -2.0  # The number of classes has to be greater than one; got 1 class
                return {"model_acc": acc}

            acc_mean = scores.mean()
            logger.info('cross_val_score scores:{}'.format(scores))
            logger.info('CV mean accuracy: train=%0.3f' % (acc_mean * 100))
            if acc_mean > max_acc:
                try:
                    model.fit(trainX, trainy)
                except Exception as e:
                    logger.error(str(e))
                    acc = -2.0 # The number of classes has to be greater than one; got 1 class
                    return {"model_acc": acc}

                os.makedirs('data/model/', exist_ok=True)
                joblib.dump(model, 'data/model/custom_faceRecognize.h5')
                shutil.copy('data/data.npz', 'data/model/last_data.npz')  # 当前模型训练时, 使用的数据

                yhat_train = model.predict(trainX)
                acc = accuracy_score(trainy, yhat_train)
                logger.info('Accuracy: train=%0.3f' % (acc*100))
            else:
                acc = -2.0
        else:
            logger.info('The path(data/data.npz) is not find!')

        return {"model_acc": acc}


    def get_untrained_pic_num(self):
        length = 0

        # faces_name = []
        # faces_embedding = []

        # embeddings_dict = self.sql_repo.query('face', {"verify_state": [1], 'trained_state': [0]}, ('faces', 'embeddings'))
        # for ele_dict in embeddings_dict:
        #     faces = eval(ele_dict['faces'])
        #     embeddings = eval(ele_dict['embeddings'])
        #     for face in faces:
        #         id = face['id']
        #         name = face['name']
        #         embedding = np.asarray(eval(embeddings[id][str(id)]))
        #         faces_embedding.append(embedding)
        #         faces_name.append(name)

        # if len(embeddings_dict) != 0:
        #     self.sql_repo.update('face', {"verify_state": [1], 'trained_state': [0]}, new_info={'trained_state': 1})
        # if len(faces_name) != 0 :
        #     saveData('data/data.npz', faces_name, faces_embedding)

        if os.path.exists('data/model/last_data.npz'):
            last_data = np.load('data/model/last_data.npz', allow_pickle=True)
            len_last_data = len(last_data['faces_name'])

            data = np.load('data/data.npz', allow_pickle=True)
            len_data = len(data['faces_name'])

            length = len_data - len_last_data
        else:
            if os.path.exists('data/data.npz'):
                data = np.load('data/data.npz', allow_pickle=True)
                length = len(data['faces_name'])

        return length


    def start_retrieve(self, file_path, dir_path, face_list):
        ret = 0

        self.retrived_pic_num = 0
        self.pendingRetrieveTotalImgsNum = 0

        engine.dispose()
        sql_repo = RepoGeneral(make_session(engine))
        backedSilencePath_list = sql_repo.query('setting', {"setting_id": [1]}, ('photo_path',))
        # parent_path_list = sql_repo.query('searchfaces', {"parent_path": [os.path.abspath(dir_path)]}, ('parent_path'))

        # 判断该dir_path路径是否有照片
        img_list = glob.glob(os.path.abspath(os.path.join(dir_path, '**', '*.*[jpg,png]')), recursive=True)
        pic_num = len(img_list)
        # if backedSilencePath_list[0]['photo_path'] == dir_path:
        #     if pic_num == 0 and len(parent_path_list) == 0: # 目录里面没有图片，并且数据库里面也没有数据
        #         ret = -1
        #         return ret
        # else:
        #     if pic_num == 0:
        #         ret = -1
        #         return ret
        if pic_num == 0:
            ret = -1
            return ret

        # 队列不为空, 表示后台正在进行以图搜图任务的特征提取
        if backedSilencePath_list[0]['photo_path'] == dir_path:
            if self.silence_queue.empty() != True: # 正在提取特征
                # 清空该队列，以便放置新的后台特征提取完成的标志位
                for _ in range(self.backedWorkIsOver_queue.qsize()):
                    self.backedWorkIsOver_queue.get()
            else:
                parent_path_list = sql_repo.query('searchfaces', {"parent_path": [os.path.abspath(dir_path)]}, ('parent_path'))
                if len(parent_path_list) == 0: # 后台定时任务即将提取特征(目前数据库还没有该路径下的数据)
                    ret = -2
                    return ret
                # else:
                #     self.search_filePath_queue.put('False_0')
        # else:
        #     self.search_filePath_queue.put('NoCare_0')

        self.search_filePath_queue.put(dir_path)
        self.search_filePath_queue.put(backedSilencePath_list[0]['photo_path'])

        logger.info('########: 开始进行人脸检索.')

        if self.search_queue.empty() == True:
            # 不管数据库没有该路径，都把待检索的人物的路径第一个放入队列
            self.search_queue.put(os.path.abspath(file_path))
            self.pendingRetrieveTotalImgsNum += 1

            for imgPath in img_list:
                self.search_queue.put(imgPath)

            self.search_faceList_queue.put(json.dumps(face_list, ensure_ascii=False))

            self.pendingRetrieveTotalImgsNum += len(img_list)
            # 唤醒子进程
            self.searchImagesProc.resume()
        return ret


    def get_retrieve_result(self, file_path, dir_path) -> list:

        retrive_results_photo_path = []
        retrive_results_face_box = []
        backedRestExtractPicCount = []

        num = self.retrived_queue.qsize()
        for i in range(num):
            retriveResultInfo = self.retrived_queue.get()
            retriveResultInfo = eval(retriveResultInfo)

            if i != (num - 1):
                retrive_results_photo_path.append(retriveResultInfo['photo_path'])
                retrive_results_face_box.append( retriveResultInfo['face_box'])
            else:
                backedRestExtractPicCount.append(retriveResultInfo)

        # print('########  retrive_results_photo_path: ',retrive_results_photo_path)
        # print('########  retrive_results_face_box: ', retrive_results_face_box)
        # print('########  backedRestExtractPicCount: ', backedRestExtractPicCount)
        return retrive_results_photo_path, retrive_results_face_box, backedRestExtractPicCount


    def get_retrieve_info(self) -> dict:
        retrivedResultInfo = {}
        self.retrived_pic_num += self.counter_queue.qsize()  # 已检索过的图片数量
        for _ in range(self.counter_queue.qsize()):
            _ = self.counter_queue.get()

        retrivedResultInfo['total_to_retrieve_photo_num'] = self.pendingRetrieveTotalImgsNum
        retrivedResultInfo['retrieved_photo_num'] = self.retrived_pic_num
        # print('retrieved_num:{}, total_num:{}'.format(self.retrived_pic_num, self.pendingRetrieveTotalImgsNum))

        return retrivedResultInfo

    def get_faces_coordinates(self, imgPath) -> list:
        det = []
        faces = []
        canvasW = 2000
        canvasH = 2000

        if imgPath == '':
            return faces

        scale = calculate_img_scaling(imgPath, canvasH, canvasW)
        img = cv2.imdecode(np.fromfile(imgPath, dtype=np.uint8), cv2.IMREAD_COLOR)
        (h, w) = img.shape[:2]
        test_img = cv2.resize(img, (int(w * scale), int(h * scale)))
        (h, w) = test_img.shape[:2]
        bbox, pts5 = self.mtcnn_detector.detect_face(test_img)
        bbox[:, 0] = np.maximum(bbox[:, 0], 0)  # x1
        bbox[:, 1] = np.maximum(bbox[:, 1], 0)  # y1
        bbox[:, 2] = np.minimum(bbox[:, 2], w)  # x2
        bbox[:, 3] = np.minimum(bbox[:, 3], h)  # y2

        for box in bbox:
            confidence = box[4]
            if confidence > 0.98:  # 0.93
                # 将超出图像边框的检测框过滤掉
                # if endX > w or endY > h:
                #     print('检测框超出了图像边框的.')
                #     continue

                # print('MTCNN置信度:%f.' % confidence)
                det.append(list(box[0:4].astype('int')))

        face_nums = len(det)
        if face_nums > 0:
            det_arr = rank_all_faces_by_top(np.asarray(det))
            for j, box in enumerate(det_arr):
                (startX, startY, endX, endY) = box
                faces.append({
                    'id': j,
                    'box': [startX / scale, startY / scale, endX / scale, endY / scale]
                })

        # print('#####:', faces)
        return faces














