# extended code from https://github.com/smartdesignworldwide/Technology-Blog-Post-Supplementary-Material
import pyrealsense2 as rs
import mediapipe as mp
import cv2
import numpy as np
import datetime as dt
import pandas as pd
import pickle

RUN_DETECTIONS = False
DRAW_LANDMARKS = True

if RUN_DETECTIONS:
    with open('body_language.pkl', 'rb') as f:
        model = pickle.load(f)

def get_distance(results, landmark_index):
    landmark = results.pose_landmarks.landmark[landmark_index]
    x = int(landmark.x*len(depth_image_flipped[0]))
    y = int(landmark.y*len(depth_image_flipped))
    if x >= len(depth_image_flipped[0]):
        x = len(depth_image_flipped[0]) - 1
    if y >= len(depth_image_flipped):
        y = len(depth_image_flipped) - 1
    return depth_image_flipped[y,x] * depth_scale

def run_posture_detections(results, images):
    # Extract Pose landmarks
    pose = results.pose_landmarks.landmark
    pose_row = list(np.array([[landmark.x, landmark.y, landmark.z, landmark.visibility] for landmark in pose]).flatten())
    
    # Extract Face landmarks
    face = results.face_landmarks.landmark
    face_row = list(np.array([[landmark.x, landmark.y, landmark.z, landmark.visibility] for landmark in face]).flatten())
    
    # Concate rows
    row = pose_row+face_row
    # Make Detections
    X = pd.DataFrame([row])
    body_language_class = model.predict(X)[0]
    body_language_prob = model.predict_proba(X)[0]
    print(body_language_class, body_language_prob)
    prediction_coords = (20, org[1] - 40)
    return cv2.putText(images, body_language_class, prediction_coords, font, fontScale, color, thickness, cv2.LINE_AA)

def draw_landmarks(results, images):
    LANDMARKS_OF_INTEREST = {
        "Nose": 0,
        "lShoulder": 11,
        "rShoulder": 12,
        "lArm": 16, #using wrist as arm indicator
        "rArm": 15, #using wrist as arm indicator
    }

    i = 1
    for name, landmark_id in LANDMARKS_OF_INTEREST.items():
        org_landmarks = (20, org[1]+(20*(i+1)))
        i += 1
        distance = get_distance(results, landmark_id)
        images = cv2.putText(images, f"{name} Distance: {distance:0.3} m away", org_landmarks, font, fontScale, color, thickness, cv2.LINE_AA)
    return images

font = cv2.FONT_HERSHEY_SIMPLEX
org = (20, 100)
fontScale = .5
color = (0,50,255)
thickness = 1

# ====== Realsense ======
realsense_ctx = rs.context()
connected_devices = [] # List of serial numbers for present cameras
for i in range(len(realsense_ctx.devices)):
    detected_camera = realsense_ctx.devices[i].get_info(rs.camera_info.serial_number)
    print(f"{detected_camera}")
    connected_devices.append(detected_camera)
device = connected_devices[0] # In this example we are only using one camera
pipeline = rs.pipeline()
config = rs.config()
background_removed_color = 153 # Grey

# ====== Mediapipe ======
mp_drawing = mp.solutions.drawing_utils # Drawing helpers
mp_holistic = mp.solutions.holistic # Mediapipe Solutions

# ====== Enable Streams ======
config.enable_device(device)

stream_res_x = 640
stream_res_y = 480
stream_fps = 30

config.enable_stream(rs.stream.depth, stream_res_x, stream_res_y, rs.format.z16, stream_fps)
config.enable_stream(rs.stream.color, stream_res_x, stream_res_y, rs.format.bgr8, stream_fps)
profile = pipeline.start(config)

align_to = rs.stream.color
align = rs.align(align_to)

# ====== Get depth Scale ======
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print(f"\tDepth Scale for Camera SN {device} is: {depth_scale}")

# ====== Set clipping distance ======
clipping_distance_in_meters = 2
clipping_distance = clipping_distance_in_meters / depth_scale
print(f"\tConfiguration Successful for SN {device}")

# ====== Get and process images ====== 
print(f"Starting to capture images on SN: {device}")
with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    while True:
        start_time = dt.datetime.today().timestamp()

        # Get and align frames
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        aligned_depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        
        if not aligned_depth_frame or not color_frame:
            continue

        # Process images
        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        depth_image_flipped = cv2.flip(depth_image,1)
        color_image = np.asanyarray(color_frame.get_data())

        depth_image_3d = np.dstack((depth_image,depth_image,depth_image)) #Depth image is 1 channel, while color image is 3
        background_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), background_removed_color, color_image)

        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        images = cv2.flip(background_removed,1)
        color_image = cv2.flip(color_image,1)
        color_images_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

        # Process pose
        results = holistic.process(color_images_rgb)
        if results.face_landmarks and results.pose_landmarks:
            mp_drawing.draw_landmarks(images, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS, 
                                    mp_drawing.DrawingSpec(color=(80,110,10), thickness=1, circle_radius=1),
                                    mp_drawing.DrawingSpec(color=(80,256,121), thickness=1, circle_radius=1)
                                    )

            mp_drawing.draw_landmarks(images, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS, 
                                    mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=4),
                                    mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                                    )
            
            if RUN_DETECTIONS:
                images = run_posture_detections(results, images)

            if DRAW_LANDMARKS:
                images = draw_landmarks(results, images)
            
            images = cv2.putText(images, f"Operator: ", org, font, fontScale, color, thickness, cv2.LINE_AA)
        else:
            images = cv2.putText(images,"No Operator", org, font, fontScale, color, thickness, cv2.LINE_AA)


        # Display FPS
        time_diff = dt.datetime.today().timestamp() - start_time
        fps = int(1 / time_diff)
        org3 = (20, org[1] - 20)
        images = cv2.putText(images, f"FPS: {fps}", org3, font, fontScale, color, thickness, cv2.LINE_AA)

        name_of_window = 'SN: ' + str(device)

        # Display images 
        cv2.namedWindow(name_of_window, cv2.WINDOW_AUTOSIZE)
        cv2.imshow(name_of_window, images)
        key = cv2.waitKey(1)
        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            print(f"User pressed break key for SN: {device}")
            break

print(f"Application Closing")
pipeline.stop()
print(f"Application Closed.")