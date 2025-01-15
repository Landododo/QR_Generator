import gdspy, numpy, os, json, sys
from subprocess import check_output
from get_inputs import *
from QR_GDSII.QR_Code_Generator import GDSIIQRGenerator
from QR_GDSII.QRWorker import generate_and_place_batch
from QR_GDSII.util import units
from QR_GDSII import QRWorker
import time
import math

class ENCODING:
        pad = [0,4]         # Pad(1) bits = 0, 4
        version_bits = 4
        row_bits = 8
        col_bits = 8
        checksum_bits = 3
        n = 25
num_modules_long = 5

#add command line arguments and usage note
def coord_to_pos(x,y, qr_size, padding, spacing):
    pos_x = padding + (x + 1) * (qr_size + spacing) - spacing
    pos_y = padding + (y + 1) * (qr_size + spacing) - spacing
    print(x,y)
    print(pos_x, pos_y)
    return pos_x,pos_y

def additional_text(qr_size, x,y, cell: gdspy.Cell, pos_x, pos_y, **kwargs):
    x_label = gdspy.Text(str(x), size=10, position=(pos_x, pos_y+qr_size * 1.05), layer=2, **kwargs)
    y_label = gdspy.Text(str(y), size=10, position=(pos_x+qr_size * 1.05 + 10, pos_y), angle=math.pi/2, layer=2, **kwargs)
    cell.add((x_label, y_label))

def main():
    # size in um of module and offset
    global module_size
    global offset
    # creates a new cell objet in the lib library
    lib = gdspy.GdsLibrary()
    lib.unit = 1.0e-6
    # generator = GDSIIQRGenerator(50,lib)

    # generate_and_place_batch(generator, lib, coord_to_pos_basic, 100, 100,
    #                       additional_drawings=None, thread_count=os.cpu_count())
    
    name, length, height, qr_size, spacing, abs_pos, no_size = input_data()
    print(name, length, height, qr_size, spacing)
    global padding, hum_text, reduction, precision
    padding, hum_text, reduction, precision, forced_version, error_correction = default_overides(qr_size)
    print(padding, hum_text, reduction, precision)
    lib.precision = 1.0e-6 * precision
    length, height, num_modules_long = adjust_qr_size_and_padding(length, height, qr_size, padding, no_size, forced_version, error_correction, abs_pos)
    module_size = qr_size / num_modules_long
    offset = module_size + .5 # size of module + a small amount for offset
    qrs_in_row = int((length + spacing - 2 * padding) / (qr_size + spacing))
    qrs_in_col = int((height + spacing - 2 * padding) / (qr_size + spacing))
    rel_spacing = float(spacing / qr_size)
    print(rel_spacing)
    measurement = units.Measurement.unitless
    if abs_pos:
        measurement = units.Measurement.micrometer
    human_text = None
    if hum_text:
        human_text = additional_text
    qr = lib.new_cell("QR")

    generator = GDSIIQRGenerator(qr_size,library = lib, unit = measurement, reduction = reduction)
    start=time.time()
    print(os.cpu_count())
    generate_and_place_batch(generator, lib, coord_to_pos, qrs_in_row, qrs_in_col, qr_size, spacing, padding,
                         additional_drawings=human_text, thread_count=os.cpu_count())
    print(f"Done generating! Took {time.time()-start:.2f} seconds.")
    path = ''
    i = 0
    fnameBase = name
    while True:
        # generates a unique file name
        if i:  # Only apply to i > 0
            fname = '%s_%i'%(fnameBase,i)
        else:
            fname = fnameBase
        if not os.path.exists(os.path.join(path,fname+'.gds')):
            fname = fname + '.gds'
            break
        i += 1

    print('Writing file %s...'%fname,)
    sys.stdout.flush()
    #gdspy.write_gds(os.path.join(path,fname), unit=1.0e-6, precision=precision * 1.0e-6)
    lib.write_gds(fname)
    print('Done.')

if __name__ == '__main__':
    main()
