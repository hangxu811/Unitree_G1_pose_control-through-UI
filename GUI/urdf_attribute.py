from yourdfpy import URDF

robot = URDF.load("g1_29dof.urdf")
print("Attributes on URDF:", dir(robot))
print(robot.joint_names)
print(robot.link_map.keys())
