import gdspy, numpy, os, json, sys
from subprocess import check_output

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
    print 'Writing file %s...'%fname,
    sys.stdout.flush()
    gdspy.write_gds(os.path.join(path,fname), unit=1.0e-6, precision=1.0e-9)
    print 'Done.'