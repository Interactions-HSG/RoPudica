import os
from dotenv import load_dotenv
from flask import Flask, request
import time
import traceback
from xarm import version
from xarm.wrapper import XArmAPI

load_dotenv()
app = Flask(__name__)

ROBOT_IP = os.getenv('ROBOT_IP')

# Speed values
MIN_ANGLE_SPEED = 40
MAX_ANGLE_SPEED = 100

MIN_ANGLE_ACC = 400
MAX_ANGLE_ACC = 800

SPEED_STEPS = 10
START_SPEED = 5     # Can be retrieved from LinkedIn component in the future
ANGLE_SPEED_INCREMENT = (MAX_ANGLE_SPEED-MIN_ANGLE_SPEED)/SPEED_STEPS
ANGLE_ACC_INCREMENT = (MAX_ANGLE_ACC-MIN_ANGLE_ACC)/SPEED_STEPS

class RobotMain(object):
    """Robot Main Class"""

    def __init__(self, robot, **kwargs):
        self.alive = True
        self._arm = robot
        self._tcp_speed = 100
        self._tcp_acc = 2000
        self._angle_speed = 20
        self._angle_acc = 500
        self._vars = {}
        self._funcs = {}
        self._current_speed = 0
        self._speed_adjustment = START_SPEED
        self._robot_init()

    # Robot init
    def _robot_init(self):
        self._arm.clean_warn()
        self._arm.clean_error()
        self._arm.motion_enable(True)
        self._arm.set_mode(0)
        self._arm.set_state(0)
        time.sleep(1)
        self._arm.register_error_warn_changed_callback(
            self._error_warn_changed_callback
        )
        self._arm.register_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, "register_count_changed_callback"):
            self._arm.register_count_changed_callback(self._count_changed_callback)

    # Register error/warn changed callback
    def _error_warn_changed_callback(self, data):
        if data and data["error_code"] != 0:
            self.alive = False
            self.pprint("err={}, quit".format(data["error_code"]))
            self._arm.release_error_warn_changed_callback(
                self._error_warn_changed_callback
            )

    # Register state changed callback
    def _state_changed_callback(self, data):
        if data and data["state"] == 4:
            self.alive = False
            self.pprint("state=4, quit")
            self._arm.release_state_changed_callback(self._state_changed_callback)

    # Register count changed callback
    def _count_changed_callback(self, data):
        if self.is_alive:
            self.pprint("counter val: {}".format(data["count"]))

    def _check_code(self, code, label):
        if not self.is_alive or code != 0:
            self.alive = False
            ret1 = self._arm.get_state()
            ret2 = self._arm.get_err_warn_code()
            self.pprint(
                "{}, code={}, connected={}, state={}, error={}, ret1={}. ret2={}".format(
                    label,
                    code,
                    self._arm.connected,
                    self._arm.state,
                    self._arm.error_code,
                    ret1,
                    ret2,
                )
            )
        return self.is_alive

    @staticmethod
    def pprint(*args, **kwargs):
        try:
            stack_tuple = traceback.extract_stack(limit=2)[0]
            print(
                "[{}][{}] {}".format(
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
                    stack_tuple[1],
                    " ".join(map(str, args)),
                )
            )
        except:
            print(*args, **kwargs)

    @property
    def arm(self):
        return self._arm

    @property
    def VARS(self):
        return self._vars

    @property
    def FUNCS(self):
        return self._funcs

    @property
    def is_alive(self):
        if self.alive and self._arm.connected and self._arm.error_code == 0:
            if self._arm.state == 5:
                cnt = 0
                while self._arm.state == 5 and cnt < 5:
                    cnt += 1
                    time.sleep(0.1)
            return self._arm.state < 4
        else:
            return False

    def adjust_speed(self):
        if self._current_speed != self._speed_adjustment:
            angle_speed = MIN_ANGLE_SPEED + (self._speed_adjustment * ANGLE_SPEED_INCREMENT)
            angle_speed = min([max([angle_speed, MIN_ANGLE_SPEED]), MAX_ANGLE_SPEED])
            self._angle_speed = angle_speed
            angle_acc = MAX_ANGLE_ACC + (self._speed_adjustment * ANGLE_ACC_INCREMENT)
            angle_acc = min([max([angle_acc, MIN_ANGLE_ACC]), MAX_ANGLE_ACC])
            self._angle_acc = angle_acc
            self._current_speed = self._speed_adjustment

    def set_position(self, angle):
        self.adjust_speed()
        return self._arm.set_servo_angle(
            angle=angle,
            speed=self._angle_speed,
            mvacc=self._angle_acc,
            wait=True,
            radius=-1.0,
        )

    def procedure(self):
        code = self.set_position([-83.2, 24.0, -0.5, 66.1, -3.9, 40.3, -84.3])
        if not self._check_code(code, "set_servo_angle"):
            return

        code = self.set_position([-19.3, 4.9, 21.7, 70.7, -2.8, 64.3, 2.7])
        if not self._check_code(code, "set_servo_angle"):
            return

        code = self.set_position([55.7, 19.5, 29.0, 56.9, -17.1, 41.4, 95.7])
        if not self._check_code(code, "set_servo_angle"):
            return

        code = self.set_position([2.1, -79.5, -6.5, -3.1, -7.3, 74.6, 1.9])
        if not self._check_code(code, "set_servo_angle"):
            return

        code = self.set_position([-83.2, 24.0, -0.5, 66.1, -3.9, 40.3, -84.3])
        if not self._check_code(code, "set_servo_angle"):
            return

    def run_iteration(self, repeat=1):
        for i in range(int(repeat)):
            if not self.is_alive:
                break
            self.procedure()

    def set_speed_adjustment(self, speed_adjustment):
        self._speed_adjustment = speed_adjustment

    # Robot Main Run
    def remote_run(self, repeat):
        try:
            # run x iterations
            self.run_iteration(repeat)

        except Exception as e:
            self.pprint("MainException: {}".format(e))
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, "release_count_changed_callback"):
            self._arm.release_count_changed_callback(self._count_changed_callback)


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

@app.route("/speed", methods=["POST"])
def speed():
    multiplier = request.args.get("multiplier", default=0, type=int)
    if multiplier >= 0 and multiplier <= 10:
        robot_main.set_speed_adjustment(multiplier)
        return "Adjusted speed from " + str(robot_main._current_speed) + " to " + str(multiplier)
    else:
        return "Invalid speed adjustment"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port="5000")
