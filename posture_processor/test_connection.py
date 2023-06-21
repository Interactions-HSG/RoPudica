import pyrealsense2 as rs

realsense_ctx = rs.context()
print(realsense_ctx)
for i in range(len(realsense_ctx.devices)):
    detected_camera = realsense_ctx.devices[i].get_info(rs.camera_info.serial_number)
    print(f"{detected_camera}")
