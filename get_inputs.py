from easygui import *
from QR_GDSII.util import constants
import argparse, sys


def input_data():
    """Collect all the important input information from the user
    and standardize it to return only essential information"""
    # collect all the input info
    title = "QR generator"
    msg = "Enter the specifications of the QR generation. Sizes are in um and should be depicted (length x height). Leave blank if want us to generat data."
    field_names = ["File name", "QR array size", "QR code length", "QR code spacing", "Size of chip"]
    field_values = []
    field_values = multenterbox(msg, title, field_names)
    print(field_values)
    array1 = []
    array2 = []
    while True:
        # ensure there is enough input data and in the right format
        if field_values == None:
            field_values = multenterbox("NEED INPUTS", title, field_names, field_values)
        errmsg = ""
        if str(field_values[0]).strip() == "":
            errmsg = "File name required"
        count = 0
        for i in range (1,5):
            if field_values[i].strip() != "":
                count += 1
                if i == 1:
                    array1 = field_values[i].split("x")
                    if len(array1) > 2:
                        errmsg = errmsg + "too many xs in size for second field"
                    elif len(array1) == 2:
                        array1[0] = float(array1[0].strip())
                        array1[1] = float(array1[1].strip())
                    else:
                        errmsg = errmsg + "need an x between the size inputs"
                elif i == 4:
                    array2 = field_values[i].split("x")
                    if len(array2) > 2:
                        errmsg = errmsg + "too many xs in size for last field"
                    elif len(array2) == 2:
                        array2[0] = float(array2[0].strip())
                        array2[1] = float(array2[1].strip())
                    else:
                        errmsg = errmsg + "need an x between the size inputs"
                else:
                    field_values[i] = float(field_values[i].strip())
        if count < 3:
            errmsg = errmsg + " need at least 3 of QR array size, QR code size, QR code spacing, and size of chip"
        if errmsg == "":
            break
        field_values = multenterbox(errmsg, title, field_names, field_values)
    
    field_values[1] = array1
    field_values[4] = array2
    abs_pos = True
    # boolean question to determine type of information to be encoded in QR codes
    if not boolbox("Should position be encoded in um or unitless relative to QR size?", "QR units", ["Absolute Position (um)", "Relative Position (QR units)"]):
        abs_pos = False
    print(abs_pos)
    
    if field_values[1] == []:
        return(field_values[0], field_values[4][0], field_values[4][1], field_values[2], field_values[3], abs_pos, False)
    elif str(field_values[2]).strip() == "" or str(field_values[3]).strip() == "":
        qrs_per_row = field_values[1][0]
        qrs_per_col = field_values[1][1]
        chip_size_length = field_values[4][0]
        chip_size_height = field_values[4][1]
        if str(field_values[2]).strip() == "":
            spacing = field_values[3]
            code_length = min((chip_size_length - (qrs_per_row - 1) * spacing)/qrs_per_row, (chip_size_height - (qrs_per_col - 1) * spacing)/qrs_per_col)
            return (field_values[0], chip_size_length, chip_size_height, code_length, field_values[3],abs_pos, False)
        else:
            code_length = field_values[2]
            spacing = 0
            if qrs_per_row != 1 and qrs_per_col != 1:
                spacing = min ((chip_size_length - qrs_per_row * code_length) / (qrs_per_row - 1), (chip_size_height - qrs_per_col * code_length) / (qrs_per_col - 1))
            elif qrs_per_col != 1:
                spacing = (chip_size_height - qrs_per_col * code_length) / (qrs_per_col - 1)
            elif qrs_per_row != 1:
                spacing = (chip_size_length - qrs_per_row * code_length) / (qrs_per_row - 1)
            print(spacing)
            print("fucks")
            return (field_values[0], chip_size_length, chip_size_height, code_length, spacing, abs_pos, False)
    elif field_values[4] == []:
        code_length = field_values[2]
        spacing = field_values[3]
        length = field_values[1][0] * (code_length + spacing) - spacing
        height = field_values[1][1] * (code_length + spacing) - spacing
        return(field_values[0], length, height, code_length, spacing, abs_pos, True)
    else:
        return(field_values[0], field_values[4][0], field_values[4][1], field_values[2], field_values[3],abs_pos, False)

def default_overides(qr_size):
    title = "Default overrides"
    msg = "These values are filled with default values but can be changed if wanted."
    field_names = ["Outer Padding (um)", "Human Text (Y/N)", "Reduction around each module(um)", "Write Precision (um)", "QR version", "Error Correction"]
    field_values = [0.1, "Y", qr_size / 200, .00005, "Any", "M"]
    field_values = multenterbox(msg, title, field_names, field_values)
    while True:
        if field_values == None:
            field_values = multenterbox("NEED INPUTS", title, field_names, field_values)
        errmsg = ""
        field_values[0], field_values[2], field_values[3] = float(field_values[0]), float(field_values[2]), float(field_values[3])
        if float(field_values[0]) < 0:
            errmsg = errmsg + "Need padding greater than 0"
        if len(field_values[1]) > 1:
             errmsg = errmsg + "Need Y/N for human text"
        if float(field_values[2]) < 0:
            errmsg = errmsg + "Need reduction greater than 0"
        if float(field_values[3]) < 0:
            errmsg = errmsg + "Need precision greater than 0"
        if (field_values[4].strip() != "Any"):
            if int(field_values[4]) not in [1,2,3,4,5,6,7,8]:
                errmsg = errmsg + "Need version as integer 1 through 8"
        if len(field_values[5].strip()) > 1 or field_values[5][0].strip() not in "LMQH":
            errmsg = errmsg + "Need a single char for error correction either L, M, Q, or H"
        if errmsg == "":
            break
        field_values = multenterbox(errmsg, title, field_names, field_values)
    if len(field_values[4]) > 1:
        field_values[4] = None
    elif(int(field_values[4]) in [1,2,3,4,5,6,7,8]):
        field_values[4] = int(field_values[4])
    else:
        field_values[4] = None
    return field_values[0], field_values[1].upper() == "Y", field_values[2], field_values[3], field_values[4], field_values[5]

def adjust_qr_size_and_padding(length, height, qr_size, padding, no_size, forced_version, ec_level, abs_pos):
    if no_size:
        length = length + 2 * padding
        height = height + 2 * padding
    needed = 7
    if abs_pos:
        needed = 13
    capacities_table = constants.QRCapacitiesToVersions[ec_level]
    qr_version = forced_version

    for capacity, version in capacities_table.items():
        if forced_version is None:
            if capacity >= needed:
                qr_version = version
                break
        else:
            if forced_version == version:
                if capacity < needed:
                    raise ValueError(
                        f"Version {version}, EC level: {ec_level} can only"
                        f"store {capacity} characters, needed {needed} characters."
                        f"You can avoid providing the qr_version argument to autofit.")
                qr_version = forced_version
    return (length, height, qr_version * 4 + 17)

def get_parser_inputs():
    parser = argparse.ArgumentParser(
            prog='QR generator',
            description='Generates a grid of qr codes of a specifized size using user input. Returns a gdsii file'
            )
    parser.add_argument('filename',help="name of file to process")
    parser.add_argument("size of chip", help="size of chip in um, seperated by an x (like 30x30)")
    parser.add_argument("size of qr code", help = "the size of each individual qr in the grid")
    parser.add_argument("spacing", help="spacing between qr codes")
    parser.add_argument('-p', "--padding", help = "Padding around the entire qr grid (um)")
    parser.add_argument('-pr', "--precision", help = "degree of precision in um for the writing of the QR codes")
    parser.add_argument('-r',"--reduction", help= "Padding around each qr module (um)")
    parser.add_argument("-hu", "--human", help="Y or N if you want human numbers around QR codes")
    parser.add_argument("-a", "--absolute", help = "encode your position absolutely (um) Y or N as answer")        
    parser.add_argument("-e", "--ec_level", help = "error correction level as H,Q,M or L (high, quality, medium or low)")        

    args = parser.parse_args()
    args_dict = vars(args)
    while True:
        no_errors= True
        print(args_dict)
        if len(args_dict["filename"]) < 1:
            print("Error: need a filename")
        elif "x" not in args_dict["size of chip"]:
            print("u need an x between the length and width (no spaces)")
        elif len(args_dict["size of chip"].split("x")) != 2:
            print("u need 2 dimensions on each side of the x")
        else:
            sizes = args_dict["size of chip"].split("x")
            args_dict["size of chip"] = sizes
            qr_size = float(args_dict["size of qr code"])
            args_dict["spacing"] = float(args_dict["spacing"])
            if args.padding != None:
                try:
                    padding = float(args.padding)
                except:
                    print("Bruh you need to put in a float for the padding")
                    no_errors = False
            else:
                padding = 0.1
            if args.precision != None:
                try:
                    precision = float(args.precision)
                except:
                    no_errors=False
                    print("Bruh you need to put in a float for the padding")
            else:
                precision = 0.001
            if args.reduction != None:
                try:
                    reduction = float(args.reduction)
                except:
                    no_errors=False
                    print("Bruh you need to put in a float for the reduction")
            else:
                reduction = qr_size/200
            if args.human != None:
                if len(args.human) != 1:
                    no_errors=False
                    print("there's gotta be only 1 char for human y or n")
                elif args.human not in "nNyY":
                    no_errors =False
                    print("you gotta be y or n")
                else:
                    args.human = args.human.lower() == 'y'
            else:
                args.human = True
            if args.ec_level != None:
                if len(args.ec_level) != 1:
                    no_errors=False
                    print("there's gotta be only 1 char for L,M,Q,or H")
                elif args.ec_level not in "LMQH":
                    no_errors=False
                    print("you gotta be L,M,Q, or H")
                else:
                    args.ec_level = "M"
            else:
                args.ec_level = "M"
            if args.absolute != None:
                if len(args.absolute) != 1:
                    no_errors=False
                    print("there's gotta be only 1 char for absolute y or n")
                elif args.absolute not in "nNyY":
                    no_errors=False
                    print("gotta be y or n")
                else:
                    abs_pos = args.absolute.lower() == 'y'
                    break
            else:
                abs_pos = True
            if no_errors:
                break
        sys.argv = [sys.argv[0]]
        args = parser.parse_args()
    name, length, height, spacing = args_dict["filename"], args_dict["size of chip"][0], args_dict["size of chip"][1], args_dict["spacing"]
    num_modules_long = 21
    return name, float(length), float(height), float(qr_size), float(spacing), abs_pos, float(padding), num_modules_long, float(precision), args.human,float(reduction), args.ec_level
