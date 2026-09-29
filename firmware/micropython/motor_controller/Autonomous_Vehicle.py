import time

from lidar import RPLidar
from lights import StatusLight
from motor import MotorController
from telemetry import Telemetry
from udp_control import CommandReceiver
from wifi import connect_wifi


connect_wifi()

status_light = StatusLight()
motors = MotorController()
lidar = RPLidar()
telemetry = Telemetry()
command_receiver = CommandReceiver(motors, status_light)

print("Autonomous vehicle test. Wheels must be lifted.")
print("Waiting for the host to connect and send a command...")

try:
    lidar.start_scan()
    while True:
        command_receiver.poll()
        command_receiver.enforce_timeout()

        if command_receiver.last_sender_ip is not None:
            telemetry.set_host(command_receiver.last_sender_ip)

        lidar.poll()
        if lidar.new_revolution:
            telemetry.send_sectors(lidar.last_sectors)
            lidar.new_revolution = False

        time.sleep_ms(10)
except KeyboardInterrupt:
    print("Autonomous vehicle test interrupted")
finally:
    command_receiver.close()
    motors.deinit()
    lidar.stop_scan()
    status_light.off()
    print("Motors and lidar stopped")
