import gdspy
from qrcode.main import QRCode

from QR_GDSII.GDSII_Factory import GDSIIFactory


def pixel_dimension_from_version(version):
    return 17 + 4 * version

if __name__ == '__main__':
    #50 micrometers
    qr_size = 50
    VERSION = 1

    qr = QRCode(version=VERSION,
                box_size=1,
                border=0,
                image_factory=GDSIIFactory)
    # Need to circumvent the integer check
    qr.add_data("Hello, World!")
    lib = gdspy.GdsLibrary()
    gdsii_builder = qr.make_image(layer=1, cell_name="QR", library = lib, gdsii_box_size=qr_size/pixel_dimension_from_version(VERSION))
    lib.write_gds("test_qr_code.gds")
    gdspy.LayoutViewer(lib)