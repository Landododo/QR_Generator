import sys, gdspy, os
import numpy as np
from ldap3 import AUTO_BIND_TLS_AFTER_BIND

## ------------------------------ ##
##      QR Parameters
## ------------------------------ ##

NAME = 'test'
CHIP_SIZE = [3000, 3000]
if __name__ == '__main__':
    NAME = sys.argv[1]
    CHIP_SIZE = (int(sys.argv[2]), int(sys.argv[2])) # In um
LAYER = 1 # Single layer for GDSII

print(f'Desired chip size: {CHIP_SIZE[0]} x {CHIP_SIZE[1]} um^2')

## ------------------------------------------------------------------ ##
##      QR Global Parameters that change version
##      Things that should attach to grid, should be normalized to SPACING
## ------------------------------------------------------------------ ##

VERSION = 5
COMMENTS = 'QPP'
CONFIG_FNAME = 'VersionConfig.json'

class ENCODING:
# |  Version  |   Row   |  Col    | Checksum(mod8) |
# |  4 bits   |  8 bits | 8 bits  |     3 bits     |
    pad = (0,4) # Pad (1) bits = 0,4 - injects ones at the specified indices at every code
    version_bits = 4
    row_bits = 8
    col_bits = 8
    n = 25 # How many total data bits are in the QR code, must be a perfect square
    checksum_bits = n - version_bits - row_bits - col_bits - len(pad)

MODULE_SIZE = 0.75 # um # Space between QR Code bits
REDUCTION = 0.1 # um for blur
SPACING = 40 # um # Space between QR Codes

MODULE_SIZE = float(MODULE_SIZE) # Casting
MODULE_TYPE = 'grid(3)' # Function call stored as string for debug purposes
# Marker spacings
PRIMARY_R = MODULE_SIZE/1.5 # Primary radius of QR code's finder patterns
SECONDARY_R = MODULE_SIZE/4.0 # Radius of "timing patterns"
NUM_SECONDARY = 3 # How many "timing pattern" dots there are
OFFSET = MODULE_SIZE+0.5 # Offset of basic cell and bit region
LEG = ENCODING.n**0.5*MODULE_SIZE+2*OFFSET # Total size of the QR Code
CHIP_SIZE = tuple(int(d/SPACING) for d in CHIP_SIZE) # Normalize chip size to spacing

class CROSS:
    """
    Creates an alignment cross at the edge of the sample
    Offset represents distance from the nearest edge
    """
    make = True
    offset = round(700/SPACING)-0.5
    length = 500 # um
    width = 3 #um
    make_bull = True
    bull_width = 0.1

class ABERRATION:
    make = True
    r = MODULE_SIZE / 2
    extent = 2*(SPACING-LEG*1.5) # Size of total aberration
    sep = 3*MODULE_SIZE
    offset = 500/SPACING # Distance from center axis
    locations = [(int(CHIP_SIZE[0]/2-offset), int(CHIP_SIZE[1]/2+offset)), #NW
                 (int(CHIP_SIZE[0]/2+offset), int(CHIP_SIZE[1]/2-offset)), #NE
                 (int(CHIP_SIZE[0]/2+offset), int(CHIP_SIZE[1]/2+offset))] #SE
print('Using chip size: %0.1f x %0.1f um^2'%tuple(d*SPACING for d in CHIP_SIZE))
print('Using Cross offset: %0.1f um'%(CROSS.offset*SPACING))
# QR code pattern is limited to 256x256
assert max(CHIP_SIZE) <= 2 ** 8, ' 8 bits cannot encode given chip size. Limited to %0.1f um'%((2**8)*SPACING)

## ------------------------------------------------------------------ ##
##      BIT (Module) Cell Type (cell type should encode all parameters used)
## ------------------------------------------------------------------ ##

def circle():
    block = gdspy.Cell('BIT%i_%i'%(REDUCTION*100, MODULE_SIZE*10))
    block.add(gdspy.Round((0,0), MODULE_SIZE/2.0-REDUCTION, layer=LAYER, tolerance=0.001))
    return block

# MODULE_SIZE defines the size of the bits
def plain():
    block = gdspy.Cell('BIT')
    block.add(gdspy.Rectangle((0,0), (MODULE_SIZE, MODULE_SIZE), layer=LAYER))
    return block

def grid(num_lines):
    start = REDUCTION
    stop = MODULE_SIZE - REDUCTION
    block = gdspy.Cell('BIT') #Combine with PLAIN
    spacing = float(stop - start)/(num_lines-0.5)
    w = spacing/2.0 # spacing represents spacing from left edge to left edge of each hline
    for i in range(num_lines):
        corner = float(spacing)*i + start
        h_line = gdspy.Rectangle((start, corner), (stop, corner+w), layer=LAYER)
        v_line = gdspy.Rectangle((corner, start), (corner+w, stop), layer=LAYER)
        block.add((h_line, v_line))
    return block

def basic_qr():
    qr = gdspy.Cell('Basic_Cell%i'%(MODULE_SIZE*10))
    # Create corner finder patterns
    for pos in ((LEG,0), (0,0), (0,LEG)):
        qr.add(gdspy.Round(pos, PRIMARY_R, layer=LAYER, tolerance=0.001))
    # Timing patterns
    div = NUM_SECONDARY + 1
    for i in range(1,div):
        # Horizontal
        qr.add(gdspy.Round((LEG*i/float(div), 0), SECONDARY_R, layer=LAYER, tolerance=0.001))
        # vertical
        qr.add(gdspy.Round((0,LEG * i / float(div)), SECONDARY_R, layer=LAYER, tolerance=0.001))
    return qr

def encode(r,c):
    # Strip sign bits off integers, pad with leading zeroes
    version = bin(VERSION)[2:].rjust(ENCODING.version_bits, '0')
    row = bin(int(r))[2:].rjust(ENCODING.row_bits, '0')
    col = bin(int(c))[2:].rjust(ENCODING.col_bits, '0')
    code = version+row+col
    # Checksum generation
    # The checksum is created by counting the number of 1s in the semi-final code, and converting
    # that count to binary. Depending on the number of checksum bits allocated, only the top
    # least significant bits are included
    checksum = bin(code.count('1'))[2:]
    # Grab LSB,s pad zeroes if checksum is a small number
    checksum_code = checksum[-ENCODING.checksum_bits:].rjust(ENCODING.checksum_bits, '0')
    code += checksum_code
    for pos in ENCODING.pad:
        # Inject a 1 at indecies specified at pad
        code = code[0:pos] + '1' + code[pos:]
    assert len(code) == ENCODING.n, f"{len(code)} bits encoded"
    return code

def make_qr(final_cell, basic_qr, bit_cell, row, col):
    code = encode(row, col)
    if type(code) == str:
        code = np.array([int(c) for c in code]) # cast into tuple of 0s and 1s
    origin = [col*SPACING, row*SPACING]
    # Reshape into perfect square
    n = int(np.sqrt(ENCODING.n))
    code = np.reshape(code, (n, -1))
    final_cell.add(gdspy.CellReference(basic_qr, origin))
    for bitrow in range(n):
        for bitcol in range(n):
            val = code[bitrow][bitcol]
            if val == 1:
                # Column major, reversed in the order of columns
                # (top to bottom, right to left)
                pos = [MODULE_SIZE*bitcol, MODULE_SIZE*(n-bitrow-1)]
                pos[0] += OFFSET + origin[0] #OFFSET represents spacing between bits
                pos[1] += OFFSET + origin[1]
                final_cell.add(gdspy.CellReference(bit_cell, pos))
    # Add numbers for readability
    height = 2*MODULE_SIZE
    final_cell.add(gdspy.Text(str(row), height,
                              (OFFSET+origin[0], LEG-PRIMARY_R/2.0+origin[1]), layer=LAYER))
    final_cell.add(gdspy.Text(str(col), height,
                              (LEG - PRIMARY_R / 2.0 + height + origin[0], OFFSET + origin[1]),
                              angle=np.pi/2, layer=LAYER))
    return final_cell

# Construction

def AberrationGrid():
    abbCirc = gdspy.Cell('AbberationCircle')
    abbCirc.add(gdspy.Round([0,0], ABERRATION.r, layer=LAYER, tolerance=0.001))
    abbRegion = gdspy.Cell('AbberationRegion')
    sep = ABERRATION.sep
    n = int(float(ABERRATION.extent)/sep)
    abbRegion.add(gdspy.CellArray(abbCirc, n,n, (sep,sep), (-(n-1)*sep/2.0, -(n-1)*sep/2.0)))
    return abbRegion

def Bullseye(rmin, rmax, width):
    bull = gdspy.Cell('Bullseye')
    bull.add(gdspy.Round((0,0), rmin, layer=LAYER, tolerance=0.001))
    r = rmin+width*2
    while r < rmax:
        larger = gdspy.Round((0,0), r, layer=LAYER, tolerance=0.001)
        # Subtract half the added diameter of the larger circle
        smaller = gdspy.Round((0,0), r-width, layer=LAYER, tolerance=0.001)
        ring = gdspy.fast_boolean(larger, smaller, 'not', layer=LAYER)
        bull.add(ring)
        r += width*2
    extent = r-width*2
    return bull, extent

def Cross():
    width = CROSS.width
    bull_width = CROSS.bull_width
    length = CROSS.length
    r1 = gdspy.Rectangle((-width/2.0, -length/2.0), (width/2.0, length/2.0), layer=LAYER)
    r2 = gdspy.Rectangle((-length/2.0, -width/2.0), (length/2.0, width/2.0), layer=LAYER)
    cross = gdspy.fast_boolean(r1, r2, 'or', layer=LAYER)
    crossCell = gdspy.Cell('Cross')
    if CROSS.make_bull:
        bullseye, extent = Bullseye(bull_width/2, width/(2**0.5)-bull_width, bull_width)
        # Carve a circle the size of the bullseye
        cross = gdspy.fast_boolean(cross, gdspy.Round((0,0), extent, tolerance=0.001), 'not', layer=LAYER)
        crossCell.add((cross, gdspy.CellReference(bullseye)))
    else:
        crossCell.add(cross)
    return crossCell

def main():
    qr = gdspy.Cell('Final')

    nrows = CHIP_SIZE[1] # rows = y
    ncols = CHIP_SIZE[0] # cols = x
    QRgrid = np.array([[1 for i in range(nrows)] for j in range(ncols)])

    labels = list('DCBA')
    if CROSS.make:
        cross = Cross()
        # Re-normalize x and y coordinates to be in terms of spacing
        for x in (CROSS.offset*SPACING, (CHIP_SIZE[0] - CROSS.offset)*SPACING):
            for y in (CROSS.offset*SPACING, (CHIP_SIZE[1] - CROSS.offset)*SPACING):
                qr.add(gdspy.CellReference(cross, (x,y)))
                label = labels.pop()
                # Place the label in the correct quadrant depending on if x and y are smaller
                # Than the centerline axis
                # Note - False converts to 0, True coverts to 1
                xLabel = x+   (2*(x<CHIP_SIZE[0]*SPACING/2.0)-1) * 3*SPACING
                yLabel = x + (2 * (y < CHIP_SIZE[0] * SPACING / 2.0) - 1) * 3 * SPACING
                qr.add(gdspy.Text(label, 10, (xLabel+SPACING, yLabel), layer=LAYER))
                if label == 'A':
                    qr.add(gdspy.Text(NAME, 10, (xLabel+SPACING, yLabel), layer=LAYER))

    if ABERRATION.make:
        abbRegion = AberrationGrid()
        for pos in ABERRATION.locations:
            QRgrid[pos[0]][pos[1]] = 0
            qr.add(gdspy.CellReference(abbRegion, tuple(d*SPACING for d in pos)))

    s = 30
    count = 0
    msg = 'Forming QR codes:'.ljust(s*s+2,' ')
    msg += '|'
    print(msg)

    basic = basic_qr()
    # Style of bit
    bit = eval(MODULE_TYPE)

    for row in range(nrows):
        for col in range(ncols):
            if not count%(nrows*ncols/s):
                print('*')
                sys.stdout.flush()
            count += 1
            # No aberration
            if QRgrid[row][col]:
                make_qr(qr, basic, bit, row ,col)
    print('*')

if __name__ == '__main__':
    main()
    path = ''
    i = 0
    fnameBase = NAME
    fname = fnameBase
    while True:
        if i:
            fname = f"{fnameBase} ({i})"
        if not os.path.exists(os.path.join(path, fname+'.gds')):
            fname += '.gds'
            break
        i += 1
    print(f'Writing file {fname}')
    sys.stdout.flush()
    gdspy.write_gds(os.path.join(path, fname), unit=1.0E-6, precision=1.0E-9)
    print('Done.')