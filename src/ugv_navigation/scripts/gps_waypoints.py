#!/usr/bin/env python3
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator
from geographic_msgs.msg import GeoPose
import time


WAYPOINTS = [  # (lat, lon)
    (40.515531, -85.655418),  # 1: 5 m east of origin (around box_1, like step 3)
    (40.515576, -85.655418),  # 2: 5 m north of point 1
    (40.515531, -85.655477),  # 3: back to origin (spawn)
]


def main():
    rclpy.init()
    nav = BasicNavigator()
    nav.waitUntilNav2Active(localizer='robot_localization')  # no AMCL in our setup

    poses = []
    for lat, lon in WAYPOINTS:
        p = GeoPose()
        p.position.latitude = lat
        p.position.longitude = lon
        poses.append(p)

    nav.followGpsWaypoints(poses)
    while not nav.isTaskComplete():
        point = nav.getFeedback().current_waypoint
        if (point is not None):
            print(nav.getFeedback().current_waypoint)
        time.sleep(1)

    print(nav.getResult())
    rclpy.shutdown()

if __name__ == '__main__':
    main()