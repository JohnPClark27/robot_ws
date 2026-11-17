import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    # Find the installed xacro via the package's share directory
    xacro_file = os.path.join(
        get_package_share_directory('ugv_description'), 'urdf', 'ugv.urdf.xacro')

    robot_description = ParameterValue(Command(['xacro ', xacro_file]), value_type=str)

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
    )

    jsp = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
    )

    return LaunchDescription([rsp, jsp])