import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix

POS_DIAG = [0.0004, 0.0004, 0.0016]   # east, north, up (m²)

class GpsCovRelay(Node):

    def __init__(self):
        super().__init__('gps_cov_relay')
        self.pub = self.create_publisher(NavSatFix, 'gps/fix_cov', 10)
        self.sub = self.create_subscription(NavSatFix, 'gps/fix', self.callback, 10)

    def callback(self, msg):
        cov = [0.0] * 9
        for i, v in enumerate(POS_DIAG):
            cov[i*3+i] = v
        msg.position_covariance = cov
        msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = GpsCovRelay()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()