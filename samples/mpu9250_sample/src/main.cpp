#include <Arduino.h>
#include "BluetoothSerial.h"
#include <EEPROM.h>
BluetoothSerial SerialBT;

#include <MPU9250.h>



MPU9250 imu;


void printIMUData(void) {  
  // After calling update_dmp_fifo() the ax, gx, mx, etc. values
  // are all updated.
  // Quaternion values are, by default, stored in Q30 long
  // format. calc_quat turns them into a float between -1 and 1

  //mX_range=-25.36 ~ 43.96
  //mY_range=29.11 ~ 83.27
  //mZ_range=-97.67 ~ -18.75
 
  
  float ax = -( imu.calc_accel(imu.ax) - imu.aX_offset);
  float ay = -( imu.calc_accel(imu.ay) - imu.aY_offset);
  float az = -( imu.calc_accel(imu.az) - imu.aZ_offset);

  float gx = (imu.calc_gyro(imu.gx) - imu.gX_offset)  * 0.01745329251;
  float gy = (imu.calc_gyro(imu.gy) - imu.gY_offset)  * 0.01745329251;
  float gz = (imu.calc_gyro(imu.gz) - imu.gZ_offset)  * 0.01745329251;

  float mx = imu.calc_mag(imu.mx)  - 10.8;
  float my = imu.calc_mag(imu.my)  - 56.19;
  float mz = imu.calc_mag(imu.mz)  + 67.0;

  //filter.update(gx, gy, gz, ax, ay, az, mx, my,mz);


  float qw = imu.calc_quat(imu.qw);
  float qx = imu.calc_quat(imu.qx);
  float qy = imu.calc_quat(imu.qy);
  float qz = imu.calc_quat(imu.qz);
  
  
  //float qw = filter.q0;
  //float qx = filter.q1;
  //float qy = filter.q2;
  //float qz = filter.q3;
  


  

  
  //Serial.println(imu.calc_mag_heading());
  Serial.println("aX="  + String(ax)  + 
                 ",aY=" + String(ay)    + 
                 ",aZ=" + String(az)    + 
                 ",gX=" + String(gx)    + 
                 ",gY=" + String(gy)    + 
                 ",gZ=" + String(gz)    +
                 ",mX=" + String(mx)    + 
                 ",mY=" + String(my)    + 
                 ",mZ=" + String(mz)    +                 
                 ",qW=" + String(qw)    + 
                 ",qX=" + String(qx)    + 
                 ",qY=" + String(qy)    + 
                 ",qZ=" + String(qz)     );
}



void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32test");
  // Call imu.begin() to verify communication and initialize
  if (imu.begin(21,22) != INT_SUCCESS)  {
    while (1)    {
      Serial.println("Unable to communicate with MPU-9250");
      Serial.println("Check connections, and try again.");
      Serial.println();
      delay(5000);
    }
  } 
  

  imu.set_sensors(INV_XYZ_GYRO | INV_XYZ_ACCEL | INV_XYZ_COMPASS);
  
  
  imu.begin_dmp(DMP_FEATURE_SEND_RAW_ACCEL|
                DMP_FEATURE_SEND_CAL_GYRO |
                DMP_FEATURE_6X_LP_QUAT    | // Enable 6-axis quat
                DMP_FEATURE_GYRO_CAL      , // Use gyro calibration
                60); // Set DMP FIFO rate to 60 Hz
  
  imu.set_mag_sample_rate(60); // Set mag rate to 10Hz


  //imu.cal_sensors();
  

  /*
  imu.set_gyro_scale(2000); // Set gyro to 2000 dps
 
  imu.set_accel_scale(2); // Set accel to +/-2g
  imu.setLPF(5); // Set LPF corner frequency to 5Hz
  imu.set_sample_rate(100); 
  imu.set_mag_sample_rate(10); // Set mag rate to 10Hz
  */

}

void loop1() {
  Serial.println(imu.get_int_status());
  delay(1000);
};


void loop()  {
  // Check for new data in the FIFO
  if ( imu.get_fifo_available() )   {
    // Use update_dmp_fifo to update the ax, gx, mx, etc. values
    if ( imu.update_dmp_fifo() ==  INT_SUCCESS)     {
      // calc_euler_angles can be used -- after updating the
      // quaternion values -- to estimate roll, pitch, and yaw
      //Serial.println(imu.calc_accel(imu.az));
      imu.update(UPDATE_ACCEL | UPDATE_GYRO | UPDATE_COMPASS);
      //imu.calc_euler_angles();
      printIMUData();

    }
  }
} 

