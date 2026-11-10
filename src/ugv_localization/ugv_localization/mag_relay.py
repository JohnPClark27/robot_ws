import math
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from sensor_msgs.msg import MagneticField

GAUSS_TO_TESLA = 1e-4
# Sim-only fix: Gazebo's mag uses NED + gauss. Measured 2026-11-10 at yaw 0 and -88.7 deg.
MAG_ROTATION = math.radians(108.4)


class MagRelay(Node):
    def __init__(self):
        super().__init__('mag_relay')
        self.pub = self.create_publisher(MagneticField, 'imu/mag', 10)
        self.sub = self.create_subscription(MagneticField, 'mag', self.callback, 10)
        
    def callback(self, msg):
        x = msg.magnetic_field.x
        y = msg.magnetic_field.y
        z = msg.magnetic_field.z

        x_new = x*math.cos(MAG_ROTATION) - y*math.sin(MAG_ROTATION)
        y_new = x*math.sin(MAG_ROTATION) + y*math.cos(MAG_ROTATION)
        z_new = -z

        x_new = x_new * GAUSS_TO_TESLA
        y_new = y_new * GAUSS_TO_TESLA
        z_new = z_new * GAUSS_TO_TESLA

        msg.magnetic_field.x = x_new
        msg.magnetic_field.y = y_new
        msg.magnetic_field.z = z_new

        self.pub.publish(msg)
        


def main():
    rclpy.init()
    node = MagRelay()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()