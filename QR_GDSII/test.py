import math
import os

import gdspy
from qrcode.main import QRCode

from QRWorker import generate_and_place_batch
from QR_Code_Generator import GDSIIQRGenerator
from util.units import Measurement
import time

def test_basic():
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


def coord_to_pos_basic(x,y):
    return x*100,y*100

def test_parallelization():
    def additional_text(x,y, cell: gdspy.Cell, pos_x, pos_y, **kwargs):
        x_label = gdspy.Text(str(x), size=10, position=(pos_x, pos_y+55), layer=2, **kwargs)
        y_label = gdspy.Text(str(y), size=10, position=(pos_x+65, pos_y), angle=math.pi/2, layer=2, **kwargs)
        cell.add((x_label, y_label))
    lib = gdspy.GdsLibrary()
    generator = GDSIIQRGenerator(50,lib)
    start=time.time()
    print(os.cpu_count())
    generate_and_place_batch(generator, lib, coord_to_pos_basic, 100, 100,
                             additional_drawings=additional_text, thread_count=os.cpu_count())
    print(f"Done generating! Took {time.time()-start:.2f} seconds.")
    lib.write_gds("test_qr_code_parallel.gds")
    gdspy.LayoutViewer(lib)

if __name__ == "__main__":
    test_parallelization()