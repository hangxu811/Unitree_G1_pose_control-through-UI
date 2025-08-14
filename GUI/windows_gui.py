# -*- coding: utf-8 -*-
import os, sys, numpy as np, trimesh
import pyqtgraph.opengl as gl
from pyqtgraph import Transform3D
from yourdfpy import URDF  # 如果用 urdfpy，请改成：from urdfpy import URDF

# 解决 Windows 下 Qt 插件路径问题
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(
    sys.prefix, "Lib", "site-packages", "PyQt5", "Qt", "plugins", "platforms"
)

from PyQt5 import QtWidgets, QtCore

URDF_PATH = "g1_29dof.urdf"

# 29 自由度 G1：输出时关节顺序（按钮打印与保存）
control_joints = [
    # 下三路
    "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
    "left_knee_joint",
    "left_ankle_pitch_joint", "left_ankle_roll_joint",
    "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
    "right_knee_joint",
    "right_ankle_pitch_joint", "right_ankle_roll_joint",
    # 小蛮腰
    "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
    # 上肢
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "left_wrist_yaw_joint", "left_wrist_pitch_joint", "left_wrist_roll_joint",
    "right_wrist_yaw_joint", "right_wrist_pitch_joint", "right_wrist_roll_joint",
]


class MyGLViewWidget(gl.GLViewWidget):
    def __init__(self, robot, joint_values,
                 shoulder_joint_names,
                 elbow_joint_names,
                 wrist_joint_names,
                 hip_joint_names,
                 knee_joint_names,
                 ankle_joint_names,
                 waist_joint_names,
                 link_items,
                 left_hip_links, left_knee_links, left_ankle_links,
                 right_hip_links, right_knee_links, right_ankle_links,
                 waist_links,
                 left_shoulder_links, right_shoulder_links,
                 left_elbow_links, right_elbow_links,
                 left_wrist_links, right_wrist_links):
        super().__init__()
        self.robot = robot
        self.joint_values = joint_values

        # --- 关节名映射 ---
        # 臀
        self.left_hip_pitch_joint = hip_joint_names['left_hip_pitch']
        self.left_hip_roll_joint  = hip_joint_names['left_hip_roll']
        self.left_hip_yaw_joint   = hip_joint_names['left_hip_yaw']
        self.right_hip_pitch_joint = hip_joint_names['right_hip_pitch']
        self.right_hip_roll_joint  = hip_joint_names['right_hip_roll']
        self.right_hip_yaw_joint   = hip_joint_names['right_hip_yaw']
        # 膝
        self.left_knee_joint  = knee_joint_names['left_knee']
        self.right_knee_joint = knee_joint_names['right_knee']
        # 踝
        self.left_ankle_pitch_joint = ankle_joint_names['left_ankle_pitch']
        self.left_ankle_roll_joint  = ankle_joint_names['left_ankle_roll']
        self.right_ankle_pitch_joint = ankle_joint_names['right_ankle_pitch']
        self.right_ankle_roll_joint  = ankle_joint_names['right_ankle_roll']
        # 腰
        self.waist_yaw_joint   = waist_joint_names['waist_yaw']
        self.waist_roll_joint  = waist_joint_names['waist_roll']
        self.waist_pitch_joint = waist_joint_names['waist_pitch']
        # 肩
        self.left_shoulder_yaw_joint   = shoulder_joint_names['left_shoulder_yaw']
        self.left_shoulder_pitch_joint = shoulder_joint_names['left_shoulder_pitch']
        self.left_shoulder_roll_joint  = shoulder_joint_names['left_shoulder_roll']
        self.right_shoulder_yaw_joint   = shoulder_joint_names['right_shoulder_yaw']
        self.right_shoulder_pitch_joint = shoulder_joint_names['right_shoulder_pitch']
        self.right_shoulder_roll_joint  = shoulder_joint_names['right_shoulder_roll']
        # 肘
        self.left_elbow_joint  = elbow_joint_names['left_elbow']
        self.right_elbow_joint = elbow_joint_names['right_elbow']
        # 腕
        self.left_wrist_yaw_joint   = wrist_joint_names['left_wrist_yaw']
        self.left_wrist_pitch_joint = wrist_joint_names['left_wrist_pitch']
        self.left_wrist_roll_joint  = wrist_joint_names['left_wrist_roll']
        self.right_wrist_yaw_joint   = wrist_joint_names['right_wrist_yaw']
        self.right_wrist_pitch_joint = wrist_joint_names['right_wrist_pitch']
        self.right_wrist_roll_joint  = wrist_joint_names['right_wrist_roll']

        # links
        self.link_items = link_items
        self.left_shoulder_links   = left_shoulder_links
        self.right_shoulder_links  = right_shoulder_links
        self.left_elbow_links      = left_elbow_links
        self.right_elbow_links     = right_elbow_links
        self.left_wrist_links      = left_wrist_links
        self.right_wrist_links     = right_wrist_links
        self.left_hip_links        = left_hip_links
        self.right_hip_links       = right_hip_links
        self.left_knee_links       = left_knee_links
        self.right_knee_links      = right_knee_links
        self.left_ankle_links      = left_ankle_links
        self.right_ankle_links     = right_ankle_links
        self.waist_links           = waist_links

        # --- 拖拽状态 ---
        self.draggingRightShoulder = False
        self.draggingLeftShoulder  = False
        self.draggingRightElbow    = False
        self.draggingLeftElbow     = False
        self.draggingRightWrist    = False
        self.draggingLeftWrist     = False
        self.draggingRightHip      = False
        self.draggingLeftHip       = False
        self.draggingRightKnee     = False
        self.draggingLeftKnee      = False
        self.draggingRightAnkle    = False
        self.draggingLeftAnkle     = False
        self.draggingWaist         = False

        self.dragPos = None

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            pos = ev.position() if hasattr(ev, 'position') else ev.localPos()
            x, y = int(pos.x()), int(pos.y())
            items = self.itemsAt((x, y, 1, 1))

            # 手腕检测
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.left_wrist_links:
                    self.draggingLeftWrist = True
                    self.dragPos = pos
                    ev.accept()
                    return
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.right_wrist_links:
                    self.draggingRightWrist = True
                    self.dragPos = pos
                    ev.accept()
                    return

            # 肘检测
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.left_elbow_links:
                    self.draggingLeftElbow = True
                    self.dragPos = pos
                    ev.accept()
                    return
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.right_elbow_links:
                    self.draggingRightElbow = True
                    self.dragPos = pos
                    ev.accept()
                    return

            # 肩检测
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.right_shoulder_links:
                    self.draggingRightShoulder = True
                    self.dragPos = pos
                    ev.accept()
                    return
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.left_shoulder_links:
                    self.draggingLeftShoulder = True
                    self.dragPos = pos
                    ev.accept()
                    return

            # 踝检测
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.left_ankle_links:
                    self.draggingLeftAnkle = True
                    self.dragPos = pos
                    ev.accept()
                    return
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.right_ankle_links:
                    self.draggingRightAnkle = True
                    self.dragPos = pos
                    ev.accept()
                    return

            # 膝检测
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.left_knee_links:
                    self.draggingLeftKnee = True
                    self.dragPos = pos
                    ev.accept()
                    return
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.right_knee_links:
                    self.draggingRightKnee = True
                    self.dragPos = pos
                    ev.accept()
                    return

            # 臀检测
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.left_hip_links:
                    self.draggingLeftHip = True
                    self.dragPos = pos
                    ev.accept()
                    return
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.right_hip_links:
                    self.draggingRightHip = True
                    self.dragPos = pos
                    ev.accept()
                    return

            # 腰检测
            for item in items:
                if hasattr(item, 'link_name') and item.link_name in self.waist_links:
                    self.draggingWaist = True
                    self.dragPos = pos
                    ev.accept()
                    return

            #没命中可拖拽目标 → 交给父类，让其初始化自己的 mousePos
            return super().mousePressEvent(ev)

        elif ev.button() == QtCore.Qt.RightButton:
            #右键直接交给父类（旋转/平移相机等）
            return super().mousePressEvent(ev)

        return super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        # 工具函数：读取位置并更新 dragPos
        def _get_diff():
            newPos = ev.position() if hasattr(ev, 'position') else ev.localPos()
            if self.dragPos is None:
                self.dragPos = newPos
            diff = newPos - self.dragPos
            self.dragPos = newPos
            return diff.x(), diff.y()

        if self.draggingRightShoulder and (ev.buttons() & QtCore.Qt.LeftButton):
            dx, dy = _get_diff()
            self.joint_values[self.right_shoulder_yaw_joint]   += -dx * 0.01
            self.joint_values[self.right_shoulder_pitch_joint] +=  dy * 0.01
            self.joint_values[self.right_shoulder_yaw_joint]   = np.clip(self.joint_values[self.right_shoulder_yaw_joint],  -2.618, 2.618)
            self.joint_values[self.right_shoulder_pitch_joint] = np.clip(self.joint_values[self.right_shoulder_pitch_joint], -3.0892, 2.6704)
            self.update_joints()
            ev.accept(); return

        elif self.draggingLeftShoulder and (ev.buttons() & QtCore.Qt.LeftButton):
            dx, dy = _get_diff()
            self.joint_values[self.left_shoulder_yaw_joint]   += -dx * 0.01
            self.joint_values[self.left_shoulder_pitch_joint] +=  dy * 0.01
            self.joint_values[self.left_shoulder_yaw_joint]   = np.clip(self.joint_values[self.left_shoulder_yaw_joint],  -2.618, 2.618)
            self.joint_values[self.left_shoulder_pitch_joint] = np.clip(self.joint_values[self.left_shoulder_pitch_joint], -3.0892, 2.6704)
            self.update_joints()
            ev.accept(); return

        elif self.draggingRightElbow and (ev.buttons() & QtCore.Qt.LeftButton):
            _, dy = _get_diff()
            self.joint_values[self.right_elbow_joint] += dy * 0.01
            self.joint_values[self.right_elbow_joint]  = np.clip(self.joint_values[self.right_elbow_joint], -1.0472, 2.0944)
            self.update_joints()
            ev.accept(); return

        elif self.draggingLeftElbow and (ev.buttons() & QtCore.Qt.LeftButton):
            _, dy = _get_diff()
            self.joint_values[self.left_elbow_joint] += dy * 0.01
            self.joint_values[self.left_elbow_joint]  = np.clip(self.joint_values[self.left_elbow_joint], -1.0472, 2.0944)
            self.update_joints()
            ev.accept(); return

        elif self.draggingLeftWrist and (ev.buttons() & QtCore.Qt.LeftButton):
            dx, dy = _get_diff()
            self.joint_values[self.left_wrist_yaw_joint]   += -dx * 0.01
            self.joint_values[self.left_wrist_pitch_joint] +=  dy * 0.01
            self.joint_values[self.left_wrist_yaw_joint]   = np.clip(self.joint_values[self.left_wrist_yaw_joint],  -1.614429558, 1.614429558)
            self.joint_values[self.left_wrist_pitch_joint] = np.clip(self.joint_values[self.left_wrist_pitch_joint], -1.614429558, 1.614429558)
            self.update_joints()
            ev.accept(); return

        elif self.draggingRightWrist and (ev.buttons() & QtCore.Qt.LeftButton):
            dx, dy = _get_diff()
            self.joint_values[self.right_wrist_yaw_joint]   += -dx * 0.01
            self.joint_values[self.right_wrist_pitch_joint] +=  dy * 0.01
            self.joint_values[self.right_wrist_yaw_joint]   = np.clip(self.joint_values[self.right_wrist_yaw_joint],  -1.614429558, 1.614429558)
            self.joint_values[self.right_wrist_pitch_joint] = np.clip(self.joint_values[self.right_wrist_pitch_joint], -1.614429558, 1.614429558)
            self.update_joints()
            ev.accept(); return

        elif self.draggingLeftHip and (ev.buttons() & QtCore.Qt.LeftButton):
            dx, dy = _get_diff()
            self.joint_values[self.left_hip_yaw_joint]   += -dx * 0.01
            self.joint_values[self.left_hip_pitch_joint] +=  dy * 0.01
            self.joint_values[self.left_hip_yaw_joint]   = np.clip(self.joint_values[self.left_hip_yaw_joint],   -2.7576, 2.7576)
            self.joint_values[self.left_hip_pitch_joint] = np.clip(self.joint_values[self.left_hip_pitch_joint], -2.5307, 2.8798)
            self.update_joints()
            ev.accept(); return

        elif self.draggingRightHip and (ev.buttons() & QtCore.Qt.LeftButton):
            dx, dy = _get_diff()
            self.joint_values[self.right_hip_yaw_joint]   += -dx * 0.01
            self.joint_values[self.right_hip_pitch_joint] +=  dy * 0.01
            self.joint_values[self.right_hip_yaw_joint]   = np.clip(self.joint_values[self.right_hip_yaw_joint],   -2.7576, 2.7576)
            self.joint_values[self.right_hip_pitch_joint] = np.clip(self.joint_values[self.right_hip_pitch_joint], -2.5307, 2.8798)
            self.update_joints()
            ev.accept(); return

        elif self.draggingLeftKnee and (ev.buttons() & QtCore.Qt.LeftButton):
            _, dy = _get_diff()
            self.joint_values[self.left_knee_joint] += -dy * 0.01
            self.joint_values[self.left_knee_joint]  = np.clip(self.joint_values[self.left_knee_joint], -0.087267, 2.8798)
            self.update_joints()
            ev.accept(); return

        elif self.draggingRightKnee and (ev.buttons() & QtCore.Qt.LeftButton):
            _, dy = _get_diff()
            self.joint_values[self.right_knee_joint] += -dy * 0.01
            self.joint_values[self.right_knee_joint]  = np.clip(self.joint_values[self.right_knee_joint], -0.087267, 2.8798)
            self.update_joints()
            ev.accept(); return

        elif self.draggingLeftAnkle and (ev.buttons() & QtCore.Qt.LeftButton):
            dx, dy = _get_diff()
            self.joint_values[self.left_ankle_pitch_joint] += -dx * 0.01
            self.joint_values[self.left_ankle_roll_joint]  +=  dy * 0.01
            self.joint_values[self.left_ankle_pitch_joint] = np.clip(self.joint_values[self.left_ankle_pitch_joint], -0.87267, 0.5236)
            self.joint_values[self.left_ankle_roll_joint]  = np.clip(self.joint_values[self.left_ankle_roll_joint],  -0.2618, 0.2618)
            self.update_joints()
            ev.accept(); return

        elif self.draggingRightAnkle and (ev.buttons() & QtCore.Qt.LeftButton):
            dx, dy = _get_diff()
            self.joint_values[self.right_ankle_pitch_joint] += -dx * 0.01
            self.joint_values[self.right_ankle_roll_joint]  +=  dy * 0.01
            self.joint_values[self.right_ankle_pitch_joint] = np.clip(self.joint_values[self.right_ankle_pitch_joint], -0.87267, 0.5236)
            self.joint_values[self.right_ankle_roll_joint]  = np.clip(self.joint_values[self.right_ankle_roll_joint],  -0.2618, 0.2618)
            self.update_joints()
            ev.accept(); return

        elif self.draggingWaist and (ev.buttons() & QtCore.Qt.LeftButton):
            dx, dy = _get_diff()
            self.joint_values[self.waist_yaw_joint]   += -dx * 0.01
            self.joint_values[self.waist_pitch_joint] +=  dy * 0.01
            self.joint_values[self.waist_yaw_joint]   = np.clip(self.joint_values[self.waist_yaw_joint],   -2.618, 2.618)
            self.joint_values[self.waist_pitch_joint] = np.clip(self.joint_values[self.waist_pitch_joint], -0.52, 0.52)
            self.update_joints()
            ev.accept(); return

        # 非拖拽 → 父类处理
        return super().mouseMoveEvent(ev)

    def wheelEvent(self, ev):
        d = ev.angleDelta().y()
        if abs(d) < 1:
            return super().wheelEvent(ev)

        step = 0.05 if d > 0 else -0.05

        if self.draggingRightShoulder:
            self.joint_values[self.right_shoulder_roll_joint] += step
            self.joint_values[self.right_shoulder_roll_joint]  = np.clip(self.joint_values[self.right_shoulder_roll_joint], -2.2515, 1.5882)
            self.update_joints(); ev.accept(); return

        if self.draggingLeftShoulder:
            self.joint_values[self.left_shoulder_roll_joint] += step
            self.joint_values[self.left_shoulder_roll_joint]  = np.clip(self.joint_values[self.left_shoulder_roll_joint], -1.5882, 2.2515)
            self.update_joints(); ev.accept(); return

        if self.draggingLeftWrist:
            self.joint_values[self.left_wrist_roll_joint] += step
            self.joint_values[self.left_wrist_roll_joint]  = np.clip(self.joint_values[self.left_wrist_roll_joint], -1.972222054, 1.972222054)
            self.update_joints(); ev.accept(); return

        if self.draggingRightWrist:
            self.joint_values[self.right_wrist_roll_joint] += step
            self.joint_values[self.right_wrist_roll_joint]  = np.clip(self.joint_values[self.right_wrist_roll_joint], -1.972222054, 1.972222054)
            self.update_joints(); ev.accept(); return

        if self.draggingLeftHip:
            self.joint_values[self.left_hip_roll_joint] += step
            self.joint_values[self.left_hip_roll_joint]  = np.clip(self.joint_values[self.left_hip_roll_joint], -0.5236, 2.9671)
            self.update_joints(); ev.accept(); return

        if self.draggingRightHip:
            self.joint_values[self.right_hip_roll_joint] += step
            self.joint_values[self.right_hip_roll_joint]  = np.clip(self.joint_values[self.right_hip_roll_joint], -2.9671, 0.5236)
            self.update_joints(); ev.accept(); return

        if self.draggingLeftAnkle:
            self.joint_values[self.left_ankle_roll_joint] += step
            self.joint_values[self.left_ankle_roll_joint]  = np.clip(self.joint_values[self.left_ankle_roll_joint], -0.2618, 0.2618)
            self.update_joints(); ev.accept(); return

        if self.draggingRightAnkle:
            self.joint_values[self.right_ankle_roll_joint] += step
            self.joint_values[self.right_ankle_roll_joint]  = np.clip(self.joint_values[self.right_ankle_roll_joint], -0.2618, 0.2618)
            self.update_joints(); ev.accept(); return

        if self.draggingWaist:
            self.joint_values[self.waist_roll_joint] += step
            self.joint_values[self.waist_roll_joint]  = np.clip(self.joint_values[self.waist_roll_joint], -0.52, 0.52)
            self.update_joints(); ev.accept(); return

        # 非拖拽滚轮：父类处理（缩放）
        return super().wheelEvent(ev)

    def mouseReleaseEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            # 重置拖拽状态
            self.draggingRightShoulder = False
            self.draggingLeftShoulder  = False
            self.draggingRightElbow    = False
            self.draggingLeftElbow     = False
            self.draggingLeftWrist     = False
            self.draggingRightWrist    = False
            self.draggingRightHip      = False
            self.draggingLeftHip       = False
            self.draggingRightKnee     = False
            self.draggingLeftKnee      = False
            self.draggingRightAnkle    = False
            self.draggingLeftAnkle     = False
            self.draggingWaist         = False
            #清空自己的拖拽点
            self.dragPos = None
        return super().mouseReleaseEvent(ev)

    def update_joints(self):
        self.robot.update_cfg(self.joint_values)
        for link_name, item in self.link_items.items():
            T = self.robot.get_transform(link_name, frame_from=None)
            transform = Transform3D(*T.flatten())
            item.setTransform(transform)
        self.update()


class RobotViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.robot = URDF.load(URDF_PATH, mesh_dir=os.path.dirname(URDF_PATH))
        joint_values = {name: 0.0 for name in self.robot.joint_names}
        self.robot.update_cfg(joint_values)

        hip_joint_names   = {}
        knee_joint_names  = {}
        ankle_joint_names = {}
        waist_joint_names = {}
        shoulder_joint_names = {}
        elbow_joint_names    = {}
        wrist_joint_names    = {}

        # --- 建立关节名称映射 ---
        for name, joint in self.robot.joint_map.items():
            # 臀
            if joint.child in [
                "left_hip_yaw_link", "left_hip_pitch_link", "left_hip_roll_link",
                "right_hip_yaw_link", "right_hip_pitch_link", "right_hip_roll_link"
            ]:
                key = joint.child.replace("_link", "")
                hip_joint_names[key] = name
            # 膝
            elif joint.child in ["left_knee_link", "right_knee_link"]:
                key = joint.child.replace("_link", "")
                knee_joint_names[key] = name
            # 踝
            elif joint.child in [
                "left_ankle_pitch_link", "left_ankle_roll_link",
                "right_ankle_pitch_link", "right_ankle_roll_link"
            ]:
                key = joint.child.replace("_link", "")
                ankle_joint_names[key] = name
            # 腰
            elif joint.child in ["waist_yaw_link", "waist_roll_link"] or joint.name == "waist_pitch_joint":
                key = joint.name.replace("_joint", "") if joint.name == "waist_pitch_joint" else joint.child.replace("_link", "")
                waist_joint_names[key] = name
            # 肩
            elif joint.child in [
                "left_shoulder_yaw_link", "left_shoulder_pitch_link", "left_shoulder_roll_link",
                "right_shoulder_yaw_link", "right_shoulder_pitch_link", "right_shoulder_roll_link"
            ]:
                key = joint.child.replace("_link", "")
                shoulder_joint_names[key] = name
            # 肘
            elif joint.child in ["left_elbow_link", "right_elbow_link"]:
                key = joint.child.replace("_link", "")
                elbow_joint_names[key] = name
            # 腕
            elif joint.child in [
                "left_wrist_yaw_link", "left_wrist_pitch_link", "left_wrist_roll_link",
                "right_wrist_yaw_link", "right_wrist_pitch_link", "right_wrist_roll_link"
            ]:
                key = joint.child.replace("_link", "")
                wrist_joint_names[key] = name

        print(f"joint_names 内容: elbow={elbow_joint_names}, wrist={wrist_joint_names}, shoulder={shoulder_joint_names}")

        # --- 收集 link 集合 ---
        def collect_links(root_set):
            result = set()
            queue = list(root_set)
            while queue:
                parent = queue.pop(0)
                result.add(parent)
                for j in self.robot.joint_map.values():
                    if j.parent == parent and j.child not in result:
                        queue.append(j.child)
            return result

        left_shoulder_links  = collect_links({"left_shoulder_yaw_link", "left_shoulder_pitch_link", "left_shoulder_roll_link"})
        right_shoulder_links = collect_links({"right_shoulder_yaw_link", "right_shoulder_pitch_link", "right_shoulder_roll_link"})
        left_elbow_links  = collect_links({"left_elbow_link"})
        right_elbow_links = collect_links({"right_elbow_link"})
        left_wrist_links  = collect_links({"left_wrist_yaw_link", "left_wrist_pitch_link", "left_wrist_roll_link"})
        right_wrist_links = collect_links({"right_wrist_yaw_link", "right_wrist_pitch_link", "right_wrist_roll_link"})
        left_hip_links    = collect_links({"left_hip_yaw_link", "left_hip_pitch_link", "left_hip_roll_link"})
        right_hip_links   = collect_links({"right_hip_yaw_link", "right_hip_pitch_link", "right_hip_roll_link"})
        left_knee_links   = collect_links({"left_knee_link"})
        right_knee_links  = collect_links({"right_knee_link"})
        left_ankle_links  = collect_links({"left_ankle_pitch_link", "left_ankle_roll_link"})
        right_ankle_links = collect_links({"right_ankle_pitch_link", "right_ankle_roll_link"})
        waist_links       = collect_links({"waist_yaw_link", "waist_roll_link", "torso_link", "waist_support_link"})

        # --- 创建所有 link 的 GLMeshItem，并缓存 ---
        link_items = {}
        for link_name, link_obj in self.robot.link_map.items():
            vertices, faces, face_colors, v_offset = [], [], [], 0
            for vis in link_obj.visuals:
                geom = vis.geometry
                try:
                    if geom.mesh:
                        mesh_path = os.path.join(os.path.dirname(URDF_PATH), geom.mesh.filename)
                        tri = trimesh.load(mesh_path, force='mesh')
                        if geom.mesh.scale:
                            tri.apply_scale(geom.mesh.scale)
                    elif geom.box:
                        tri = trimesh.creation.box(extents=geom.box.size)
                    elif geom.cylinder:
                        tri = trimesh.creation.cylinder(radius=geom.cylinder.radius, height=geom.cylinder.length)
                    elif geom.sphere:
                        tri = trimesh.creation.icosphere(radius=geom.sphere.radius)
                    else:
                        continue
                    if vis.origin is not None:
                        tri.apply_transform(vis.origin)
                except Exception:
                    continue

                v, f = tri.vertices, tri.faces
                vertices.append(v)
                faces.append(f + v_offset)
                rgba = vis.material.color.rgba if (vis.material and vis.material.color) else (0.7, 0.7, 0.7, 1.0)
                face_colors.append(np.tile(rgba, (f.shape[0], 1)))
                v_offset += v.shape[0]

            if not vertices:
                continue
            vertices   = np.vstack(vertices)
            faces      = np.vstack(faces)
            face_colors= np.vstack(face_colors)

            mesh_item = gl.GLMeshItem(vertexes=vertices, faces=faces, faceColors=face_colors, smooth=False)
            mesh_item.link_name = link_name
            T = self.robot.get_transform(link_name, frame_from=None)
            mesh_item.setTransform(Transform3D(*T.flatten()))
            mesh_item.setGLOptions('opaque')
            link_items[link_name] = mesh_item

        # 视图与控件
        self.view = MyGLViewWidget(
            self.robot, joint_values,
            shoulder_joint_names,
            elbow_joint_names,
            wrist_joint_names,
            hip_joint_names,
            knee_joint_names,
            ankle_joint_names,
            waist_joint_names,
            link_items,
            left_hip_links, left_knee_links, left_ankle_links,
            right_hip_links, right_knee_links, right_ankle_links,
            waist_links,
            left_shoulder_links, right_shoulder_links,
            left_elbow_links, right_elbow_links,
            left_wrist_links, right_wrist_links
        )

        self.btn_output = QtWidgets.QPushButton("输出当前关节弧度")
        self.btn_output.clicked.connect(self.output_joint_values)

        main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(main_widget)
        layout.addWidget(self.btn_output)
        layout.addWidget(self.view)
        self.setCentralWidget(main_widget)

        for item in link_items.values():
            self.view.addItem(item)

        # 视角参数
        self.view.opts['distance']  = 2.0
        self.view.opts['azimuth']   = 45
        self.view.opts['elevation'] = 20

    def output_joint_values(self):
        jv = self.view.joint_values
        lines = ["当前控制关节弧度："]
        for name in control_joints:
            val = jv.get(name, 0.0)
            lines.append(f"  {name}: {val:.4f} rad")
        txt = "\n".join(lines)
        print(txt)

        arr = np.array([jv.get(name, 0.0) for name in control_joints], dtype=np.float32)
        np.save("target_pose.npy", arr)

        # 远程上传（可选）
        try:
            import subprocess
            ssh_host = input("你自己的机器人ssh主机地址：")
            remote_path = "~/intern/hang/GUI/target_pose.npy"
            subprocess.run(["scp", "target_pose.npy", f"{ssh_host}:{remote_path}"], check=True)
            print("✅ target_pose.npy 已上传到机器人")
        except Exception as e:
            print("（提示）未上传远程：", e)

        QtWidgets.QMessageBox.information(self, "关节弧度", txt)


def run_ui():
    app = QtWidgets.QApplication(sys.argv)
    viewer = RobotViewer()
    viewer.setWindowTitle("G1 控制")
    viewer.resize(1000, 800)
    viewer.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(run_ui())
