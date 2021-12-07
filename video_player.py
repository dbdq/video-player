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
KEYS = {'left':2424832, 'right':2555904, 'up':2490368, 'down':2621440,
        'pgup':2162688, 'pgdn':2228224, 'home':2359296, 'end':2293760,
       'space':32, 'esc':27, ',':44, '.':46, '0':48, 'c':99, 'f':102, '[':91, ']':93}

import os
import sys
import cv2 as cv
import q_common as qc

def show_help():
    print('\n=== Controls ===')
    print('Space        : Pause / resume')
    print('f            : Toggle full screen')
    print('Left / Right : Frame -100 / +100')
    print('[ / ]        : Frame  -10 / +10')
    print(', / .        : Frame   -1 / +1')
    print('Home / End   : First / last frame')
    print('Up / Down    : Increase / decrease playback speed')
    print('0 (zero)     : Reset speed to 100%')
    print('c            : Capture the current frame into a file')
    print('ESC          : Quit\n')

def show_video_info(cap):
    print('=== Video info ===')
    print('Frame rate: %.2f' % cap.get(cv.CAP_PROP_FPS))
    print('Number of frames: %d' % cap.get(cv.CAP_PROP_FRAME_COUNT))
    print('Frame size: %d x %d' % (cap.get(cv.CAP_PROP_FRAME_WIDTH), cap.get(cv.CAP_PROP_FRAME_HEIGHT)))
    fourcc = ''.join([chr((int(cap.get(cv.CAP_PROP_FOURCC)) >> 8 * i) & 0xFF) for i in range(4)])
    print('Codec (FourCC): %s' % fourcc)

def embed_msg(img, msg):
    cv.putText(img, msg, (1,15), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255))

def play_video(vfile):
    if not os.path.exists(vfile):
        raise FileNotFoundError('>> %s does not exist or accessible.' % vfile)

    # load video
    cap = cv.VideoCapture(vfile)
    if cap is None or not cap.isOpened():
        raise RuntimeError('>> Error loading %s'% vfile)
    show_video_info(cap)

    # check the if the video header has valid number of frames
    frame_end = int(cap.get(cv.CAP_PROP_FRAME_COUNT)) - 1
    cap.set(cv.CAP_PROP_POS_FRAMES, frame_end)
    if cap.read()[0] is False:
        print('** Warning: Invalid number of frames in video header **')

    frame = 0
    fps_list = [0] * 10
    fps_index = 0
    frame_delay_raw = 1.0 / cap.get(cv.CAP_PROP_FPS)
    frame_delay = frame_delay_raw
    ch = -1
    capseq = 0
    pause = False
    full_screen = False
    timer = qc.Timer(autoreset=False)

    show_help()
    cv.namedWindow(vfile)
    cv.moveWindow(vfile, PLAYER_POS[0], PLAYER_POS[1])
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
        if frame != cap.get(cv.CAP_PROP_POS_FRAMES):
            cap.set(cv.CAP_PROP_POS_FRAMES, frame)
        ret, img = cap.read()
        embed_msg(img, 'Frame %d / %d (%.1f FPS)' % (frame, frame_end, fps))
        if img is not None:
            if WINDOW_SIZE is None:
                cv.imshow(vfile, img)
            else:
                cv.imshow(vfile, cv.resize(img, WINDOW_SIZE))

        # process command
        if ch == KEYS['space']:
            pause = not pause
        elif ch == KEYS['left']:
            frame -= 100
        elif ch == KEYS['right']:
            frame += 100
        elif ch == KEYS['up']:
            frame_delay /= 2
        elif ch == KEYS['down']:
            frame_delay *= 2
        elif ch == KEYS['0']:
            frame_delay = frame_delay_raw
        elif ch == KEYS[',']:
            frame -= 1
            pause= True
        elif ch == KEYS['.']:
            frame += 1
            pause= True
        elif ch == KEYS['[']:
            frame -= 10
            pause= True
        elif ch == KEYS[']']:
            frame += 10
            pause = True
        elif ch == KEYS['home']:
            frame = 0
            pause = True
        elif ch == KEYS['end']:
            frame = frame_end
            pause = True
        elif ch == KEYS['c'] and img is not None:
            capfile= 'cap%02d.png'% capseq
            print('>> Image captured to %s'% capfile)
            cv.imwrite(capfile, img)
            capseq += 1
        elif ch == KEYS['esc']:
            break
        elif ch == KEYS['f']:
            cv.destroyWindow(vfile)
            full_screen = not full_screen
            if full_screen:
                cv.namedWindow(vfile, cv.WND_PROP_FULLSCREEN)
                cv.setWindowProperty(vfile, cv.WND_PROP_FULLSCREEN, cv.WINDOW_FULLSCREEN)
            else:
                cv.namedWindow(vfile)
                cv.moveWindow(vfile, PLAYER_POS[0], PLAYER_POS[1])
        elif frame < frame_end and not pause:
            frame += 1

        # boundary check
        if frame < 0:
            frame = 0
        if frame > frame_end:
            frame = frame_end

        # get command
        ch = cv.waitKeyEx(1)
        if ch == KEYS['esc']:
            break

    cap.release()
    cv.destroyWindow(vfile)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('USAGE: python %s.py [VIDEO_FILE]' % qc.parse_path(sys.argv[0]).name)
        sys.exit()

    play_video(sys.argv[1])
