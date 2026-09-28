from machine import Pin, PWM

import config


class MotorController:
    def __init__(self):
        self.ain1 = Pin(config.MOTOR_A_IN1, Pin.OUT, value=0)
        self.ain2 = Pin(config.MOTOR_A_IN2, Pin.OUT, value=0)
        self.bin1 = Pin(config.MOTOR_B_IN1, Pin.OUT, value=0)
        self.bin2 = Pin(config.MOTOR_B_IN2, Pin.OUT, value=0)
        self.pwma = PWM(Pin(config.MOTOR_A_PWM), freq=config.PWM_FREQUENCY_HZ)
        self.pwmb = PWM(Pin(config.MOTOR_B_PWM), freq=config.PWM_FREQUENCY_HZ)

        self.standby = None
        if config.MOTOR_STBY_GPIO is not None:
            self.standby = Pin(config.MOTOR_STBY_GPIO, Pin.OUT, value=0)

        self.stop()

    @staticmethod
    def _bounded_speed(speed):
        if speed > 1000:
            return 1000
        if speed < -1000:
            return -1000
        return speed

    @staticmethod
    def _set_motor(in1, in2, pwm, speed):
        speed = MotorController._bounded_speed(speed)
        if speed > 0:
            in1.value(1)
            in2.value(0)
        elif speed < 0:
            in1.value(0)
            in2.value(1)
        else:
            in1.value(0)
            in2.value(0)

        duty = abs(speed) * config.PWM_DUTY_MAX // 1000
        pwm.duty(duty)

    def set(self, left_speed, right_speed):
        if self.standby is not None:
            self.standby.value(1)
        self._set_motor(self.ain1, self.ain2, self.pwma, left_speed)
        self._set_motor(self.bin1, self.bin2, self.pwmb, right_speed)

    def stop(self):
        self._set_motor(self.ain1, self.ain2, self.pwma, 0)
        self._set_motor(self.bin1, self.bin2, self.pwmb, 0)
        if self.standby is not None:
            self.standby.value(0)

    def deinit(self):
        self.stop()
        self.pwma.deinit()
        self.pwmb.deinit()