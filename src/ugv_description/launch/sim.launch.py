import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import AppendEnvironmentVariable


def generate_launch_description():
    # Find the installed xacro via the package's share directory
    xacro_file = os.path.join(
        get_package_share_directory('ugv_description'), 'urdf', 'ugv.urdf.xacro')

    world_file = os.path.join(
        get_package_share_directory('ugv_description'), 'worlds', 'test_world.sdf')

    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
    )

    gz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': '-r ' + world_file}.items(),
    )

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'ugv', '-z', '0.2'],
        output='screen',
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # format: '<topic>@<ros type>[<gz type>'   ( [ gz→ROS, ] ROS→gz )
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            #'/model/ugv/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/front_left_cam/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/front_left_cam/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/front_right_cam/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/front_right_cam/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            '/gps/fix@sensor_msgs/msg/NavSatFix[gz.msgs.NavSat',
            '/depth_cam@sensor_msgs/msg/Image[gz.msgs.Image',
            '/depth_cam/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked',
            '/scan_curb@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/mag@sensor_msgs/msg/MagneticField[gz.msgs.Magnetometer',
        ],
        remappings=[('/depth_cam', '/depth_cam/depth_image')],
        output='screen',
    )

    gz_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(get_package_share_directory('ugv_description'), '..'))

    
    return LaunchDescription([gz_resource_path, rsp,gz, spawn, bridge])