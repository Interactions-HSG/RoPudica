from time import sleep
from time import time
import keyboard
from xarm.wrapper import XArmAPI
import pyrealsense2 as rs
import mediapipe as mp
import cv2
import numpy as np
from datetime import datetime
import csv
from random import randrange
MAX_SPEED = 150 #300 for high-speed
SPEED_CONVERT = 3
current_speed=50
adaptive=True

def robot_init(arm):
    arm.clean_warn()
    arm.clean_error()
    arm.motion_enable(True)
    arm.set_mode(0)
    arm.set_state(0)

def adjust_to_human(arm, human_distance):
    if not adaptive:
        return False
    TOLERANCE = 50
    MAX_TOLERANCE = 130
    current_pos = arm.get_position(is_radian=False)[1]

    # Don't do any adjustments if the robot arm is not far extended
    if current_pos[0] <= 320:
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
        arm.set_position(x=max(current_pos[0]-move_back_amount, 300), y=current_pos[1], z=current_pos[2], roll=current_pos[3], pitch=current_pos[4], yaw=current_pos[5], is_radian=False, wait=True, speed=current_speed*10)
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
        arm.set_servo_angle(angle=[-104.2, -12.2, -9.5, 48.3, -0.9, 59.8, -114.0], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 2:
        arm.set_servo_angle(angle=[-109.1, 43.9, 4.9, 127.8, 3.0, 84.5, -107.9], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 3:
        arm.set_servo_angle(angle=[-99.1, 65.0, -53.3, 149.0, -89.8, -33.1, 33.7], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 4:
        arm.set_servo_angle(angle=[-131.2, 21.0, -17.8, 89.0, -170.1, -66.6, 32.2], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 5:
        arm.set_servo_angle(angle=[-129.2, 35.9, 23.3, 117.7, -10.7, 84.2, -111.8], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 6:
        arm.set_servo_angle(angle=[-113.2, 38.7, 3.4, 115.1, 1.6, 77.1, -113.3], speed=speed, is_radian=False, wait=False, radius=-1.0)
    else:
        return False
    return True

def execute_episode_two_step(arm, step, speed):
    if step == 1:
        arm.set_servo_angle(angle=[-89.5, 59.6, -1.8, 134.2, 2.7, 72.8, -94.3], speed=speed*0.6, is_radian=False, wait=False, radius=-1.0)
    elif step == 2:
        arm.set_servo_angle(angle=[-59.1, 44.9, -2.0, 110.7, 3.2, 64.1, -63.8], speed=speed*0.6, is_radian=False, wait=False, radius=-1.0)
    elif step == 3:
        arm.set_servo_angle(angle=[-39.1, 28.0, -0.9, 81.9, 4.3, 51.0, -44.3], speed=speed*0.6, is_radian=False, wait=False, radius=-1.0)
    elif step == 4:
        arm.set_position(*[299.5, -5.5, 146.3, 178.4, -4.9, -0.1], speed=speed*7, radius=70.0, is_radian=False, wait=False)
        #arm.set_servo_angle(angle=[-3.5, -35.2, 3.6, 20.5, 0.6, 50.8, -0.7], speed=speed*0.6, is_radian=False, wait=False, radius=-1.0)
    elif step == 5:
        arm.set_servo_angle(angle=[-7.8, -35.5, 7.9, 20.6, 4.0, 50.9, -3.3], speed=speed, is_radian=False, wait=False, radius=-1.0)
        arm.set_gripper_position(549, wait=True, speed=5000, auto_enable=True)
    elif step == 6:
        arm.set_servo_angle(angle=[-4.0, -24.4, 4.4, 14.2, 0.3, 33.5, 0.0], speed=speed, is_radian=False, wait=False, radius=-1.0)
        arm.set_gripper_position(270, wait=False, speed=5000, auto_enable=True)
        arm.set_servo_angle(angle=[-3.9, -36.5, 4.0, 22.0, 1.0, 53.5, -1.1], speed=speed, is_radian=False, wait=False, radius=-1.0)
    else:
        return False
    return True

def execute_episode_three_a_step(arm, step, speed):
    if step == 1:
        arm.set_servo_angle(angle=[-3.9, -36.5, 4.0, 22.0, 1.0, 53.5, -1.1], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 2:
        arm.set_servo_angle(angle=[-25.7, 23.7, -17.3, 88.8, 11.1, 63.6, -48.0], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 3:
        arm.set_servo_angle(angle=[-54.0, 43.5, -12.2, 124.9, 10.0, 80.5, -66.3], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 4:
        arm.set_servo_angle(angle=[-84.0, 42.2, -9.8, 117.9, 11.5, 76.1, -95.5], speed=speed, is_radian=False, wait=False, radius=-1.0)
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
        arm.set_servo_angle(angle=[-2.1, -34.9, 1.6, 64.7, -0.6, 94.6, -0.8], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 2:
        arm.set_servo_angle(angle=[-42.5, -39.7, -22.3, 60.8, -27.6, 50.5, 5.7], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 3:
        arm.set_servo_angle(angle=[-73.9, -19.9, -37.6, 48.9, -12.3, 63.9, -11.8], speed=speed, is_radian=False, wait=False, radius=-1.0)
    elif step == 4:
        arm.set_servo_angle(angle=[-81.2, -4.5, -32.8, 40.1, -1.8, 43.4, -113.6], speed=speed, is_radian=False, wait=True, radius=-1.0)
    elif step == 5:
        arm.set_gripper_position(549, wait=True, speed=5000, auto_enable=True)
        arm.set_servo_angle(angle=[-70.4, -17.9, -39.8, 51.9, -11.2, 65.6, -105.2], speed=speed, is_radian=False, wait=False, radius=-1.0)
    # elif step == 6:
    #     arm.set_servo_angle(angle=[-81.2, -4.5, -32.8, 40.1, -1.8, 43.4, -113.6], speed=speed, is_radian=False, wait=True, radius=-1.0)
    #     arm.set_gripper_position(549, wait=True, speed=5000, auto_enable=True)
    #     arm.set_servo_angle(angle=[-97.0, -14.0, -15.8, 51.9, -2.9, 65.0, -112.2], speed=speed, is_radian=False, wait=True, radius=-1.0)
    #     arm.set_gripper_position(100, wait=True, speed=5000, auto_enable=True)
    else:
        return False
    return True

def new_iteration():
    iterations += 1
    if iterations >= 0:
        adaptive = not adaptive
        iterations = 0
        

CONSECUTIVE_ITERATIONS = 3
iterations = 0

arm = XArmAPI("130.82.171.8", baud_checkset=False)
robot_init(arm)
current_step = 0
current_episode = 1
human_distance = 400
last_measurements = [400,400,400]
input("Press Enter to continue...")
start_time = time()
two_down_move_timer = time()
executed_two = False

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

participant_nr = randrange(100000)

processed_images = 0
with open(str(participant_nr)+'_data.csv', 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Time", "Distance", "Average Distance", "Episode", "Step", "Speed", "X", "Y", "Z", "Pitch", "Yaw", "Roll", "is adaptive?"])
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
            estimated_distance = -1
            if results.pose_landmarks:
                # Process distance
                estimated_distance = process_proxemics(results)-750
                print("Measured: ", estimated_distance)
                #Check for outliers
                if estimated_distance > 200 and estimated_distance < 2000:
                    last_measurements.pop(0)
                    last_measurements.append(estimated_distance)
                    human_distance = np.average(last_measurements)
                print("Average: ", human_distance)
                print("array: ", last_measurements)
            
            # print(time()-start_time)

            # Different timer for adaptive and non-adaptive
            episode_one_timer = 30
            if adaptive:
                episode_one_timer = 20
            if time()-start_time < episode_one_timer:
                current_episode = 1
            elif executed_two == False:
                print("Moving to step two")
                two_down_move_timer = time()
                executed_two = True
                # arm.set_state(4)
                # arm.set_state(0)
                current_episode = 2
                current_step = 0
            
            # Adjust speed
            if not adaptive:
                current_speed = MAX_SPEED
            elif human_distance < 300:
                current_speed = 0.3*MAX_SPEED
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
                    if human_distance > 450 and current_step == 4:
                        current_step = 5
                    # Check if x seconds have elapsed since ending episode 1
                    print(time()-two_down_move_timer)
                    if current_step == 6:
                        episode_two_timer = 5
                        if adaptive:
                            episode_two_timer = 15
                        if time()-two_down_move_timer > episode_two_timer:
                            execute_episode_two_step(arm, current_step, current_speed)
                            if human_distance < 400 and adaptive:
                                current_episode = 4
                            else:
                                current_episode = 3
                            current_step = 0
                        else:
                            current_step = 5
                    elif (execute_episode_two_step(arm, current_step, current_speed) == False) and (current_step != 6):
                        if human_distance < 400:
                            current_episode = 4
                        else:
                            current_episode = 3
                        current_step = 0
                elif current_episode == 3:
                    if execute_episode_three_a_step(arm, current_step, current_speed) == False:
                        iterations += 1
                        input("Press Enter to continue...")
                        if iterations >= CONSECUTIVE_ITERATIONS:
                            adaptive = not adaptive
                            iterations = 0
                        start_time = time()
                        executed_two = False
                        current_step = 0
                        current_episode = 1
                        # exit()
                elif current_episode == 4:
                    if execute_episode_three_b_step(arm, current_step, current_speed) == False:
                        iterations += 1
                        input("Press Enter to continue...")
                        if iterations >= CONSECUTIVE_ITERATIONS:
                            adaptive = not adaptive
                            iterations = 0
                        start_time = time()
                        executed_two = False
                        current_step = 0
                        current_episode = 1
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
            current_pos = arm.get_position(is_radian=False)[1]
            writer.writerow([time(), estimated_distance, human_distance, current_episode, current_step, current_speed, current_pos[0], current_pos[1], current_pos[2], current_pos[3], current_pos[4], current_pos[5], adaptive])
        
