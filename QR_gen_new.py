import gdspy, numpy, os, json, sys
from subprocess import check_output
from get_inputs import *
from QR_GDSII.QR_Code_Generator import GDSIIQRGenerator
from QR_GDSII.QRWorker import generate_and_place_batch, round_floats
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
global padding, qr_size, spacing
#add command line arguments and usage note
def additional_text(qr_size, x,y, cell: gdspy.Cell, pos_x, pos_y, **kwargs):
    x_label = gdspy.Text(str(x), size=10, position=(pos_x, pos_y+qr_size * 1.05), layer=2, **kwargs)
    y_label = gdspy.Text(str(y), size=10, position=(pos_x+qr_size * 1.05 + 10, pos_y), angle=math.pi/2, layer=2, **kwargs)
    cell.add((x_label, y_label))
# def coord_to_pos(x,y, padding, qr_size, spacing):
#         pos_x = padding + (x + 1) * (qr_size + spacing) - spacing
#         pos_y = padding + (y + 1) * (qr_size + spacing) - spacing
#         #print(x,y)
#         #print(pos_x, pos_y)
#         return pos_x,pos_y

# def coord_to_pos(x,y):
#         padding,qr_size, spacing = get_data()
#         pos_x = padding + (x + 1) * (qr_size + spacing) - spacing
#         pos_y = padding + (y + 1) * (qr_size + spacing) - spacing
#         #print(x,y)
#         #print(pos_x, pos_y)
#         return pos_x,pos_y

def main():
    # size in um of module and offset
    global module_size
    global offset
    # creates a new cell objet in the lib library
    lib = gdspy.GdsLibrary()
    lib.unit = 1.0e-6
    # generator = GDSIIQRGenerator(50,lib)
    global hum_text, reduction, precision
    name, length, height, qr_size, spacing, abs_pos, no_size, padding, forced_version, error_correction, num_modules_long,precision, reduction, hum_text = (None,None,None,None,None,None,None,None,None,None,None, None,None,None)
    if len(sys.argv) > 1:
        name, length, height, qr_size, spacing, abs_pos, padding, num_modules_long, precision ,hum_text, reduction, ec_level = get_parser_inputs()
        length, height, num_modules_long = adjust_qr_size_and_padding(length, height, qr_size, padding, False, None, ec_level, abs_pos)
    else:
    # generate_and_place_batch(generator, lib, coord_to_pos_basic, 100, 100,
    #                       additional_drawings=None, thread_count=os.cpu_count())
    #global qr_size, spacing
        name, length, height, qr_size, spacing, abs_pos, no_size = input_data()
        padding, hum_text, reduction, precision, forced_version, error_correction = default_overides(qr_size)
        length, height, num_modules_long = adjust_qr_size_and_padding(length, height, qr_size, padding, no_size, forced_version, error_correction, abs_pos)
    module_size = qr_size / num_modules_long
    lib.precision = 1.0e-6 * precision
    offset = module_size + .5 # size of module + a small amount for offset
    qrs_in_row = int((length + spacing - 2 * padding) / (qr_size + spacing))
    qrs_in_col = int((height + spacing - 2 * padding) / (qr_size + spacing))
    rel_spacing = float(spacing / qr_size)
    def coord_to_pos(x,y):
        pos_x = padding + (x + 1) * (qr_size + spacing) - spacing
        pos_y = padding + (y + 1) * (qr_size + spacing) - spacing
        return pos_x,pos_y
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
    generate_and_place_batch(generator, lib, coord_to_pos, qrs_in_row, qrs_in_col,
                         additional_drawings=human_text, thread_count=os.cpu_count(), data_format=round_floats)
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
