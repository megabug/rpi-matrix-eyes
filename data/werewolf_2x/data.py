# SPDX-FileCopyrightText: 2020 Phillip Burgess for Adafruit Industries
#
# SPDX-License-Identifier: MIT

double = lambda x, y: (x * 2, y * 2)

""" Configuration data for the werewolf eyes """
EYE_PATH = __file__[: __file__.rfind("/") + 1]
EYE_DATA = {
    "eye_image": EYE_PATH + "werewolf-eyes.png",
    "upper_lid_image": EYE_PATH + "werewolf-upper-lids.png",
    "lower_lid_image": EYE_PATH + "werewolf-lower-lids.png",
    "stencil_image": EYE_PATH + "werewolf-stencil.png",
    "eye_move_min": double(-3, -5),  # eye_image (left, top) move limit
    "eye_move_max": double(7, 6),  # eye_image (right, bottom) move limit
    "upper_lid_open": double(7, -4),  # upper_lid_image pos when open
    "upper_lid_center": double(7, -1),  # " when eye centered
    "upper_lid_closed": double(7, 8),  # " when closed
    "lower_lid_open": double(7, 22),  # lower_lid_image pos when open
    "lower_lid_center": double(7, 21),  # " when eye centered
    "lower_lid_closed": double(7, 17),  # " when closed
}
