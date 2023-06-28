import time
import traceback
from robot_utils import set_position
from special_movements import greeting, episodic_action

# Speed values
MIN_ANGLE_SPEED = 40
MAX_ANGLE_SPEED = 150

MIN_ANGLE_ACC = 100
MAX_ANGLE_ACC = 1000

SPEED_STEPS = 10
ANGLE_SPEED_INCREMENT = (MAX_ANGLE_SPEED - MIN_ANGLE_SPEED) / SPEED_STEPS
ANGLE_ACC_INCREMENT = (MAX_ANGLE_ACC - MIN_ANGLE_ACC) / SPEED_STEPS

PROXEMICS_ANGLES = [
    {"angles": [-0.8, -25.9, -1.0, 0.2, -0.5, -69.4, -2.0], "x_extension": 400},
    {"angles": [-0.7, -12.2, -0.6, 10.9, 0.0, -72.4, -1.9], "x_extension": 455},
    {"angles": [-0.6, -2.1, -0.4, 21.7, 0.3, -71.6, -1.9], "x_extension": 511},
    {"angles": [-0.4, 6.3, -0.4, 32.7, 0.5, -69.2, -2.0], "x_extension": 566},
    {"angles": [-0.3, 14.3, -0.4, 44.3, 0.7, -65.5, -2.0], "x_extension": 622},
    {"angles": [-0.1, 22.2, -0.6, 56.7, 0.8, -61.0, -2.0], "x_extension": 677},
    {"angles": [0.1, 30.4, -0.7, 70.3, 1.0, -55.6, -2.1], "x_extension": 733},
    {"angles": [0.3, 39.5, -0.9, 85.9, 1.1, -49.1, -2.0], "x_extension": 788},
    {"angles": [0.4, 50.5, -1.3, 105.4, 1.4, -40.5, -1.9], "x_extension": 844},
    {"angles": [0.4, 68.0, -2.3, 137.4, 2.4, -26.1, -1.9], "x_extension": 900},
]


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
        self._speed_reactive = True
        self._current_speed = 0
        self.is_param_init = False
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

    def initialize_params(self, params: dict):
        self._speed_adjustment = params["speed"]
        self._current_proxemics = params["proxemics"]
        self._additional_rotations = params["rotation"]
        self._smooth = params["smoothness"]
        self._episodic_trigger = False
        self.is_param_init = True

    def get_max_x_extension(self):
        if hasattr(self, "_current_proxemics"):
            return PROXEMICS_ANGLES[self._current_proxemics - 1]["x_extension"]
        return PROXEMICS_ANGLES[0]["x_extension"]

    def set_angle_values(self, angle_speed=None, angle_acc=None):
        if angle_speed is not None:
            self._angle_speed = angle_speed
        if angle_acc is not None:
            self._angle_acc = angle_acc

    def adjust_speed(self):
        if self._current_speed != self._speed_adjustment:
            angle_speed = MIN_ANGLE_SPEED + (
                self._speed_adjustment * ANGLE_SPEED_INCREMENT
            )
            angle_speed = min([max([angle_speed, MIN_ANGLE_SPEED]), MAX_ANGLE_SPEED])
            angle_acc = MAX_ANGLE_ACC + (self._speed_adjustment * ANGLE_ACC_INCREMENT)
            angle_acc = min([max([angle_acc, MIN_ANGLE_ACC]), MAX_ANGLE_ACC])
            self.set_angle_values(angle_speed, angle_acc)
            self._current_speed = self._speed_adjustment

    def adjust_proxemics(self, new_proxemics):
        if self._current_proxemics == new_proxemics:
            return {"old": self._current_proxemics, "new": new_proxemics}
        old = self._current_proxemics
        self._current_proxemics = new_proxemics
        return {"old": old, "new": new_proxemics}

    def procedure(self):
        set_position(self, [-83.2, 24.0, -0.5, 66.1, -3.9, 40.3, -84.3])
        set_position(self, PROXEMICS_ANGLES[self._current_proxemics - 1]["angles"])
        set_position(self, [55.7, 19.5, 29.0, 56.9, -17.1, 41.4, 95.7])
        set_position(self, [2.1, -79.5, -6.5, -3.1, -7.3, 74.6, 1.9])
        set_position(self, [-83.2, 24.0, -0.5, 66.1, -3.9, 40.3, -84.3])

    def new_procedure(self):
        set_position(self, [-83.2, 24, -0.5, 66.1, -3.9, 40.3, -84.3])

        if self._additional_rotations:
            # additional waypoint for rotation
            set_position(
                self, [-19.1, -0.1, -27.3, 40.5, -125.6, 62.5, 54.3], wait=False
            )

        set_position(self, PROXEMICS_ANGLES[self._current_proxemics - 1]["angles"])

        if self._additional_rotations:
            # additional waypoint for rotation
            set_position(self, [3.9, -21, 40.5, 26, 129.7, 69.6, -50.8], wait=False)

        set_position(self, [42.1, 9.7, 34.2, 55.1, -11.8, 47, 80.3])
        set_position(self, [26.9, -33.2, 13.9, 15.5, 7.6, 45.7, 29.9])
        set_position(self, [-18.8, -26.5, -29.7, 22.1, -15.2, 44.1, -38.9])
        set_position(self, [-83.2, 24, -0.5, 66.1, -3.9, 40.3, -84.3])

    def run_iteration(self, repeat=1):
        for i in range(int(repeat)):
            if not self.is_alive:
                break

            self.new_procedure()

            if self._episodic_trigger:
                angle_speed, angle_acc = self._angle_speed, self._angle_acc
                episodic_action(self)
                self._episodic_trigger = False
                self.set_angle_values(angle_speed, angle_acc)

    # Robot Main Run
    def remote_run(self, repeat):
        if not self.is_param_init:
            return "Unable to start robot because parameters have not been initialized."
        try:
            greeting(self)
            # run x iterations
            self.run_iteration(repeat)

        except Exception as e:
            self.pprint("MainException: {}".format(e))
        self._arm.release_error_warn_changed_callback(self._error_warn_changed_callback)
        self._arm.release_state_changed_callback(self._state_changed_callback)
        if hasattr(self._arm, "release_count_changed_callback"):
            self._arm.release_count_changed_callback(self._count_changed_callback)
