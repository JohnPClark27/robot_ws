import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    ekf_config = os.path.join(
        get_package_share_directory('ugv_localization'), 'config', 'ekf.yaml')

    relay = Node(
        package='ugv_localization',
        executable='odom_cov_relay',
        parameters=[{'use_sim_time': True}],
    )

    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        parameters=[ekf_config], 
    )

    mag = Node(
        package='ugv_localization',
        executable='mag_relay',
        parameters=[{'use_sim_time': True}],
    )

    madgwick = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        parameters=[{
            'use_sim_time': True,
            'use_mag': True,
            'world_frame': 'enu',
            'publish_tf': False,          
            'orientation_stddev': 0.05,  
        }],
        remappings=[('imu/data_raw', '/imu')],
    )

    navsat_config = os.path.join(get_package_share_directory('ugv_localization'), 'config', 'navsat.yaml')

    navsat = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform',
        parameters=[navsat_config],
        remappings=[('imu','/imu/data'), ('gps/fix', '/gps/fix_cov')],
    )

    gps_relay = Node(
        package='ugv_localization',
        executable='gps_cov_relay',
        parameters=[{'use_sim_time': True}],
    )

    return LaunchDescription([relay, ekf, mag, madgwick, navsat, gps_relay])