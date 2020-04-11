// Copyright 2019 Nina Marie Wahl og Charlotte Heggem.
// Copyright 2019 Norwegian University of Science and Technology.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package API_ROS2_Sunrise;


import java.util.concurrent.TimeUnit;

import API_ROS2_Sunrise.ISocket;
import API_ROS2_Sunrise.TCPSocket;
import API_ROS2_Sunrise.UDPSocket;

import com.kuka.roboticsAPI.deviceModel.LBR;


public class LBR_sensor_reader extends Node{
	
	// Runtime variables
	Boolean LBR_sensor_requested;

	// Robot
	LBR lbr;
	
	// LBR sensor
	private double[] JointPosition;
	private double[] MeasuredTorque;
	
	// Socket
	int port;
	ISocket socket;
	String ConnectionType;
	
	
	public LBR_sensor_reader(int port, LBR robot, String ConnectionType) {
		super(port, ConnectionType);
		this.lbr = robot;
		LBR_sensor_requested = false;
		
		if(!(isSocketConnected())){
			Thread monitorLBRsensorConnections = new MonitorSensorConnectionThread();
			monitorLBRsensorConnections.start();
		}else {
			LBR_sensor_requested=true;
		}

	}
	
		
	public class MonitorSensorConnectionThread extends Thread {
		int timeout = 3000;
		public void run(){
			while(!(isSocketConnected()) && (!(closed))) {

				createSocket();
				if (isSocketConnected()){
					break;
				}
				try {
					Thread.sleep(timeout);
				} catch (InterruptedException e) {
					System.out.println("Waiting for connection to LBR commander node ..");
				}
			}
			if(!closed){
				LBR_sensor_requested=true;
				System.out.println("Connection with KMP Command Node OK!");
				runmainthread();
				}	
		}
	}

	@Override
	public void run() {
		while(isNodeRunning())
		{	
			//FIND OUT HOW MUCH TO SLEEP. SAMME RATE SOM ODOMETRY?
			updateMeasuredTorque();
			updateJointPosition();
			
			if(!isSocketConnected() || (closed)){
				break;
			}
			sendStatus();
			try {
				TimeUnit.MILLISECONDS.sleep(30);
			} catch (InterruptedException e) {
				System.out.println("LBR sensor thread could not sleep");
			}
		}
	}

	private void updateJointPosition() {
		try{
		JointPosition = lbr.getCurrentJointPosition().getInternalArray();
		}catch(Exception e){}
	}

	private void updateMeasuredTorque() {
		try{
		MeasuredTorque = lbr.getMeasuredTorque().getTorqueValues();
		}catch(Exception e){}
	}

	private String generateSensorString() {
		return 	">lbr_sensordata ,"  + System.nanoTime() +  
				",JointPosition:" + JointPosition[0]+"," + JointPosition[1]+"," + JointPosition[2]+"," + JointPosition[3]+"," + JointPosition[4]+"," + JointPosition[5]+"," + JointPosition[6]+
				",MeasuredTorque:" + MeasuredTorque[0] +","+ MeasuredTorque[1] +","+MeasuredTorque[2] +","+MeasuredTorque[3] +","+MeasuredTorque[4] +","+MeasuredTorque[5] +","+MeasuredTorque[6] ;
	}
	
	public void sendStatus() {
		String sensorString = generateSensorString();
		if(isNodeRunning()){
			try{
				this.socket.send_message(sensorString);
				if(closed){
					System.out.println("LBR sensor sender selv om han ikke f�r lov");
				}
			}catch(Exception e){
				System.out.println("Could not send Operation mode to ROS: " + e);
			}
		}
	}
	
	@Override
	public void close() {
		closed = true;
		socket.close();
		System.out.println("LBR sensor closed!");

	}
	
}
