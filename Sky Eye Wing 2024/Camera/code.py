import time

import board
import busio
import digitalio

import adafruit_mlx90640
import adafruit_rfm9x

# Initialize RFM9x LoRa module
spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)
reset = digitalio.DigitalInOut(board.D6)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915.0)

# Initialize I2C communication for MLX90640 thermal camera
i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)
mlx = adafruit_mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C")
print([hex(i) for i in mlx.serial_number])

# Set refresh rate of MLX90640
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_8_HZ

# Function to convert frame to a message format
def imageToMessage(frame):
    s = ""
    for i in frame:
        s = s + str(round(i)) + ","
    return s[:-1]


# Initialize a frame buffer
frame = [0] * 768

# Function to send image frame over RFM9x
def sendImage(frame):
    imageSize = 768
    packets = 16
    packetLength = imageSize // packets

    for i in range(packets):
        print(i)
        j = i * packetLength
        subFrame = frame[j : j + packetLength]
        message = str(i) + ":"
        for k in subFrame:
            message = message + str(round(k)) + ","
        rfm9x.send(message[:-1])
    print("Image frame sent")


# Main loop to continuously capture and send frames
start_time = time.monotonic() - 1  # Start with a smaller initial time difference
stamp = time.monotonic()

while True:
    stamp = time.monotonic()
    print("Current timestamp:", stamp)

    # Check if it's time to capture a new frame (every 1 second)
    if (stamp - start_time) > 0:
        try:
            mlx.getFrame(frame)
        except ValueError:
            # Handle potential errors in frame acquisition
            continue
        print("Sending image frame...")
        sendImage(frame)
        start_time = stamp  # Update start time for next frame capture
