def set_position(robot, angle, wait=True):
    if robot._speed_reactive:
        robot.adjust_speed()
    return robot._arm.set_servo_angle(
        angle=angle,
        speed=robot._angle_speed,
        mvacc=robot._angle_acc,
        wait=wait,
        radius=120 if robot._smooth else -1.0,
    )


def set_gripper(robot, value, speed):
    return robot._arm.set_gripper_position(
        value, wait=True, speed=speed, auto_enable=True
    )
