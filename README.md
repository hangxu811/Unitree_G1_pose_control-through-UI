# Unitree G1 Motion Design & Control GUI

## 📖 概述
本项目为 **Unitree G1** 人形机器人开发了**动作设计与同步控制系统**，由**Windows 端 GUI**与**机器人端控制程序**组成。  

- **Windows 端**：3D 可视化界面，可通过鼠标拖拽/滚轮调整各关节姿态，并保存为姿态文件 `target_pose.npy`。  
- **机器人端**：读取姿态文件，平滑插值到目标姿态，并通过 **Unitree SDK-2** 控制真实 G1 电机，使机器人实时还原 GUI 中的姿态。  

适用于**动作设计**、**姿态同步演示**、**远程控制实验**等场景。

---

## 📂 项目结构

```
.
├── g1_29dof.urdf           # G1 机器人 URDF 模型（29 自由度）
├── target_pose.npy         # 保存 GUI 端导出的关节角度数据（弧度制）
├── windows_gui.py          # Windows 端 GUI 程序（PyQt5 + pyqtgraph）
├── robot_control.py        # 机器人端控制程序（Unitree SDK-2）
├── requirements.txt        # Windows 端依赖
└── README.md
```

---

## 💻 环境要求

### Windows 端

- **系统**：Windows 10/11
- **Python**: 3.8 ~ 3.10
- **依赖**：详见 `requirements.txt`
  ```bash
  pip install -r requirements.txt
  ```

### 机器人端

- **系统**：Ubuntu 20.04（建议运行在 G1 原生控制电脑）
- **Python**: 3.8 ~ 3.10
- **依赖**：
  - [Unitree SDK-2 for Python](https://github.com/unitreerobotics)
  - numpy
  ```bash
  pip install numpy
  ```
  > ⚠️ Unitree SDK-2 for Python 需手动安装，请参考 Unitree 官方文档或仓库。

---

## 🔌 通信方式

当前版本采用**共享文件**方式同步姿态：

1. Windows 端保存 `target_pose.npy`
2. 通过 scp 上传到机器人端固定路径
   - 可在 GUI 按钮点击时输入 SSH 地址，自动上传
3. 机器人端程序定时读取文件并执行

如需**实时网络通信**，可扩展为 TCP/UDP 传输 JSON 数据，协议可后续自定义。

---

## 🚀 使用方法

### 1. 启动机器人端控制程序

将 robot_control.py 保存到机器人主板

在 G1 控制电脑上运行：

```bash
python3 robot_control.py
```

- 程序会初始化 DDS 频道（rt/lowcmd / rt/lowstate）
- 等待 `target_pose.npy` 文件更新后，平滑插值执行姿态

> ⚠️ **安全提示**：请确保机器人周围无障碍物，防止姿态切换时发生碰撞！

---

### 2. 启动 Windows 端 GUI

在 Windows 电脑上运行：

```bash
python windows_gui.py
```

- 鼠标左键拖拽对应关节，滚轮可调整部分关节的额外旋转
- 点击按钮“输出当前关节弧度”即可保存姿态
- 保存时可输入 SSH 地址（如 `unitree@192.168.123.10`）直接上传到机器人

---

### 3. 关节控制说明

- **拖拽控制**：在 3D 模型中直接选中关节部位拖动
- **滚轮调整**：部分关节（如肩、腕、髋、踝、腰）的第三自由度可用滚轮调节
- **限制范围**：每个关节已设置机械极限，超出范围会自动裁剪

---

## 📏 数据格式

- `target_pose.npy`：numpy.float32 数组，长度 29
- 单位：**弧度**
- 顺序：见 `windows_gui.py` 中的 `control_joints` 列表

---

## 🛠 常见问题

- **GUI 启动报 Qt 插件错误**  
  → 已在代码中自动设置 QT_QPA_PLATFORM_PLUGIN_PATH，请确保使用 venv 安装依赖。

- **机器人端无动作**  
  → 检查 `target_pose.npy` 是否已更新到机器人端路径，或直接在终端确认 npy 文件内容。

- **SCP 上传失败**  
  → 确保 Windows 电脑已安装 OpenSSH，并且能免密/输入密码连接 G1 控制电脑。

---

## ⚠️ 安全警告

- 姿态切换过程中请确保机器人周围无障碍物
- 建议先在仿真模式或吊挂保护状态下调试
- **不要一次性切换到危险姿态**（大幅关节弯曲、极限姿态）

---

## 📬 联系与贡献

如有问题或需求，欢迎提 issue 或 PR！
