import os
from flask import Flask, request
from flask_cors import CORS
from xarm import version
from xarm.wrapper import XArmAPI
from robot import RobotMain

app = Flask(__name__)
CORS(app)

ROBOT_IP = "130.82.171.8"
RobotMain.pprint("xArm-Python-SDK Version:{}".format(version.__version__))
arm = XArmAPI(ROBOT_IP, baud_checkset=False)
robot_main = RobotMain(arm)


@app.route("/run", methods=["POST"])
def run_robot():
    iterations = request.args.get("iterations", default=1, type=int)
    robot_main.remote_run(iterations)
    return "Started running the robot!"


@app.route("/stop", methods=["POST", "GET"])
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
    current = robot_main._speed_adjustment
    robot_main._speed_adjustment = min(current + 1, 10)
    return "Increased speed"


@app.route("/decrease_speed", methods=["POST"])
def decrease_speed():
    current = robot_main._speed_adjustment
    robot_main._speed_adjustment = max(current - 1, 1)
    return "Decreased speed"


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
    if robot_main._current_speed >= 6:
        robot_main._smooth = False
        robot_main._additional_rotations = True
        return "Added additional rotations"
    return "Speed is too low to add additional rotations"


@app.route("/remove_rotations", methods=["POST"])
def remove_rotations():
    robot_main._additional_rotations = False
    return "Removed additional rotations"


@app.route("/add_smoothness", methods=["POST"])
def add_smoothness():
    if robot_main._current_speed <= 5 and not robot_main._smooth:
        robot_main._additional_rotations = False
        decrease_speed()
        robot_main._smooth = True
        return "Added smoothness"
    return "Speed is too high to add smoothness or smoothness is already added"


@app.route("/remove_smoothness", methods=["POST"])
def remove_smoothness():
    robot_main._smooth = False
    increase_speed()
    return "Removed smoothness"


@app.route("/initialize_robot_params", methods=["POST"])
def initialize_robot_params():
    if request.json:
        robot_main.initialize_params(request.json)
        return "Initialized the robot params"
    return "There was no json in the request"


@app.route("/params", methods=["GET"])
def get_params():
    if robot_main.is_param_init:
        return {
            "speed_adjustment": robot_main._speed_adjustment,
            "current_speed": robot_main._current_speed,
            "proxemics": robot_main._current_proxemics,
            "rotations": robot_main._additional_rotations,
            "smoothness": robot_main._smooth,
        }
    return dict.fromkeys(
        [
            "speed_adjustment",
            "current_speed",
            "proxemics",
            "rotations",
            "smoothness",
        ],
        0,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="5000")
