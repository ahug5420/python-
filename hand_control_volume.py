"""
功能：手势操作电脑音量
1. 使用 OpenCV 读取摄像头视频流
2. 使用 MediaPipe 检测手掌关键点
3. 根据拇指与食指的距离计算手指间距
4. 将间距映射为电脑音量并设置
"""

# TODO：导入 OpenCV（cv2）
import cv2

# TODO：导入 MediaPipe（mp.solutions.hands）
import mediapipe as mp
from mediapipe.framework.formats import landmark_pb2
# TODO：电脑音量控制（如 macOS 的 applescript 或 Windows pycaw）
import pycaw
import ctypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# TODO：导入其他依赖：time、math、numpy 等
import time
import math 
import numpy as np

class HandControlVolume:
    def __init__(self):
        """
        初始化 MediaPipe 相关组件
        """
        # TODO：初始化 mp_drawing、mp_drawing_styles、mp_hands
        self.mp_hands=mp.solutions.hands
        self.mp_drawing=mp.solutions.drawing_utils
        self.mp_drawing_stytles=mp.solutions.drawing_styles

        #（可选）初始化电脑音量控制（Windows pycaw / macOS applescript）
        # TODO：获取音量控制对象与音量范围
        self.devices = AudioUtilities.GetSpeakers() 
        self.interface = self.devices.Activate(
        IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(self.interface, POINTER(IAudioEndpointVolume))
        min_volume, max_volume = self.volume.GetVolumeRange()[:2]
        self.min_vol=min_volume
        self.max_vol=max_volume

    def recognize(self):
        """
        主函数：读取摄像头、检测手势、计算音量、显示画面
        """

        # TODO：初始化 FPS 计时
        fpsTime =time.time()

        # TODO：打开摄像头（cv2.VideoCapture）
        cap = cv2.VideoCapture(0)

        # TODO：设置窗口分辨率（例如 640×480）
        resize_w = 640
        resize_h = 480

        # 音量条绘制变量（初始化）
        rect_height = 0
        rect_percent_text = 0

        # TODO：创建 MediaPipe Hands 实例（min_detection_confidence、max_num_hands 等）
        with self.mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5,
            max_num_hands=2
        ) as hands:
        

            # TODO：循环读取摄像头数据
            while True:
                
                # TODO：读取一帧图像 success, image = cap.read()
                success,image=cap.read()
                if not success:
                    break

                # TODO：调整图像大小
                cv2.resize(image,(resize_w,resize_h))

                # TODO：图像标记为不可写，提高速度
                image.flags.writeable=False

                # TODO：转换为 RGB
                image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)

                # TODO：镜像图像（cv2.flip）
                cv2.flip(image,1)

                # TODO：MediaPipe 处理图像，检测手势
                results =hands.process(image)
                

                # TODO：恢复为可写，并转回 BGR 便于显示
                image.flags.writeable=True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                # TODO：判断是否检测到手
                if results.multi_hand_landmarks:  # 修改为 results.multi_hand_landmarks 判断
                    # TODO：遍历检测到的每只手
                    for hand_landmarks in results.multi_hand_landmarks:

                        # TODO：绘制手部关键点和连线
                        mp.solutions.drawing_utils.draw_landmarks(image,
                                hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)

                        # TODO：提取手指 21 个关键点，存入列表 landmark_list
                        landmark_list=[]
                        for idx, lm in enumerate(hand_landmarks.landmark):
                            landmark_list.append([idx, lm.x*resize_w, lm.y*resize_h])
                        print(landmark_list)
                        # 提取 landmark 的示例框架
                        # for idx, lm in enumerate(hand_landmarks.landmark):
                        #     landmark_list.append([idx, lm.x, lm.y, lm.z])


                        # 当 landmark_list 有数据时
                        if landmark_list:
                            # TODO：提取拇指指尖（ID=4）像素坐标
                            thumb_x =int(landmark_list[4][1])
                            thumb_y =int(landmark_list[4][2])

                            # TODO：提取食指指尖（ID=8）像素坐标
                            index_x =int(landmark_list[8][1])
                            index_y =int(landmark_list[8][2])

                            # TODO：绘制指尖圆点
                            cv2.circle(image,(int(thumb_x),int(thumb_y)),15,(255,0,255),cv2.FILLED)
                            cv2.circle(image,(int(index_x),int(index_y)),15,(255,0,255),cv2.FILLED)


                            # TODO：绘制两点间连线
                            cv2.line(image,(thumb_x,thumb_y),(index_x,index_y),(255,255,0),4)

                            # TODO：计算两点距离（math.hypot）
                            line_len = math.hypot(index_x-thumb_x,index_y-thumb_y)

                            # TODO：将距离映射为音量值（np.interp）
                            vol = np.interp(line_len, [30, 300], [self.min_vol, self.max_vol])

                            # TODO：将距离映射为音量条高度与百分比
                            rect_height = np.interp(line_len, [30, 300], [resize_h-100, 100])
                            rect_percent_text = np.interp(line_len, [30, 300], [0, 100])

                            # TODO：设置系统音量
                            self.volume.SetMasterVolumeLevel(vol, None)

                # TODO：绘制音量条矩形与百分比文字
                cv2.rectangle(image, (20, 100), (50, resize_h-100), (0, 255, 0), 3)
                cv2.rectangle(image, (20, int(rect_height)), (50, resize_h-100), (0, 255, 0), cv2.FILLED)
                cv2.putText(image, f"{int(rect_percent_text)}%", (10, resize_h-50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # TODO：计算 FPS 并显示
                cTime=time.time()
                fps=1/(cTime-fpsTime)
                fpsTime=cTime
                cv2.putText(image,f"FPS:{int(fps)}",(10,50),cv2.FONT_HERSHEY_SIMPLEX,1,(255,0,100),2)


                # TODO：显示窗口 cv2.imshow()
                cv2.imshow("img",image)
                key=cv2.waitKey(1)
                # TODO：按任意键退出
                if key!=-1:
                    cap.release
                    break
                

        # TODO：释放摄像头资源 cap.release()
        


# 程序入口
control = HandControlVolume()
control.recognize()