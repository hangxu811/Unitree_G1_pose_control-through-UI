#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, sys, pathlib 
import numpy as np
# ---------- Unitree SDK‑2 ----------
from unitree_sdk2py.core.channel import ChannelFactoryInitialize, ChannelPublisher, ChannelSubscriber
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_, unitree_hg_msg_dds__LowState_
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_
from unitree_sdk2py.utils.crc import CRC
from unitree_sdk2py.utils.thread import RecurrentThread
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient
# -----------------------------------

#正弦插值算法
def sinusoidal_interpolation(q0, q1, ratio):
    """
    正弦插值，从 q0 平滑过渡到 q1，ratio ∈ [0, 1]
    """
    r = 0.5 - 0.5 * np.cos(np.pi * ratio)  # 正弦插值核心
    return (1 - r) * q0 + r * q1


# ----------------- 与示例保持一致的常量 -----------------
G1_NUM_MOTOR = 29

Kp = [
    60, 60, 60, 100, 40, 40,      # legs
    60, 60, 60, 100, 40, 40,      # legs
    60, 40, 40,                   # waist
    40, 40, 40, 40,  40, 40, 40,  # arms
    40, 40, 40, 40,  40, 40, 40   # arms
]

Kd = [
    1, 1, 1, 2, 1, 1,     # legs
    1, 1, 1, 2, 1, 1,     # legs
    1, 1, 1,              # waist
    1, 1, 1, 1, 1, 1, 1,  # arms
    1, 1, 1, 1, 1, 1, 1   # arms 
]

class G1JointIndex:
    LeftHipPitch = 0; LeftHipRoll = 1; LeftHipYaw = 2; LeftKnee = 3
    LeftAnklePitch = 4; LeftAnkleRoll = 5

    RightHipPitch = 6; RightHipRoll = 7; RightHipYaw = 8; RightKnee = 9
    RightAnklePitch = 10; RightAnkleRoll = 11

    WaistYaw = 12; WaistRoll = 13; WaistPitch = 14

    LeftShoulderPitch = 15; LeftShoulderRoll = 16; LeftShoulderYaw = 17; LeftElbow = 18
    LeftWristRoll = 19; LeftWristPitch = 20; LeftWristYaw = 21

    RightShoulderPitch = 22; RightShoulderRoll = 23; RightShoulderYaw = 24; RightElbow = 25
    RightWristRoll = 26; RightWristPitch = 27; RightWristYaw = 28

class Mode:
    PR = 0  # Series Control for Pitch/Roll Joints
    AB = 1  # Parallel Control for A/B Joints

class Custom:
    def __init__(self):
        self.time_ = 0.0
        self.control_dt_ = 0.002  # 改回2ms，与示例保持一致
        self.duration_ = 3.0   
        self.counter_ = 0
        self.mode_machine_ = 0
        self.low_cmd = unitree_hg_msg_dds__LowCmd_()  
        self.low_state = None 
        self.update_mode_machine_ = False
        self.crc = CRC()

        # ---------- UI 相关 ----------
        self.npy_path  = pathlib.Path("target_pose.npy")
        self.npy_mtime = 0.0
        self.ui_pose   = np.zeros(G1_NUM_MOTOR, dtype=np.float32)
        self.initial_pose = np.zeros(G1_NUM_MOTOR, dtype=np.float32) 
        self.current_pose = np.zeros(G1_NUM_MOTOR, dtype=np.float32)
    # ---------------- DDS 初始化 ----------------
    def Init(self):
        # 添加 MotionSwitcherClient 初始化
        self.msc = MotionSwitcherClient()
        self.msc.SetTimeout(5.0)
        self.msc.Init()

        # 检查并释放当前模式
        status, result = self.msc.CheckMode()
        while result['name']:
            self.msc.ReleaseMode()
            status, result = self.msc.CheckMode()
            time.sleep(1)

        # 创建发布者和订阅者
        self.pub = ChannelPublisher("rt/lowcmd", LowCmd_)
        self.pub.Init()
        self.sub = ChannelSubscriber("rt/lowstate", LowState_)
        self.sub.Init(self.LowStateHandler, 10)

    def Start(self):
        self.lowCmdWriteThreadPtr = RecurrentThread(
            interval=self.control_dt_, target=self.LowCmdWrite, name="control"
        )
        while self.update_mode_machine_ == False:
            time.sleep(1)

        if self.update_mode_machine_ == True:
            self.lowCmdWriteThreadPtr.Start()

    def LowStateHandler(self, msg: LowState_):
        self.low_state = msg
        for idx in range(G1_NUM_MOTOR):
            self.current_pose[idx] = msg.motor_state[idx].q

        if self.update_mode_machine_ == False:
            # 记录所有电机的初始角度
            for idx in range(G1_NUM_MOTOR):
                self.initial_pose[idx] = msg.motor_state[idx].q
            print("初始电机角度记录完成")
            self.mode_machine_ = self.low_state.mode_machine
            self.update_mode_machine_ = True

        # 定时打印电机角度
        # self.counter_ += 1
        # if self.counter_ % 1000 == 0:  # 调整为2秒一次（1000 * 0.002）
        #     self.counter_ = 0
        #     print("当前电机角度（弧度）:")
        #     for i in range(G1_NUM_MOTOR):
        #         print(f"Joint {i}: {msg.motor_state[i].q:.4f}", end=" | ")
        #         if (i + 1) % 6 == 0:  # 每6个换行
        #             print()
        #     print("\n" + "-"*60)

    # -------------- 热加载 UI 参数 --------------
    def _update_ui_pose(self):
        if not self.npy_path.exists(): 
            return
        
        mt = self.npy_path.stat().st_mtime
        if mt == self.npy_mtime: 
            return
            
        try:
            arr = np.load(self.npy_path).astype(np.float32)
            if arr.size >= G1_NUM_MOTOR:
                self.ui_pose[:] = arr[:G1_NUM_MOTOR]
            else:
                self.ui_pose[:arr.size] = arr
                self.ui_pose[arr.size:] = 0.0
            
            self.npy_mtime = mt
            
            # [关键修改] 检测到新的目标姿态时，重置时间并更新起始位置
            self.time_ = 0.0
            self.initial_pose[:] = self.current_pose[:]  # 将当前位置设为新的起始位置
            
            print(f"成功加载目标姿态，时间已重置，更新时间: {time.strftime('%H:%M:%S')}")
            
        except Exception as e:
            print("[UI] pose load failed:", e)

    # -------------- 主发送循环 ------------------
    def LowCmdWrite(self):
        self._update_ui_pose()  # 加载最新 UI 目标位置
        self.time_ += self.control_dt_  # 累计运行时间
        
        # 初始化所有电机命令（重要！）
        for i in range(G1_NUM_MOTOR):
            self.low_cmd.motor_cmd[i].mode = 1  # Enable
            self.low_cmd.motor_cmd[i].tau = 0.0
            self.low_cmd.motor_cmd[i].dq = 0.0
            self.low_cmd.motor_cmd[i].kp = Kp[i]
            self.low_cmd.motor_cmd[i].kd = Kd[i]

        if self.time_ < self.duration_:
            # 阶段1：从初始位置平滑过渡到目标位置
            ratio = np.clip(self.time_ / self.duration_, 0.0, 1.0)
        #线性平滑
            for i in range(G1_NUM_MOTOR):
                # 对所有电机进行插值控制
                self.low_cmd.motor_cmd[i].q = (1.0 - ratio) * self.initial_pose[i] + ratio * self.ui_pose[i]
        # 正弦插值（Sinusoidal interpolation）
            # for i in range(G1_NUM_MOTOR):
            #     self.low_cmd.motor_cmd[i].q = sinusoidal_interpolation(
            #         self.initial_pose[i],
            #         self.ui_pose[i],
            #         ratio
            #      )

        else:
            # 阶段2：保持目标位置
            for i in range(G1_NUM_MOTOR):
                self.low_cmd.motor_cmd[i].q = self.ui_pose[i]

        # 设置模式
        self.low_cmd.mode_pr = Mode.PR
        self.low_cmd.mode_machine = self.mode_machine_
        
        # 计算并发送CRC
        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.pub.Write(self.low_cmd)

# --------------------------- main ---------------------------
if __name__ == "__main__":
    print("WARNING: 请确保机器人周围没有障碍物！")
    print("请确保 target_pose.npy 文件已存在并包含目标姿态数据。")
    input("准备好后按 Enter 开始 → ")

    if len(sys.argv) > 1:
        ChannelFactoryInitialize(0, sys.argv[1])
    else:
        ChannelFactoryInitialize(0)

    custom = Custom()
    custom.Init()
    custom.Start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n用户停止程序。")