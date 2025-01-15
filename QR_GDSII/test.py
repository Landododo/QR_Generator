import gdspy
from qrcode.main import QRCode

from QR_GDSII.GDSII_Factory import GDSIIFactory
from QR_GDSII.QR_Code_Generator import GDSIIQRGenerator
from util.units import Measurement


def pixel_dimension_from_version(version):
    return 17 + 4 * version

if __name__ == '__main__':
    #50 micrometers
    qr_size = 50

    # Add global metadata here. Global metadata must have a tag that is less than
    # 3 characters long.
    lib = gdspy.GdsLibrary()
    qr_maker = GDSIIQRGenerator(qr_size, library=lib, unit=Measurement.unitless, layer=1, MI="T")

    main_cell = gdspy.Cell("MAIN")

    # Additional parameters are layer and any extra kwargs are inferred as metadata
    # For instance, T is an example instance metadata, or metadata local to the QR code
    # You can add instance metadata to the QR code such as an ID,
    qr_cell = qr_maker.create_gdsii("Hello, world!",T="A")
    main_cell.add(gdspy.CellReference(qr_cell, (0,0)))

    qr_cell_2 = qr_maker.create_gdsii("255,255",T="B")
    main_cell.add(gdspy.CellReference(qr_cell_2, (0, 70)))
    lib.add(main_cell, True)

    lib.write_gds("test_qr_code.gds")
    gdspy.LayoutViewer(lib)