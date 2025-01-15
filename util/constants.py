from enum import Enum
import qrcode.constants

class QRErrorCorrectionLevels(Enum):
    L = qrcode.constants.ERROR_CORRECT_L
    M = qrcode.constants.ERROR_CORRECT_M
    Q = qrcode.constants.ERROR_CORRECT_Q
    H = qrcode.constants.ERROR_CORRECT_H

QRCapacitiesToVersions = {
    "L": {25: 1,
          47: 2,
          77: 3,
          114: 4,
          154: 5,
          195: 6,
          224: 7,
          279: 8},
    "M": {20: 1,
          38: 2,
          61: 3,
          90: 4,
          122: 5,
          154: 6,
          178: 7,
          221: 8},
    "Q": {16: 1,
          29: 2,
          47: 3,
          67: 4,
          87: 5,
          108: 6,
          125: 7,
          157: 8},
    "H": {10: 1,
          20: 2,
          35: 3,
          50: 4,
          64: 5,
          84: 6,
          93: 7,
          122: 8}
}
