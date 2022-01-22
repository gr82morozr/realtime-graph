#include <Arduino.h>

/************************************************************
MPU9250_Basic
 Basic example sketch for MPU-9250 DMP Arduino Library 
Jim Lindblom @ SparkFun Electronics
original creation date: November 23, 2016
https://github.com/sparkfun/SparkFun_MPU9250_Arduino_Library

This example sketch demonstrates how to initialize the 
MPU-9250, and stream its sensor outputs to a serial monitor.

Development environment specifics:
Arduino IDE 1.6.12
SparkFun 9DoF Razor IMU M0

Supported Platforms:
- ATSAMD21 (Arduino Zero, SparkFun SAMD21 Breakouts)
*************************************************************/
#include <MPU9250.h>



MPU9250 imu;


void printIMUData(void) {  
  // After calling update() the ax, ay, az, gx, gy, gz, mx,
  // my, mz, time, and/or temerature class variables are all
  // updated. Access them by placing the object. in front:

  // Use the calc_accel, calc_gyro, and calc_mag functions to
  // convert the raw sensor readings (signed 16-bit values)
  // to their respective units.
  float aX = imu.calc_accel(imu.ax);
  float aY = imu.calc_accel(imu.ay);
  float aZ = imu.calc_accel(imu.az);
  
  float gX = imu.calc_gyro(imu.gx);
  float gY = imu.calc_gyro(imu.gy);
  float gZ = imu.calc_gyro(imu.gz);
  
  float mX = imu.calc_mag(imu.mx);
  float mY = imu.calc_mag(imu.my);
  float mZ = imu.calc_mag(imu.mz);
  
  float qW = imu.calc_quat(imu.qw);
  float qX = imu.calc_quat(imu.qx);
  float qY = imu.calc_quat(imu.qy);
  float qZ = imu.calc_quat(imu.qz);
  
  float Roll  = imu.roll;
  float Pitch = imu.pitch;
  float Yaw   = imu.yaw;

  // avoid quat norm is 0 at begining of the program
  if ( qW==0.0 && qX == 0.0 && qY == 0.0 && qZ == 0.0) return;

  Serial.println("aX=" + String(aX) + ",aY=" +  String(aY) + ",aZ=" + String(aZ) + ",gX=" + String(gX) + ",gY=" +String(gY) + ",gZ=" + String(gZ) + ",qW=" + String(qW) + ",qX=" + String(qX) + ",qY=" + String(qY) + ",qZ=" + String(qZ) + ",Roll=" + String(Roll) + ",Pitch=" + String(Pitch) + ",Yaw=" + String(Yaw) +  ",mX=" + String(mX) + ",mY="  +  String(mY) + ",mZ=" + String(mZ) + ",TS=" + String(imu.time));
  
}




void setup() 
{
  Serial.begin(115200);

  // Call imu.begin() to verify communication with and
  // initialize the MPU-9250 to it's default values.
  // Most functions return an error code - INT_SUCCESS (0)
  // indicates the IMU was present and successfully set up
  if (imu.begin() != INT_SUCCESS) {
    while (1)  {
      Serial.println("Unable to communicate with MPU-9250");
      Serial.println("Check connections, and try again.");
      Serial.println();
      delay(5000);
    }
  }

  imu.begin_dmp(DMP_FEATURE_6X_LP_QUAT | // Enable 6-axis quat
               DMP_FEATURE_GYRO_CAL, // Use gyro calibration
              60); // Set DMP FIFO rate to 40 Hz

  // Use set_sensors to turn on or off MPU-9250 sensors.
  // Any of the following defines can be combined:
  // INV_XYZ_GYRO, INV_XYZ_ACCEL, INV_XYZ_COMPASS,
  // INV_X_GYRO, INV_Y_GYRO, or INV_Z_GYRO
  // Enable all sensors:
  imu.set_sensors(INV_XYZ_GYRO | INV_XYZ_ACCEL | INV_XYZ_COMPASS);

  // Use set_gyro_scale() and set_accel_scale() to configure the
  // gyroscope and accelerometer full scale ranges.
  // Gyro options are +/- 250, 500, 1000, or 2000 dps
  imu.set_gyro_scale(2000); // Set gyro to 2000 dps
  // Accel options are +/- 2, 4, 8, or 16 g
  imu.set_accel_scale(2); // Set accel to +/-2g
  // Note: the MPU-9250's magnetometer FSR is set at 
  // +/- 4912 uT (micro-tesla's)

  // setLPF() can be used to set the digital low-pass filter
  // of the accelerometer and gyroscope.
  // Can be any of the following: 188, 98, 42, 20, 10, 5
  // (values are in Hz).
  imu.setLPF(5); // Set LPF corner frequency to 5Hz

  // The sample rate of the accel/gyro can be set using
  // set_sample_rate. Acceptable values range from 4Hz to 1kHz
  imu.set_sample_rate(10); // Set sample rate to 10Hz

  // Likewise, the compass (magnetometer) sample rate can be
  // set using the set_mag_sample_rate() function.
  // This value can range between: 1-100Hz
  imu.set_mag_sample_rate(10); // Set mag rate to 10Hz


}

void loop() {
  // is_data_ready() checks to see if new accel/gyro data
  // is available. It will return a boolean true or false
  // (New magnetometer data cannot be checked, as the library
  //  runs that sensor in single-conversion mode.)
  if ( imu.is_data_ready() )   {
    // Call update() to update the imu objects sensor data.
    // You can specify which sensors to update by combining
    // UPDATE_ACCEL, UPDATE_GYRO, UPDATE_COMPASS, and/or
    // UPDATE_TEMPERATURE.
    // (The update function defaults to accel, gyro, compass,
    //  so you don't have to specify these values.)
    imu.update(UPDATE_ACCEL | UPDATE_GYRO | UPDATE_COMPASS);
    // Check for new data in the FIFO
    if ( imu.get_fifo_available() )   {
      // Use update_dmp_fifo to update the ax, gx, mx, etc. values
      if ( imu.update_dmp_fifo() == INT_SUCCESS)   {
        // calc_euler_angles can be used -- after updating the
        // quaternion values -- to estimate roll, pitch, and yaw
        imu.calc_euler_angles();
        printIMUData();
      }
    }
  }
}

