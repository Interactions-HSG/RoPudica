# extended code from https://github.com/smartdesignworldwide/Technology-Blog-Post-Supplementary-Material
import pyrealsense2 as rs
import mediapipe as mp
import cv2
import numpy as np
import datetime as dt
import csv
import os

CLASS_NAME = "sad"

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

# ====== Writing Coordinates to CSV ======
def write_csv(results):
    # Create file if not existing
    if (not os.path.isfile('coords.csv')):
        num_coords = len(results.pose_landmarks.landmark)+len(results.face_landmarks.landmark)
        print(f"Number of coordinates: {num_coords}")
        landmarks = ['class']
        for val in range(1, num_coords+1):
            landmarks += ['x{}'.format(val), 'y{}'.format(val), 'z{}'.format(val), 'v{}'.format(val)]

        with open('coords.csv', mode='w', newline='') as f:
            csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(landmarks)

    # Export coordinates
    try:
        # Extract Pose landmarks
        pose = results.pose_landmarks.landmark
        pose_row = list(np.array([[landmark.x, landmark.y, landmark.z, landmark.visibility] for landmark in pose]).flatten())
        
        # Extract Face landmarks
        face = results.face_landmarks.landmark
        face_row = list(np.array([[landmark.x, landmark.y, landmark.z, landmark.visibility] for landmark in face]).flatten())
        
        # Concate rows
        row = pose_row+face_row
        
        # Append class name 
        row.insert(0, CLASS_NAME)
        
        # Export to CSV
        with open('coords.csv', mode='a', newline='') as f:
            csv_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(row) 
    except:
        pass    


recording = False
# ====== Start Image Stream ======
print(f"Starting to capture images on SN: {device}")
with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
    while True:

        # Get and align frames
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        aligned_depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        
        if not aligned_depth_frame or not color_frame:
            continue

        # Process images
        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        # depth_image_flipped = cv2.flip(depth_image,1)
        color_image = np.asanyarray(color_frame.get_data())

        # depth_image_3d = np.dstack((depth_image,depth_image,depth_image)) #Depth image is 1 channel, while color image is 3
        # background_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), background_removed_color, color_image)

        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)

        # images = cv2.flip(background_removed,1)
        color_image = cv2.flip(color_image,1)
        color_images_rgb = cv2.cvtColor(color_image, cv2.COLOR_BGR2RGB)

        # Process pose
        results = holistic.process(color_image)
        # results = pose.process(color_images_rgb)
        if results.face_landmarks and results.pose_landmarks:
            if recording:
                write_csv(results)

            # 1. Draw face landmarks
            mp_drawing.draw_landmarks(color_image, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS, 
                                    mp_drawing.DrawingSpec(color=(80,110,10), thickness=1, circle_radius=1),
                                    mp_drawing.DrawingSpec(color=(80,256,121), thickness=1, circle_radius=1)
                                    )

            # 4. Pose Detections
            mp_drawing.draw_landmarks(color_image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS, 
                                    mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=4),
                                    mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                                    )
            
        # Display images 
        name_of_window = 'SN: ' + str(device)
        cv2.namedWindow(name_of_window, cv2.WINDOW_AUTOSIZE)
        cv2.imshow(name_of_window, color_image)

        # Press esc or 'q' to close the image window
        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.waitKey(1) == 27:
            print(f"User pressed break key for SN: {device}")
            break
        if cv2.waitKey(1) & 0xFF == ord('r'):
            recording = not recording
            print(f"Recording: {recording}")

print(f"Application Closing")
pipeline.stop()
cv2.destroyAllWindows()
print(f"Application Closed.")