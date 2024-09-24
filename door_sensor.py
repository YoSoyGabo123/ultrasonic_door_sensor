import RPi.GPIO as GPIO
import time
import csv
from datetime import datetime

# Set GPIO Pins to the holes in the Raspberry Pi
GPIO_TRIGGER = 23
GPIO_ECHO = 24

# Set the Raspberry Pi numbering system on
GPIO.setmode(GPIO.BCM)
# Set which of the pins is going to output signal from the board to the sensor
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
# Set which of the pins will get the signal from the sensor to the board
GPIO.setup(GPIO_ECHO, GPIO.IN)


def measure_distance():
    """Trigger ultrasonic sensor and return the measured distance."""
    # This command starts the pulse
    GPIO.output(GPIO_TRIGGER, True)
    # This command makes the pulse be 0.00001 seconds long
    time.sleep(0.00001)
    # This command turns off the ultrasonic pulse
    GPIO.output(GPIO_TRIGGER, False)

    # Initialize times
    StartTime = time.time()
    StopTime = time.time()

    # Save StartTime
    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()

    # Save time of arrival
    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()

    # Time difference between start and arrival
    TimeElapsed = StopTime - StartTime
    # Calculate distance in centimeters
    return (TimeElapsed * 34300) / 2


def write_to_csv(index, date_time, milliseconds, people_detected):
    """Write detection data to a CSV file."""
    with open('people_log.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([index, date_time, milliseconds, people_detected])


def main():
    people_count = 0
    start_time = time.time()
    csv_index = 0  # To keep track of each entry's index

    # Variables for detection logic
    is_in_detection_window = False
    detection_window_start_time = 0

    # Create or overwrite the CSV file with headers
    with open('people_log.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Index", "Date and Time", "Time in Milliseconds", "People Detected"])

    print("Starting distance measurement...")

    try:
        while True:
            dist = measure_distance()
            current_time = time.time()
            print(f"Measured Distance = {dist:.2f} cm")

            if dist < 100:  # Assuming an object is detected within 100 cm
                if not is_in_detection_window:
                    # Detected a new person
                    people_count += 1
                    is_in_detection_window = True
                    detection_window_start_time = current_time
                    print(f"Person detected! Total count: {people_count}")
                else:
                    # Reset the detection window timer since we still detect the person
                    detection_window_start_time = current_time
            else:
                if is_in_detection_window and (current_time - detection_window_start_time) >= 0.7:
                    # Detection window has expired
                    is_in_detection_window = False

            # Check if it's time to log the detections
            if current_time - start_time >= 1800:  # 30 minutes
                # Log the number of people detected in the interval
                if people_count > 0:
                    elapsed_milliseconds = int((current_time - start_time) * 1000)
                    write_to_csv(csv_index, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), elapsed_milliseconds, people_count)
                    print(f"Logged {people_count} people at index {csv_index}")
                    csv_index += 1
                    people_count = 0  # Reset count after logging
                # Reset start_time for the next interval
                start_time = current_time

            time.sleep(0.05)  # Short sleep to reduce CPU load

    except KeyboardInterrupt:
        print("Measurement stopped by User")
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()
