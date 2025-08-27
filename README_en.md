# Unitree G1 Motion Design & Control GUI

## Overview

This project offers a complete solution for designing and controlling poses for the Unitree G1 humanoid robot. It consists of two main components:

- **Windows GUI**: An interactive 3D visualization tool for designing robot joint poses, which can be exported as pose files.
- **Robot Control Program**: A script that runs on the robot, reads the pose files, smoothly interpolates to target poses, and commands the real robot via the Unitree SDK-2.

The system is ideal for motion design, pose synchronization demonstrations, and remote control experiments.

---

## Project Structure

```
.
├── meshes/                  # 3D robot model files, textures, etc.
├── g1_29dof.urdf            # URDF model for G1 (29 degrees of freedom)
├── target_pose.npy          # Joint angle data file (exported by GUI, in radians)
├── windows_gui.py           # Windows GUI application (PyQt5 + pyqtgraph)
├── robot_control.py         # Robot-side control script (using Unitree SDK-2)
├── requirements.txt         # Python dependencies for Windows
└── README.md
```

---

## Requirements

### Windows Side

- **OS:** Windows 10/11
- **Python:** 3.8 ~ 3.10
- **Dependencies:** Listed in `requirements.txt`
- **Additional:** Download the `meshes` folder from [unitree_rl_gym](https://github.com/unitreerobotics/unitree_rl_gym) and place it next to the GUI code.

Install dependencies:
```sh
pip install -r requirements.txt
```

### Robot Side

- **OS:** Ubuntu 20.04 (recommended for G1 onboard computer)
- **Python:** 3.8 ~ 3.10
- **Dependencies:**
    - Unitree SDK-2 for Python (**install manually, see Unitree docs**)
    - numpy

Install numpy:
```sh
pip install numpy
```

---

## Communication Method

The default synchronization uses a shared file workflow:
1. The GUI saves the target pose as `target_pose.npy`.
2. The file is uploaded to the robot via `scp` to a pre-defined path.
3. The GUI allows SSH address input for automatic upload.
4. The robot-side program monitors the file and executes the pose upon change.

> **Tip:** For real-time networked control, you can extend this to use TCP/UDP and a custom JSON protocol.

---

## Usage

### 1. Start the Robot Control Program

Copy `robot_control.py` to the robot (G1's onboard computer), then run:
```sh
python3 robot_control.py
```
- Initializes DDS channels (`rt/lowcmd`, `rt/lowstate`)
- Waits for updates to `target_pose.npy` and interpolates to the new pose

> **Safety Reminder:** Ensure the robot is in a clear area before switching poses.

### 2. Start the Windows GUI

On your Windows PC, run:
```sh
python windows_gui.py
```
- Use the mouse to drag joints and adjust the 3D model pose
- Use the scroll wheel for extra rotations (shoulder, wrist, hip, ankle, waist third DOF)
- Click "Export current joint radians" to save the pose
- Optionally, enter the robot's SSH address (e.g., `unitree@192.168.123.10`) for direct upload

### 3. Joint Control Notes

- **Drag Control:** Select and drag joints in the 3D model
- **Scroll Adjustment:** For certain joints, use the scroll wheel
- **Range Limits:** Joint angles are clipped to mechanical limits automatically

---

## Data Format

- **target_pose.npy:** 1D numpy float32 array, length 29 (one per joint)
    - **Unit:** radians
    - **Order:** See `control_joints` in `windows_gui.py`

---

## Troubleshooting

- **Qt plugin error when launching GUI:**  
  - The code auto-sets `QT_QPA_PLATFORM_PLUGIN_PATH`. Make sure all dependencies are installed in your Python environment.
- **No motion on robot side:**  
  - Verify that `target_pose.npy` is updated on the robot. Inspect the file's contents if needed.
- **SCP upload failure:**  
  - Ensure OpenSSH is installed on Windows, and confirm you can connect to the G1 robot via SSH.

---

## Safety Warnings

- Always keep the robot’s surroundings clear when switching poses
- Debug in simulation or with a safety harness first
- Avoid switching directly to extreme or mechanically limited poses

---

## Contact & Contributions

Questions, feature requests, or contributions are welcome! Please open an issue or pull request on this repository.
