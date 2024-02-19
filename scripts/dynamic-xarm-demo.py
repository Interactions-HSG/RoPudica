from time import sleep
import keyboard
from xarm.wrapper import XArmAPI

current_speed=100

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
        return current_pos[0]-move_back_amount
    if absolute_distance > MAX_TOLERANCE:
        print("Too far from the robot: ", absolute_distance)
        # Stop and resume
        arm.set_state(4)
        arm.set_state(0)
        # Move a bit further back to avoid too many adjustments
        move_forward_amount = absolute_distance - 80
        new_x = min(current_pos[0]+move_forward_amount, 400)
        print("Moving robot x to: ", new_x)
        arm.set_position(x=new_x, y=current_pos[1], z=current_pos[2], roll=current_pos[3], pitch=current_pos[4], yaw=current_pos[5], is_radian=False, wait=True, speed=current_speed)
        return new_x
    return 0

def move_arm(arm, pos, target_x):
    if pos == 1:
        arm.set_position(x=target_x, y=-350, z=220, roll=180, pitch=0, yaw=0, is_radian=False, wait=False, speed=current_speed)
    if pos == 2:
        arm.set_position(x=target_x, y=350, z=220, roll=180, pitch=0, yaw=0, is_radian=False, wait=False, speed=current_speed)

arm = XArmAPI("130.82.171.8", baud_checkset=False)
robot_init(arm)
arm.set_position(x=400, y=350, z=220, roll=180, pitch=0, yaw=0, is_radian=False, wait=True, speed=current_speed)
last_position = 1
print(arm.get_position(is_radian=False)[1][1])
human_distance = 500
target_x = 400
while True:
    if arm.get_position(is_radian=False)[1][1] > 340:
        move_arm(arm, 1, target_x)
        last_position = 1
    elif arm.get_position(is_radian=False)[1][1] < -340:
        move_arm(arm, 2, target_x)
        last_position = 2
    if keyboard.is_pressed("w"):
        # move closer to robot
        human_distance -= 10
        print("Current Distance: ", human_distance)
        sleep(0.2)
    if keyboard.is_pressed("s"):
        # move further away from robot
        human_distance += 10
        print("Current Distance: ", human_distance)
        sleep(0.2)
    if keyboard.is_pressed("a"):
        # Decrease speed
        current_speed -= 30
        print("Decreasing speed to : ", current_speed)
        sleep(0.2)
    if keyboard.is_pressed("d"):
        # Increase speed
        current_speed += 30
        print("Increasing speed to : ", current_speed)
        sleep(0.2)
    r = adjust_to_human(arm,human_distance)
    if r != 0:
        target_x = r
    if arm.get_is_moving() == False:
        move_arm(arm, last_position, target_x)
    if keyboard.is_pressed("q"):
        # Key was pressed
        break
        