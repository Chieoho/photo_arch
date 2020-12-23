# -*- coding: utf-8 -*-
"""
@file: business_recognition.py
@desc:
@author: Jaden Wu
@time: 2020/9/3 10:15
"""
import hashlib
import json
import os
import shutil

import cv2
import glob
import time
import threading
import numpy as np
import tensorflow as tf
from keras.models import load_model
from mtcnn import MTCNN
from sklearn.metrics import accuracy_score
from sklearn.svm import SVC
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.model_selection import cross_val_score
from multiprocessing import Process, Event, Queue, Manager

from recognition.utils import *

from photo_arch.adapters.sql.repo import RepoGeneral
from photo_arch.infrastructures.databases.db_setting import engine, make_session



class RecognizeProcess(Process):
    graph = None
    mtcnn_detector = None
    facenet_model = None
    margin = 32

    faceProp = 0.9
    euclideanDist = 0.79
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
            print("识别子进程休眠")
            self.event.clear()  # 设置为False, 让进程阻塞
        else:
            print("识别子进程结束")

    def resume(self):
        if self.is_alive():
            self.event.set()  # 设置为True, 进程唤醒
            print("识别子进程唤醒")
        else:
            print("识别子进程结束")


    def run(self):
        if self.graph == None:
            self.graph = tf.get_default_graph()
            print('######:识别 graph')
        with self.graph.as_default():
            if self.mtcnn_detector == None:
                self.mtcnn_detector = MTCNN()
                print('######:识别 mtcnn_detector')
            if self.facenet_model == None:
                self.facenet_model = load_model('model/facenet_keras.h5')
                print('######:识别 load model')


        engine.dispose()
        sql_repo = RepoGeneral(make_session(engine))

        while 1:
            if self.data_queue.empty() == True:
                print('#### 识别:队列空,子进程暂停')
                self.pause()
            else:
                if self.from_queue.empty(): # 如果为空，说明不是通过‘识别’按钮进来的
                    self.pause()
                    print('#### 识别:等待点击识别按钮')
            self.event.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后才立即返回

            imgPath = self.data_queue.get()
            # print('#####:pid=%d, imgPath=%s' %(os.getpid(), imgPath))
            det = []
            rectangles = []
            # cf = []
            tupFData = []

            if not self.param_queue.empty():
                try:
                    params = self.param_queue.get_nowait()
                    params = eval(params)
                    self.faceProp = params['threshold']
                except Exception as e:
                    print(repr(e))
                    self.faceProp = 0.9

            scale = calculate_img_scaling(imgPath, self.canvasH, self.canvasW)
            img = cv2.cvtColor(cv2.imdecode(np.fromfile(imgPath, dtype=np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            (h, w) = img.shape[:2]
            test_img = cv2.resize(img, (int(w*scale), int(h*scale)))
            (h, w) = test_img.shape[:2]
            with self.graph.as_default():
                detect_faces = self.mtcnn_detector.detect_faces(test_img)

            for face in detect_faces:
                confidence = face['confidence']
                if confidence > 0.9:
                    box = face['box']
                    (startX, startY, endX, endY) = box[0] , box[1], box[0] + box[2], box[1] + box[3]
                    tmp_box = [startX, startY, endX, endY]

                    # 将超出图像边框的检测框过滤掉
                    if endX > w or endY > h:
                        print('检测框超出了图像边框的.')
                        continue

                    # print('MTCNN置信度:%f.' % confidence)
                    det.append(tmp_box)
                    # cf.append(confidence)
                    rectangle = tmp_box + [face['confidence']] + list(face['keypoints']['left_eye']) + list(face['keypoints']['right_eye']) + list(face['keypoints']['nose']) + list(face['keypoints']['mouth_left']) + list(face['keypoints']['mouth_right'])
                    crop_img = test_img[int(rectangle[1]):int(rectangle[3]), int(rectangle[0]):int(rectangle[2])]
                    rectangles.append(rectangle)

            rectangles_array = np.array(rectangles)
            rectangles_array[:, 0] = np.maximum(rectangles_array[:, 0] - self.margin / 2, 0)  # x1
            rectangles_array[:, 1] = np.maximum(rectangles_array[:, 1] - self.margin / 2, 0)  # y1
            rectangles_array[:, 2] = np.minimum(rectangles_array[:, 2] + self.margin / 2, w)  # x2
            rectangles_array[:, 3] = np.minimum(rectangles_array[:, 3] + self.margin / 2, h)  # y2
            rectanglesExd = rectangles_array.tolist()
            squareRect = rect2square(np.array(rectanglesExd)) # 将长方形调整为正方形
            face_nums = len(det)
            src_dir = os.path.abspath(os.path.join(imgPath, ".."))
            if face_nums > 0:
                # src_det_x1 = np.asarray(det)[:, 0].tolist()
                if self.face_rank_rule_by_top:
                    det_arr = rank_all_faces_by_top(np.asarray(det))
                else:
                    det_arr = rank_all_faces_by_bottom(np.asarray(det))
                # cf_arr = rank_confidence(src_det_x1, det_arr, cf)

                faces = []
                embeddings = []
                peoples = ''
                curFaceRecNum = 0  # 当前图片里面的人脸数
                faceRecNum = 0
                for j, box in enumerate(det_arr):
                    (startX, startY, endX, endY) = box.astype("int")
                    bb = np.zeros(4, dtype=np.int32)
                    bb[0] = np.maximum(startX - self.margin / 2, 0)  # x1
                    bb[1] = np.maximum(startY - self.margin / 2, 0)  # y1
                    bb[2] = np.minimum(endX + self.margin / 2, w)  # x2
                    bb[3] = np.minimum(endY + self.margin / 2, h)  # y2
                    # cropped = test_img[bb[1]:bb[3], bb[0]:bb[2], :]
                    # scaled = np.array(Image.fromarray(cropped).resize((160, 160)))
                    # scaled = alignFace(test_img, rectangles, squareRect, box)
                    scaled, face_landmarks = alignFace2(test_img, rectangles, rectanglesExd, squareRect, box)
                    # cv2.imwrite("reco_align_{}.jpg".format(time.time()), cv2.cvtColor(scaled, cv2.COLOR_RGB2BGR))
                    # cv2.rectangle(test_img, (startX, startY), (endX, endY), (0,255,0), 2)
                    with self.graph.as_default():
                        unknown_embedding = get_embedding(self.facenet_model, scaled)
                    who_name = get_name_by_embedding(imgPath, unknown_embedding, self.faceProp, self.euclideanDist)
                    if who_name != '':
                        faceRecNum += 1
                        curFaceRecNum += 1
                    faces.append({
                        'id': j,
                        'box': str([startX / scale, startY / scale, endX / scale, endY / scale]),
                        'name': who_name,
                        'landmark': str((np.asarray(face_landmarks)/scale).tolist())
                        # 'embedding':str(list(unknown_embedding))
                    })  # box和embedding如果不转换成str,json.dumps就会报错(目前没有找到解决方法)

                    embeddings.append({
                        str(j): str(list(unknown_embedding))
                    })

                    if j < len(det_arr)-1 :
                        if who_name != '':
                            peoples += '{},'.format(who_name)
                    else:
                        peoples += '{}'.format(who_name)


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

            # cv2.imwrite("img_{}.jpg".format(time.time()), cv2.cvtColor(test_img, cv2.COLOR_RGB2BGR))
            recognizedResultInfo = {'face_nums': face_nums, 'face_recog_state': face_recog_state, 'faceRecNum': faceRecNum, 'img_path': imgPath}
            self.done_queue.put(json.dumps(recognizedResultInfo, ensure_ascii=False))

            # 更新数据库photo_path为imgPath的记录
            sql_repo.update('face', {"photo_path": [imgPath]},
                            new_info={'faces': jsonFaces, 'recog_state': face_recog_state, 'parent_path': os.path.abspath(imgPath + os.path.sep + ".."),
                                      'embeddings': jsonEmbeddings })
            sql_repo.update('photo', {"photo_path": [imgPath]}, new_info={'peoples': peoples})


class VerifyProcess(Process):
    # graph = None
    # mtcnn_detector = None
    # facenet_model = None
    # margin = 32
    img_path = ''
    faces_list = []
    table_widget = []
    # canvasW = 0
    # canvasH = 0


    def __init__(self, verify_queue):
        super(VerifyProcess, self).__init__()
        self.event = Event()
        self.event.set()  # 设置为True
        self.verify_queue = verify_queue


    def pause(self):
        if self.is_alive():
            print("核验子进程休眠")
            self.event.clear()  # 设置为False, 让进程阻塞
        else:
            print("核验子进程结束")

    def resume(self):
        if self.is_alive():
            self.event.set()  # 设置为True, 进程唤醒
            print("核验子进程唤醒")
        else:
            print("核验子进程结束")


    def run(self):
        # if self.graph == None:
        #     self.graph = tf.get_default_graph()
        #     print('###### VerifyProcess:graph')
        # with self.graph.as_default():
        #     if self.facenet_model == None:
        #         self.facenet_model = load_model('model/facenet_keras.h5')
        #         print('###### VerifyProcess:load model')

        engine.dispose()
        sql_repo = RepoGeneral(make_session(engine))

        while 1:
            if self.verify_queue.empty() == True:
                print('#### VerifyProcess :队列空,子进程暂停')
                self.pause()
            self.event.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后才立即返回

            checkedInfoDict = self.verify_queue.get()
            checkedInfoDict = eval(checkedInfoDict)

            self.img_path = checkedInfoDict['path']
            self.faces_list = eval(checkedInfoDict['faces'])
            # self.archivalNum = checkedInfoDict['arch_num']
            # self.subject = checkedInfoDict['theme']
            self.table_widget = checkedInfoDict['table_widget']
            # self.canvasW = checkedInfoDict['label_size'][0]
            # self.canvasH = checkedInfoDict['label_size'][1]


            # faces_name = []
            # faces_embedding = []

            new_faces = []
            peoples = ''
            new_faces_name = []
            new_faces_id = []

            orig_faces_id = list(range(len(self.faces_list)))

            # scale = calculate_img_scaling(self.img_path, self.canvasH, self.canvasW)
            # img = cv2.cvtColor(cv2.imdecode(np.fromfile(self.img_path, dtype=np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            # (h, w) = img.shape[:2]
            # test_img = cv2.resize(img, (int(w*scale), int(h*scale)))
            # (h, w) = test_img.shape[:2]

            for item in self.table_widget:
                if item['id'] == '':
                    continue
                new_faces_id.append(int(item['id']))
                new_faces_name.append(item['name'])

            # embeddings_dict = sql_repo.query('face', {"photo_path": [self.img_path]}, ('embeddings'))

            for id in orig_faces_id:
                if id in new_faces_id: # 没有删除
                    index = new_faces_id.index(id)
                    name = new_faces_name[index]
                else:
                    name = '已删除'

                new_faces.append({
                    'id':id,
                    'box':self.faces_list[id]['box'],
                    'name': name,
                    'landmark': self.faces_list[id]['landmark']
                })

                if id < len(orig_faces_id) - 1:
                    if name != '' and name != '已删除':
                        peoples += '{},'.format(name)
                else:
                    peoples += '{}'.format(name)

                # if name != '':
                    # (startX, startY, endX, endY) = eval(self.faces_list[id]['box'])
                    # (startX, startY, endX, endY) = startX*scale, startY*scale, endX*scale, endY*scale
                    # bb = np.zeros(4, dtype=np.int32)
                    # bb[0] = np.maximum(startX - self.margin / 2, 0)  # x1
                    # bb[1] = np.maximum(startY - self.margin / 2, 0)  # y1
                    # bb[2] = np.minimum(endX + self.margin / 2, w)  # x2
                    # bb[3] = np.minimum(endY + self.margin / 2, h)  # y2

                    # squareRect = rect2square(np.array([[bb[0], bb[1], bb[2], bb[3]]]))
                    # marginValue = int((bb[0] - squareRect[0][0])/2)
                    # print('#### verify_margin:', marginValue)
                    # face_landmark = (np.asarray(eval(self.faces_list[id]['landmark']))*scale).tolist()
                    # scaled = alignFace2WithVerify(test_img, marginValue, face_landmark)
                    # cv2.imwrite("verify_align_{}.jpg".format(time.time()), cv2.cvtColor(scaled, cv2.COLOR_RGB2BGR))

                    # cropped = test_img[bb[1]:bb[3], bb[0]:bb[2], :]
                    # scaled = np.array(Image.fromarray(cropped).resize((160, 160)))
                    # with self.graph.as_default():
                    #     embedding = get_embedding(self.facenet_model, scaled)

                    # embedding = embeddings_dict[0][id]

                    # faces_embedding.append(embedding)
                    # faces_name.append(name)
                # else:
                #     print('核验---id:{},name:{}'.format(id, name))

            # saveData('data/data.npz', faces_name, faces_embedding)
            jsonFaces = json.dumps(new_faces, ensure_ascii=False)
            verifyState = 1
            sql_repo.update('face', {"photo_path": [self.img_path]}, new_info={'faces': jsonFaces, 'verify_state': verifyState})
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


    def __init__(self, search_queue, retrived_queue):
        super(SearchImagesProcess, self).__init__()
        self.event = Event()
        self.event.set()  # 设置为True
        self.search_queue = search_queue
        self.retrived_queue = retrived_queue


    def pause(self):
        if self.is_alive():
            print("检索子进程休眠")
            self.event.clear()  # 设置为False, 让进程阻塞
        else:
            print("检索子进程结束")

    def resume(self):
        if self.is_alive():
            self.event.set()  # 设置为True, 进程唤醒
            print("检索子进程唤醒")
        else:
            print("检索子进程结束")

    def run(self):
        if self.graph == None:
            self.graph = tf.get_default_graph()
            print('######:检索 graph')

        with self.graph.as_default():
            if self.mtcnn_detector == None:
                self.mtcnn_detector = MTCNN()
                print('######:检索 mtcnn_detector')
            if self.facenet_model == None:
                self.facenet_model = load_model('model/facenet_keras.h5')
                print('######:检索 load model')

        engine.dispose()
        sql_repo = RepoGeneral(make_session(engine))

        while 1:
            if self.search_queue.empty() == True:
                print('#### 检索:队列空,子进程暂停')
                self.pause()
            self.event.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后才立即返回

            imgPath = self.search_queue.get()
            print('#####: imgPath=%s' % imgPath)

            det = []
            rectangles = []

            scale = calculate_img_scaling(imgPath, self.canvasH, self.canvasW)
            img = cv2.cvtColor(cv2.imdecode(np.fromfile(imgPath, dtype=np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            (h, w) = img.shape[:2]
            test_img = cv2.resize(img, (int(w * scale), int(h * scale)))
            (h, w) = test_img.shape[:2]
            with self.graph.as_default():
                detect_faces = self.mtcnn_detector.detect_faces(test_img)

            for face in detect_faces:
                confidence = face['confidence']
                if confidence > 0.9:
                    box = face['box']
                    (startX, startY, endX, endY) = box[0], box[1], box[0] + box[2], box[1] + box[3]
                    tmp_box = [startX, startY, endX, endY]

                    # 将超出图像边框的检测框过滤掉
                    if endX > w or endY > h:
                        print('检测框超出了图像边框的.')
                        continue

                    # print('MTCNN置信度:%f.' % confidence)
                    det.append(tmp_box)
                    # cf.append(confidence)
                    rectangle = tmp_box + [face['confidence']] + list(face['keypoints']['left_eye']) + list(
                        face['keypoints']['right_eye']) + list(face['keypoints']['nose']) + list(
                        face['keypoints']['mouth_left']) + list(face['keypoints']['mouth_right'])
                    # crop_img = test_img[int(rectangle[1]):int(rectangle[3]), int(rectangle[0]):int(rectangle[2])]
                    rectangles.append(rectangle)

            rectangles_array = np.array(rectangles)
            rectangles_array[:, 0] = np.maximum(rectangles_array[:, 0] - self.margin / 2, 0)  # x1
            rectangles_array[:, 1] = np.maximum(rectangles_array[:, 1] - self.margin / 2, 0)  # y1
            rectangles_array[:, 2] = np.minimum(rectangles_array[:, 2] + self.margin / 2, w)  # x2
            rectangles_array[:, 3] = np.minimum(rectangles_array[:, 3] + self.margin / 2, h)  # y2
            rectanglesExd = rectangles_array.tolist()
            squareRect = rect2square(np.array(rectanglesExd))  # 将长方形调整为正方形
            face_nums = len(det)
            src_dir = os.path.abspath(os.path.join(imgPath, ".."))
            if face_nums > 0:
                searchfacesDatas = []
                searchface = {}
                box_list = []
                embedding_list = []
                for j, box in enumerate(np.asarray(det)):

                    (startX, startY, endX, endY) = box.astype("int")
                    bb = np.zeros(4, dtype=np.int32)
                    bb[0] = np.maximum(startX - self.margin / 2, 0)  # x1
                    bb[1] = np.maximum(startY - self.margin / 2, 0)  # y1
                    bb[2] = np.minimum(endX + self.margin / 2, w)  # x2
                    bb[3] = np.minimum(endY + self.margin / 2, h)  # y2
                    # cropped = test_img[bb[1]:bb[3], bb[0]:bb[2], :]
                    # scaled = np.array(Image.fromarray(cropped).resize((160, 160)))
                    # scaled = alignFace(test_img, rectangles, squareRect, box)
                    scaled, face_landmarks = alignFace2(test_img, rectangles, rectanglesExd, squareRect, box)
                    # cv2.imwrite("reco_align_{}.jpg".format(time.time()), cv2.cvtColor(scaled, cv2.COLOR_RGB2BGR))
                    # cv2.rectangle(test_img, (startX, startY), (endX, endY), (0,255,0), 2)
                    with self.graph.as_default():
                        embedding = get_embedding(self.facenet_model, scaled)

                    box_list.append([startX / scale, startY / scale, endX / scale, endY / scale])
                    embedding_list.append(list(embedding))

                searchface['photo_path'] = imgPath
                searchface['face_box'] = str(box_list)
                searchface['embedding'] = str(embedding_list)
                searchface['parent_path'] = src_dir
                searchfacesDatas.append(searchface)

                sql_repo.add('searchfaces', searchfacesDatas)

            self.retrived_queue.put(imgPath)




class Recognition(object):
    def __init__(self):
        os.makedirs('data', exist_ok=True)
        self.pending_dirs_list = []

        self.data_queue = Queue() # 点击“添加”按钮的时候,用来写入图片路径
        self.param_queue = Queue()
        self.from_queue = Queue()  # 在进行人脸识别的时候，判断是否通过'识别'按钮进行识别操作的
        self.verify_queue = Queue()  # 用来填充核验信息
        self.search_queue = Queue()  # 用来填充以图搜图的图片路径
        self.done_queue = Manager().Queue() # 返回识别结果信息
        self.retrived_queue = Manager().Queue()  # 返回已检索信息的队列
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

        self.sql_repo = RepoGeneral(make_session(engine))

        # 实例化识别子进程
        for i in range(os.cpu_count()):
            proc = RecognizeProcess(self.done_queue, self.data_queue, self.param_queue, self.from_queue)
            proc.daemon = True
            proc.start()
            print('### pid %d will start' % i)
            self.jobs_proc.append(proc)


        # 开启核验子进程
        self.verifyProc = VerifyProcess(self.verify_queue)
        self.verifyProc.daemon = True
        self.verifyProc.start()


        # 开启以图搜图子进程
        self.searchImagesProc = SearchImagesProcess(self.search_queue, self.retrived_queue)
        self.searchImagesProc.daemon = True
        self.searchImagesProc.start()


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
                print('### pid will resume')

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

        print('########:', arch_num_info)

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
                    os.rename(all_files[key], newPath)
                    # 修改缩略图的路径
                    old0, old1 = os.path.split(all_files[key])
                    new0, new1 = os.path.split(newPath)
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
                for img in photo_path_dict:
                    face_dict = self.sql_repo.query('face', {"photo_path": [img['photo_path']], "recog_state": recog_state},
                                               ('faces', 'verify_state'))
                    photo_dict = self.sql_repo.query('photo', {"photo_path": [img['photo_path']]}, (
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
            scores = cross_val_score(model, trainX, trainy, cv=strKFold)
            acc_mean = scores.mean()
            print('cross_val_score scores:', scores)
            print('CV mean accuracy: train=%0.3f' % (acc_mean * 100))
            if acc_mean > max_acc:
                try:
                    model.fit(trainX, trainy)
                except Exception as e:
                    print(str(e))
                    acc = -2.0 # The number of classes has to be greater than one; got 1 class
                    return {"model_acc": acc}

                os.makedirs('data/model/', exist_ok=True)
                joblib.dump(model, 'data/model/custom_faceRecognize.h5')
                shutil.copy('data/data.npz', 'data/model/last_data.npz')  # 当前模型训练时, 使用的数据

                yhat_train = model.predict(trainX)
                acc = accuracy_score(trainy, yhat_train)
                print('Accuracy: train=%0.3f' % (acc*100))

        return {"model_acc": acc}


    def get_untrained_pic_num(self):
        length = 0

        faces_name = []
        faces_embedding = []

        embeddings_dict = self.sql_repo.query('face', {"verify_state": [1], 'trained_state': [0]}, ('faces', 'embeddings'))
        for ele_dict in embeddings_dict:
            faces = eval(ele_dict['faces'])
            embeddings = eval(ele_dict['embeddings'])
            for face in faces:
                id = face['id']
                name = face['name']
                embedding = np.asarray(eval(embeddings[id][str(id)]))
                faces_embedding.append(embedding)
                faces_name.append(name)

        if len(embeddings_dict) != 0:
            self.sql_repo.update('face', {"verify_state": [1], 'trained_state': [0]}, new_info={'trained_state': 1})
        if len(faces_name) != 0 :
            saveData('data/data.npz', faces_name, faces_embedding)

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


    def start_retrieve(self, file_path, dir_path):
        ret = 0

        self.retrived_pic_num = 0
        self.pendingRetrieveTotalImgsNum = 0

        print('########: 开始进行人脸检索.')

        # 判断该dir_path路径是否已经检索过了
        parent_path_list = self.sql_repo.query('searchfaces', {"parent_path": [os.path.abspath(dir_path)]}, ('parent_path'))
        if len(parent_path_list) > 0:
            ret = -2
            return ret

        # 判断该dir_path路径是否有照片
        img_list = glob.glob(os.path.abspath(os.path.join(dir_path, '*.*[jpg,png]')))
        pic_num = len(img_list)
        if pic_num == 0:
            ret = -1
            return ret
        else:
            self.pendingRetrieveTotalImgsNum = pic_num

        if self.search_queue.empty() == True:
            self.searchImagesProc.resume()

            self.search_queue.put(os.path.abspath(file_path))
            for imgPath in img_list:
                self.search_queue.put(imgPath)

        return ret


    def get_retrieve_result(self, file_path, dir_path) -> list:

        photo_path = []
        retrive_des_box = []
        retrive_des_embedding = []

        retrive_results_photo_path = []
        retrive_results_face_box = []

        src_embedding_list = self.sql_repo.query('searchfaces', {"photo_path": [os.path.abspath(file_path)]}, ('embedding'))
        retrive_src_embedding = eval(src_embedding_list[0]['embedding'])

        des_embedding_list = self.sql_repo.query('searchfaces', {"parent_path": [os.path.abspath(dir_path)]}, ('photo_path', 'face_box', 'embedding'))
        for ele_dict in des_embedding_list:
            for box in eval(ele_dict['face_box']):
                retrive_des_box.append(box)
                photo_path.append(ele_dict['photo_path'])
            for emd in eval(ele_dict['embedding']):
                retrive_des_embedding.append(emd)

        dist = np.linalg.norm(np.asarray(retrive_des_embedding) - np.asarray(retrive_src_embedding), axis=1)
        dist = list(dist)
        sortDist = sorted(dist)
        des_dist = [x for x in sortDist if x <= 0.8]
        for x in des_dist:
            index = dist.index(x)
            retrive_results_photo_path.append(photo_path[index])
            retrive_results_face_box.append(retrive_des_box[index])

        return retrive_results_photo_path, retrive_results_face_box


    def get_retrieve_info(self) -> dict:
        retrivedResultInfo = {}
        self.retrived_pic_num += self.retrived_queue.qsize()  # 已检索过的图片数量
        for _ in range(self.retrived_queue.qsize()):
            _ = self.retrived_queue.get()

        retrivedResultInfo['total_to_retrieve_photo_num'] = self.pendingRetrieveTotalImgsNum
        retrivedResultInfo['retrieved_photo_num'] = self.retrived_pic_num

        return retrivedResultInfo
















