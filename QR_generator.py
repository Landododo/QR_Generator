import gdspy, numpy, os, json, sys
from subprocess import check_output

## ------------------------------------------------------------------ ##
##      QR Parameters
## ------------------------------------------------------------------ ##

NAME = 'test'
CHIP_SIZE = [3000,3000]
if __name__ == '__main__':
    NAME = sys.argv[1]
    CHIP_SIZE = [int(sys.argv[2]) for i in range(2)] # um (normalized later)
LAYER = 1                # Layer to write everything

print('Desired chip size:  %0.1f x %0.1f um^2'%tuple(CHIP_SIZE))

## ------------------------------------------------------------------ ##
##      QR Global Parameters that change version
##      Things that should attach to grid, should be normalized to SPACING
## ------------------------------------------------------------------ ##

VERSION = 5  # Increment this when modifying anything in this section
COMMENTS = 'QPP'
CONFIG_FNAME = 'VersionConfig.json'

class ENCODING:
#|  Version  |   Row   |  Col    | Checksum(mod8) |
#|  4 bits   |  8 bits | 8 bits  |     3 bits     |
    pad = [0,4]         # Pad(1) bits = 0, 4
    version_bits = 4
    row_bits = 8
    col_bits = 8
    checksum_bits = 3
    n = 25

MODULE_SIZE = .75   # um
REDUCTION = 0.1     # um for blur
SPACING = 40        # um

MODULE_SIZE = float(MODULE_SIZE)
MODULE_TYPE = 'grid(3)'         # Function call as string (see below)
PRIMARY_R = MODULE_SIZE/1.5
SECONDARY_R = MODULE_SIZE/4.0   # Size of secondary markers
NUM_SECONDARY = 3               # Number of secondary markers on one arm
OFFSET = MODULE_SIZE+0.5        # Offset of basic cell and bit region
LEG = ENCODING.n**0.5*MODULE_SIZE+2*OFFSET
CHIP_SIZE = tuple([int(d/SPACING) for d in CHIP_SIZE])   # Normalized to spacing

class CROSS:
    make = True                     # Make the cross
    offset = round(700.0/SPACING)-0.5 # normalized from edge of sample in x and y
    length = 500                     # um from end to end of an arm
    width = 3                        # um wide for the arms of the cross
    make_bull = True                # Make bullseye in cross
    bull_width = 0.1                 # Distance between concentric circles

class ABERRATION:
    make = True
    r = MODULE_SIZE/2
    extent = 2*(SPACING-LEG*1.5)
    sep = 3*MODULE_SIZE
    locations = [[CHIP_SIZE[0]/2-500/SPACING,CHIP_SIZE[1]/2+500/SPACING],
                 [CHIP_SIZE[0]/2+500/SPACING,CHIP_SIZE[1]/2-500/SPACING],
                 [CHIP_SIZE[0]/2+500/SPACING,CHIP_SIZE[1]/2+500/SPACING]] # Normalized, also integer math, so floor.

print('Using chip size:    %0.1f x %0.1f um^2'%tuple([d*SPACING for d in CHIP_SIZE]))
print('Using Cross offset: %0.1f um'%(CROSS.offset*SPACING))
assert max(CHIP_SIZE)<=2**8, '8 Bits cannot encode given chip size. Limited to %0.1f um.'%((2**8)*SPACING)
## ------------------------------------------------------------------ ##
##      BIT (Module) Cell Type (cell type should encode all parameters used)
## ------------------------------------------------------------------ ##

def circle():
    block = gdspy.Cell('BIT%i_%i'%(REDUCTION*100,MODULE_SIZE*10))
    circ = gdspy.Round((0,0),MODULE_SIZE/2.0-REDUCTION,layer=LAYER,tolerance=0.001)
    block.add(circ)
    return block

def plain():
    block = gdspy.Cell('BIT')
    square = gdspy.Rectangle((0,0),(MODULE_SIZE,MODULE_SIZE),layer=LAYER)
    block.add(square)
    return block

def grid(num_lines):
    start = REDUCTION
    stop = MODULE_SIZE - REDUCTION
    block = gdspy.Cell('BIT')
    spacing = float(stop-start)/(num_lines-0.5)
    pos = start
    w = spacing/2.0
    for i in range(num_lines):
        corner = float(spacing)*i + REDUCTION
        Hline = gdspy.Rectangle((start,corner),(stop,corner+w),layer=LAYER)
        block.add(Hline)
        Vline = gdspy.Rectangle((corner,start),(corner+w,stop),layer=LAYER)
        block.add(Vline)
    return block


## ------------------------------------------------------------------ ##
##      QR Basic Cell - includes constant part of all codes (including pad)
## ------------------------------------------------------------------ ##

def basic_qr():
    # module_size is the bit module in um
    qr = gdspy.Cell('Basic_Cell%i'%(MODULE_SIZE*10))
    # Primary markers
    corner1 = gdspy.Round([LEG,0],PRIMARY_R,layer=LAYER,tolerance=0.001)
    corner2 = gdspy.Round([0,0],PRIMARY_R,layer=LAYER,tolerance=0.001)
    corner3 = gdspy.Round([0,LEG],PRIMARY_R,layer=LAYER,tolerance=0.001)
    qr.add([corner1,corner2,corner3])
    # Secondary markers
    c = gdspy.Round((0,0),MODULE_SIZE/4.0,layer=LAYER,tolerance=0.001)
    div = NUM_SECONDARY+1
    for i in range(1,div):
        c1 = gdspy.Round([LEG*i/float(div),0],SECONDARY_R,layer=LAYER,tolerance=0.001)
        qr.add(c1)
        c1 = gdspy.Round([0,LEG*i/float(div)],SECONDARY_R,layer=LAYER,tolerance=0.001)
        qr.add(c1)
    return qr

## ------------------------------------------------------------------ ##
##      Final QR
## ------------------------------------------------------------------ ##

def encode(n,m):
    version = bin(VERSION)[2:].rjust(ENCODING.version_bits,'0')
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

def make_qr(final_cell,basic_qr,bit_cell,row,col):
    code = encode(row,col)
    if type(code)==str:
        code = [int(c) for c in code]
    origin = [col*SPACING,row*SPACING]
    code = numpy.reshape(code,(int(len(code)**0.5),-1))
    n = int(ENCODING.n**0.5)
    final_cell.add(gdspy.CellReference(basic_qr,origin))
    for bitrow in range(n):
        for bitcol in range(n):
            val = code[bitrow][bitcol]
            if val==1:
               pos = [MODULE_SIZE*(bitcol),MODULE_SIZE*(n-bitrow-1)]
               pos[0] += OFFSET + origin[0]
               pos[1] += OFFSET + origin[1]
               final_cell.add(gdspy.CellReference(bit_cell,pos))
    # Human part
    height = 2*MODULE_SIZE
    row = gdspy.Text(str(row),height,(OFFSET+origin[0],LEG-PRIMARY_R/2.0+origin[1]),layer=LAYER)
    col = gdspy.Text(str(col),height,(LEG-PRIMARY_R/2.0+height+origin[0],OFFSET+origin[1]),angle=numpy.pi/2,layer=LAYER)
    final_cell.add([row,col])

## ------------------------------------------------------------------ ##
##      Construction
## ------------------------------------------------------------------ ##

def AberrationGrid():
    abbCirc = gdspy.Cell('AberrationCircle')
    abbCirc.add(gdspy.Round([0,0],ABERRATION.r,layer=LAYER,tolerance=0.001))
    abbRegion = gdspy.Cell('AberrationRegion')
    sep = ABERRATION.sep
    n = int(float(ABERRATION.extent)/sep)
    abbRegion.add(gdspy.CellArray(abbCirc,n,n,(sep,sep),(-(n-1)*sep/2.0,-(n-1)*sep/2.0)))
    return abbRegion

def Bullseye(rmin,rmax,width):
    bull = gdspy.Cell('Bullseye')
    bull.add(gdspy.Round([0,0],rmin,layer=LAYER,tolerance=0.001))
    r = rmin+width*2
    while r < rmax:
        larger = gdspy.Round([0,0],r,layer=LAYER,tolerance=0.001)
        smaller = gdspy.Round([0,0],r-width,layer=LAYER,tolerance=0.001)
        ring = gdspy.fast_boolean(larger,smaller,'not',layer=LAYER)
        bull.add(ring)
        r += width*2
    extent = r-width*2
    return bull, extent

def Cross():
    width = CROSS.width
    bull_width = CROSS.bull_width
    length = CROSS.length
    r1 = gdspy.Rectangle((-width/2.0,-length/2.0),(width/2.0,length/2.0),layer=LAYER)
    r2 = gdspy.Rectangle((-length/2.0,-width/2.0),(length/2.0,width/2.0),layer=LAYER)
    cross = gdspy.fast_boolean(r1,r2,'or',layer=LAYER)
    crossCell = gdspy.Cell('Cross')
    if CROSS.make_bull:
        bullseye,extent = Bullseye(bull_width/2,width/(2**0.5)-bull_width,bull_width)
        cross = gdspy.fast_boolean(cross,gdspy.Round([0,0],extent,tolerance=0.001),'not',layer=LAYER)
        crossCell.add([cross,gdspy.CellReference(bullseye)])
    else:
        crossCell.add(cross)
    return crossCell

def main():
    global MODULE_SIZE
    global REDUCTION
    global PRIMARY_R
    global SECONDARY_R
    global OFFSET
    global LEG
    qr = gdspy.Cell('Final')

    # Create grid to say where QR codes should go
    nrows = CHIP_SIZE[1]  # rows = y
    ncols = CHIP_SIZE[0]  # cols = x
    QRgrid = numpy.array([[1 for i in xrange(nrows)] for j in xrange(ncols)])  # QRgrid[col][row]

    # Add Crosses to GDS
    labels = list('DCBA') # pop from end
    if CROSS.make:
        cross = Cross()
        for x in [CROSS.offset*SPACING,(CHIP_SIZE[0]-CROSS.offset)*SPACING]:
            for y in [CROSS.offset*SPACING,(CHIP_SIZE[1]-CROSS.offset)*SPACING]:
                qr.add(gdspy.CellReference(cross,(x,y)))
                label = labels.pop()
                xLabel = x+(2*(x<CHIP_SIZE[0]*40/2.0)-1) * 3*40
                yLabel = y+(2*(y<CHIP_SIZE[1]*40/2.0)-1) * 3*40
                qr.add(gdspy.Text(label,10,(xLabel,yLabel),layer=LAYER))
                if label == 'A':
                    qr.add(gdspy.Text(NAME,10,(xLabel+40,yLabel),layer=LAYER))

    # Add aberration Grids
    if ABERRATION.make:
        abbRegion = AberrationGrid()
        for pos in ABERRATION.locations:
            QRgrid[pos[0]][pos[1]] = 0
            qr.add(gdspy.CellReference(abbRegion,[d*SPACING for d in pos]))

    # Add QRs
    s = 30 # Console Characters wide
    count = 0
    msg = 'Forming QR codes:'.ljust(2*s+2,' ')
    msg += '|'
    print(msg)

    basic = basic_qr()
    bit = eval(MODULE_TYPE)
    
    for row in xrange(nrows):
        for col in xrange(ncols):
            if not count%(nrows*ncols/s):
                print('*',)
                sys.stdout.flush()
            count += 1
            if QRgrid[col][row]:
                make_qr(qr,basic,bit,row,col)
    print('*')

def class2dict(c):
    out = c.__dict__
    for key in out.keys():
        if '__' in key:
            del out[key]
    return out

def makeConfigFile(path):
    print('Creating new Version config file.')
    params = {'ENCODING':class2dict(ENCODING),
              'CROSS':class2dict(CROSS),
              'ABERRATION':class2dict(ABERRATION),
              'MODULE_SIZE':MODULE_SIZE,
              'MODULE_TYPE':MODULE_TYPE,
              'SPACING':SPACING,
              'PRIMARY_R':PRIMARY_R,
              'SECONDARY_R':SECONDARY_R,
              'NUM_SECONDARY':NUM_SECONDARY,
              'OFFSET':OFFSET,
              'LEG':LEG,
              'COMMENTS':COMMENTS}
    with open(os.path.join(path,CONFIG_FNAME),'w') as f:
        json.dump(params,f)
    print('Pushing to remote repo...',)
    check_output('git add -A',shell=True)
    check_output('git commit -m "Added new version config file."',shell=True)
    check_output('git push',shell=True)


if __name__ == '__main__':
    main()
    # Make sure repo is up to date on master!
    # check_output('git fetch',shell=True)
    # git_status = check_output('git status',shell=True)
    # if not ('is up to date' in git_status and
    #        'master' in git_status and
    #        'nothing to commit' in git_status):
    #     print 'Warning: Not up to date with origin master!'

    # Find unused filename
    path = ''
    i = 0
    fnameBase = NAME
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