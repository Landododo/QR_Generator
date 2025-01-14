from easygui import *

def input_data():
    """Collect all the important input information from the user
    and standardize it to return only essential information"""
    # collect all the input info
    title = "QR generator"
    msg = "Enter the specifications of the QR generation. Sizes are in um and should be depicted (length x height). Leave blank if want us to generat data."
    field_names = ["File name", "QR array size", "QR code length", "QR code spacing", "Size of chip"]
    field_values = []
    field_values = multenterbox(msg,title, field_names)
    print(field_values)
    array1 = []
    array2 = []
    while True:
        # ensure there is enough input data and in the right format
        if field_values == None:
            field_values = multenterbox("NEED INPUTS", title, field_names, field_values)
        errmsg = ""
        if field_values[0] == None:
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

    if field_values[1] == None:
        return(field_values[0], field_values[4][0], field_values[4][1], field_values[2], field_values[3])
    elif field_values[2] == None or field_values[3] == None:
        qrs_per_row = field_values[1][0]
        qrs_per_col = field_values[1][1]
        chip_size_length = field_values[4][0]
        chip_size_height = field_values[4][1]
        if field_values[2] == None:
            spacing = field_values[3]
            code_length = min((chip_size_length - (qrs_per_row - 1) * spacing)/qrs_per_row, (chip_size_height - (qrs_per_col - 1) * spacing)/qrs_per_col)
            return (field_values[0], chip_size_length, chip_size_height, code_length, field_values[3])
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
            return (field_values[0], chip_size_length, chip_size_height, code_length, spacing)
    elif field_values[4] == None:
        code_length = field_values[2]
        spacing = field_values[3]
        length = field_values[1][0] * (code_length + spacing - 1)
        height = field_values[1][1] * (code_length + spacing - 1)
        return(field_values[0], length, height, code_length, spacing)
    else:
        return(field_values[0], field_values[4][0], field_values[4][1], field_values[2], field_values[3])


        

    print("name for file:")
    name = str(input())
    print("length of array in um")
    length = float(input())
    print("hieght of array in um")
    height = float(input())
    print("dimension of qr codes:")
    qr_size = float(input())
    print("spacing between adjacent qr codes:")
    spacing = float(input())
    return (field_values)
    return (name, length, height, qr_size, spacing)