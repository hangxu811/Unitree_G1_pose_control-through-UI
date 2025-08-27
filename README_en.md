Unitree G1 Motion Design & Control GUI
📖 Overview

This project provides a motion design and synchronized control system for the Unitree G1 humanoid robot, consisting of a Windows GUI and a robot-side control program.

Windows GUI: A 3D visualization interface that allows adjusting joint poses via mouse drag/wheel and saving them as a pose file target_pose.npy.

Robot-side program: Reads the pose file, performs smooth interpolation to the target pose, and controls the real G1 motors through Unitree SDK-2, enabling the robot to replicate the pose designed in the GUI in real time.

Designed for motion design, pose synchronization demos, and remote control experiments.

📂 Project Structure
.
├── meshes                  # Robot model files, textures, etc.
├── g1_29dof.urdf           # G1 robot URDF model (29 DOFs)
├── target_pose.npy         # Joint angle data exported from GUI (radians)
├── windows_gui.py          # Windows-side GUI program (PyQt5 + pyqtgraph)
├── robot_control.py        # Robot-side control program (Unitree SDK-2)
├── requirements.txt        # Dependencies for Windows
└── README.md

💻 Requirements
Windows Side

OS: Windows 10/11

Python: 3.8 ~ 3.10

Dependencies: see requirements.txt

You need to download the meshes folder from unitree_rl_gym
 and place it in the same directory as the GUI code.

pip install -r requirements.txt

Robot Side

OS: Ubuntu 20.04 (recommended to run on G1’s onboard computer)

Python: 3.8 ~ 3.10

Dependencies:

Unitree SDK-2 for Python

numpy

pip install numpy


⚠️ Unitree SDK-2 for Python must be installed manually. Please refer to the official Unitree documentation or repository.

🔌 Communication Method

The current version uses a shared file mechanism for synchronization:

Windows GUI saves target_pose.npy

File is uploaded to the robot via scp into a fixed path

GUI provides a button to enter SSH address and upload automatically

Robot-side program periodically checks the file and executes the pose

If real-time network communication is required, it can be extended to TCP/UDP JSON data transfer with a custom protocol.

🚀 Usage
1. Run the Robot Control Program

Copy robot_control.py to the robot’s onboard computer.

On the G1 control computer, run:

python3 robot_control.py


Initializes DDS channels (rt/lowcmd / rt/lowstate)

Waits for target_pose.npy updates and interpolates to the target pose

⚠️ Safety Note: Ensure the robot is in a safe environment with no obstacles before switching poses.

2. Run the Windows GUI

On your Windows PC, run:

python windows_gui.py


Drag joints in the 3D model with the mouse, use the scroll wheel for some extra rotations

Click “Export current joint radians” to save pose

Optionally input SSH address (e.g., unitree@192.168.123.10) for direct upload to the robot

3. Joint Control Notes

Drag control: Select joints in the 3D model and drag

Scroll adjustment: For some joints (shoulder, wrist, hip, ankle, waist third DOF)

Range limits: Each joint has mechanical limits; angles beyond the range are automatically clipped

📏 Data Format

target_pose.npy: numpy.float32 array, length 29

Unit: radians

Order: defined in windows_gui.py under control_joints list

🛠 Troubleshooting

Qt plugin error when launching GUI
→ The code auto-sets QT_QPA_PLATFORM_PLUGIN_PATH. Ensure dependencies are installed in your venv.

No motion on robot side
→ Check if target_pose.npy is updated on the robot. Inspect the npy file content directly.

SCP upload failure
→ Make sure OpenSSH is installed on Windows and that you can connect to the G1 with/without password.

⚠️ Safety Warnings

Ensure no obstacles around the robot during pose switching

Debug first in simulation or with safety harness support

Do not directly switch to extreme poses (large bends or mechanical limits)

📬 Contact & Contributions

Feel free to open issues or PRs for questions, feature requests, or contributions!
