/**
 * SYSTEM IDENTIFICATION FIRMWARE - mBot Ranger Self-Balancing
 *
 * Colectează date pentru identificarea:
 * 1. MODEL MOTOR: PWM → Viteză encoder (open-loop)
 * 2. MODEL ANGLE: PWM → Unghi înclinație (closed-loop balancing active)
 *
 * TESTE INCLUSE:
 * - Test 1 (0-30s): Motor step response (open-loop)
 * - Test 2 (30-60s): Angle disturbance rejection (closed-loop)
 *
 * OUTPUT CSV: time,pwm_left,pwm_right,speed_1,speed_2,angleX,gyroY
 */

#include <Arduino.h>
#include <MeAuriga.h>
#include <Wire.h>

// Hardware instances
MeEncoderOnBoard Encoder_1(SLOT1);
MeEncoderOnBoard Encoder_2(SLOT2);
MeGyro gyro(1, 0x69);

// Encoder ISR functions
void isr_process_encoder1(void)
{
    if (digitalRead(Encoder_1.getPortB()) == 0)
    {
        Encoder_1.pulsePosMinus();
    }
    else
    {
        Encoder_1.pulsePosPlus();
    }
}

void isr_process_encoder2(void)
{
    if (digitalRead(Encoder_2.getPortB()) == 0)
    {
        Encoder_2.pulsePosMinus();
    }
    else
    {
        Encoder_2.pulsePosPlus();
    }
}

// PID structure from control.cpp
typedef struct
{
    double P, I, D;
    double Setpoint, Output, Integral, differential, last_error;
} PID;

PID PID_angle, PID_speed, PID_turn;

// Self-balancing parameters (from control.cpp)
#define RELAX_ANGLE -1.0
double CompAngleX = 0;
double GyroXangle = 0;
double angle_speed = 0;

// Test state machine
enum TestPhase
{
    PHASE_IDLE,
    PHASE_MOTOR_TEST,
    PHASE_BALANCE_TEST,
    PHASE_COMPLETE
};

TestPhase current_phase = PHASE_IDLE;
unsigned long phase_start_time = 0;
unsigned long test_start_time = 0;

// Timing
const unsigned long MOTOR_TEST_DURATION = 30000;   // 30 sec motor test
const unsigned long BALANCE_TEST_DURATION = 30000; // 30 sec balance test

// Move function (from control.cpp)
void move(int direction, int speed)
{
    int leftSpeed = 0;
    int rightSpeed = 0;

    if (direction == 1)
    {
        leftSpeed = speed;
        rightSpeed = speed;
    }
    else if (direction == 2)
    {
        leftSpeed = -speed;
        rightSpeed = -speed;
    }
    else if (direction == 3)
    {
        leftSpeed = -speed;
        rightSpeed = speed;
    }
    else if (direction == 4)
    {
        leftSpeed = speed;
        rightSpeed = -speed;
    }

    Encoder_1.setMotorPwm(-leftSpeed);
    Encoder_2.setMotorPwm(rightSpeed);
}

// PID angle compute (simplified from control.cpp)
void PID_angle_compute()
{
    double error = CompAngleX - PID_angle.Setpoint;

    PID_angle.Integral += error;
    PID_angle.Integral = constrain(PID_angle.Integral, -100, 100);

    PID_angle.differential = error - PID_angle.last_error;
    PID_angle.last_error = error;

    PID_angle.Output = PID_angle.P * error +
                       PID_angle.I * PID_angle.Integral +
                       PID_angle.D * PID_angle.differential;

    PID_angle.Output = constrain(PID_angle.Output, -255, 255);

    // Apply to motors
    move(1, (int)PID_angle.Output);
}

// PID speed compute (simplified from control.cpp)
void PID_speed_compute()
{
    double speed_1 = Encoder_1.getCurrentSpeed();
    double speed_2 = Encoder_2.getCurrentSpeed();
    double speed_now = (speed_1 + speed_2) / 2.0;

    double speed_error = speed_now - PID_speed.Setpoint;

    PID_speed.Integral += speed_error;
    PID_speed.Integral = constrain(PID_speed.Integral, -500, 500);

    PID_speed.differential = speed_error - PID_speed.last_error;
    PID_speed.last_error = speed_error;

    PID_speed.Output = PID_speed.P * speed_error +
                       PID_speed.I * PID_speed.Integral +
                       PID_speed.D * PID_speed.differential;

    PID_speed.Output = constrain(PID_speed.Output, -10, 10);

    // Update angle setpoint
    PID_angle.Setpoint = RELAX_ANGLE - PID_speed.Output;
}

// Balanced model (cascaded PID)
void balanced_model()
{
    gyro.fast_update();
    CompAngleX = gyro.getAngleX();

    PID_speed_compute();
    PID_angle_compute();
}

// Motor test (open-loop step response)
void motor_test()
{
    unsigned long elapsed = millis() - phase_start_time;

    int pwm_command = 0;

    if (elapsed < 10000)
    {
        // Step 1: 0 → 150
        pwm_command = 150;
    }
    else if (elapsed < 20000)
    {
        // Step 2: 150 → 220
        pwm_command = 220;
    }
    else
    {
        // Step 3: 220 → 0
        pwm_command = 0;
    }

    // Update gyro for angle reading
    gyro.fast_update();
    
    // Apply directly to motors
    Encoder_1.setMotorPwm(-pwm_command);
    Encoder_2.setMotorPwm(pwm_command);
}

// Balance test (closed-loop with disturbance)
void balance_test()
{
    unsigned long elapsed = millis() - phase_start_time;

    // Apply speed disturbance every 5 seconds
    if ((elapsed / 5000) % 2 == 0)
    {
        PID_speed.Setpoint = 50.0; // Forward push
    }
    else
    {
        PID_speed.Setpoint = -50.0; // Backward push
    }

    balanced_model();
}

// Data logging
void log_data()
{
    static unsigned long last_log = 0;
    if (millis() - last_log < 100)
        return; // 10 Hz logging
    last_log = millis();

    double time_s = (millis() - test_start_time) / 1000.0;
    double speed_1 = Encoder_1.getCurrentSpeed();
    double speed_2 = Encoder_2.getCurrentSpeed();
    double angleX = gyro.getAngleX();
    double gyroY = gyro.getGyroY();

    int pwm_left = (int)Encoder_1.getCurrentSpeed(); // Approximation
    int pwm_right = (int)Encoder_2.getCurrentSpeed();

    // CSV: time,phase,pwm_left,pwm_right,speed_1,speed_2,angleX,gyroY
    Serial.print(time_s, 2);
    Serial.print(",");
    Serial.print((int)current_phase);
    Serial.print(",");
    Serial.print(pwm_left);
    Serial.print(",");
    Serial.print(pwm_right);
    Serial.print(",");
    Serial.print(speed_1, 2);
    Serial.print(",");
    Serial.print(speed_2, 2);
    Serial.print(",");
    Serial.print(angleX, 2);
    Serial.print(",");
    Serial.println(gyroY, 2);
}

void setup()
{
    Serial.begin(115200);
    delay(1000);

    // Initialize encoders
    TCCR1A = _BV(WGM10);
    TCCR1B = _BV(CS11) | _BV(WGM12);
    TCCR2A = _BV(WGM21) | _BV(WGM20);
    TCCR2B = _BV(CS21);
    attachInterrupt(Encoder_1.getIntNum(), isr_process_encoder1, RISING);
    attachInterrupt(Encoder_2.getIntNum(), isr_process_encoder2, RISING);

    // Set encoder motion mode
    Encoder_1.setMotionMode(DIRECT_MODE);
    Encoder_2.setMotionMode(DIRECT_MODE);

    // Initialize gyro
    gyro.begin();
    delay(500);

    // Calibrate gyro
    for (int i = 0; i < 200; i++)
    {
        gyro.fast_update();
        delay(5);
    }

    // Initialize PID (values from control.cpp)
    PID_angle.P = 18.0;
    PID_angle.I = 0.0;
    PID_angle.D = 0.6;
    PID_angle.Setpoint = RELAX_ANGLE;

    PID_speed.P = -0.1;
    PID_speed.I = -0.25;
    PID_speed.D = 0.0;
    PID_speed.Setpoint = 0.0;

    PID_turn.P = 0.0;
    PID_turn.I = 0.0;
    PID_turn.D = 0.0;
    PID_turn.Setpoint = 0.0;

    Serial.println("=== SYSTEM IDENTIFICATION TEST ===");
    Serial.println("CSV Header: time,phase,pwm_left,pwm_right,speed_1,speed_2,angleX,gyroY");
    Serial.println("Phase 1 (0-30s): Motor open-loop test (WHEELS LIFTED!)");
    Serial.println("Phase 2 (30-60s): Balance closed-loop test (ON GROUND!)");
    Serial.println("READY");
    Serial.println("Waiting for START command from Python...");

    // Wait for 'S' (START) command from Serial
    while (true)
    {
        if (Serial.available() > 0)
        {
            char cmd = Serial.read();
            if (cmd == 'S' || cmd == 's')
            {
                Serial.println("START command received!");
                break;
            }
        }
        delay(10);
    }

    // Countdown
    for (int i = 3; i > 0; i--)
    {
        Serial.print("Starting in ");
        Serial.print(i);
        Serial.println("...");
        delay(1000);
    }

    Serial.println("=== TEST STARTED ===");

    test_start_time = millis();
    current_phase = PHASE_MOTOR_TEST;
    phase_start_time = millis();
}

void loop()
{
    unsigned long total_elapsed = millis() - test_start_time;

    // Update encoders (CRITICAL for speed calculation!)
    Encoder_1.loop();
    Encoder_2.loop();

    // State machine
    switch (current_phase)
    {
    case PHASE_MOTOR_TEST:
        motor_test();
        if (millis() - phase_start_time > MOTOR_TEST_DURATION)
        {
            current_phase = PHASE_BALANCE_TEST;
            phase_start_time = millis();
            Serial.println("# Switching to BALANCE TEST");
        }
        break;

    case PHASE_BALANCE_TEST:
        balance_test();
        if (millis() - phase_start_time > BALANCE_TEST_DURATION)
        {
            current_phase = PHASE_COMPLETE;
            Encoder_1.setMotorPwm(0);
            Encoder_2.setMotorPwm(0);
            Serial.println("# TEST COMPLETE");
        }
        break;

    case PHASE_COMPLETE:
        Encoder_1.setMotorPwm(0);
        Encoder_2.setMotorPwm(0);
        return;

    default:
        break;
    }

    log_data();

    // Emergency stop after 65 seconds
    if (total_elapsed > 65000)
    {
        move(1, 0);
        current_phase = PHASE_COMPLETE;
    }
}
