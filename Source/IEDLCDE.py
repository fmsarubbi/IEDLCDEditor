#!/usr/bin/env python3

"""
Infinity ErgoDox LCD Editor, by LuX
The program will insert image and color data into pre-compiled *.dfu.bin files

More info:
    * https://geekhack.org/index.php?topic=82904.0
    * https://input.club/forums/topic/ied-lcd-editor-v0-9-gui-editor-to-modify-the-lcd  # nopep8

Code distributed "as is", use at your own risk
"""

from time import sleep
from tkinter import *
from PIL import Image, ImageTk
import easygui as gui
import serial
from serial.tools import list_ports


# GLOBALS
__version__ = '0.9.1'
__title__ = 'IED LCD Editor'
__author__ = ['LuX', 'hymnis']
__licence__ = 'MS-PL'

IDERR = 0
IDOK = 1
IDCANCEL = 2
IDABORT = 3
IDRETRY = 4
IDIGNORE = 5
IDYES = 6
IDNO = 7
IDTRYAGAIN = 10
IDCONTINUE = 11

in_image = [None] * 8
image_data = [[] for y in range(8)]


class Application(object):
    """IED LCD Editor main application"""

    root = None

    display_frame = [None for y in range(8)]
    display_photo = [None for y in range(8)]

    color_slide = [[None for x in range(3)] for y in range(8)]
    color_value = [[None for x in range(3)] for y in range(8)]
    color_int = [[None for x in range(3)] for y in range(8)]
    color_box = [None for y in range(8)]

    img_buttons = [[None for x in range(3)] for y in range(8)]
    gui_buttons = [None for y in range(6)]

    author_box = None
    status_box = None

    ser = None

    def __init__(self):
        self.root = Tk()
        self.root.title("{} {}".format(__title__, __version__))
        self.root.resizable(0, 0)

        # Load images to black-white format
        for n in range(0, 8):
            try:
                in_image[n] = Image.open("F{0}.bmp".format(n)).convert("1")
            except (IOError, OSError):
                gui.msgbox(
                    "Error loading image 'F{0}.bmp'\n"
                    "The app will now close".format(n), "File not found")
                exit(1)

            if not in_image[n].width == 128 - 96 * min(1, n) or \
                    not in_image[n].height == 32:
                gui.msgbox(
                    "Image 'F{0}.bmp' is of wrong size\n"
                    "Should be:  {1} x 32\nImage is:  {2} x {3}\n"
                    "The app will now close".format(
                        n, 128 - 96 * min(1, n),
                        in_image[n].width, in_image[n].height),
                    "Wrong size")
                exit(1)

        # Transform images into LCD acceptable data
        image_data[0] = [0] * 4 * 128
        for i in range(1, 8):
            image_data[i] = [0] * 4 * 32

        for i in range(0, 8):
            imgwidth = in_image[i].width
            for p in range(0, 4):
                for z in range(0, 8):
                    for x in range(0, imgwidth):
                        if in_image[i].getpixel((x, (3 - p) * 8 + 7 - z)) == 0:
                            image_data[i][p * imgwidth + x] |= (1 << z)

        # Load and make color scales
        colors = []
        try:
            with open('colors.txt') as f:
                line_num = 0
                for line in f:
                    line_num += 1
                    try:
                        colors.append(max(0, min(int(line), 100)))
                    except ValueError:
                        gui.msgbox(
                            "Invalid color in 'colors.txt': '{0}', at line:"
                            " {1}\nThe app will now close".format(
                                line.rstrip(), line_num),
                            "Invalid color")
                        exit(1)
        except (IOError, OSError):
            gui.msgbox(
                "Error loading 'colors.txt'!\n"
                "The app will now close",
                "File not found")
            exit(1)

        if len(colors) != 24:
            gui.msgbox(
                "Invalid number of colors in 'colors.txt'\n"
                "Make sure there are 24 lines of numbers in the file\n"
                "The app will now close",
                "Invalid file")
            exit(1)

        for i in range(0, 8):
            for c in range(0, 3):
                colorr = "red"
                if c == 1:
                    colorr = "green"
                elif c == 2:
                    colorr = "blue"

                self.color_value[i][c] = IntVar()
                self.color_slide[i][c] = Scale(
                    self.root, bg=colorr, from_=0, to=100,
                    variable=self.color_value[i][c], orient=HORIZONTAL,
                    showvalue=0, width=12, length=200, sliderlength=20,
                    command=self.update_color)
                self.color_slide[i][c].set(int(colors[i * 3 + c]))
                self.color_slide[i][c].place(x=40, y=20 + i * 80 + c * 20)

                self.color_int[i][c] = Label(self.root, text="0%")
                self.color_int[i][c].place(x=5, y=19 + i * 80 + c * 20)

            self.color_box[i] = Label(
                self.root, text="", width=1, padx=71,
                height=1, pady=19, bg="#FFFFFF")
            self.color_box[i].place(x=260, y=22 + i * 80)

        for i in range(0, 8):
            temp_img = Image.new("1", (128, 32), "white")
            temp_img.paste(in_image[i], (0, 0))
            self.display_photo[i] = ImageTk.PhotoImage(temp_img)

            self.display_frame[i] = Label(
                self.root, image=self.display_photo[i], padx=0, pady=0)
            self.display_frame[i].place(x=270, y=32 + i * 80)

        for i in range(0, 8):
            self.img_buttons[i][0] = Button(
                self.root, text='Preview', bg='#AAAAAA',
                font=('arial', 8), width=14, pady=-2,
                command=lambda ind=i: self.preview_setting(ind))
            self.img_buttons[i][0].place(x=430, y=15 + i * 80)
            self.img_buttons[i][1] = Button(
                self.root, text='Reload Image', bg='#999999',
                font=('arial', 8), width=14, pady=-2,
                command=lambda ind=i: self.reload_image(ind))
            self.img_buttons[i][1].place(x=430, y=38 + i * 80)
            self.img_buttons[i][2] = Button(
                self.root, text='Reload Color', bg='#888888',
                font=('arial', 8), width=14, pady=-2,
                command=lambda ind=i: self.reload_color(ind))
            self.img_buttons[i][2].place(x=430, y=61 + i * 80)

        self.gui_buttons[0] = Button(
            self.root, text='Default colors', bg='#9999AA',
            width=20, pady=-2, command=self.default_all)
        self.gui_buttons[0].place(x=10, y=665)
        self.gui_buttons[1] = Button(
            self.root, text='Reload all', bg='#99AA99',
            width=20, pady=-2, command=self.reload_all)
        self.gui_buttons[1].place(x=195, y=665)
        self.gui_buttons[2] = Button(
            self.root, text='Exit', bg='#AA9999',
            width=20, pady=-2, command=self.root.destroy)
        self.gui_buttons[2].place(x=380, y=665)
        self.gui_buttons[3] = Button(
            self.root, text='Save LEFT.dfu.bin', bg='#44FF44',
            width=20, pady=-2,
            command=lambda left=True: self.save_to_file(left))
        self.gui_buttons[3].place(x=10, y=700)
        self.gui_buttons[4] = Button(
            self.root, text='Save RIGHT.dfu.bin', bg='#44FF44',
            width=20, pady=-2,
            command=lambda left=False: self.save_to_file(left))
        self.gui_buttons[4].place(x=195, y=700)
        self.gui_buttons[5] = Button(
            self.root, text='Connect to IED', bg='#faff00',
            width=20, pady=-2, command=self.connect_ied)
        self.gui_buttons[5].place(x=380, y=700)

        self.author_box = Label(
            self.root, text='by: {}'.format(', '.join(__author__)))
        self.author_box.place(x=10, y=730)

        self.status_box = Label(self.root, text='')
        self.status_box.place(x=380, y=730)

        # Connect to keyboard (if possible)
        self.connect_ied()

        self.root.geometry("580x750")
        self.root.mainloop()

    # Serial #
    def connect_ied(self):
        """Look for connected keyboard"""

        com_selection = None

        # Find all available COM ports
        port_list = []
        available_ports = list_ports.grep('1c11:b04d')
        for port_no, description, address in available_ports:
            port_list.append(port_no)

        # Select port to use
        if len(port_list) > 0:
            if len(port_list) > 1:
                com_selection = gui.choicebox(
                    "Please select COM port to use", "Select COM port",
                    port_list)
            else:
                com_selection = port_list[0]

            try:
                self.ser = serial.Serial()
                self.ser.baudrate = 115200
                self.ser.timeout = 0.5
                self.ser.port = com_selection
                self.ser.open()

                if self.ser.isOpen():
                    self.status_box['text'] = 'Connected to: {}'.format(
                        com_selection)

                self.ser.close()
            except IOError:
                gui.msgbox(
                    "Could not connect to the Infinity Ergodox!\n"
                    "If the keyboard was just connected, wait a couple "
                    "of seconds before trying to connect.",
                    "Connection error")
                self.ser = None
                self.status_box['text'] = ''

    def clear_lcd(self):
        """Clears the LCD"""

        self.ser.write(bytes('lcdInit\r'.encode('ascii')))
        sleep(0.1)

    def set_lcd_color(self, i):
        """Sets the color of the screen"""

        command = 'lcdColor ' \
            + str(int(655.35 * self.color_value[i][0].get())) \
            + ' ' + str(int(655.35 * self.color_value[i][1].get())) \
            + ' ' + str(int(655.35 * self.color_value[i][2].get())) + ' \r'
        self.ser.write(bytes(command.encode('ascii')))
        sleep(0.05)

    def set_lcd_image(self, i):
        """Sets the image on the screen"""

        # Only allow full image width for image 0
        width = 128
        if i > 0:
            width = 32

        for segment in range(8):
            for z in range(0, 4):
                command = 'lcdDisp ' + \
                    hex(z) + ' ' + hex(segment * 16) + ' '
                for x in range(segment * 16, segment * 16 + 16):
                    if x < width:
                        command += hex(image_data[i][z * width + x]) + ' '
                    else:
                        command += hex(0) + ' '
                command += '\r'
                self.ser.write(bytes(command.encode('ascii')))
                sleep(0.03)

    def preview_setting(self, i):
        """Show preview of image and color"""

        try:
            if self.ser is not None:
                self.ser.open()

                self.clear_lcd()
                self.set_lcd_color(i)
                self.set_lcd_image(i)

                self.ser.close()

        except (IOError, OSError):
            if gui.ccbox(
                    "Error while previewing an image!\n"
                    "Try to reconnect to keyboard?",
                    "Error"):
                self.status_box['text'] = ''
                self.connect_ied()
            else:
                self.status_box['text'] = ''

    # GUI #
    def update_color(self, a):
        """Updates color value"""

        for i in range(0, 8):
            col_r = int(pow(self.color_value[i][0].get(), 1 / 4) * 80.638)
            col_g = int(pow(self.color_value[i][1].get(), 1 / 4) * 80.638)
            col_b = int(pow(self.color_value[i][2].get(), 1 / 4) * 80.638)

            self.color_box[i].config(
                bg=('#%02x%02x%02x' % (col_r, col_g, col_b)))
            self.color_int[i][0].config(
                text="{0}%".format(self.color_value[i][0].get()))
            self.color_int[i][1].config(
                text="{0}%".format(self.color_value[i][1].get()))
            self.color_int[i][2].config(
                text="{0}%".format(self.color_value[i][2].get()))

    def reload_image(self, i):
        """Reloads the image from file"""

        try:
            in_image[i] = Image.open("F{0}.bmp".format(i)).convert("1")
        except (IOError, OSError):
            self.root.destroy()

        # Clear previous buffer
        for n in range(0, len(image_data[i])):
            image_data[i][n] = 0

        # Transform new image to buffer
        imgwidth = in_image[i].width
        for p in range(0, 4):
            for z in range(0, 8):
                for x in range(0, imgwidth):
                    if in_image[i].getpixel((x, (3 - p) * 8 + 7 - z)) == 0:
                        image_data[i][p * imgwidth + x] |= (1 << z)

        # Re-present the GUI image
        temp_img = Image.new("1", (128, 32), "white")
        temp_img.paste(in_image[i], (0, 0))
        self.display_photo[i] = ImageTk.PhotoImage(temp_img)
        self.display_frame[i].config(image=self.display_photo[i])

    def reload_color(self, i):
        """Reloads color value"""

        with open("colors.txt") as f:
            colors = f.readlines()

        if len(colors) != 24:
            gui.msgbox(
                "Invalid number of colors in 'colors.txt'\n"
                "Make sure there are 24 lines of numbers in the file\n"
                "The app will now close",
                "Invalid file")
            exit(1)

        self.color_slide[i][0].set(int(colors[i * 3]))
        self.color_slide[i][1].set(int(colors[i * 3 + 1]))
        self.color_slide[i][2].set(int(colors[i * 3 + 2]))

    def default_all(self):
        """Resets values to default"""

        # default images
        # set images here...

        # default colors (approximate)
        self.color_slide[0][0].set(int(6))
        self.color_slide[0][1].set(int(6))
        self.color_slide[0][2].set(int(6))

        self.color_slide[1][0].set(int(65))
        self.color_slide[1][1].set(int(15))
        self.color_slide[1][2].set(int(12))

        self.color_slide[2][0].set(int(30))
        self.color_slide[2][1].set(int(55))
        self.color_slide[2][2].set(int(20))

        self.color_slide[3][0].set(int(0))
        self.color_slide[3][1].set(int(50))
        self.color_slide[3][2].set(int(70))

        self.color_slide[4][0].set(int(96))
        self.color_slide[4][1].set(int(64))
        self.color_slide[4][2].set(int(28))

        self.color_slide[5][0].set(int(72))
        self.color_slide[5][1].set(int(36))
        self.color_slide[5][2].set(int(52))

        self.color_slide[6][0].set(int(74))
        self.color_slide[6][1].set(int(71))
        self.color_slide[6][2].set(int(18))

        self.color_slide[7][0].set(int(1))
        self.color_slide[7][1].set(int(50))
        self.color_slide[7][2].set(int(34))

    def reload_all(self):
        """Reload all values"""

        for i in range(0, 8):
            self.reload_image(i)
            self.reload_color(i)

    # Files #
    def save_colors(self):
        """Saves colors to file"""

        with open("colors.txt", 'w') as cfile:
            for i in range(0, 8):
                cfile.write(str(self.color_value[i][0].get()) + "\n")
                cfile.write(str(self.color_value[i][1].get()) + "\n")
                cfile.write(str(self.color_value[i][2].get()) + "\n")
        cfile.close()

    def save_to_file(self, left_side=True):
        """Saves data to .dfu.bin file"""

        # Save color values
        self.save_colors()

        # Save data
        dfu_file = "left_kiibohd.dfu.bin" if not left_side \
            else "right_kiibohd.dfu.bin"

        try:
            with open(dfu_file, 'rb') as infile, \
                    open("custom_" + dfu_file[0:], 'wb') as outfile:
                search = True
                functionsSaved = False
                colorsSaved = False
                defaultSaved = False
                sstr = b"12345678901234567890"

                while search:
                    byte = infile.read(1)
                    sstr = (sstr + byte)[1:]
                    if not byte == b'':
                        if not functionsSaved and sstr == bytes(
                                [0xFC, 0xFC, 0xFC, 0xFC, 0xFC, 0xFC, 0xFC,
                                 0xFC, 0xFC, 0xFC, 0xFC, 0xFF, 0xFF, 0xFF,
                                 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00]
                        ):
                            functionsSaved = True

                            outfile.write(bytes(2))
                            outfile.write(
                                (''.join(chr(i) for i in image_data[1]))
                                .encode('latin-1'))
                            outfile.write(
                                (''.join(chr(i) for i in image_data[2]))
                                .encode('latin-1'))
                            outfile.write(
                                (''.join(chr(i) for i in image_data[3]))
                                .encode('latin-1'))
                            outfile.write(
                                (''.join(chr(i) for i in image_data[4]))
                                .encode('latin-1'))
                            outfile.write(
                                (''.join(chr(i) for i in image_data[5]))
                                .encode('latin-1'))
                            outfile.write(
                                (''.join(chr(i) for i in image_data[6]))
                                .encode('latin-1'))
                            outfile.write(
                                (''.join(chr(i) for i in image_data[7]))
                                .encode('latin-1'))
                            infile.read(897)

                        elif not colorsSaved and sstr == bytes(
                                [0xFC, 0xFC, 0xFC, 0xFC, 0xFC, 0xFF, 0xFF,
                                 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00,
                                 0x39, 0xB9, 0xEA, 0xAA, 0x8D, 0x8D]
                        ):
                            colorsSaved = True

                            outfile.write(bytes([0x8D]))
                            for col in range(1, 8):
                                for chan in range(0, 3):
                                    lo, hi = divmod(
                                        int(655.35
                                            * self.color_value[col][chan]
                                            .get()),
                                        1 << 8)
                                    outfile.write(chr(hi).encode('latin-1'))
                                    outfile.write(chr(lo).encode('latin-1'))
                            infile.read(42)

                        elif not defaultSaved and \
                                sstr == b"Defaults to control.":
                            defaultSaved = True

                            outfile.write(b"." + bytes(1))
                            outfile.write(
                                (''.join(chr(i) for i in image_data[0]))
                                .encode('latin-1'))
                            infile.read(513)
                        else:
                            outfile.write(byte)
                    else:
                        search = False

                if not (functionsSaved and colorsSaved and defaultSaved):
                    gui.msgbox(
                        "An error may have occurred while saving '{}'!\n"
                        "Remake the .dfu.bin files from the online "
                        "configurator and try again".format(
                            "custom_" + dfu_file[0:]), "Error while saving")
                else:
                    gui.msgbox("'{}' Saved successfully!".format(
                        "custom_" + dfu_file[0:]), "File saved")

            infile.close()
            outfile.close()
        except (IOError, OSError):
            gui.msgbox(
                "Error while saving file!", "File not found")


app = Application()
