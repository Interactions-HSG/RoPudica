import random
from robot_utils import set_gripper, set_position 

# Function to execute a random greeting action from the list
def greeting(robot):
    set_of_actions = [winken]
    execute_random_action(robot, set_of_actions)

# Function to execute a random episodic action from the list
def episodic_action(robot):
    set_of_actions = [troete]
    execute_random_action(robot, set_of_actions)

def execute_random_action(robot, actions):
    action_to_execute = random.choice(actions)
    action_to_execute(robot)

def winken(robot):
    try:
        set_gripper(robot, 50, 5000)
        set_position(robot, [-83.2, 24.0, -0.5, 66.1, -3.9, 40.3, -84.3], wait=False)
        set_position(robot, [-130.8, -1.8, 39.4, 86.2, 181.4, 91.5, -81.2], wait=True)
        
        robot.set_angle_values(100, 800)
        
        for i in range(random.randint(3, 7)):
            set_position(robot, [-131.0, -1.8, 39.4, 86.2, 177.3, 57.4, -81.2], wait=False)
            set_position(robot, [-130.9, -1.8, 43.0, 86.0, 188.8, 128.0, -81.2], wait=False)

    except Exception as e:
        robot.pprint('MainException: {}'.format(e))

def troete(robot):
    try:
        robot.set_angle_values(60)

        set_position(robot, [-215.2, -32.1, 31.7, 37.0, 13.6, 64.7, -195.6], wait=False)
        set_gripper(robot, 700, 5000)
        set_position(robot, [-141.5, -26.3, -39.6, 31.3, -20.8, 55.2, -164.5])
        set_gripper(robot, 400, 1000)
        set_position(robot, [-141.9, -11.4, 14.2, 55.4, 5.1, 67.0, -130.1], wait=False)
        set_position(robot, [-141.4, -11.3, 65.4, 44.4, 104.3, 87.8, -129.4])
        
        for i in range(int(3)):
            set_gripper(robot, 50, 5000)
            set_gripper(robot, 400, 1000)
            
        set_position(robot, [-215.2, -32.1, 31.7, 37.0, 13.6, 64.7, -195.6], wait=False)
        set_position(robot, [-141.5, -26.3, -39.6, 31.3, -20.8, 55.2, -164.5], wait=False)
        set_gripper(robot, 700, 5000)
        
    except Exception as e:
        robot.pprint('MainException: {}'.format(e))
    