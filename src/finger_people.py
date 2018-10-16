"""
This is the main loop of the controller.

It reads video, passes it through the CNN, and performs an input action to the
game based on the CNN's output.
"""

import cv2
import keras
import argparse
import numpy as np
from capture import Capture, CapType
from cnn_input import CnnInput
import dataset
from game_input import GameInput

cap_source_template = 'http://192.168.0.{}:8080/video'
sticky_size = 1

def finger_people(model_path, cap_source, cap_type):
    model = keras.models.load_model(model_path)
    cap = Capture(cap_source, cap_type)
    game_input = GameInput()

    ret, first_frame = cap.read()
    cnn_input = CnnInput(first_frame)

    action = None
    prev_label = None
    sticky = 0

    h = first_frame.shape[0]

    while cap.is_opened():
        ret, frame = cap.read()
        if not ret:
            break

        ''' CNN '''
        cnn_input.update(frame)
        cnn_input_4d = np.expand_dims(cnn_input.frame, 0)
        prediction = model.predict(cnn_input_4d)

        class_id = np.argmax(prediction)
        class_label = dataset.id_to_class[class_id]
        if class_label == 'walk':
            class_label = 'run'

        ''' STICKY OUTPUT '''
        if class_label != prev_label:
            sticky_i = 0
        if sticky_i < sticky_size:
            sticky_i += 1
        else:
            action = class_label
        prev_label = class_label

        ''' GAME INPUT '''
        game_input.do(action)

        ''' OUTPUT / DEBUG '''
        cnn_input_show = cv2.resize(cnn_input.frame, (h,h))
        cv2.putText(frame, action, (2, h-3), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0,255,0))
        cv2.imshow('frame', np.hstack((frame, cnn_input_show)))

        ''' KEYBOARD INPUT '''
        key = cv2.waitKey(2) & 0xFF
        if key == ord('q'):
            break
        if key == ord('g'):
            game_input.enabled = not game_input.enabled

    cap.kill()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('model', type=str,
            help='Path to gesture recognition .hdf5 keras model')
    parser.add_argument('cap_source', type=str,
            help='The source of the Capture object.')
    parser.add_argument('cap_type', nargs='*', default=['video'],
            help='The type of the Capture device used as video input.')
    args = parser.parse_args()

    model_path = args.model

    cap_source = args.cap_source
    if args.cap_source.isdigit():
        cap_source = cap_source_template.format(str(args.cap_source))

    cap_type = args.cap_type[0].lower()
    if cap_type == 'video':
        cap_type = CapType.VIDEO
    elif cap_type == 'camera':
        cap_type = CapType.CAMERA


    finger_people(model_path, cap_source, cap_type)