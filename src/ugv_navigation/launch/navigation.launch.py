import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    params = os.path.join(
        get_package_share_directory('ugv_navigation'), 'config', 'nav2_params.yaml')

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('nav2_bringup'), 'launch', 'navigation_launch.py')),
        launch_arguments={
            'use_sim_time': 'True',
            'params_file': params,
        }.items(),
    )

    curb_cloud = Node(
        package='pointcloud_to_laserscan',
        executable='laserscan_to_pointcloud_node',
        name='curb_scan_to_cloud',
        parameters=[{'use_sim_time': True}],
        remappings=[
            ('scan_in', '/scan_curb'),       # input: the curb lidar
            ('cloud', '/scan_curb_cloud'),   # output: our chosen name
        ],
    )

    return LaunchDescription([nav2, curb_cloud])