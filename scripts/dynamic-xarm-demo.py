from time import sleep
import keyboard
from xarm.wrapper import XArmAPI
import pyrealsense2 as rs
import mediapipe as mp
import cv2
import numpy as np
from datetime import datetime
MAX_SPEED = 200
current_speed=50

def robot_init(arm):
    arm.clean_warn()
    arm.clean_error()
    arm.motion_enable(True)
    arm.set_mode(0)
    arm.set_state(0)

def adjust_to_human(arm, human_distance):
    TOLERANCE = 50
    MAX_TOLERANCE = 130
    current_pos = arm.get_position(is_radian=False)[1]

    # Don't do any adjustments if the robot arm is not far extended
    if current_pos[0] <= 300:
        return False
    absolute_distance = human_distance - current_pos[0]
    if absolute_distance < TOLERANCE:
        print("Too close to the robot: ", absolute_distance)
        # Stop and resume
        arm.set_state(4)
        arm.set_state(0)
        # Move a bit further back to avoid too many adjustments
        move_back_amount = TOLERANCE - absolute_distance + 30
        print("Moving robot x to: ", current_pos[0]-move_back_amount)
        arm.set_position(x=current_pos[0]-move_back_amount, y=current_pos[1], z=current_pos[2], roll=current_pos[3], pitch=current_pos[4], yaw=current_pos[5], is_radian=False, wait=True, speed=current_speed)
        return True
    # if absolute_distance > MAX_TOLERANCE:
    #     print("Too far from the robot: ", absolute_distance)
    #     # Stop and resume
    #     arm.set_state(4)
    #     arm.set_state(0)
    #     # Move a bit further back to avoid too many adjustments
    #     move_forward_amount = absolute_distance - 80
    #     new_x = min(current_pos[0]+move_forward_amount, 400)
    #     print("Moving robot x to: ", new_x)
    #     arm.set_position(x=new_x, y=current_pos[1], z=current_pos[2], roll=current_pos[3], pitch=current_pos[4], yaw=current_pos[5], is_radian=False, wait=True, speed=current_speed)
    #     return True
    return False

# Returns True if the curren episode is still running
def execute_episode_one_step(arm, step, speed):
    if step == 1:
        arm.set_servo_angle(angle=[-104.2, -12.2, -9.5, 48.3, -0.9, 59.8, -114], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 2:
        arm.set_servo_angle(angle=[-114.5, 48.2, 12.7, 109.1, -3.4, 62.2, -106.4], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 3:
        arm.set_servo_angle(angle=[-98.5, 72.6, -45.5, 140.3, -87.7, -33.4, 22.1], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 4:
        arm.set_servo_angle(angle=[-117.6, 68.7, -46.4, 137.2, -135.6, -81, 32.2], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 5:
        arm.set_servo_angle(angle=[-140.1, 41.4, 36.1, 101.2, -21.9, 67.5, -105.5], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 6:
        arm.set_servo_angle(angle=[-109.8, 61.1, 2.3, 141.8, 1.6, 80.3, -112.6], speed=speed, is_radian=False, wait=False, radius=-1.0)
    else:
        return False
    return True

def execute_episode_two_step(arm, step, speed):
    if step == 1:
        arm.set_position(*[1.4, -714.6, 87.8, 178.1, -0.9, 3.2], speed=speed*3, radius=70.0, is_radian=False, wait=False)
    elif step == 2:
        arm.set_position(*[337.3, -581.7, 101.7, 179.1, -2.1, 2.0], speed=speed*3, radius=70.0, is_radian=False, wait=False)
    elif step == 3:
        arm.set_position(*[464.8, -373.4, 97.4, -179.8, -4.2, 1.8], speed=speed*3, radius=70.0, is_radian=False, wait=False)
    elif step == 4:
        arm.set_position(*[299.5, -5.5, 146.3, 178.4, -4.9, -0.1], speed=speed*3, radius=70.0, is_radian=False, wait=False)
    elif step == 5:
        arm.set_servo_angle(angle=[-7.1, -15.0, 7.8, 12.3, 0.8, 22.2, -0.1], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 6:
        arm.set_servo_angle(angle=[-3.9, -36.5, 4.0, 22.0, 1.0, 53.5, -1.1], speed=speed, is_radian=False, wait=False, radius=-1.0)
    else:
        return False
    return True

def execute_episode_three_a_step(arm, step, speed):
    if step == 1:
        arm.set_position(*[299.5, -5.5, 146.3, 178.4, -4.9, -0.1], speed=speed*3, radius=20.0, is_radian=False, wait=False)
    elif step == 2:
        arm.set_position(*[464.8, -373.4, 97.4, -179.8, -4.2, 1.8], speed=speed*3, radius=20.0, is_radian=False, wait=False)
    elif step == 3:
        arm.set_position(*[337.3, -581.7, 101.7, 179.1, -2.1, 2.0], speed=speed*3, radius=20.0, is_radian=False, wait=False)
    elif step == 4:
        arm.set_position(*[1.4, -714.6, 87.8, 178.1, -0.9, 3.2], speed=speed*3, radius=20.0, is_radian=False, wait=False)
    elif step == 5:
        arm.set_servo_angle(angle=[-97.0, -14.0, -15.8, 51.9, -2.9, 65.0, -112.2], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 6:
        arm.set_servo_angle(angle=[-81.2, -4.5, -32.8, 40.1, -1.8, 43.4, -113.6], speed=speed, is_radian=False, wait=True, radius=-1.0)
        arm.set_gripper_position(549, wait=True, speed=5000, auto_enable=True)
        arm.set_servo_angle(angle=[-97.0, -14.0, -15.8, 51.9, -2.9, 65.0, -112.2], speed=speed, is_radian=False, wait=True, radius=-1.0)
        arm.set_gripper_position(100, wait=True, speed=5000, auto_enable=True)
    else:
        return False
    return True

def execute_episode_three_b_step(arm, step, speed):
    if step == 1:
        arm.set_position(*[51.0, 426.1, 117.7, -179.7, -5.8, 0.9], speed=speed*3, radius=20.0, is_radian=False, wait=False)
    elif step == 2:
        arm.set_position(*[-311.2, 317.5, 112.7, 178.5, 2.8, 3.0], speed=speed*3, radius=20.0, is_radian=False, wait=False)
    elif step == 3:
        arm.set_position(*[-405.9, -158.8, 111.7, -179.5, 1.7, 1.6], speed=speed*3, radius=20.0, is_radian=False, wait=False)
    elif step == 4:
        arm.set_position(*[-260.1, -440.7, 158.9, 178.7, -0.6, 1.4], speed=speed*3, radius=20.0, is_radian=False, wait=False)
    elif step == 5:
        arm.set_position(*[-260.1, -440.7, 73.5, 178.7, -0.6, 1.4], speed=speed*3, radius=20.0, is_radian=False, wait=False)
        arm.set_gripper_position(549, wait=True, speed=5000, auto_enable=True)
        arm.set_position(*[-260.1, -440.7, 158.9, 178.7, -0.6, 1.4], speed=speed*3, radius=20.0, is_radian=False, wait=False)
        arm.set_gripper_position(100, wait=True, speed=5000, auto_enable=True)
    else:
        return False
    return True

arm = XArmAPI("130.82.171.8", baud_checkset=False)
robot_init(arm)
current_step = 0
current_episode = 1
human_distance = 1000

## Initialize Cam

CONSIDER_ROBOT_POSITION = True
CAMERA_OFFSET = 600  # mm the camera is offset from the robot
ROBOT_POSITION_REQUEST_OFFSET = (
    1  # Number of frames to wait before requesting robot position
)

def get_landmark_distance(results, landmark_index):
    landmark = results.pose_landmarks.landmark[landmark_index]
    x = int(landmark.x * len(depth_image_flipped[0]))
    y = int(landmark.y * len(depth_image_flipped))
    if x >= len(depth_image_flipped[0]):
        x = len(depth_image_flipped[0]) - 1
    if y >= len(depth_image_flipped):
        y = len(depth_image_flipped) - 1
    return depth_image_flipped[y, x] * depth_scale

def process_proxemics(results):
    lShoulder_distance = get_landmark_distance(results, 11)
    rShoulder_distance = get_landmark_distance(results, 12)
    operator_distance = (
        lShoulder_distance + rShoulder_distance
    ) / 2  # middle of shoulders
    operator_distance = operator_distance * 1000  # convert to mm

    return operator_distance - CAMERA_OFFSET


font = cv2.FONT_HERSHEY_SIMPLEX
org = (20, 100)
fontScale = 0.5
color = (0, 50, 255)
thickness = 1

# ====== Realsense ======
realsense_ctx = rs.context()
connected_devices = []  # List of serial numbers for present cameras
for i in range(len(realsense_ctx.devices)):
    detected_camera = realsense_ctx.devices[i].get_info(rs.camera_info.serial_number)
    print(f"{detected_camera}")
    connected_devices.append(detected_camera)
device = connected_devices[0]  # In this example we are only using one camera
pipeline = rs.pipeline()
config = rs.config()
background_removed_color = 153  # Grey

# ====== Mediapipe ======
mp_drawing = mp.solutions.drawing_utils  # Drawing helpers
mp_holistic = mp.solutions.holistic  # Mediapipe Solutions

# ====== Enable Streams ======
config.enable_device(device)

stream_res_x = 640
stream_res_y = 480
stream_fps = 30

config.enable_stream(
    rs.stream.depth, stream_res_x, stream_res_y, rs.format.z16, stream_fps
)
config.enable_stream(
    rs.stream.color, stream_res_x, stream_res_y, rs.format.bgr8, stream_fps
)
profile = pipeline.start(config)

align_to = rs.stream.color
align = rs.align(align_to)

# ====== Get depth Scale ======
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print(f"\tDepth Scale for Camera SN {device} is: {depth_scale}")

# ====== Set clipping distance ======
clipping_distance_in_meters = 3
clipping_distance = clipping_distance_in_meters / depth_scale
print(f"\tConfiguration Successful for SN {device}")

# ====== Get and process images ======
print(f"Starting to capture images on SN: {device}")
processed_images = 0
with mp_holistic.Holistic(
    min_detection_confidence=0.5, min_tracking_confidence=0.5
) as holistic:
    while True:
        # Calculate Distance
        # Get and align frames
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        aligned_depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not aligned_depth_frame or not color_frame:
            continue

        # Process images
        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        depth_image_flipped = cv2.flip(depth_image, 1)
        color_image = np.asanyarray(color_frame.get_data())
        color_image = cv2.flip(color_image, 1)
        color_images_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

        # Process pose
        results = holistic.process(color_images_rgb)
        if results.face_landmarks and results.pose_landmarks:
            # Process distance
            human_distance = process_proxemics(results)-750
            print(human_distance)
        
        # Adjust speed
        if human_distance < 300:
            current_speed = 0.2*MAX_SPEED
        elif human_distance < 600:
            current_speed = 0.5*MAX_SPEED
        elif human_distance < 1000:
            current_speed = 0.8*MAX_SPEED
        else:
            current_speed = MAX_SPEED
        
        if arm.get_is_moving() == False:
            current_step += 1
            print("Executing episode ", current_episode, ", step ", current_step)
            if current_episode == 1:
                if execute_episode_one_step(arm, current_step, current_speed) == False:
                    current_episode = 2
                    current_step = 0
            elif current_episode == 2:
                if execute_episode_two_step(arm, current_step, current_speed) == False:
                    if human_distance < 400:
                        current_episode = 4
                    else:
                        current_episode = 3
                    current_step = 0
            elif current_episode == 3:
                if execute_episode_three_a_step(arm, current_step, current_speed) == False:
                    current_step = 0
                    current_episode = 1
                    # exit()
            elif current_episode == 4:
                if execute_episode_three_b_step(arm, current_step, current_speed) == False:
                    current_step = 0
                    current_episode = 1
                    # exit()
        if keyboard.is_pressed("w"):
            # move closer to robotd
            human_distance -= 60
            print("Current Distance: ", human_distance)
            sleep(0.2)
        if keyboard.is_pressed("s"):
            # move further away from robot
            human_distance += 60
            print("Current Distance: ", human_distance)
            sleep(0.2)
        if keyboard.is_pressed("a"):
            # Decrease speed
            current_speed -= 60
            print("Decreasing speed to : ", current_speed)
            sleep(0.2)
        if keyboard.is_pressed("d"):
            # Increase speed
            current_speed += 60
            print("Increasing speed to : ", current_speed)
            sleep(0.2)
        if adjust_to_human(arm,human_distance):
            if current_episode == 3 and current_step == 2:
                current_step = current_step
            elif current_episode == 3 and current_step == 3:
                current_step = 3
            elif current_episode == 2 and current_step == 2:
                current_step = 3
            elif current_episode == 2 and current_step == 3:
                current_step = 3
            else:
                current_step -= 1
        if keyboard.is_pressed("q"):
            # Key was pressed
            break
        