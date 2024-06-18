# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import displayio
import digitalio
import terminalio
from adafruit_display_text.label import Label
from simpleio import map_range
import adafruit_rfm9x

THRESHOLD_TEMP=30

#In Celsius
#Temp of fire is 815 Celsius

spi = board.SPI()

cs = digitalio.DigitalInOut(board.D10)
reset = digitalio.DigitalInOut(board.D11)
rfm9x = adafruit_rfm9x.RFM9x(spi, cs, reset, 915.0)


number_of_colors = 64  # Number of color in the gradian
last_color = number_of_colors - 1  # Last color in palette
palette = displayio.Palette(number_of_colors)  # Palette with all our colors

## Heatmap code inspired from: http://www.andrewnoske.com/wiki/Code_-_heatmaps_and_color_gradients
color_A = [
    [0, 0, 0],
    [0, 0, 255],
    [0, 255, 255],
    [0, 255, 0],
    [255, 255, 0],
    [255, 0, 0],
    [255, 255, 255],
]
color_B = [[0, 0, 255], [0, 255, 255], [0, 255, 0], [255, 255, 0], [255, 0, 0]]
color_C = [[0, 0, 0], [255, 255, 255]]
color_D = [[0, 0, 255], [255, 0, 0]]

color = color_B
NUM_COLORS = len(color)


def MakeHeatMapColor():
    for c in range(number_of_colors):
        value = c * (NUM_COLORS - 1) / last_color
        idx1 = int(value)  # Our desired color will be after this index.
        if idx1 == value:  # This is the corner case
            red = color[idx1][0]
            green = color[idx1][1]
            blue = color[idx1][2]
        else:
            idx2 = idx1 + 1  # ... and before this index (inclusive).
            fractBetween = value - idx1  # Distance between the two indexes (0-1).
            red = int(
                round((color[idx2][0] - color[idx1][0]) * fractBetween + color[idx1][0])
            )
            green = int(
                round((color[idx2][1] - color[idx1][1]) * fractBetween + color[idx1][1])
            )
            blue = int(
                round((color[idx2][2] - color[idx1][2]) * fractBetween + color[idx1][2])
            )
        palette[c] = (0x010000 * red) + (0x000100 * green) + (0x000001 * blue)


MakeHeatMapColor()

# Bitmap for colour coded thermal value
image_bitmap = displayio.Bitmap(32, 24, number_of_colors)
# Create a TileGrid using the Bitmap and Palette
image_tile = displayio.TileGrid(image_bitmap, pixel_shader=palette)
# Create a Group that scale 32*24 to 128*96
image_group = displayio.Group(scale=4)
image_group.append(image_tile)

scale_bitmap = displayio.Bitmap(number_of_colors, 1, number_of_colors)
# Create a Group Scale must be 128 divided by number_of_colors
scale_group = displayio.Group(scale=2)
scale_tile = displayio.TileGrid(scale_bitmap, pixel_shader=palette, x=0, y=60)
scale_group.append(scale_tile)

for i in range(number_of_colors):
    scale_bitmap[i, 0] = i  # Fill the scale with the palette gradian

# Create the super Group
group = displayio.Group()

min_label = Label(terminalio.FONT, color=palette[0], x=0, y=110)
max_label = Label(terminalio.FONT, color=palette[last_color], x=80, y=110)
skyeyerangelabel = Label(terminalio.FONT, color=(137,207,240), x=135, y=10)
seperatelabel = Label(terminalio.FONT, color=(255,255,255), x=135, y=20)
statustitlelabel = Label(terminalio.FONT, color=(255,255,255), x=135, y=30)
statustextlabel = Label(terminalio.FONT, color=(255,0,0), x=135, y=40)
lastimagelabel = Label(terminalio.FONT, color=(210,210,210), x=135, y=50)
timestamplabel = Label(terminalio.FONT, color=(200,200,200), x=135, y=60)
linelabel = Label(terminalio.FONT, color=(255,255,255), x=135, y=70)


statslabel = Label(terminalio.FONT, color=(255,255,255), x=135, y=80)
thresholdlabel = Label(terminalio.FONT, color=(210,210,210), x=135, y=90)
thresholdValueLabel = Label(terminalio.FONT, color=(200,200,200), x=135, y=100)
seperatevertlabel = Label(terminalio.FONT, color=(190,190,190), x=135, y=110)
seperatevert2label = Label(terminalio.FONT, color=(190,190,190), x=135, y=120)

skyeyerangelabel.text = "Sky Eye Wing V2.0"
seperatelabel.text = "-----------------"
statustitlelabel.text = "SIGNAL STATUS:"
statustextlabel.text = "No Signal..."
lastimagelabel.text = "Latest Image: N/A"
timestamplabel.text = "0"
linelabel.text = "-----------------"
statslabel.text = "FIRE STATUS:"
thresholdlabel.text = "AI Fire Detect --%:"
thresholdValueLabel.text = "Fire Temp: {:.0}C".format(THRESHOLD_TEMP)
seperatevertlabel.text = "|       |       |"
seperatevert2label.text = "|       |       |"
# Add all the sub-group to the SuperGroup
group.append(image_group)
group.append(scale_group)
group.append(min_label)
group.append(max_label)
group.append(skyeyerangelabel)
group.append(seperatelabel)
group.append(statustitlelabel)
group.append(statustextlabel)
group.append(lastimagelabel)
group.append(timestamplabel)
group.append(linelabel)
group.append(statslabel)
group.append(thresholdlabel)
group.append(thresholdValueLabel)
group.append(seperatevertlabel)
group.append(seperatevert2label)
# Add the SuperGroup to the Display
board.DISPLAY.show(group)

min_t = 20  # Initial minimum temperature range, before auto scale
max_t = 37  # Initial maximum temperature range, before auto scale


image_size = 24 * 32

image = []
image_index = 0

start_time = time.monotonic()
timeout = 5

stamp = time.monotonic() - start_time


def showImage():
    global image
    global packet_index
    global image_bitmap
    global last_color
    global min_t, max_t
    #global threshold_count


    if len(image) == image_size:

        statustextlabel.text = "Image Recieved!"
        lastimagelabel.text = "At %0.1f Seconds" % (stamp)

        # Calculate the percent
        fire_count = 0


        mini = image[0]  # Define a min temperature of current image
        maxi = image[0]  # Define a max temperature of current image

        for h in range(24):
            for w in range(32):
                t = image[h * 32 + w]
                if(t >= THRESHOLD_TEMP):
                    fire_count = fire_count + 1
                if t > maxi:
                    maxi = t
                if t < mini:
                    mini = t
                image_bitmap[w, (23 - h)] = int(map_range(t, min_t, max_t, 0, last_color))

        fire_percent = fire_count / 768
        thresholdlabel.text  = "Fire Detect: {:.0%}".format(fire_percent)


        min_label.text = "%0.2f" % (min_t)

        max_string = "%0.2f" % (max_t)
        max_label.x = 120 - (5 * len(max_string))  # Tricky calculation to left align
        max_label.text = max_string

        min_t = mini  # Automatically change the color scale
        max_t = maxi
    else:
        statustextlabel.text = "Image Lost..."

    packet_index = 0
    print(len(image))
    image = []
    #threshold_count = 0


imageSize = 768
packets = 16
packetLength = imageSize // packets

packet_index = 0
#threshold_count = 0

while True:
    stamp = time.monotonic() - start_time
    timestamplabel.text = "Scout Time: %0.1f" % (stamp)

    packet = rfm9x.receive()

    if packet is not None:
        packet_text = str(packet, 'ascii')
        packet_data =  packet_text.split(':')

        print(packet_data[0])

        if int(packet_data[0]) == packet_index:
            packet_index += 1
            str_data = packet_data[1].split(',')
            for s in str_data:
#                if int(s) >= THRESHOLD_TEMP:
#                    threshold_count=threshold_count+1
                image.append(int(s))
        else:
            #missed packet
            pixel = 30
            if len(image) > 1:
                pixel = image[-1]
            for x in range(packetLength):
                pass
                image.append(pixel)

            print('Missed Packet...', packet_index, packet_data[0])
            print(packet_data)
            packet_index = int(packet_data[0]) + 1
            str_data = packet_data[1].split(',')
            for s in str_data:
                image.append(int(s))
            pass


        if packet_index >= packets:
            print('showImage')
            showImage()

    else:
        print('Listining...')
