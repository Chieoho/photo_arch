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

from recognition.SQL import *
from recognition.utils import *
from photo_arch.adapters.sql.repo import RepoGeneral
from photo_arch.infrastructures.databases.db_setting import init_db
sql_repo = RepoGeneral(init_db())

recognizedInfoDict = {}
verifyed_img_list = []
part_recog_img_list = []
all_recog_img_list = []

class RecognizeThread(threading.Thread):
    margin = 32
    facesNum = 0 # 统计检测出的人脸总数
    faceRecNum = 0 # 统计识别出的人脸总数
    processedImg = 0 # 统计已处理的图片
    partRecFaceImg = 0 # 统计部分识别出人脸的照片
    noRecFaceImg = 0  # 统计没有识别出人脸的照片
    faceProp = 0.0
    euclideanDist = 0.79
    canvasW = 0
    canvasH = 0
    pending_imgs_list = []
    pending_dirs_list = []


    def __init__(self, mtcnn_detector, graph, facenet_model, sql_faces, sql_volume):
        super().__init__()
        self.mtcnn_detector =  mtcnn_detector
        self.graph = graph
        self.facenet_model = facenet_model
        self.sql_faces = sql_faces
        self.sql_volume = sql_volume
        self.event = threading.Event()
        self.event.set() # 设置为True, wait函数不会阻塞



    def pause(self):
        if self.is_alive():
            print("线程休眠")
            self.event.clear()  # 设置为False, 让线程阻塞
        else:
            print("线程已结束")


    def resume(self):
        if self.is_alive():
            print("线程唤醒")
            self.event.set()  # 设置为True, 让线程唤醒
        else:
            print("线程已结束")


    def updateData(self, pending_imgs_list, pending_dirs_list, params):
        self.pending_imgs_list = pending_imgs_list
        self.pending_dirs_list = pending_dirs_list
        self.faceProp = params['threshold']
        self.canvasW = params['label_size'][0]
        self.canvasH = params['label_size'][1]


    def initialize(self):
        recognizedInfoDict.clear()
        self.facesNum = 0
        self.faceRecNum = 0
        self.processedImg = 0
        self.partRecFaceImg = 0
        self.noRecFaceImg = 0


    def run(self):
        faceDbData = []
        pendingImgsTotalNum = len(self.pending_imgs_list)
        for imgPath in self.pending_imgs_list:
            self.event.wait()

            print('#####:', imgPath)
            det = []
            rectangles = []
            # cf = []
            tupFData = []
            self.processedImg += 1
            # statement = "SELECT count(*) from {} WHERE img_path='{}'".format(self.sql_faces.tableName, imgPath)
            # itemNum = self.sql_faces.isExistCurrentRecord(statement)
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
            self.facesNum += face_nums # 统计本次识别中，有多少张人脸
            src_dir = os.path.abspath(os.path.join(imgPath, ".."))
            if face_nums > 0:
                # src_det_x1 = np.asarray(det)[:, 0].tolist()
                det_arr = rank_all_faces(np.asarray(det))
                # cf_arr = rank_confidence(src_det_x1, det_arr, cf)

                faces = []
                curFaceRecNum = 0 # 当前图片里面的人脸数
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
                    with self.graph.as_default():
                        unknown_embedding = get_embedding(self.facenet_model, scaled)
                    who_name = get_name_by_embedding(unknown_embedding, self.faceProp, self.euclideanDist)
                    if who_name != '':
                        self.faceRecNum += 1
                        curFaceRecNum += 1
                    faces.append({
                        'id':j,
                        'box':str([startX/scale, startY/scale, endX/scale, endY/scale]),
                        'name':who_name,
                        # 'embedding':str(list(unknown_embedding))
                    })# box和embedding如果不转换成str,json.dumps就会报错(目前没有找到解决方法)

                if curFaceRecNum == face_nums:
                    face_recog_state = 1 # 全部识别
                    all_recog_img_list.append(imgPath)
                else:
                    face_recog_state = 0 # 部分识别
                    self.partRecFaceImg += 1
                    part_recog_img_list.append(imgPath)

                jsonFaces = json.dumps(faces, ensure_ascii=False)
            else:
                face_recog_state = 2 # 没有检测出脸
                jsonFaces = ''
                self.noRecFaceImg += 1

            tupFData.append(jsonFaces) # faces
            tupFData.append(face_recog_state) # face_recog_state
            tupFData.append(0) # verify_state
            tupFData.append(imgPath) # img_path
            faceDbData.append(tuple(tupFData))

            recRatio = round(self.faceRecNum / self.facesNum, 3) # 识别出的人脸/总的人脸
            unprocessedImg = len(self.pending_imgs_list) - self.processedImg # 未处理的图片
            allRecFaceImg = self.processedImg - self.partRecFaceImg - self.noRecFaceImg # 全部识别出人脸的图片的总数

            recognizedInfoDict['recognition_rate'] = recRatio # 识别率
            recognizedInfoDict['recognized_face_num'] = self.faceRecNum # 已识别人脸
            recognizedInfoDict['part_recognized_pic_num'] = self.partRecFaceImg # 部分识别出人脸的图片的总数
            recognizedInfoDict['all_recognized_pic_num'] = allRecFaceImg # 全部识别出人脸的图片的总数
            recognizedInfoDict['handled_pic_num'] = self.processedImg # 已处理图片
            recognizedInfoDict['unhandled_pic_num'] = unprocessedImg # 未处理的图片

        if len(faceDbData) > 0:
            self.sql_faces.connectDB()
            sql = "update facesRecgnizeInfo set faces=?, face_recog_state=?, verify_state=?  where img_path=?"
            self.sql_faces.executeManyStatement(sql, faceDbData)
            self.sql_faces.closeDB()

        tupDirData = []
        dirDbData = []
        for dirPath in self.pending_dirs_list:
            tupDirData.append(1)
            tupDirData.append(dirPath)
        dirDbData.append(tuple(tupDirData))
        if len(dirDbData) > 0:
            self.sql_volume.connectDB()
            sql = "update volumeInfo set volume_recog_state=?  where volume_path=?"
            self.sql_volume.executeManyStatement(sql, dirDbData)
            self.sql_volume.closeDB()


class VerifyThread(threading.Thread):
    item = []
    margin = 32
    archivalNum = ''
    subject = ''
    img_path = ''
    faces_list = []
    table_widget = []
    canvasW = 0
    canvasH = 0

    def __init__(self, graph, facenet_model, sql_faces):
        super(VerifyThread, self).__init__()
        self.graph = graph
        self.sql_faces = sql_faces
        self.facenet_model = facenet_model


    def updataData(self, checked_info):
        self.img_path = checked_info['path']
        self.faces_list = eval(checked_info['faces'])
        self.archivalNum = checked_info['arch_num']
        self.subject = checked_info['theme']
        self.table_widget = checked_info['table_widget']
        self.canvasW = checked_info['label_size'][0]
        self.canvasH = checked_info['label_size'][1]


    def run(self):
        faces_name = []
        faces_embedding = []

        new_faces = []
        new_faces_name = []
        new_faces_id = []

        # img_path = self.item['img_path']
        # faces_list = eval(self.item['faces'])
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
        verifyed_img_list.append(self.img_path)

        self.sql_faces.connectDB()
        jsonFaces = json.dumps(new_faces, ensure_ascii=False)
        verifyState = 1
        updateStatement = "UPDATE {} SET faces='{}', verify_state={}, archival_num='{}', subject='{}' WHERE img_path='{}'".format(self.sql_faces.tableName, jsonFaces, verifyState, self.archivalNum, self.subject ,self.img_path)
        self.sql_faces.executeStatement(updateStatement)
        self.sql_faces.closeDB()




class Recognition(object):
    def __init__(self):
        os.makedirs('data', exist_ok=True)
        self.rootVolumePath = ''
        self.rootVolumeName = ''  # 根文件夹的名字
        self.rootVolumeNum = ''  # 根文件夹的档号
        self.volume_dict = {}  # 用来填充选择的文件夹
        self.default_select_dirPath = 'D:/'
        self.pending_dirs_list = []
        self.pending_imgs_list = []
        self.margin = 32
        self.faceProp = ''
        self.last_verifyed_img_nums = 0

        self.graph = tf.get_default_graph()
        with self.graph.as_default():
            self.mtcnn_detector = MTCNN() # steps_threshold = [0.5,0.7,0.9]
            self.facenet_model = load_model('model/facenet_keras.h5')


        dbName_faces = './data/faces_recgnize.db'
        tableName_faces = 'facesRecgnizeInfo'
        facesColumns = 'id integer primary key, img_path text UNIQUE, archival_num text,faces text, face_recog_state integer, verify_state integer, src_dir text, subject text'
        dbName_volume = './data/volume.db'
        tableName_volume = 'volumeInfo'
        volumeColums = 'id integer primary key, volume_path text UNIQUE, volume_name text, volume_num text, volume_recog_state integer, root_volume_path text, root_volume_num text'

        self.sql_faces = SQL_method(dbName_faces, tableName_faces, facesColumns)
        self.sql_volume = SQL_method(dbName_volume, tableName_volume, volumeColums)

        try:
            # 创建数据库文件
            self.sql_faces.connectDB()
            self.sql_faces.creatTable()
            print(">>> facesRecgnizeInfo表创建成功！")
        except:
            print(">>> facesRecgnizeInfo表已创建！")
        finally:
            self.sql_faces.closeDB()

        try:
            # 创建数据库文件
            self.sql_volume.connectDB()
            self.sql_volume.creatTable()
            print(">>> volumeInfo表创建成功！")
        except:
            print(">>> volumeInfo表已创建！")
        finally:
            self.sql_volume.closeDB()



    def recognition(self, params):
        ret = 0
        self.last_verifyed_img_nums = len(verifyed_img_list)
        not_verifyed_img_list = [x for x in self.pending_imgs_list if x not in verifyed_img_list]
        if len(not_verifyed_img_list) > 0:
            self.pending_imgs_list = not_verifyed_img_list
        else: #所有图片已经核验完了
            ret = 1
            return ret

        # 再次识别的时候，将图片存入两个list中
        part_recog_img_list.clear()
        all_recog_img_list.clear()

        self.recognizeThread = RecognizeThread(self.mtcnn_detector, self.graph, self.facenet_model, self.sql_faces, self.sql_volume)
        self.recognizeThread.initialize()
        self.recognizeThread.updateData(self.pending_imgs_list, self.pending_dirs_list, params)
        self.recognizeThread.start()
        return ret


    def pauseRecognition(self):
        self.recognizeThread.pause()


    def continueRecognition(self):
        self.recognizeThread.resume()


    def add_folderItem(self, arch_num_info):
        print(arch_num_info)
        ret = True
        faceDbData = []
        volumeDbData = []
        self.pending_imgs_list.clear()
        self.pending_dirs_list.clear()
        verifyed_img_list.clear()
        part_recog_img_list.clear()
        all_recog_img_list.clear()

        if len(arch_num_info['root']) == 0 or len(arch_num_info['children']) == 0:
            return False

        self.rootVolumePath = list(arch_num_info['root'].keys())[0]
        self.rootVolumeNum = list(arch_num_info['root'].values())[0]
        self.volume_dict = arch_num_info['children']

        self.sql_volume.connectDB()
        for volume_name, volume_num in self.volume_dict.items():  # 取绝对路径,数据才会保持一样的形式. 例如 'D:\\深圳市社保局联谊活动\\合影\\0.jpg',否则'D:/深圳市社保局联谊活动\\合影'
            volume_name = volume_name.split('\\')[-1]
            fileData = glob.glob(os.path.abspath(os.path.join(self.rootVolumePath, volume_name, '*.*[jpg,png]')))
            for i, path in enumerate(fileData):
                tupFList = []
                tupFList.append(path)  # img_path
                tupFList.append(volume_num + '-{0:0>4}'.format(i + 1))  # archival_num
                tupFList.append(os.path.abspath(os.path.join(path, "..")))  # src_dir
                tupFList.append(self.rootVolumePath.split('\\')[-1])  # subject
                faceDbData.append(tuple(tupFList))
            self.pending_imgs_list.extend(fileData)
            self.pending_dirs_list.append(os.path.abspath(os.path.join(self.rootVolumePath, volume_name)))

            tupVList = []
            volume_path = os.path.abspath(os.path.join(self.rootVolumePath, volume_name))
            tupVList.append(volume_path)  # volume_path
            tupVList.append(volume_name)  # volume_name
            tupVList.append(volume_num)  # volume_num
            volume_recog_state = 0
            selectStatement = "select volume_recog_state from volumeInfo where volume_path='{}'".format(volume_path)
            recogStateList = self.sql_volume.getAllData(selectStatement)
            if len(recogStateList) > 0 :
                volume_recog_state = recogStateList[0]['volume_recog_state']
            tupVList.append(volume_recog_state)  # volume_recog_state
            tupVList.append(self.rootVolumePath)  # root_volume_path
            tupVList.append(self.rootVolumeNum)  # root_volume_num
            volumeDbData.append(tuple(tupVList))
        self.sql_volume.closeDB()

        self.sql_faces.connectDB()
        sql = "insert or ignore into facesRecgnizeInfo(img_path, archival_num, src_dir, subject) values(?,?,?,?)"
        self.sql_faces.executeManyStatement(sql, faceDbData)
        self.sql_faces.closeDB()

        self.sql_volume.connectDB()
        sql = "insert or replace into volumeInfo(volume_path, volume_name, volume_num, volume_recog_state, root_volume_path, root_volume_num) values(?,?,?,?,?,?)"
        self.sql_volume.executeManyStatement(sql, volumeDbData)
        self.sql_volume.closeDB()

        return ret


    def updateRecognitionInfo(self):
        return recognizedInfoDict


    def get_recognized_face_info(self, pic_type, dir_type):
        browse_img_list = []
        for dirPath in self.pending_dirs_list:
            if pic_type == 1 : # 所有图片
                selectStatement = "SELECT img_path, archival_num, subject, faces, verify_state FROM {} WHERE face_recog_state in (0, 1) and src_dir='{}'".format(
                    self.sql_faces.tableName, dirPath)
            else:
                if  pic_type == 2: # 代表部分识别图片
                    faceRecState = 0
                else: # 3代表全部识别图片
                    faceRecState = 1

                selectStatement = "SELECT img_path, archival_num, subject, faces, verify_state FROM {} WHERE face_recog_state={} and src_dir='{}'".format(
                    self.sql_faces.tableName, faceRecState, dirPath)

            self.sql_faces.connectDB()
            data = self.sql_faces.getAllData(selectStatement)
            self.sql_faces.closeDB()

            if dir_type == 1: # 代表本次识别
                total_img_list = part_recog_img_list + all_recog_img_list
                if len(total_img_list) > 0 and (len(verifyed_img_list) - self.last_verifyed_img_nums) < len(total_img_list): # 进行过识别.并且还没识别完
                    if pic_type == 1:
                        dataTmp = [item for item in data if item['img_path'] in total_img_list]
                    elif pic_type == 2:
                        dataTmp = [item for item in data if item['img_path'] in part_recog_img_list]
                    else:  # 3代表全部识别图片
                        dataTmp = [item for item in data if item['img_path'] in all_recog_img_list]

                    browse_img_list.extend(dataTmp)
                else: #没进行识别，先查看数据库的数据
                    browse_img_list.extend(data)
            else: # 2代表所选目录的识别情况
                browse_img_list.extend(data)

        return browse_img_list


    def checke_faces_info(self, checked_info):
        self.verifyThread = VerifyThread(self.graph, self.facenet_model, self.sql_faces)
        self.verifyThread.updataData(checked_info)
        self.verifyThread.start()


    def get_archival_number(self, path):
        arch_num_info = {
            "root": {},
            "children": {}
        }
        self.sql_volume.connectDB()
        selectStatement = "select volume_path, volume_num, root_volume_num from volumeInfo  where root_volume_path='{}'".format(path)
        dataList = self.sql_volume.getAllData(selectStatement)
        self.sql_volume.closeDB()

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







