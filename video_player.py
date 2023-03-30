#!/usr/bin/python
from __future__ import print_function, division

'''
Video player with precise frame selection

See show_help() function for supported features.

Author: Kyuhwa Lee
Imperial College London, 2014

'''

# global setting
PLAYER_POS = [100, 10]
WINDOW_SIZE = None # None or tuple, e.g. (1680, 1050)
KEYS = {'space':32, 'esc':27, 'home':80, 'backspace':8, 'end':87, 'lshift':225, 'rshift':226, 'enter':13,
        ',':44, '.':46, '0':48, 'c':99, 'd':100, 'e':101, 'f':102, '[':91, ']':93}


import os
import sys
import cv2
import time


class Timer(object):
    """
    Timer class

    if autoreset=True, timer is reset after any member function call

    """

    def __init__(self, autoreset=False):
        self.autoreset = autoreset
        self.reset()

    def sec(self):
        read = time.time() - self.ref
        if self.autoreset: self.reset()
        return read

    def msec(self):
        return self.sec() * 1000.0

    def reset(self):
        self.ref = time.time()

    def sleep_atleast(self, sec):
        """
        Sleep up to sec seconds
        It's more convenient if autoreset=True
        """
        timer_sec = self.sec()
        if timer_sec < sec:
            time.sleep(sec - timer_sec)
            if self.autoreset: self.reset()

def parse_path(file_path):
    """
    Input:
        full path
    Returns:
        self.dir = base directory of the file
        self.name = file name without extension
        self.ext = file extension
    """

    class path_info:
        def __init__(self, path):
            path_abs = os.path.realpath(path).replace('\\', '/')
            s = path_abs.split('/')
            f = s[-1].split('.')
            basedir = '/'.join(s[:-1])
            if len(f) == 1:
                name, ext = f[-1], ''
            else:
                name, ext = '.'.join(f[:-1]), f[-1]
            self.dir = basedir
            self.name = name
            self.ext = ext
            self.txt = 'self.dir=%s\nself.name=%s\nself.ext=%s\n' % (self.dir, self.name, self.ext)
        def __repr__(self):
            return self.txt
        def __str__(self):
            return self.txt

    return path_info(file_path)

def show_help():
    print('\n=== Controls ===')
    print('Space             : Pause / resume')
    print('Enter             : Toggle full screen')
    print('L-Shift / R-Shift : Frame -100 / +100')
    print('[ / ]             : Frame  -10 / +10')
    print('d / f             : Frame   -1 / +1')
    print('Home or Backspace : First frame')
    print('End or e          : Last frame')
    print(', / .             : Increase / decrease playback speed')
    print('0 (zero)          : Reset speed to 100%')
    print('c                 : Capture the current frame into a file')
    print('ESC               : Quit\n')

def show_video_info(cap):
    print('=== Video info ===')
    print('Frame rate: %.2f' % cap.get(cv2.CAP_PROP_FPS))
    print('Number of frames: %d' % cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print('Frame size: %d x %d' % (cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fourcc = ''.join([chr((int(cap.get(cv2.CAP_PROP_FOURCC)) >> 8 * i) & 0xFF) for i in range(4)])
    print('Codec (FourCC): %s' % fourcc)

def embed_msg(img, msg):
    cv2.putText(img, msg, (1,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)

def play_video(vfile):
    if not os.path.exists(vfile):
        raise FileNotFoundError('>> %s does not exist or accessible.' % vfile)

    # load video
    cap = cv2.VideoCapture(vfile)
    if cap is None or not cap.isOpened():
        raise RuntimeError('>> Error loading %s'% vfile)
    show_video_info(cap)

    # check the if the video header has valid number of frames
    frame_end = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_end)
    if cap.read()[0] is False:
        print('** Warning: Invalid number of frames in video header **')

    frame = 0
    fps_list = [0] * 10
    fps_index = 0
    frame_delay_raw = 1.0 / cap.get(cv2.CAP_PROP_FPS)
    frame_delay = frame_delay_raw
    ch = -1
    capseq = 0
    pause = False
    full_screen = False
    timer = Timer(autoreset=False)

    show_help()
    cv2.namedWindow(vfile)
    cv2.moveWindow(vfile, PLAYER_POS[0], PLAYER_POS[1])
    while True:
        # control playback speed
        timer.sleep_atleast(frame_delay)

        # calculate mean FPS
        time_currnet = timer.sec()
        timer.reset()
        fps_list[fps_index % len(fps_list)] = 1.0 / time_currnet
        fps = sum(fps_list) / len(fps_list)
        fps_index += 1

        # show image
        if frame != cap.get(cv2.CAP_PROP_POS_FRAMES):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
        ret, img = cap.read()
        embed_msg(img, 'Frame %d / %d (%.1f FPS)' % (frame, frame_end, fps))
        if img is not None:
            if WINDOW_SIZE is None:
                cv2.imshow(vfile, img)
            else:
                cv2.imshow(vfile, cv2.resize(img, WINDOW_SIZE))

        # process command
        if ch == KEYS['space']:
            pause = not pause
        elif ch == KEYS['lshift']:
            frame -= 100
        elif ch == KEYS['rshift']:
            frame += 100
        elif ch == KEYS[',']:
            frame_delay /= 2
        elif ch == KEYS['.']:
            frame_delay *= 2
        elif ch == KEYS['0']:
            frame_delay = frame_delay_raw
        elif ch == KEYS['d']:
            frame -= 1
            pause= True
        elif ch == KEYS['f']:
            frame += 1
            pause= True
        elif ch == KEYS['[']:
            frame -= 10
            pause= True
        elif ch == KEYS[']']:
            frame += 10
            pause = True
        elif ch == KEYS['home'] or ch == KEYS['backspace']:
            frame = 0
            pause = True
        elif ch == KEYS['end']:
            frame = frame_end
            pause = True
        elif ch == KEYS['c'] and img is not None:
            capfile= 'cap%02d.png'% capseq
            print('>> Image captured to %s'% capfile)
            cv2.imwrite(capfile, img)
            capseq += 1
        elif ch == KEYS['esc']:
            break
        elif ch == KEYS['enter']:
            cv2.destroyWindow(vfile)
            full_screen = not full_screen
            if full_screen:
                cv2.namedWindow(vfile, cv2.WND_PROP_FULLSCREEN)
                cv2.setWindowProperty(vfile, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.namedWindow(vfile)
                cv2.moveWindow(vfile, PLAYER_POS[0], PLAYER_POS[1])
        elif frame < frame_end and not pause:
            frame += 1

        # boundary check
        if frame < 0:
            frame = 0
        if frame > frame_end:
            frame = frame_end

        # get command (avoid arrow keys as codes may dependent on OS)
        ch = cv2.waitKey(1)
        if ch == KEYS['esc']:
            break
        if ch > 0: print(ch)

    cap.release()
    cv2.destroyWindow(vfile)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('USAGE: python %s.py [VIDEO_FILE]' % parse_path(sys.argv[0]).name)
        sys.exit()

    play_video(sys.argv[1])
