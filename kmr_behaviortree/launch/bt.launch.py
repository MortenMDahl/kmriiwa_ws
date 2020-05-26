import os
import yaml
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    
    moveit_launch_file_dir = os.path.join(get_package_share_directory('kmr_moveit2'), 'launch')
    navigation_launch_file_dir = os.path.join(get_package_share_directory('kmr_navigation2'), 'launch')
    
    #xml_file_name = 'manipulator_tree.xml'
    xml_file_name = 'test.xml'
    xml = os.path.join(
        get_package_share_directory('kmr_behaviortree'),
        'behavior_trees',
        xml_file_name)
    bt_param_dir = LaunchConfiguration(
        'bt_param_dir',
        default=os.path.join(
            get_package_share_directory('kmr_behaviortree'),
            'param',
            'param.yaml'))

    
    connection_type_TCP='TCP'
    robot = 'KMR2'
    param_dir = LaunchConfiguration(
        'param_dir',
        default=os.path.join(
            get_package_share_directory('kmr_communication'),
            'param',
            'bringup.yaml'))

    return LaunchDescription([

        Node(
             package="kmr_communication",
             node_executable="lbr_commands_node.py",
             node_name="lbr_commands_node",
             output="screen",
             emulate_tty=True,
             arguments=['-c', connection_type_TCP, '-ro', robot],
             parameters=[param_dir]),

        Node(
             package="kmr_communication",
             node_executable="lbr_statusdata_node.py",
             node_name="lbr_statusdata_node",
             output="screen",
             emulate_tty=True,
             arguments=['-c', connection_type_TCP, '-ro', robot],
             parameters=[param_dir]),

        Node(
             package="kmr_communication",
             node_executable="lbr_sensordata_node.py",
             node_name="lbr_sensordata_node",
             output="screen",
             emulate_tty=True,
             arguments=['-c', connection_type_TCP, '-ro', robot],
             parameters=[param_dir]),


        Node(
            package="kmr_behaviortree",
            node_executable="behavior_tree_node",
            node_name="behavior_tree_node",
            output='screen',
            parameters=[{'bt_xml_filename': xml}, bt_param_dir],
            emulate_tty=True,
            ),

        ])