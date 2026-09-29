import time

from machine import Pin, PWM, Timer

import config


class MotorController:
    """TB6612FNG control with a speed cap, ramping, and a pause at zero before reversing.

    set() only records a target speed. A timer steps each motor toward its target every
    RAMP_TICK_MS, so a full-forward to full-reverse command slows to zero, waits
    REVERSE_PAUSE_MS, then speeds back up instead of slamming the motor into reverse.
    stop() still cuts both motors immediately.
    """

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

        self._limit = (config.MOTOR_A_MAX_PERCENT * 10, config.MOTOR_B_MAX_PERCENT * 10)
        self._target = [0, 0]
        self._speed = [0, 0]
        self._hold_until = [0, 0]
        self._last_tick_ms = time.ticks_ms()

        self.stop()

        self._timer = Timer(0)
        self._timer.init(period=config.RAMP_TICK_MS, mode=Timer.PERIODIC, callback=self._tick)

    @staticmethod
    def _bounded_speed(speed, limit):
        if speed > limit:
            return limit
        if speed < -limit:
            return -limit
        return speed

    @staticmethod
    def _set_motor(in1, in2, pwm, speed):
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

    def _apply(self):
        self._set_motor(self.ain1, self.ain2, self.pwma, self._speed[0])
        self._set_motor(self.bin1, self.bin2, self.pwmb, self._speed[1])

    def _step_toward_target(self, index, step, now):
        speed = self._speed[index]
        target = self._target[index]

        if time.ticks_diff(self._hold_until[index], now) > 0:
            return 0

        # Reversing or stopping: come down to zero first.
        if speed != 0 and (target == 0 or (target > 0) != (speed > 0)):
            if speed > 0:
                speed = max(0, speed - step)
            else:
                speed = min(0, speed + step)
            if speed == 0 and target != 0:
                self._hold_until[index] = time.ticks_add(now, config.REVERSE_PAUSE_MS)
            return speed

        if speed < target:
            return min(target, speed + step)
        return max(target, speed - step)

    def _tick(self, _timer):
        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self._last_tick_ms)
        self._last_tick_ms = now
        step = max(1, elapsed * 1000 // config.RAMP_MS_ZERO_TO_FULL)

        speed_a = self._step_toward_target(0, step, now)
        speed_b = self._step_toward_target(1, step, now)
        if speed_a != self._speed[0] or speed_b != self._speed[1]:
            self._speed[0] = speed_a
            self._speed[1] = speed_b
            self._apply()

    def set(self, left_speed, right_speed):
        if self.standby is not None:
            self.standby.value(1)
        self._target[0] = self._bounded_speed(left_speed, self._limit[0])
        self._target[1] = self._bounded_speed(right_speed, self._limit[1])

    def stop(self):
        self._target[0] = self._target[1] = 0
        self._speed[0] = self._speed[1] = 0
        self._apply()
        if self.standby is not None:
            self.standby.value(0)

    def deinit(self):
        self._timer.deinit()
        self.stop()
        self.pwma.deinit()
        self.pwmb.deinit()
