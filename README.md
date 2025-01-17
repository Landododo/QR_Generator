
# **QR Code GDSII Generator**

## **Overview**
This project is a Python-based application designed to generate and position a grid of QR codes in a GDSII file format. These QR codes will encode their own positions, enabling knowledge of precise position on a microscopic chip using this data.

---

## **Features**
- Generates QR codes in GDSII format with customizable size, spacing, and encoding, along with other parameters, automatically adjusting the qr size and layout based on user input.
- Supports human-readable labels near QR codes for better identification.
- Multi-threaded QR code generation for improved performance.

---

## **Dependencies**
The following Python libraries are required:
- `gdspy`: For GDSII file handling and manipulation.
- `numpy`: For numerical operations.
- `json`: For parsing and managing configuration files.
- `os`: For file path management.
- `sys`: For command-line argument handling.
- `subprocess`: To execute external commands.
- `time`: For execution timing.
- `math`: For geometric computations.
---

## **Usage**
### **Command-Line Arguments**
The script can accept arguments through the command line or prompt the user for inputs interactively (when given no command line arguments). 

#### **Required Arguments**:
- `name`: Name for the output GDSII file.
- `size of chip`: The size of the chip in um, with length and height seperated by an x (like 300x400).
- `qr_size`: Size of each QR code in micrometers.
- `spacing`: Spacing between QR codes.
#### **Optional Arguments**:
- `absolute`: Use absolute positioning for QR codes? Input of y or n, with default value of y.
- `padding`: Padding around the QR code grid (in um). Defaults to 0.1 um.
- `precision`: Precision for the GDSII output (in um). Defaults to 0.0001 um.
- `reduction`: Amount of white space around each QR module. Essentially padding between each module. Defaults to 0.
- `hum_text`: Enable human-readable labels depicing the coordinates of each QR code. Input y or n, with default being y.
- `ec_level`: Error correction level to use in the QR code generation. Can be L (low), M (medium), Q (quartile), or H(high), with the default being M.

#### **Example**:
```bash
python QR_gen_new.py test_file 300x300 10 20 -absolute n -spacing 10 -padding 20 -hum_text n
```

### **Interactive Mode**
If no arguments are passed via the command line, the script will prompt the user interactively for required inputs.
The first page will prompt for file name, qr array size, qr code length, spacing, and the size of the chip, with it being able to calculate 
one of the last 4 arguments if not given. Then there is a question asking if you'd like to encode the absolute position or coordinates, and finally a page with all the default values for additional
variables provided but that can be changed if any overrides are wanted.

---


## **Output**
The script generates a `.gds` file with the specified QR code layout. The file is saved in the working directory with a unique name to avoid overwriting.

---

## **Performance**
The application leverages multi-threading to efficiently handle large grid layouts, ensuring quick generation even for complex designs.

---


## **License**
This project is licensed under the MIT License. See the LICENSE file for details.

---

Feel free to edit this file to align it with the specific objectives and context of your project.
