#!/usr/bin/env python3
import pyaudio
import audioop as aop
import numpy as np
import struct
import math
import sys
import time
import graphics

class SoundVisualizer:
    __maximum = 1
    __avg_max = 0
    __cnt1 = 0
    __cnt2 = 0
    __values = None
    __multiplier = 9


    __curr_pos = 0
    __graphics = None
    __p = None


    CHUNK_SIZE = 512
    RATE = 44100
    NUM_CHANNELS = 2
    DEV_INDEX = 0

    WINDOW = 1000
    WIDTH = 1000


    def __init__(self):
        self.__graphics = graphics.Graphics()
        self.__p = pyaudio.PyAudio()
        self.__values = list()

    def run(self):
        # entry point
        self.__init_scrn()
        self.__select_device()
        self.__graphics.clear()
        self.__select_buffer()
        self.__graphics.nodelay(1)
        self.__graphics.cbreak()
        self.__graphics.keypad(1)
        s = self.__init_audio_stream()
        while True:
            self.visualize(s)
            time.sleep(0.01)

    def __init_scrn(self):
        # initializes screen, updates height and width and refreshes it
        self.__graphics.update()
        self.WINDOW = self.__graphics.get_height() - 1
        self.WIDTH = self.__graphics.get_width()
        self.__graphics.refresh()

    def __select_device(self):
        # prompts a menu for selecting the input device
        self.__graphics.nodelay(0)
        self.__graphics.noecho()
        while True:
            info = self.__p.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            devices = {}
            x = 0
            for i in range(0, numdevices):
                channels = self.__p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')
                if (channels) > 0:
                    name = self.__p.get_device_info_by_host_api_device_index(0, i).get('name')
                    rate = self.__p.get_device_info_by_index(i).get('defaultSampleRate')
                    devices[x] = (name, i, channels, rate)
                    self.__graphics.write (x + 1, 2, str(x) + ": " + name +  ", " + str(channels) + " channels, " + str(rate) + "\n")
                    x = x + 1

            self.__graphics.write(x+2, 2, "ESC: Exit \n\n")


            c = self.__graphics.input("Select a device: ")
            if c != self.__graphics.ERR:
                if c >= ord('0') and c < ord('0') + len(devices):
                    c = c - ord('0')
                    self.RATE = int(devices[c][3])
                    self.NUM_CHANNELS = devices[c][2]
                    self.DEV_INDEX = devices[c][1]
                    break
                elif c == self.__graphics.KEY_ESC:
                    self.__graphics.exit()
                    sys.exit()

    def __select_buffer(self):
        # promts a menue for selecting the buffer size
        while True:
            for i in range(8, 14):
                    self.__graphics.write (i - 8 + 1, 2, str(i - 8) + ": " + str(2**i))

            self.__graphics.write(i-5, 2, "ESC: Exit\n\n")


            c = self.__graphics.input("Select the size of the buffer: ")
            if c != self.__graphics.ERR:
                if c >= ord('0') and c < ord('7'):
                    self.CHUNK_SIZE = 2**(c - ord('0') + 6)
                    break
                elif c == self.__graphics.KEY_ESC:
                    self.__graphics.exit()
                    sys.exit()

    def __init_audio_stream(self):
        # initializes audio stream
        return self.__p.open(rate=self.RATE, channels=self.NUM_CHANNELS, format=pyaudio.paInt16, input=True, input_device_index=self.DEV_INDEX, frames_per_buffer=self.CHUNK_SIZE)

    def __print_bar(self, line, name, color, value, max):
        # prints the bars that visualize different frequency ranges
        s = str(( name.rjust(8, " ") + "|".ljust(int(value/max * self.WIDTH), color).ljust(self.WIDTH - 8, " ")))
        self.__graphics.write(line, 0, s[:self.WIDTH])

    def __calculate_amp_max(self, stream):
        # calculate the amplitude and maximum amplitude
        block = stream.read(self.CHUNK_SIZE, exception_on_overflow = False)
        amp = aop.rms(block, self.NUM_CHANNELS)
        max = aop.max(block, self.NUM_CHANNELS)
        if max > self.__maximum:
                self.__maximum = max
        self.__cnt1 = self.__cnt1 + 1
        self.__avg_max = (self.__avg_max + max) / 2
        if self.__cnt1 is 50:
            if self.__avg_max < self.__maximum * 0.4:
                self.__maximum = int(self.__maximum * 0.4) + 1
                self.__cnt1 = 0
        return amp, self.__maximum, block

    def __calculate_freq_max(self, block):
        # calculates the different frequency ranges and
        mono = aop.tomono(block, self.NUM_CHANNELS, 1.0, 1.0)

        data = struct.unpack('{n}h'.format(n=self.CHUNK_SIZE), mono)
        data = np.array(data)

        sp = np.fft.rfft(data)
        frequencies = np.array(np.abs(sp))

        f = np.fft.fftfreq(int(self.CHUNK_SIZE/self.NUM_CHANNELS)+1, 1/self.RATE)
        m = f.size - 2
        if len(self.__values) == 0:
            for i in range(0,int(m/2)):
                self.__values.append(0)
        ranges = list()
        for i in range(0, int(m/2)):
                ranges.append(np.array([frequencies[i], frequencies[m-i]]))
                self.__values[i] = (self.__values[i] + np.amax(ranges[i])) / 2
        self.__cnt2 = self.__cnt2 + 1
        if self.__cnt2 > 50:
            for i in range(0, int(m/2)):
                self.__values[i] = np.amax(ranges[i])
            self.__cnt2 = 0
        return self.__values, f, m

    def visualize(self, stream):
        if stream.get_read_available():
            amp, max, block = self.__calculate_amp_max(stream)

            self.__graphics.clear()

            self.__print_bar(0, " Level", "█", amp * 3/2, max)

            vals, f, m = self.__calculate_freq_max(block)

            state = 0

            for i in range(self.__curr_pos, self.__curr_pos + self.WINDOW):
                if i >= len(vals) or i >= len(f):
                    break
                c = "?"
                if state == 0:
                    c = "*"
                    state = 1
                elif state == 1:
                    c = "#"
                    state = 2
                elif state == 2:
                    c = "+"
                    state = 3
                elif state == 3:
                    c = "="
                    state = 0
                else:
                    c = "*"
                    state = 1

                self.__print_bar(i - self.__curr_pos + 1, str(int(f[i])) + "Hz", c, vals[i], 10000000000 / (int(f[1])*self.__multiplier))

            self.__graphics.write_footer("ESC:Exit  ↑:Up  ↓:Down  →:Page down  ←:Page up  +/=:Zoom+  -:Zoom-  Zoom:" + str(self.__multiplier+1))
            self.__graphics.refresh()

            c = self.__graphics.input()
            if c != self.__graphics.ERR:
                if c == self.__graphics.KEY_RESIZE:
                    self.__init_scrn()
                if c == self.__graphics.KEY_UP:
                    if self.__curr_pos > 0:
                        self.__curr_pos = self.__curr_pos - 1
                elif c == self.__graphics.KEY_DOWN:
                    if self.__curr_pos + self.WINDOW < int(m/2) - 1:
                        self.__curr_pos = self.__curr_pos + 1
                elif c == ord(' ') or c == self.__graphics.KEY_RIGHT:
                    if self.__curr_pos < int(m/2) - self.WINDOW - 1:
                        self.__curr_pos = self.__curr_pos + self.WINDOW
                    else:
                        self.__curr_pos = int(m/2) - self.WINDOW - 1
                elif c == self.__graphics.KEY_LEFT:
                    if self.__curr_pos > self.WINDOW:
                        self.__curr_pos = self.__curr_pos - self.WINDOW
                    else:
                        self.__curr_pos = 0
                elif c == ord('+') or c == ord('=') :
                    self.__multiplier = self.__multiplier + 1
                elif c == ord('-'):
                    self.__multiplier = self.__multiplier - 1
                elif c == self.__graphics.KEY_ESC:
                    self.__graphics.exit()
                    sys.exit()

if __name__ == "__main__":
    sv = SoundVisualizer()
    sv.run()
