import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry

TWIST_DIAG = [0.0025, 0.001, 1e3, 1e3, 1e3, 0.03]
POSE_DIAG  = [0.01, 0.01, 1e3, 1e3, 1e3, 0.05]


class OdomCovRelay(Node):
    def __init__(self):
        super().__init__('odom_cov_relay')
        self.pub = self.create_publisher(Odometry, 'wheel/odom', 10)
        self.sub = self.create_subscription(Odometry, 'odom', self.callback, 10)

    def callback(self, msg):
        
        cov = [0.0]*36
        for i, v in enumerate(TWIST_DIAG):
            cov[i*6+i] = v
        msg.twist.covariance = cov

        cov = [0.0]*36
        for i, v in enumerate(POSE_DIAG):
            cov[i*6+i] = v
        msg.pose.covariance = cov
        
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = OdomCovRelay()
    rclpy.spin(node)        
    node.destroy_node()
    rclpy.shutdown()