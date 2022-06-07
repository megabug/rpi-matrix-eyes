#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2020 Phillip Burgess for Adafruit Industries, ported 2022 by mattd
# SPDX-License-Identifier: MIT

import math
import random
import time

import PIL.Image
import rgbmatrix

from data.werewolf_2x.data import EYE_DATA

# from data.werewolf.data import EYE_DATA
# from data.cyclops.data import EYE_DATA
# from data.kobold.data import EYE_DATA
# from data.adabot.data import EYE_DATA
# from data.skull.data import EYE_DATA


# Pixel coords of eye image when centered ('neutral' position)
EYE_CENTER = (
    (EYE_DATA["eye_move_min"][0] + EYE_DATA["eye_move_max"][0]) / 2,
    (EYE_DATA["eye_move_min"][1] + EYE_DATA["eye_move_max"][1]) / 2,
)
# Max eye image motion delta from center
EYE_RANGE = (
    abs(EYE_DATA["eye_move_max"][0] - EYE_DATA["eye_move_min"][0]) / 2,
    abs(EYE_DATA["eye_move_max"][1] - EYE_DATA["eye_move_min"][1]) / 2,
)
# Motion bounds of upper and lower eyelids
UPPER_LID_MIN = (
    min(EYE_DATA["upper_lid_open"][0], EYE_DATA["upper_lid_closed"][0]),
    min(EYE_DATA["upper_lid_open"][1], EYE_DATA["upper_lid_closed"][1]),
)
UPPER_LID_MAX = (
    max(EYE_DATA["upper_lid_open"][0], EYE_DATA["upper_lid_closed"][0]),
    max(EYE_DATA["upper_lid_open"][1], EYE_DATA["upper_lid_closed"][1]),
)
LOWER_LID_MIN = (
    min(EYE_DATA["lower_lid_open"][0], EYE_DATA["lower_lid_closed"][0]),
    min(EYE_DATA["lower_lid_open"][1], EYE_DATA["lower_lid_closed"][1]),
)
LOWER_LID_MAX = (
    max(EYE_DATA["lower_lid_open"][0], EYE_DATA["lower_lid_closed"][0]),
    max(EYE_DATA["lower_lid_open"][1], EYE_DATA["lower_lid_closed"][1]),
)


class Sprite:
    def __init__(self, filename, transparent=None):
        self.image = PIL.Image.open(filename).convert("RGBA")

        if transparent is not None:
            for y in range(self.image.size[1]):
                for x in range(self.image.size[0]):
                    if self.image.getpixel((x, y))[:3] == transparent:
                        self.image.putpixel((x, y), (0, 0, 0, 0))

        self.pos: tuple[int, int] = (0, 0)


options = rgbmatrix.RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 2
options.gpio_slowdown = 4
matrix = rgbmatrix.RGBMatrix(options=options)

stage = PIL.Image.new("RGBA", (matrix.width * 2, matrix.height * 2))

sprites = [
    Sprite(EYE_DATA["eye_image"]),
    Sprite(EYE_DATA["lower_lid_image"], EYE_DATA.get("transparent")),
    Sprite(EYE_DATA["upper_lid_image"], EYE_DATA.get("transparent")),
    Sprite(EYE_DATA["stencil_image"], EYE_DATA.get("transparent")),
]

eye_prev = (0, 0)
eye_next = (0, 0)
move_state = False  # Initially stationary
move_event_duration = random.uniform(0.1, 3)  # Time to first move
blink_state = 2  # Start eyes closed
blink_event_duration = random.uniform(0.25, 0.5)  # Time for eyes to open
time_of_last_move_event = time_of_last_blink_event = time.monotonic()

while True:
    now = time.monotonic()

    # Eye movement ---------------------------------------------------------

    if now - time_of_last_move_event > move_event_duration:
        time_of_last_move_event = now  # Start new move or pause
        move_state = not move_state  # Toggle between moving & stationary
        if move_state:  # Starting a new move?
            move_event_duration = random.uniform(0.08, 0.17)  # Move time
            angle = random.uniform(0, math.pi * 2)
            # (0,0) in center, NOT pixel coords
            eye_next = (
                math.cos(angle) * EYE_RANGE[0],
                math.sin(angle) * EYE_RANGE[1],
            )
        else:  # Starting a new pause
            move_event_duration = random.uniform(0.04, 3)  # Hold time
            eye_prev = eye_next

    # Fraction of move elapsed (0.0 to 1.0), then ease in/out 3*e^2-2*e^3
    ratio = (now - time_of_last_move_event) / move_event_duration
    ratio = 3 * ratio * ratio - 2 * ratio * ratio * ratio
    eye_pos = (
        eye_prev[0] + ratio * (eye_next[0] - eye_prev[0]),
        eye_prev[1] + ratio * (eye_next[1] - eye_prev[1]),
    )

    # Blinking -------------------------------------------------------------

    if now - time_of_last_blink_event > blink_event_duration:
        time_of_last_blink_event = now  # Start change in blink
        blink_state += 1  # Cycle paused/closing/opening
        if blink_state == 1:  # Starting a new blink (closing)
            blink_event_duration = random.uniform(0.03, 0.07)
        elif blink_state == 2:  # Starting de-blink (opening)
            blink_event_duration *= 2
        else:  # Blink ended, paused
            blink_state = 0
            blink_event_duration = random.uniform(blink_event_duration * 3, 4)

    if blink_state:  # Currently in a blink?
        # Fraction of closing or opening elapsed (0.0 to 1.0)
        ratio = (now - time_of_last_blink_event) / blink_event_duration
        if blink_state == 2:  # Opening
            ratio = 1.0 - ratio  # Flip ratio so eye opens instead of closes
    else:  # Not blinking
        ratio = 0

    # Eyelid tracking ------------------------------------------------------

    # Initial estimate of 'tracked' eyelid positions
    upper_lid_pos = (
        EYE_DATA["upper_lid_center"][0] + eye_pos[0],
        EYE_DATA["upper_lid_center"][1] + eye_pos[1],
    )
    lower_lid_pos = (
        EYE_DATA["lower_lid_center"][0] + eye_pos[0],
        EYE_DATA["lower_lid_center"][1] + eye_pos[1],
    )
    # Then constrain these to the upper/lower lid motion bounds
    upper_lid_pos = (
        min(max(upper_lid_pos[0], UPPER_LID_MIN[0]), UPPER_LID_MAX[0]),
        min(max(upper_lid_pos[1], UPPER_LID_MIN[1]), UPPER_LID_MAX[1]),
    )
    lower_lid_pos = (
        min(max(lower_lid_pos[0], LOWER_LID_MIN[0]), LOWER_LID_MAX[0]),
        min(max(lower_lid_pos[1], LOWER_LID_MIN[1]), LOWER_LID_MAX[1]),
    )
    # Then interpolate between bounded tracked position to closed position
    upper_lid_pos = (
        upper_lid_pos[0] + ratio * (EYE_DATA["upper_lid_closed"][0] - upper_lid_pos[0]),
        upper_lid_pos[1] + ratio * (EYE_DATA["upper_lid_closed"][1] - upper_lid_pos[1]),
    )
    lower_lid_pos = (
        lower_lid_pos[0] + ratio * (EYE_DATA["lower_lid_closed"][0] - lower_lid_pos[0]),
        lower_lid_pos[1] + ratio * (EYE_DATA["lower_lid_closed"][1] - lower_lid_pos[1]),
    )

    # Move eye sprites -----------------------------------------------------

    sprites[0].pos = (
        int(EYE_CENTER[0] + eye_pos[0] + 0.5),
        int(EYE_CENTER[1] + eye_pos[1] + 0.5),
    )
    sprites[2].pos = (
        int(upper_lid_pos[0] + 0.5),
        int(upper_lid_pos[1] + 0.5),
    )
    sprites[1].pos = (
        int(lower_lid_pos[0] + 0.5),
        int(lower_lid_pos[1] + 0.5),
    )

    # Render ---------------------------------------------------------------

    for sprite in sprites:
        stage.alpha_composite(
            sprite.image,
            (sprite.pos[0] + stage.size[0] // 2, sprite.pos[1] + stage.size[1] // 2),
        )

    matrix.SetImage(
        stage.crop((stage.size[0] // 2, stage.size[1] // 2) + stage.size)
        .resize((matrix.width, matrix.height))
        .convert("RGB")
    )
