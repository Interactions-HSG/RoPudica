import os
from dotenv import load_dotenv
from flask import Flask, request
from xarm import version
from xarm.wrapper import XArmAPI
from special_movements import greeting, episodic_action
from robot import RobotMain

load_dotenv()
app = Flask(__name__)

ROBOT_IP = os.getenv('ROBOT_IP')
RobotMain.pprint("xArm-Python-SDK Version:{}".format(version.__version__))
arm = XArmAPI(ROBOT_IP, baud_checkset=False)
robot_main = RobotMain(arm)

@app.route("/run", methods=["POST"])
def run_robot():
    iterations = request.args.get("iterations", default=1, type=int)
    robot_main.remote_run(iterations)
    return "Started running the robot!"

@app.route("/fast", methods=["POST"])
def fast():
    robot_main.set_speed_adjustment(10)
    return "I am speed!"

@app.route("/slow", methods=["POST"])
def slow():
    robot_main.set_speed_adjustment(0)
    return "I am slooooow!"

@app.route("/stop", methods=["POST"])
def stop_robot():
    robot_main._arm.emergency_stop()
    return "Emergency stopped the robot!"

@app.route("/position", methods=["GET"])
def get_robot_position():
    position = robot_main._arm.get_position()[1]
    return {"x": position[0], "y": position[1], "z": position[2]}

@app.route("/episodic_behaviour", methods=["POST"])
def episodic_behaviour():
    robot_main._episodic_trigger = True
    return "Will mix it up"

@app.route("/speed", methods=["POST"])
def speed():
    multiplier = request.args.get("multiplier", default=0, type=int)
    if multiplier >= 0 and multiplier <= 10:
        robot_main._speed_adjustment = multiplier
        return "Adjusted speed from " + str(robot_main._current_speed) + " to " + str(multiplier)
    else:
        return "Invalid speed adjustment"

@app.route("/proxemics", methods=["POST"])
def proxemics():
    multiplier = request.args.get("multiplier", default=0, type=int)
    if multiplier >= 0 and multiplier <= 10:
        changes = robot_main.adjust_proxemics(multiplier)
        return "Adjusted speed from " + str(changes["old"]) + " to " + str(changes["new"])
    else:
        return "Invalid speed adjustment"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="5000")
