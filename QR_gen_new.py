import gdspy, numpy, os, sys
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

# =======================================
# Payload Formatting
# =======================================
def format_relative(x,y, _, __):
    return f"{x},{y}"

def format_absolute(_, __, x_actual, y_actual):
    return f"{x_actual:.3f},{y_actual:.3f}"


global padding, qr_size, spacing
#add command line arguments and usage note
def additional_text(qr_size, x,y, cell: gdspy.Cell, pos_x, pos_y, **kwargs):
    """Creates human text around each qr code"""
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
    use_interactive = False
    global hum_text, reduction, precision
    name, length, height, qr_size, spacing, abs_pos, no_size, padding, forced_version, error_correction, num_modules_long,precision, reduction, hum_text = (None,None,None,None,None,None,None,None,None,None,None, None,None,None)
    if len(sys.argv) > 1:
        name, length, height, qr_size, spacing, abs_pos, padding, num_modules_long, precision ,hum_text, reduction, ec_level = get_parser_inputs()
        qrs_in_row = int(round((length + spacing) / (qr_size + spacing), 5))
        qrs_in_col = int(round((height + spacing) / (qr_size + spacing), 5))
        length, height, num_modules_long, spacing = adjust_qr_size_and_padding(length, height, padding, False, None, ec_level, abs_pos, qrs_in_row, qrs_in_col, spacing, False)
    else:
        use_interactive = True
        name, length, height, qr_size, spacing, abs_pos, no_size, no_spacing = input_data()
        padding, hum_text, reduction, precision, forced_version, error_correction = default_overides(qr_size)
        qrs_in_row = int(round((length + spacing) / (qr_size + spacing), 5))
        qrs_in_col = int(round((height + spacing) / (qr_size + spacing), 5))
        print(length, height, spacing, padding, qr_size)
        print(qrs_in_col)

        length, height, num_modules_long, spacing = adjust_qr_size_and_padding(length, height, padding, no_size, forced_version, error_correction, abs_pos, qrs_in_row, qrs_in_col, spacing, no_spacing)
    module_size = qr_size / num_modules_long
    lib.precision = 1.0e-6 * precision
    offset = module_size + .5 # size of module + a small amount for offset
    qrs_in_row = int(round((length + spacing - 2 * padding) / (qr_size + spacing),5))
    qrs_in_col = int(round((height + spacing - 2 * padding) / (qr_size + spacing), 5))
    print(qrs_in_col)
    def coord_to_pos(x,y):
        pos_x = padding + (x) * (qr_size + spacing)
        pos_y = padding + (y) * (qr_size + spacing)
        return pos_x,pos_y

    measurement = units.Measurement.unitless
    format_func = format_relative

    if abs_pos:
        measurement = units.Measurement.micrometer
        format_func = format_absolute
    human_text = None
    if hum_text:
        human_text = additional_text
    generator = GDSIIQRGenerator(qr_size,library = lib, unit = measurement, reduction = reduction)
    start=time.time()
    print(os.cpu_count())
    generate_and_place_batch(generator, lib, qrs_in_row, qrs_in_col, coordinate_to_position_func=coord_to_pos,
                         additional_drawings=human_text, thread_count=os.cpu_count(), data_format=format_func)
    print(f"Done generating! Took {time.time()-start:.2f} seconds.")
    path = ''
    i = 0
    fnameBase = name
    while True:
        # generates a unique file name
        if i:  # Only apply to i > 0
            fname = '%s (%i)'%(fnameBase,i)
        else:
            fname = fnameBase
        if not os.path.exists(os.path.join(path,fname+'.gds')):
            fname+='.gds'
            break
        i += 1

    # write file
    print('Writing file %s...'%fname,)
    sys.stdout.flush()
    lib.write_gds(fname)
    print('Done.')
    if use_interactive:
        msgbox(f"Done generating! Took {time.time() - start:.2f} seconds. File saved at {fname}.", "QR Generator")

if __name__ == '__main__':
    main()
