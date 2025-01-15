from typing import Callable

import gdspy
from qrcode.main import QRCode

import abc

from QR_GDSII.GDSII_Factory import GDSIIFactory
from QR_GDSII.util.constants import QRErrorCorrectionLevels, QRCapacitiesToVersions
from QR_GDSII.util.units import Measurement

# x=100,y=200,U=UL


def pixel_dimension_from_qr_version(version):
    return 17 + 4 * version

class GDSIIQRGenerator:
    def __init__(self, qr_code_size: float,
                 library: gdspy.GdsLibrary,
                 error_correction = QRErrorCorrectionLevels.M,
                 qr_version = None,
                 unit: Measurement = Measurement.unitless,
                 reduction = 0,
                 **kwargs):
        self.library = library
        self.error_correction = error_correction
        self.qr_code_size = qr_code_size
        self.force_qr_version = qr_version
        self.default_metadata = {"U": unit.value, "E": error_correction.name}
        self.reduction = reduction
        for kwarg, val in kwargs.items():
            if len(kwarg) < 3:
                self.default_metadata[kwarg] = str(val)

    def create_gdsii(self, data, layer=1, id_provider: Callable[[None], int]=None, **meta):

        data_str = str(data)
        for kwarg, val in self.default_metadata.items():
            data_str += ":" + kwarg + "=" + str(val)
        for kwarg, val in meta.items():
            data_str += ":" + kwarg + "=" + str(val)

        needed = len(data_str)
        ec_level = self.error_correction.name
        capacities_table = QRCapacitiesToVersions[ec_level]
        qr_version = None

        for capacity, version in capacities_table.items():
            if self.force_qr_version is None:
                if capacity >= needed:
                    qr_version = version
                    break
            else:
                if self.force_qr_version == version:
                    if capacity < needed:
                        raise ValueError(
                            f"Version {version}, EC level: {self.error_correction} can only"
                            f"store {capacity} characters, needed {needed} characters."
                            f"You can avoid providing the qr_version argument to autofit.")
                    qr_version = self.force_qr_version
        if qr_version is None:
            raise ValueError("Could not find a suitable QR version between 1-8 to encode.")
        qr = QRCode(version=qr_version,
                    error_correction=self.error_correction.value,
                    box_size=1,
                    border=0,
                    image_factory=GDSIIFactory)
        qr.add_data(data_str)
        qr_version = qr.best_fit(qr_version)
        return qr.make_image(layer=layer,
                             library=self.library,
                             cell_name="QR",
                             gdsii_box_size=self.qr_code_size / pixel_dimension_from_qr_version(qr_version),
                             reduction=self.reduction,
                             id_provider=id_provider).get_image()


