# Programming Assignment 1 November 2023 Evan Hammerstein CID:02228390

#The goal of these six functions is to be able to open and process RGB, uncompressed, .tif tiles and display a list of the correct RGB pixels in the proper orientation

#ifd = image file directory

import math

# FUNCTION ONE - load_file()

def load_file(file_name):
    """load_file takes a file name and stores the file's contents as bytes into the list 'data'
        the name of the file is stored in the variableinfo"""
    try:
        info = file_name
        #extracting the data from the file
        tif_file = open(file_name, 'rb')
        data = tif_file.read()
        tif_file.close()
    except FileNotFoundError: #if no file is found locally matching the name, the message 'file not found' will replace the typical error
        print('file not found')
        return bytes(),'file not found'
    return data, info

# FUNCTION TWO - get_file_header()

def get_file_header(data):
    """get_file_header analyzes the first 8 bytes of the file (the file header)
        gets the endianness (stored in byte_order) and the offset to where the field entries are (stored in ifd_offset)  """
    if data[:2] == b'II': #determining the endianness of the function to accurately process data
         byte_order = 'little'
    elif data[:2] == b'MM':
         byte_order = 'big'
    else:
        raise ValueError("Invalid byte order tag")
    ifd_offset = int.from_bytes(data[4:8], byte_order, signed = False) #converting the 4 bytes into its respective integer to determine how many bytes into the code the ifd entries start
    return byte_order, ifd_offset


#FUNCTION THREE - extract_ifd_entries()
    
def extract_ifd_entries(data, byte_order, ifd_offset):
    """extract_ifd_entries uses data and the ifd_set in order to find the location of the ifd entries in the files and the number of entries (ifd_entries_N)
        Creates a list of the raw byte entries (ifd_entries)"""
    ifd_entries_N = int.from_bytes(data[ifd_offset:ifd_offset+2], byteorder = byte_order) #first 2 bytes translate to the amount of ifd entries
    ifd_entries = []
    for i in range(ifd_entries_N): #adding all of the entries into the list (each entry is 12 bytes long)
        ifd_entries.append(data[ifd_offset+2+(i*12):ifd_offset+14+(i*12)]) 
    return ifd_entries, ifd_entries_N


#FUNCTION FOUR - extract_ifd_entry()

def extract_ifd_entry(ifd_entry, byte_order):
    """extract_ifd_entry takes a raw byte entry and translates it into integers such as the tag, length, and count of the values, and the type such as 'SHORT' or 'ASCII'
        Outputs a list comprising of this processed data (field_entry)  """
    type_name = {1:'BYTE', 2:'ASCII', 3:'SHORT', 4:'LONG', 5:'RATIONAL'} #lookup table for types and length in bytes used in translating the data 
    type_size = {'BYTE':int(1), 'ASCII':int(1), 'SHORT':int(2), 'LONG':int(4), 'RATIONAL':int(8)}
    field_entry = []
    field_entry.append(int.from_bytes(ifd_entry[:2], byte_order, signed = False))
    if byte_order == 'little':
        field_entry.append(type_name[ifd_entry[2]])
        field_entry.append(type_size[type_name[ifd_entry[2]]])
    else: #if the .tif file is written as bigendian, the type is found in ifd_entry[3] instead of ifd_entry[2]
        field_entry.append(type_name[ifd_entry[3]]) 
        field_entry.append(type_size[type_name[ifd_entry[3]]])
    field_entry.append(int.from_bytes(ifd_entry[4:8], byte_order))
    field_entry.append(ifd_entry[8:]) #adding the last 4 bytes to the list for later processing (results in the value associated with the tag or the value offset)
    return field_entry


# FUNCTION FIVE - extract_field_values()

def extract_field_values(data, field_entry, byte_order):
    """   extract_field_values takes a field_entry created in Function 4 and analyzes the last element in order to either translate directly or find the actual
          location of the raw value for the entry. This outputs a dictionary entry comprising of {Tag of the entry: Value of that tag}     """
    temp_value_list = [] #list that will be filled with the integer/string value of the later processed bytes
    field_value = {}
    if field_entry[2]*field_entry[3] <= 4: #if necessary bytes <= 4, the values are found locally in the entry
        if field_entry[1] == 'BYTE':
            for i in range(field_entry[3]):
                temp_value_list.append(field_entry[-1][i:i+i])
        else:
            for i in range(field_entry[3]):
                temp_value_list.append(int.from_bytes(field_entry[-1][i*field_entry[2]:field_entry[2]+i*field_entry[2]], byte_order))
    else: #if necessary bytes > 4, the local values translate to the location where the actual values are stored
        if field_entry[1] == 'BYTE':
            for i in range(field_entry[3]):
                temp_value_list.append(data[int.from_bytes(field_entry[-1],byte_order)+i:int.from_bytes(field_entry[-1],byte_order)+i+1])
        elif field_entry[1] == 'RATIONAL': #must process separately due to each count is two separate integers (that are divided)
            for i in range(field_entry[3]):
                numerator = int.from_bytes(data[int.from_bytes(field_entry[-1], byte_order) + (i*field_entry[2]):int.from_bytes(field_entry[-1], byte_order) + (i*field_entry[2])+4],byte_order)
                denominator = int.from_bytes(data[int.from_bytes(field_entry[-1], byte_order)+ (i*field_entry[2])+4:int.from_bytes(field_entry[-1], byte_order)+(i*field_entry[2]+8)], byte_order)
                temp_value_list.append(numerator/denominator)
        else:
            for i in range(field_entry[3]): 
                temp_value_list.append(int.from_bytes(data[int.from_bytes(field_entry[-1], byte_order)+(i*field_entry[2]):int.from_bytes(field_entry[-1], byte_order) + field_entry[2] + (i*field_entry[2])], byte_order))
    if field_entry[1] == 'ASCII':
        word = []
        del temp_value_list[-1] #last element of an ASCII entry is a null byte
        word.append(''.join(chr(code) for code in temp_value_list))
        field_value[field_entry[0]] = word
    else:
        field_value[field_entry[0]] = temp_value_list #associates the tag and the value into the dictionary
    return field_value


#FUNCTION SIX - extract_image()

def extract_image(data, field_values, byte_order):
    """   extract_image takes the raw data and a dictionary of all of the field_value pairs, and processes the image pixel data found in strips separated amongst the file
            Then combine the RGB values into pixels, then rows, and then into one 3D list based on the dimensions in the tags' values   """
    rgb_raw_values = []
    img = []
    #accessing the dictionary made in Function 5 to assign values to the tag variables
    img_length = field_values[257][0]
    img_width = field_values[256][0]
    samples_per_pixel = field_values[277][0]
    rows_per_strip = field_values[278][0]
    strips_N = math.ceil(img_length / rows_per_strip) 
    for i in range(strips_N): #compiles all of the bytes in separate strings into one big list of integer RGB intensities
        for j in range(field_values[279][i]):
            rgb_raw_values.append(int.from_bytes(data[field_values[273][i] + j: field_values[273][i] + j+1], byte_order))
    for k in range(img_length):   #groups the rows into a 3D list (representing a rectangle)
        row = []
        for l in range(img_width): #groups the pixels into rows
            pixel = []
            for m in range(samples_per_pixel): #groups the RGB components into pixels
                pixel.append(rgb_raw_values[m+samples_per_pixel*l+samples_per_pixel*img_width*k])
            row.append(pixel)
        img.append(row)
    return img
