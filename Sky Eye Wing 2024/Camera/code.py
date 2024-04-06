import time

import board
import busio
import digitalio

import adafruit_mlx90640
import adafruit_rfm9x


spi = board.SPI()

cs = digitalio.DigitalInOut(board.D5)
reset = digitalio.DigitalInOut(board.D6)

rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915.0)


i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)

mlx = adafruit_mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C")
print([hex(i) for i in mlx.serial_number])

# mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ


def imageToMessage(frame):
    s = ""
    for i in frame:
        s = s + str(round(i)) + ","
        # s = s + str(chr(round(i)))
    return str(1)
    return s[:-1]
    return "" + str(chr(round(frame[0])))

frame = [0] * 768

def sendImage(frame):
    imageSize = 768
    packets = 16
    packetLength = imageSize // packets

    count = 0
    for i in range(packets):
        print(i)
        j = i * packetLength
        subFrame = frame[j:j+packetLength]
        message = str(i) + ":"
        for k in subFrame:
            message = message + str(round(k)) + ','
        #print(message)
        rfm9x.send(message[:-1])

    # for i in frame:

    #     message = str(count) + ": " + str(round(i))
    #     count += 1
    #     # print('sending: ' + message)
    #     rfm9x.send(message)
    print('sent')



start_time = time.monotonic() - 10
stamp = time.monotonic()

while True:
    stamp = time.monotonic()
    print(stamp)

    if (stamp-start_time) > 5:

        try:
            mlx.getFrame(frame)
        except ValueError:
            # these happen, no biggie - retry
            continue

        #    print("Time for data aquisition: %0.2f s" % (time.monotonic()-stamp))



        print('sending')

        sendImage(frame)
        start_time = stamp
