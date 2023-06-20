import os
from dotenv import load_dotenv
from flask import Flask, request
from xarm import version
from xarm.wrapper import XArmAPI
from special_movements import greeting, episodic_action
from robot import RobotMain

load_dotenv()
app = Flask(__name__)

ROBOT_IP = os.getenv("ROBOT_IP")
RobotMain.pprint("xArm-Python-SDK Version:{}".format(version.__version__))
arm = XArmAPI(ROBOT_IP, baud_checkset=False)
robot_main = RobotMain(arm)


@app.route("/run", methods=["POST"])
def run_robot():
    iterations = request.args.get("iterations", default=1, type=int)
    robot_main.remote_run(iterations)
    return "Started running the robot!"


@app.route("/stop", methods=["POST"])
def stop_robot():
    robot_main._arm.emergency_stop()
    return "Emergency stopped the robot!"


@app.route("/position", methods=["GET"])
def get_robot_position():
    position = robot_main._arm.get_position()[1]
    return {"x": position[0], "y": position[1], "z": position[2]}


@app.route("/extension", methods=["GET"])
def get_extension():
    return {"x": robot_main.get_max_x_extension()}


@app.route("/episodic_behaviour", methods=["POST"])
def episodic_behaviour():
    robot_main._episodic_trigger = True
    return "Will mix it up"


@app.route("/speed", methods=["POST"])
def speed():
    multiplier = request.args.get("multiplier", default=0, type=int)
    if multiplier >= 0 and multiplier <= 10:
        robot_main._speed_adjustment = multiplier
        return (
            "Adjusted speed from "
            + str(robot_main._current_speed)
            + " to "
            + str(multiplier)
        )
    else:
        return "Invalid speed adjustment"


@app.route("/increase_speed", methods=["POST"])
def increase_speed():
    current = robot_main._current_speed
    new = min(current + 1, 10)
    robot_main._speed_adjustment = new
    return "Increased speed from " + str(current) + " to " + str(new)


@app.route("/decrease_speed", methods=["POST"])
def decrease_speed():
    current = robot_main._current_speed
    new = max(current - 1, 1)
    robot_main._speed_adjustment = new
    return "Decreased speed from " + str(current) + " to " + str(new)


@app.route("/proxemics", methods=["POST"])
def proxemics():
    multiplier = request.args.get("multiplier", default=0, type=int)
    if multiplier >= 1 and multiplier <= 10:
        changes = robot_main.adjust_proxemics(multiplier)
        return (
            "Adjusted speed from " + str(changes["old"]) + " to " + str(changes["new"])
        )
    else:
        return "Invalid speed adjustment"


@app.route("/increase_proxemics", methods=["POST"])
def increase_proxemics():
    current = robot_main._current_proxemics
    changes = robot_main.adjust_proxemics(min(current + 1, 10))
    return "Increased speed from " + str(changes["old"]) + " to " + str(changes["new"])


@app.route("/decrease_proxemics", methods=["POST"])
def decrease_proxemics():
    current = robot_main._current_proxemics
    changes = robot_main.adjust_proxemics(max(current - 1, 1))
    return "Increased speed from " + str(changes["old"]) + " to " + str(changes["new"])


@app.route("/add_rotations", methods=["POST"])
def add_rotations():
    robot_main._additional_rotations = True
    return "Added additional rotations"


@app.route("/remove_rotations", methods=["POST"])
def remove_rotations():
    robot_main._additional_rotations = False
    return "Removed additional rotations"


@app.route("/add_smoothness", methods=["POST"])
def add_smoothness():
    robot_main._smooth = True
    return "Added smoothness"


@app.route("/remove_smoothness", methods=["POST"])
def remove_smoothness():
    robot_main._smooth = False
    return "Removed smoothness"


@app.route("/initialize_robot_params", methods=["POST"])
def initialize_robot_params():
    if request.json:
        robot_main.initialize_params(request.json)
        return "Initialized the robot params"
    return "There was no json in the request"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="5000")
