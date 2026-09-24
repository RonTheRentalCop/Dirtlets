from machine import Pin, PWM

import config


class MotorController:
    def __init__(self):
        self._standby = Pin(config.MOTOR_STBY, Pin.OUT, value=0)
        self._left_in1 = Pin(config.MOTOR_A_IN1, Pin.OUT, value=0)
        self._left_in2 = Pin(config.MOTOR_A_IN2, Pin.OUT, value=0)
        self._right_in1 = Pin(config.MOTOR_B_IN1, Pin.OUT, value=0)
        self._right_in2 = Pin(config.MOTOR_B_IN2, Pin.OUT, value=0)
        self._left_pwm = PWM(Pin(config.MOTOR_A_PWM), freq=config.PWM_FREQUENCY_HZ)
        self._right_pwm = PWM(Pin(config.MOTOR_B_PWM), freq=config.PWM_FREQUENCY_HZ)
        self.stop()

    @staticmethod
    def _bound(value):
        if value > 1000:
            return 1000
        if value < -1000:
            return -1000
        return value

    @staticmethod
    def _set_direction(in1, in2, pwm, command):
        command = MotorController._bound(command)
        if command == 0:
            in1.value(0)
            in2.value(0)
            pwm.duty_u16(0)
            return

        if command > 0:
            in1.value(1)
            in2.value(0)
        else:
            in1.value(0)
            in2.value(1)

        duty = abs(command) * config.PWM_MAX // 1000
        pwm.duty_u16(duty)

    def set(self, left, right):
        self._standby.value(1)
        self._set_direction(self._left_in1, self._left_in2, self._left_pwm, left)
        self._set_direction(self._right_in1, self._right_in2, self._right_pwm, right)

    def stop(self):
        self._set_direction(self._left_in1, self._left_in2, self._left_pwm, 0)
        self._set_direction(self._right_in1, self._right_in2, self._right_pwm, 0)
        self._standby.value(0)

    def deinit(self):
        self.stop()
        self._left_pwm.deinit()
        self._right_pwm.deinit()
