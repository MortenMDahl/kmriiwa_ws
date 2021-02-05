# Copyright 2019 Nina Marie Wahl and Charlotte Heggem.
# Copyright 2019 Norwegian University of Science and Technology.
# Modifications copyright (C) 2020 Morten M. Dahl
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default=False)
    map_dir = LaunchConfiguration(
        'map',
        default=os.path.join(
            get_package_share_directory('kmr_slam_toolbox'),
            'created_maps',
            'GAZEBO.yaml'))

    param_dir = LaunchConfiguration(
        'params_file',
        default=os.path.join(
            get_package_share_directory('kmr_navigation2'),
            'param',
            'test.yaml'))
    
    xml = LaunchConfiguration(
        'bt_xml_file',
        default=os.path.join(
            get_package_share_directory('nav2_bt_navigator'),
            'behavior_trees',
            # Changed from 'navigate_w_replanning' to '_time' is the equal file in the Foxy release of Nav2
            'navigate_w_replanning_time.xml'))

    nav2_launch_file_dir = os.path.join(get_package_share_directory('nav2_bringup'), 'launch')
    state_publisher_launch_file_dir = os.path.join(get_package_share_directory('kmr_bringup'), 'launch')

    rviz_config_dir = os.path.join(
        get_package_share_directory('kmr_navigation2'),
        'rviz',
        'nav2_default_view.rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=map_dir,
            description='Full path to map file to load'),

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'),

        IncludeLaunchDescription(
            #Changed path from '/nav2_bringup_launch.py' as it is deprecated.
            PythonLaunchDescriptionSource([nav2_launch_file_dir, '/bringup_launch.py']),
            launch_arguments={
                'map': map_dir,
                'use_sim_time': use_sim_time,
                'bt_xml_file': xml,
                'params_file': param_dir}.items(),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([state_publisher_launch_file_dir, '/state_publisher.launch.py']),
        ),

        #Node(
        #    package='kmr_navigation2',
        #   node_executable='navigation_support_node.py',
        #    node_name='navigation_support_node',
        #    output='screen'),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': use_sim_time}],
            #output='screen'
            ),
    ])
