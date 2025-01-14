import gdspy, numpy, os, json, sys
from subprocess import check_output
from get_inputs import *

class ENCODING:
        pad = [0,4]         # Pad(1) bits = 0, 4
        version_bits = 4
        row_bits = 8
        col_bits = 8
        checksum_bits = 3
        n = 25
lib = gdspy.GdsLibrary()


def empty_qr(qr_size):
    # module_size is the bit module in um
    basic_cell = gdspy.Cell('Basic_Cell%i'%(qr_size*10))
    # Primary markers
    module_size = qr_size / 5
    reduction = module_size / 10
    leg = ENCODING.n**0.5*module_size + 2 * offset
    print(leg)
    primary_r = module_size / 1.5
    secondary_r = module_size / 4

    corner1 = gdspy.Round([leg,0],primary_r,layer=1,tolerance=0.001)
    corner2 = gdspy.Round([0,0],primary_r,layer=1,tolerance=0.001)
    corner3 = gdspy.Round([0,leg],primary_r,layer=1,tolerance=0.001)
    basic_cell.add([corner1,corner2,corner3])
    # Secondary markers
    c = gdspy.Round((0,0),module_size/4.0,layer=1,tolerance=0.001)
    div = 4
    for i in range(1,div):
        c1 = gdspy.Round([leg*i/float(div),0],secondary_r,layer=1,tolerance=0.001)
        basic_cell.add(c1)
        c1 = gdspy.Round([0,leg*i/float(div)],secondary_r,layer=1,tolerance=0.001)
        basic_cell.add(c1)
    return basic_cell

def make_grid(qrs_in_row, qrs_in_col, qr, rel_spacing, qr_size):
    QRgrid = numpy.array([[1 for i in range(qrs_in_row)] for j in range(qrs_in_col)])
    basic_cell = empty_qr(qr_size)
    individual_cell = grid(3, qr_size /50)
    for row in range(qrs_in_row):
        for col in range(qrs_in_col):
            if QRgrid[row][col]:
                make_qr(qr, row, col, basic_cell, rel_spacing, qr_size, individual_cell)

def encode(n,m):
    version = bin(5)[2:].rjust(ENCODING.version_bits,'0')
    row = bin(int(n))[2:].rjust(ENCODING.row_bits,'0')
    col = bin(int(m))[2:].rjust(ENCODING.col_bits,'0')
    code = version+row+col
    # Create checksum
    checksum = bin(code.count('1'))[2:]
    checksum = checksum[-ENCODING.checksum_bits:].rjust(ENCODING.checksum_bits,'0')   # Take checksum%(2**checksum_bits)
    code = code+checksum
    # Put in pad
    pad = ENCODING.pad[:]  # Make copy
    for pos in pad:
        code = code[0:pos]+'1'+code[pos:]
    assert len(code) == 25
    return code

def make_qr(qr, row, col, empty_qr, rel_spacing, qr_size, individual_cell):
    data = encode(row, col)
    if type(data)==str: #probably not necessary but incluing for now
        data = [int(c) for c in data]
    origin = (col * (rel_spacing + 1) * qr_size, row * (rel_spacing + 1) * qr_size) # (rel spacing +1) *qr size bc spacing between qr codes is more
    data = numpy.reshape(data,(int(len(data)**0.5),-1))
    n = int(ENCODING.n**0.5)
    print(n)
    qr.add(gdspy.CellReference(empty_qr,origin))

    #reduction = module_size / 10 # reduction in um around each module
    spacing = rel_spacing * qr_size # spacing in um between each qr code
    #grids = eval('grid(3, module_size, reduction)')
    for bitrow in range(n):
        for bitcol in range(n):
            val = data[bitrow][bitcol]
            if val==1:
               pos = [module_size*(bitcol),module_size*(n-bitrow-1)]
               pos[0] += offset + origin[0]
               pos[1] += offset + origin[1]
               qr.add(gdspy.CellReference(individual_cell, pos))
    # Human part
    height = 2 * module_size
    leg = ENCODING.n**0.5*module_size + 2 * offset
    print(leg)
    primary_r = module_size / 1.5
    row = gdspy.Text(str(row),height,(offset+origin[0],leg-primary_r/2.0+origin[1]),layer=1)
    col = gdspy.Text(str(col),height,(leg-primary_r/2.0+height+origin[0],offset+origin[1]),angle=numpy.pi/2,layer=1)
    qr.add([row,col])

def grid(num_lines, reduction):
    start = reduction
    stop = module_size - reduction
    block = lib.new_cell('BIT')
    spacing = float(stop-start)/(num_lines-0.5)
    pos = start
    w = spacing/2.0
    for i in range(num_lines):
        corner = float(spacing)*i + reduction
        Hline = gdspy.Rectangle((start,corner),(stop,corner+w),layer=1)
        block.add(Hline)
        Vline = gdspy.Rectangle((corner,start),(corner+w,stop),layer=1)
        block.add(Vline)
    return block

def main():
    global module_size
    global offset
    # creates a new cell objet in the lib library
    qr = lib.new_cell("QR")

    name, length, height, qr_size, spacing = input_data()
    print(name, length, height, qr_size, spacing)
    spacing = float(spacing)
    module_size = qr_size / 5
    offset = module_size +.5
    qrs_in_row = int(length / (qr_size + spacing))
    qrs_in_col = int(height / (qr_size + spacing))
    rel_spacing = float(spacing / qr_size)
    print(rel_spacing)
    make_grid(qrs_in_row, qrs_in_col, qr, rel_spacing, qr_size)
    # display cell in internal viewer
    # gdspy.LayoutViewer(library=lib, cells = [qr])
    path = ''
    i = 0
    fnameBase = name
    while True:
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
    gdspy.write_gds(os.path.join(path,fname), unit=1.0e-6, precision=1.0e-9)
    print('Done.')

if __name__ == '__main__':
    main()
