# -*- coding: utf-8 -*-
"""
@file: business_recognition.py
@desc:
@author: Jaden Wu
@time: 2020/9/3 10:15
"""
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
from multiprocessing import Process, Event, Queue, Manager

from recognition.utils import *

from photo_arch.adapters.sql.repo import RepoGeneral
from photo_arch.infrastructures.databases.db_setting import engine, make_session



class RecognizeProcess(Process):
    graph = None
    mtcnn_detector = None
    facenet_model = None
    margin = 32

    faceProp = 0.0
    euclideanDist = 0.79
    canvasW = 0
    canvasH = 0

    def __init__(self, done_queue):
        super(RecognizeProcess, self).__init__()
        self.event = Event()
        self.event.set() # 设置为True
        self.done_queue = done_queue # 写入返回数据

    def updataData(self, data_queue):
        self.data_queue =data_queue

    def pause(self):
        if self.is_alive():
            print("子进程休眠")
            self.event.clear()  # 设置为False, 让进程阻塞
        else:
            print("子进程结束")

    def resume(self):
        if self.is_alive():
            self.event.set()  # 设置为True, 进程唤醒
            print("子进程唤醒")
        else:
            print("子进程结束")


    def run(self):
        if self.graph == None:
            self.graph = tf.get_default_graph()
            print('######:graph')
        with self.graph.as_default():
            if self.mtcnn_detector == None:
                self.mtcnn_detector = MTCNN()
                print('######:mtcnn_detector')
            if self.facenet_model == None:
                self.facenet_model = load_model('model/facenet_keras.h5')
                print('######:load model')

        engine.dispose()
        sql_repo = RepoGeneral(make_session(engine))

        while 1:
            if self.data_queue.empty() == True:
                print('####:队列空,子进程暂停')
                self.pause()
            self.event.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后才立即返回

            imgPath = self.data_queue.get()
            print('#####:pid=%d, imgPath=%s' %(os.getpid(), imgPath))
            det = []
            rectangles = []
            # cf = []
            tupFData = []

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
                det_arr = rank_all_faces(np.asarray(det))
                # cf_arr = rank_confidence(src_det_x1, det_arr, cf)

                faces = []
                peoples = []
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
                    scaled = alignFace2(test_img, rectangles, rectanglesExd, squareRect, box)
                    # cv2.imwrite("./align/align_{}.jpg".format(time.time()), cv2.cvtColor(scaled, cv2.COLOR_RGB2BGR))
                    # cv2.rectangle(test_img, (startX, startY), (endX, endY), (0,255,0), 2)
                    with self.graph.as_default():
                        unknown_embedding = get_embedding(self.facenet_model, scaled)
                    who_name = get_name_by_embedding(unknown_embedding, self.faceProp, self.euclideanDist)
                    if who_name != '':
                        faceRecNum += 1
                        curFaceRecNum += 1
                    faces.append({
                        'id': j,
                        'box': str([startX / scale, startY / scale, endX / scale, endY / scale]),
                        'name': who_name
                        # 'embedding':str(list(unknown_embedding))
                    })  # box和embedding如果不转换成str,json.dumps就会报错(目前没有找到解决方法)

                    peoples.append({
                        'id': j,
                        'name': who_name
                    })


                if curFaceRecNum == face_nums:
                    face_recog_state = 1  # 全部识别
                else:
                    face_recog_state = 0  # 部分识别

                jsonFaces = json.dumps(faces, ensure_ascii=False)
                jsonPeoples = json.dumps(peoples, ensure_ascii=False)
            else:
                face_recog_state = 2  # 没有检测出脸
                jsonFaces = ''
                jsonPeoples = ''

            # cv2.imwrite("img_{}.jpg".format(time.time()), cv2.cvtColor(test_img, cv2.COLOR_RGB2BGR))
            recognizedResultInfo = {'face_nums': face_nums, 'face_recog_state': face_recog_state, 'faceRecNum': faceRecNum, 'img_path': imgPath}
            self.done_queue.put(json.dumps(recognizedResultInfo, ensure_ascii=False))

            # 更新数据库photo_path为imgPath的记录
            sql_repo.update('face', {"photo_path": [imgPath]},
                                new_info={'faces': jsonFaces, 'recog_state': face_recog_state,
                                     'parent_path': os.path.abspath(imgPath + os.path.sep + "..")})
            sql_repo.update('photo', {"photo_path": [imgPath]}, new_info={'peoples': jsonPeoples})


class VerifyProcess(Process):
    graph = None
    mtcnn_detector = None
    facenet_model = None
    margin = 32
    img_path = ''
    faces_list = []
    table_widget = []
    canvasW = 0
    canvasH = 0


    def __init__(self):
        super(VerifyProcess, self).__init__()
        self.event = Event()
        self.event.set()  # 设置为True


    def updataData(self, verify_queue):
        self.verify_queue =verify_queue


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
        if self.graph == None:
            self.graph = tf.get_default_graph()
            print('###### VerifyProcess:graph')
        with self.graph.as_default():
            if self.facenet_model == None:
                self.facenet_model = load_model('model/facenet_keras.h5')
                print('###### VerifyProcess:load model')

        engine.dispose()
        sql_repo = RepoGeneral(make_session(engine))

        while 1:
            if self.verify_queue.empty() == True:
                self.pause()
                print('#### VerifyProcess :队列空,子进程暂停')
            self.event.wait()  # 为True时立即返回, 为False时阻塞直到内部的标识位为True后才立即返回

            checkedInfoDict = self.verify_queue.get()
            checkedInfoDict = eval(checkedInfoDict)

            self.img_path = checkedInfoDict['path']
            self.faces_list = eval(checkedInfoDict['faces'])
            # self.archivalNum = checkedInfoDict['arch_num']
            # self.subject = checkedInfoDict['theme']
            self.table_widget = checkedInfoDict['table_widget']
            self.canvasW = checkedInfoDict['label_size'][0]
            self.canvasH = checkedInfoDict['label_size'][1]


            faces_name = []
            faces_embedding = []

            new_faces = []
            new_people = []
            new_faces_name = []
            new_faces_id = []

            orig_faces_id = list(range(len(self.faces_list)))

            scale = calculate_img_scaling(self.img_path, self.canvasH, self.canvasW)
            img = cv2.cvtColor(cv2.imdecode(np.fromfile(self.img_path, dtype=np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            (h, w) = img.shape[:2]
            test_img = cv2.resize(img, (int(w*scale), int(h*scale)))
            (h, w) = test_img.shape[:2]

            for item in self.table_widget:
                if item['id'] == '':
                    continue
                new_faces_id.append(int(item['id']))
                new_faces_name.append(item['name'])


            for id in orig_faces_id:
                if id in new_faces_id: # 没有删除
                    index = new_faces_id.index(id)
                    name = new_faces_name[index]
                else:
                    name = '已删除'

                new_faces.append({
                    'id':id,
                    'box':self.faces_list[id]['box'],
                    'name': name
                })
                new_people.append({
                    'id': id,
                    'name': name
                })

                if name != '':
                    (startX, startY, endX, endY) = eval(self.faces_list[id]['box'])
                    (startX, startY, endX, endY) = startX*scale, startY*scale, endX*scale, endY*scale
                    bb = np.zeros(4, dtype=np.int32)
                    bb[0] = np.maximum(startX - self.margin / 2, 0)  # x1
                    bb[1] = np.maximum(startY - self.margin / 2, 0)  # y1
                    bb[2] = np.minimum(endX + self.margin / 2, w)  # x2
                    bb[3] = np.minimum(endY + self.margin / 2, h)  # y2
                    cropped = test_img[bb[1]:bb[3], bb[0]:bb[2], :]
                    scaled = np.array(Image.fromarray(cropped).resize((160, 160)))
                    with self.graph.as_default():
                        embedding = get_embedding(self.facenet_model, scaled)

                    faces_embedding.append(embedding)
                    faces_name.append(name)
                else:
                    print('核验---id:{},name:{}'.format(id, name))

            saveData('data/data.npz', faces_name, faces_embedding)
            jsonFaces = json.dumps(new_faces, ensure_ascii=False)
            jsonPeople = json.dumps(new_people, ensure_ascii=False)
            verifyState = 1
            sql_repo.update('face', {"photo_path": [self.img_path]}, new_info={'faces': jsonFaces, 'verify_state': verifyState})
            sql_repo.update('photo', {"photo_path": [self.img_path]}, new_info={'peoples': jsonPeople})


class Recognition(object):
    def __init__(self):
        os.makedirs('data', exist_ok=True)
        self.volume_dict = {}  # 用来填充选择的文件夹
        self.pending_dirs_list = []

        self.data_queue = Queue() # 点击“添加”按钮的时候,用来写入图片路径
        self.verify_queue = Queue()  # 用来填充核验信息
        self.done_queue = Manager().Queue() # 返回识别结果信息
        self.jobs_proc = []   # 将进程对象放进list
        self.pendingTotalImgsNum = 0 #待处理的图片总数量

        # 返回UI层的识别结果信息
        self.noRecFaceImg = 0 # 没有识别出人脸的图片的总数
        self.facesNum = 0  # 总的检测到的所有人脸
        self.recognized_face_num = 0 # 已识别人脸的总数
        self.part_recognized_pic_num = 0 # 部分识别出人脸的图片的总数
        self.all_recognized_pic_num = 0  # 全部识别出人脸的图片的总数
        self.handled_pic_num = 0 # 已处理图片的总数

        # 用于本次识别
        self.part_recog_img_list = []
        self.all_recog_img_list = []

        self.sql_repo = RepoGeneral(make_session(engine))

        # 实例化识别子进程
        for _ in range(os.cpu_count()):
            proc = RecognizeProcess(self.done_queue)
            proc.daemon = True
            self.jobs_proc.append(proc)

        # 开启核验子进程
        self.verifyProc = VerifyProcess()
        self.verifyProc.daemon = True
        self.verifyProc.updataData(self.verify_queue)
        self.verifyProc.start()


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
        if self.data_queue.qsize() == 0: # 队列已被取空,说明已经识别完了,这里将未核验的图片数据再次取出进行识别
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

        for job in self.jobs_proc:
            if not job.is_alive():
                print('### pid will start')
                job.updataData(self.data_queue)
                job.start()
            else:
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

        if len(arch_num_info['children']) == 0:
            return False

        self.volume_dict = arch_num_info['children']

        for volume_name, volume_num in self.volume_dict.items():  # 取绝对路径,数据才会保持一样的形式. 例如 'D:\\深圳市社保局联谊活动\\合影\\0.jpg',否则'D:/深圳市社保局联谊活动\\合影'
            fileData = glob.glob(os.path.abspath(os.path.join(volume_name, '*.*[jpg,png]')))
            print(fileData)
            for i, path in enumerate(fileData):
                self.data_queue.put(path)
                photoInfo = {}
                faceInfo = {}
                photoInfo['arch_code'] = 'A1_lzd_{}'.format(i)
                photoInfo['photo_path'] = path
                photoInfo['group_code'] = 'A1_anyun'
                photoInfo['fonds_code'] = 'A1'
                photoInfo['arch_category_code'] = 'ZP'
                photoInfo['year'] = '2020'
                photoInfo['group_code'] = '0001'
                photoInfo['photo_code'] = '{0:0>4}'.format(i + 1)
                photoInfo['format'] ='JPGE'
                photoInfo['photographer'] = 'lzd'
                photoInfo['taken_time'] = '20201116'
                photoInfo['taken_locations'] = '深圳'
                photoInfo['security_classification'] = '公开'
                photoInfo['reference_code'] = '深字001'
                photoDbData.append(photoInfo)
                faceInfo['photo_path'] = path
                faceInfo['photo_archival_code'] = 'A1_lzd_{}'.format(i)
                faceInfo['recog_state'] = 0
                faceInfo['verify_state'] = 0
                faceInfo['parent_path'] = volume_name
                faceDbData.append(faceInfo)
            self.pending_dirs_list.append(os.path.abspath(os.path.join(volume_name)))

        self.pendingTotalImgsNum = self.data_queue.qsize()
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
        recognizedResultInfo['part_recognized_pic_num'] = self.part_recognized_pic_num  # 部分识别出人脸的图片的总数
        recognizedResultInfo['all_recognized_pic_num'] = self.all_recognized_pic_num  # 全部识别出人脸的图片的总数
        recognizedResultInfo['handled_pic_num'] = self.handled_pic_num  # 已处理图片
        recognizedResultInfo['unhandled_pic_num'] = unprocessedImg  # 未处理的图片

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


    def trainModel(self):
        acc = -1.0
        if os.path.exists('data/data.npz'):
            data = np.load('data/data.npz', allow_pickle=True)
            faces_name, faces_embedding = data['faces_name'], data['faces_embedding']
            trainX = np.asarray(faces_embedding)
            trainy = np.asarray(faces_name)

            label_encoder = LabelEncoder()
            trainy = label_encoder.fit_transform(trainy)

            model = SVC(kernel='linear', probability=True)
            try:
                model.fit(trainX, trainy)
            except Exception as e:
                print(str(e))
                acc = -2.0 # The number of classes has to be greater than one; got 1 class
                return {"model_acc": acc}

            os.makedirs('data/model/', exist_ok=True)
            joblib.dump(model, 'data/model/custom_faceRecognize.h5')
            shutil.copy('data/data.npz', 'data/model/last_data.npz') # 当前模型训练时, 使用的数据

            # if os.path.exists('data/last_no_train_data.npz'):
            #     os.remove('data/last_no_train_data.npz')

            yhat_train = model.predict(trainX)
            acc = accuracy_score(trainy, yhat_train)
            print('Accuracy: train=%0.3f' % (acc*100))
            # label_encoder.inverse_transform(yhat_train)

        return {"model_acc": acc}

    def get_untrained_pic_num(self):
        length = 0
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







