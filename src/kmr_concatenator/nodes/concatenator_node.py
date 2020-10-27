#!/usr/bin/env python3

# Copyright 2020 Morten Melby Dahl.
# Copyright 2020 Norwegian University of Science and Technology.
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

import sys
import argparse
from rclpy.qos import qos_profile_sensor_data
from rclpy.utilities import remove_ros_args

import rclpy
import numpy as np

import struct
import ctypes

from rclpy.node import Node

from std_msgs.msg import String
from sensor_msgs.msg import LaserScan, PointCloud2, PointField
import std_msgs


from message_filters import Subscriber, ApproximateTimeSynchronizer



class LaserConcatenator(Node):

	def __init__(self):
		super().__init__('laser_concatenator')
		self.name = 'laser_concatenator'

		self.publisher_ = self.create_publisher(PointCloud2, 'pc_concatenated', 10)

		# Make a LaserProjection object
		self.lp = LaserProjection()

		# Subscribes to the two laser scan topics. Might have to change QoS to 10 when subscribing to real laser readings.
		self.subscriber_1 = Subscriber(self, LaserScan, 'scan', qos_profile = rclpy.qos.qos_profile_sensor_data)
		self.subscriber_2 = Subscriber(self, LaserScan, 'scan_2', qos_profile = rclpy.qos.qos_profile_sensor_data)

		# Syncronizes messages from the two laser scanner topics when messages are less than 0.1 seconds apart.
		self.syncronizer = ApproximateTimeSynchronizer([self.subscriber_1, self.subscriber_2], 10, 0.1, allow_headerless=False)

		print('Initialized laser scan syncronizer.')
		
		# Calling callback function when syncronized messages are received.
		self.syncronizer.registerCallback(self.callback)


	def callback(self, scan, scan2):
		# Insert frame transform here


		# Make two PointCloud2 messages from the scans
		pc2_msg1 = self.lp.projectLaser(scan)
		pc2_msg2 = self.lp.projectLaser(scan2)

		print(pc2_msg1.header)

# Class for creating PointCloud2 messages from LaserScan messages

class LaserProjection():

    LASER_SCAN_INVALID   = -1.0
    LASER_SCAN_MIN_RANGE = -2.0
    LASER_SCAN_MAX_RANGE = -3.0

    class ChannelOption:
        NONE      = 0x00 # Enable no channels
        INTENSITY = 0x01 # Enable "intensities" channel
        INDEX     = 0x02 # Enable "index"       channel
        DISTANCE  = 0x04 # Enable "distances"   channel
        TIMESTAMP = 0x08 # Enable "stamps"      channel
        VIEWPOINT = 0x10 # Enable "viewpoint"   channel
        DEFAULT   = (INTENSITY | INDEX)

    def __init__(self):
        self.__angle_min = 0.0
        self.__angle_max = 0.0
        self.__cos_sin_map = np.array([[]])

        self._DATATYPES = {}
        self._DATATYPES[PointField.INT8]    = ('b', 1)
        self._DATATYPES[PointField.UINT8]   = ('B', 1)
        self._DATATYPES[PointField.INT16]   = ('h', 2)
        self._DATATYPES[PointField.UINT16]  = ('H', 2)
        self._DATATYPES[PointField.INT32]   = ('i', 4)
        self._DATATYPES[PointField.UINT32]  = ('I', 4)
        self._DATATYPES[PointField.FLOAT32] = ('f', 4)
        self._DATATYPES[PointField.FLOAT64] = ('d', 8)

    def projectLaser(self, scan_in,
            range_cutoff=-1.0, channel_options=ChannelOption.DEFAULT):
        """
        Project a sensor_msgs::LaserScan into a sensor_msgs::PointCloud2.
        Project a single laser scan from a linear array into a 3D
        point cloud. The generated cloud will be in the same frame
        as the original laser scan.
        Keyword arguments:
        scan_in -- The input laser scan.
        range_cutoff -- An additional range cutoff which can be
            applied which is more limiting than max_range in the scan
            (default -1.0).
        channel_options -- An OR'd set of channels to include.
        """
        return self.__projectLaser(scan_in, range_cutoff, channel_options)


    def __projectLaser(self, scan_in, range_cutoff, channel_options):
        N = len(scan_in.ranges)

        ranges = np.array(scan_in.ranges)

        if (self.__cos_sin_map.shape[1] != N or
            self.__angle_min != scan_in.angle_min or
            self.__angle_max != scan_in.angle_max):

            self.__angle_min = scan_in.angle_min
            self.__angle_max = scan_in.angle_max
            
            angles = scan_in.angle_min + np.arange(N) * scan_in.angle_increment
            self.__cos_sin_map = np.array([np.cos(angles), np.sin(angles)])

        output = ranges * self.__cos_sin_map

        # Set the output cloud accordingly
        cloud_out = PointCloud2()

        fields = [PointField() for _ in range(3)]

        fields[0].name = "x"
        fields[0].offset = 0
        fields[0].datatype = PointField.FLOAT32
        fields[0].count = 1

        fields[1].name = "y"
        fields[1].offset = 4
        fields[1].datatype = PointField.FLOAT32
        fields[1].count = 1

        fields[2].name = "z"
        fields[2].offset = 8
        fields[2].datatype = PointField.FLOAT32
        fields[2].count = 1

        idx_intensity = idx_index = idx_distance =  idx_timestamp = -1
        idx_vpx = idx_vpy = idx_vpz = -1

        offset = 12

        if (channel_options & self.ChannelOption.INTENSITY and
            len(scan_in.intensities) > 0):
            field_size = len(fields)
            fields.append(PointField())
            fields[field_size].name = "intensity"
            fields[field_size].datatype = PointField.FLOAT32
            fields[field_size].offset = offset
            fields[field_size].count = 1
            offset += 4
            idx_intensity = field_size

        if channel_options & self.ChannelOption.INDEX:
            field_size = len(fields)
            fields.append(PointField())
            fields[field_size].name = "index"
            fields[field_size].datatype = PointField.INT32
            fields[field_size].offset = offset
            fields[field_size].count = 1
            offset += 4
            idx_index = field_size

        if channel_options & self.ChannelOption.DISTANCE:
            field_size = len(fields)
            fields.append(PointField())
            fields[field_size].name = "distances"
            fields[field_size].datatype = PointField.FLOAT32
            fields[field_size].offset = offset
            fields[field_size].count = 1
            offset += 4
            idx_distance = field_size

        if channel_options & self.ChannelOption.TIMESTAMP:
            field_size = len(fields)
            fields.append(PointField())
            fields[field_size].name = "stamps"
            fields[field_size].datatype = PointField.FLOAT32
            fields[field_size].offset = offset
            fields[field_size].count = 1
            offset += 4
            idx_timestamp = field_size

        if channel_options & self.ChannelOption.VIEWPOINT:
            field_size = len(fields)
            fields.extend([PointField() for _ in range(3)])
            fields[field_size].name = "vp_x"
            fields[field_size].datatype = PointField.FLOAT32
            fields[field_size].offset = offset
            fields[field_size].count = 1
            offset += 4
            idx_vpx = field_size
            field_size += 1

            fields[field_size].name = "vp_y"
            fields[field_size].datatype = PointField.FLOAT32
            fields[field_size].offset = offset
            fields[field_size].count = 1
            offset += 4
            idx_vpy = field_size
            field_size += 1

            fields[field_size].name = "vp_z"
            fields[field_size].datatype = PointField.FLOAT32
            fields[field_size].offset = offset
            fields[field_size].count = 1
            offset += 4
            idx_vpz = field_size

        if range_cutoff < 0:
            range_cutoff = scan_in.range_max
        else:
            range_cutoff = min(range_cutoff, scan_in.range_max)

        points = []
        for i in range(N):
            ri = scan_in.ranges[i]
            if ri < range_cutoff and ri >= scan_in.range_min:
                point = output[:, i].tolist()
                point.append(0)

                if idx_intensity != -1:
                    point.append(scan_in.intensities[i])

                if idx_index != -1:
                    point.append(i)

                if idx_distance != -1:
                    point.append(scan_in.ranges[i])

                if idx_timestamp != -1:
                    point.append(i * scan_in.time_increment)

                if idx_vpx != -1 and idx_vpy != -1 and idx_vpz != -1:
                    point.extend([0 for _ in range(3)])

                points.append(point)

        cloud_out = self.create_cloud(scan_in.header, fields, points)

        return cloud_out

    def create_cloud(self, header, fields, points):
    	"""
    	Create a L{sensor_msgs.msg.PointCloud2} message.
    	@param header: The point cloud header.
    	@type  header: L{std_msgs.msg.Header}
    	@param fields: The point cloud fields.
    	@type  fields: iterable of L{sensor_msgs.msg.PointField}
    	@param points: The point cloud points.
    	@type  points: list of iterables, i.e. one iterable for each point, with the
    	               elements of each iterable being the values of the fields for 
    	               that point (in the same order as the fields parameter)
    	@return: The point cloud.
    	@rtype:  L{sensor_msgs.msg.PointCloud2}
    	"""

    	cloud_struct = struct.Struct(self._get_struct_fmt(False, fields))

    	buff = ctypes.create_string_buffer(cloud_struct.size * len(points))

    	point_step, pack_into = cloud_struct.size, cloud_struct.pack_into
    	offset = 0
    	for p in points:
    	    pack_into(buff, offset, *p)
    	    offset += point_step

    	return PointCloud2(header=header,
        	               height=1,
        	               width=len(points),
        	               is_dense=False,
        	               is_bigendian=False,
        	               fields=fields,
        	               point_step=cloud_struct.size,
        	               row_step=cloud_struct.size * len(points),
        	               data=buff.raw)

    def _get_struct_fmt(self, is_bigendian, fields, field_names=None):
    	fmt = '>' if is_bigendian else '<'

    	offset = 0
    	for field in (f for f in sorted(fields, key=lambda f: f.offset) if field_names is None or f.name in field_names):
    	    if offset < field.offset:
    	        fmt += 'x' * (field.offset - offset)
    	        offset = field.offset
    	    if field.datatype not in self._DATATYPES:
    	        print('Skipping unknown PointField datatype [%d]' % field.datatype, file=sys.stderr)
    	    else:
    	        datatype_fmt, datatype_length = self._DATATYPES[field.datatype]
    	        fmt    += field.count * datatype_fmt
    	        offset += field.count * datatype_length

    	return fmt



def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    args = parser.parse_args(remove_ros_args(args=argv))
    rclpy.init(args=argv)
    concatenator_node = LaserConcatenator()

    rclpy.spin(concatenator_node)
    try:
        concatenator_node.destroy_node()
        rclpy.shutdown()
    except:
        print("Error: rclpy shutdown failed")


if __name__ == '__main__':
    main()