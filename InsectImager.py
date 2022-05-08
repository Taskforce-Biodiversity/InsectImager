# -*- coding: utf-8 -*-
"""
Created on Sun Apr 16 2022
@author: Ate
@version: 1.0
"""
import webbrowser
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
from PIL import Image, ImageTk
import serial
import serial.tools.list_ports
import os
from pathlib import Path
import time
import gphoto2 as gp
import cv2
import re


class Main:

    def __init__(self, root):
        root.winfo_toplevel().title('Taskforce Kleine biodiversiteit - InsectImager -')
        mainframe = ttk.Frame(root, padding="3 3 3 3")
        mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
        tabcontrol = ttk.Notebook(mainframe)
        sett = ttk.Frame(tabcontrol)
        wps = ttk.Frame(tabcontrol)
        st = ttk.Frame(tabcontrol)
        mvt = ttk.Frame(tabcontrol)
        hlp = ttk.Frame(tabcontrol)

        tabcontrol.add(sett, text='settings')
        tabcontrol.add(wps, text='well-plates')
        tabcontrol.add(st, text='sticky-traps')
        tabcontrol.add(mvt, text='move xy-table')
        tabcontrol.add(hlp, text='help/about')
        def update_tabs():
            self.Wellplate = Wellplate(wps, settings)
            self.Stickytrap = Stickytrap(st, settings)
        tabcontrol.bind('<<NotebookTabChanged>>', lambda e: update_tabs())
        tabcontrol.grid(column=0, row=0)

        settings = Settings()
        SettingsTab(sett, settings)
        # self.Wellplate = Wellplate(wps, settings)
        Move(mvt, settings)
        Help(hlp)

        # add some padding to all widgets
        for child in mainframe.winfo_children():
            child.grid_configure(padx=5, pady=5)
        root.mainloop()


class Settings:
    """Class to hold settings variables to be re-used at other parts of the app"""

    nr_wp = 1  # number of wellplates to scan
    wp_type = 6  # well plate type, number of wells per plate
    # the path were imaged wells can be saved
    safe_path = os.path.join(Path.home(), "InsectImager/data/")
    safe_temp_path = os.path.join(safe_path, ".tempfiles/")
    project_name = "default-project"   # project name
    sample_name = "default-sample"  # sample name
    project_sample_path = os.path.join(safe_path, project_name, sample_name)
    prj_fn_add = True  # setting to add the project ande sample name to the filename (default = yes)
    append_files = True  # setting increment platenames when existing files are present in the folder

    #############################
    # camera details            #
    #############################
    # camera used is Nikon D800 interfaced via libgphoto2
    # variable for camera_object
    cam = None
    cam_connected = False

    ################################
    # y y table serial connection  #
    ################################
    comport_list = None
    comport = "/dev/ttyUSB0"
    # variable for serial object
    ser = None
    xy_connected = connected = False

    #############################
    #  y y table details        #
    #############################
    # xy-table is a modified laser engraver * (Atomstack A10)
    #
    # usb connection details (not currently used):
    # ID 1a86:7523 QinHeng Electronics HL-340 USB-Serial adapter
    # xy_usb_vendor_ID = 0x1a86  #QinHeng Electronics
    # xy_usb_product_ID = 0x7523 #HL-340 USB-Serial adapter

    # xytable dimensions (mm)
    xy_x_max = 399
    xy_y_max = 399
    # speed setting, officially F = in mm/(or inch) per min
    # in practice, based on calibration it seems to be mm/min roughly divided by 1.4
    # ( max speed probably roughly 100 mm/sec = around F8300)
    xy_f_speed = 8300
    xy_f_corr_fact = 1.4

    # ccordinates for different imaging positions in mm per wp type:
    # 6W
    # Greiner plates
    caps_perwp_6w = 6
    nr_crops_6w = 1
    xy_6w_coords = [[7, 0], [7, 39], [7, 78], [46, 0], [46, 39], [46, 78],
                    [92, 0], [92, 39], [92, 78], [131, 0], [131, 39], [131, 78],
                    [177, 0], [177, 39], [177, 78], [216, 0], [216, 39], [216, 78],
                    [262, 0], [262, 39], [262, 78], [301, 0], [301, 39], [301, 78]]

    # 12W
    # Greiner plates
    caps_perwp_12w = 6
    nr_crops_12w = 2
    xy_12w_coords = [[0, 10], [0, 62], [27, 10], [27, 62], [54, 10], [54, 62],
                     [87, 10], [87, 62], [113, 10], [113, 62], [139, 10], [139, 62],
                     [173, 10], [173, 62], [198, 10], [198, 62], [223, 10], [223, 62],
                     [257, 10], [257, 62], [283, 10], [283, 62], [309, 10], [309, 62]]

    crop_offsets_px_12w = []

    # 24W = 6
    caps_perwp_24w = 6
    nr_crops_24w = 4
    # co star plates (+ greiner)
    xy_24w_coords = [[8, 0], [8, 39], [8, 78], [47, 0], [47, 39], [47, 78],
                     [93, 0], [93, 39], [93, 78], [132, 0], [132, 39], [132, 78],
                     [178, 0], [178, 39], [178, 78], [217, 0], [217, 39], [217, 78],
                     [263, 0], [263, 39], [263, 78], [302, 0], [302, 39], [302, 78]]

    # 48W

    # default stickytraps no overlap
    caps_per_st = 4
    nr_crops_st = 1
    xy_st_coords = [[390, 0], [390, 77], [390, 154], [390, 231], [390, 308], [390, 385]]
    #xy_st_coords = [[399, 0], [399, 75], [399, 150], [399, 225], [399, 300], [399, 375]]

    # delay in taking picture to avoid shaking table/camera after movement (in seconds)
    cam_capture_delay = 2

    # xy_f_calibration = dict (1000 = 12, 2000 = 24, 3000 = 36, 4000 = 48, 5000 = 6000 = 72 )

    # def __int__(self, nr_well_plates, safe_path, safe_temp_path):
    #
    #     self.nr_wp = nr_well_plates
    #     self.safe_path = safe_path
    #     self.safe_temp_path = safe_temp_path

    def __init__(self):
        self.comport_list = self.find_comports()
        # self.create_safe_path()

    def create_safe_path(self):
        try:
            # also create a temp folder for downloaded camera images
            os.makedirs(self.safe_path, exist_ok=True)
            os.makedirs(self.safe_temp_path, exist_ok=True)
        except FileExistsError:
            # directory already exists
            pass

    def check_max_existing_plate_nr(self):
        max_plt = 0
        max_plt_apnd = 0
        pltnr = 0
        appendstr = self.project_name + "_" + self.sample_name + "_"

        for imf in os.listdir(self.project_sample_path):
            if imf.endswith("jpg"):
                pos = imf.rfind("plate_")
                if pos != -1:
                    startpos = pos + 6
                    endpos = len(imf) - 7
                    pltnr = int(imf[startpos:endpos])

                if appendstr in imf:
                    if pltnr > max_plt_apnd:
                        max_plt_apnd = pltnr
                else:
                    if pltnr > max_plt:
                        max_plt = pltnr

        if self.prj_fn_add:
            max_plt = max_plt_apnd

        return max_plt

    def create_project_sample_path(self):
        try:
            # also create a temp folder for downloaded camera images
            self.project_sample_path = os.path.join(self.safe_path, self.project_name, self.sample_name)
            os.makedirs(os.path.join(self.project_sample_path), exist_ok=True)
        except FileExistsError:
            # directory already exists
            pass

    def find_comports(self):
        comports = list()
        for i in serial.tools.list_ports.comports():
            # print(type(serial.build_binary.list_ports.comports()))
            # d = serial.Serial(i[0])
            # print ('%s - ' % i[0] , d.isOpen())
            # print(i[0])
            # print(i[1])
            comports.append(i[0])
        return comports

    # port='/dev/ttyUSB0'
    def open_serial_connection(self, baudrate=115200):

        try:
            ser = serial.Serial(self.comport, baudrate)
            time.sleep(2)  # delay to allow for time to pass communication over the bus.
            self.xy_connected = True
            print("connection " + str(ser))
            return ser, True

        except:
            messagebox.showwarning("connection failure", "Could not connect to xy table")

    def close_serial_connection(self, ser):

        time.sleep(2)  # delay to allow for time to pass communication over the bus.
        ser.close()
        print("closed serial connection")

    def initialize_xy(self):
        # set gcode coordinate system to mm (not inch)
        self.ser.write(bytes("G21\n", 'utf-8'))


class SettingsTab:

    def __init__(self, parent, settings):

        # assign settings object to store variables in the app
        self.s = settings
        self.s.create_safe_path()

        # row 0
        frame = ttk.Frame(parent, padding="10 10 10 10")
        frame.grid(column=0, row=0, sticky=(N, W, E, S))

        # row 1
        dfframe = ttk.LabelFrame(frame, text="Data folder: ", padding="10 10 10 10")
        dfframe.grid(column=0, row=0, sticky=(N, W, E, S))

        # TODO fix error when empty string is returned on cancel
        # open button
        open_button = ttk.Button(
            dfframe,
            text='Select data folder',
            command=self.select_folder
        )
        # self.s.safe_path = "~/wellplate_scanner/samples"
        ttk.Label(dfframe, text="Current data folder: ").grid(row=0, column=0, pady=5, sticky=W)
        self.safe_path_lbl = ttk.Label(dfframe, text=self.s.safe_path)
        self.safe_path_lbl.grid(row=0, column=1)
        open_button.grid(row=1, column=0, pady=5, sticky=W)

        spframe = ttk.LabelFrame(frame, text="Sample name: ", padding="10 10 10 10")
        spframe.grid(row=1, column=0, sticky=(N, W, E, S))

        ttk.Label(spframe, text="Project name: ", padding="5 5 5 5").grid(row=0, column=0, sticky=W)
        ttk.Label(spframe, text="Sample name: ", padding="5 5 5 5").grid(row=1, column=0, sticky=W)

        self.validate_entry_wrapper = (root.register(self.validate_entry), '%P')

        self.prj_name = StringVar()
        self.prj_name_entry = ttk.Entry(spframe, textvariable=self.prj_name, validate='key',
                                        validatecommand=self.validate_entry_wrapper)
        self.prj_name_entry.grid(row=0, column=1)
        self.prj_name.set(self.s.project_name)

        def callback_upd_prj_name(var, index, mode):
            self.upd_prj_name()
        self.prj_name.trace_add("write", callback_upd_prj_name)

        self.sp_name = StringVar()
        self.sp_name_entry = ttk.Entry(spframe, textvariable=self.sp_name, validate='key',
                                       validatecommand=self.validate_entry_wrapper)
        self.sp_name_entry.grid(row=1, column=1)
        self.sp_name.set(self.s.sample_name)

        def callback_upd_sp_name(var, index, mode):
            self.upd_sp_name()

        self.sp_name.trace_add("write", callback_upd_sp_name)

        self.prj_fn_add = BooleanVar()
        self.prj_fn_add_check = ttk.Checkbutton(spframe,
                                                text="Add sample and project name to the filename",
                                                variable=self.prj_fn_add,
                                                state="True",
                                                command=self.upd_prjfn_add_check)
        self.prj_fn_add_check.grid(row=2, column=0, columnspan=2, pady=5, sticky=W)
        self.prj_fn_add.set(True)

        # row 2
        wpframe = ttk.LabelFrame(frame, text="Well-plate settings: ", padding="10 10 10 10")
        wpframe.grid(column=0, row=2, sticky=(N, W, E, S))

        self.wpnr = IntVar()
        self.wpnr.set(1)
        self.s.nr_wp = self.wpnr.get()
        ttk.Label(wpframe, text="Number of well-plates: ").grid(row=0, column=0, sticky=E)
        ttk.Radiobutton(wpframe, text="1", variable=self.wpnr, value=1, command=self.upd_wp_nr).grid(row=0, column=1,
                                                                                                     sticky=NW, padx=3,
                                                                                                     pady=5)
        ttk.Radiobutton(wpframe, text="2", variable=self.wpnr, value=2, command=self.upd_wp_nr).grid(row=0, column=2,
                                                                                                     sticky=NW, padx=3,
                                                                                                     pady=5)
        ttk.Radiobutton(wpframe, text="3", variable=self.wpnr, value=3, command=self.upd_wp_nr).grid(row=0, column=3,
                                                                                                     sticky=NW, padx=3,
                                                                                                     pady=5)
        ttk.Radiobutton(wpframe, text="4", variable=self.wpnr, value=4, command=self.upd_wp_nr).grid(row=0, column=4,
                                                                                                     sticky=NW, padx=3,
                                                                                                     pady=5)

        self.wptype = IntVar()
        self.wptype.set(6)
        self.s.wp_type = self.wptype.get()
        ttk.Label(wpframe, text="Well-plate type: ").grid(row=1, column=0, sticky=E)
        ttk.Radiobutton(wpframe, text="6-wells", variable=self.wptype, value=6, command=self.upd_wp_type).grid(row=1,
                                                                                                               column=1,
                                                                                                               sticky=NW,
                                                                                                               padx=3,
                                                                                                               pady=5)
        ttk.Radiobutton(wpframe, text="12-wells", variable=self.wptype, value=12, command=self.upd_wp_type).grid(row=1,
                                                                                                                 column=2,
                                                                                                                 sticky=NW,
                                                                                                                 padx=3,
                                                                                                                 pady=5)
        ttk.Radiobutton(wpframe, text="24-wells", variable=self.wptype, value=24, command=self.upd_wp_type).grid(row=1,
                                                                                                                 column=3,
                                                                                                                 sticky=NW,
                                                                                                                 padx=3,
                                                                                                                 pady=5)
        # ttk.Radiobutton(wpframe, text="48-wells", variable=self.wptype, value=48, command=self.upd_wp_type).grid(row=1, column=4)

        ###################################################################################
        # Devices (2nd column in interface
        ###################################

        # XY table
        # row 0 --> ### column 1
        xytableframe = ttk.LabelFrame(frame, text="XY-table ", padding="10 10 10 10")
        xytableframe.grid(column=1, row=0, sticky=(N, W, E, S))

        self.xy_table = StringVar()
        self.xy_comports = ttk.Combobox(xytableframe,
                                        state="readonly",
                                        values=self.s.comport_list,
                                        textvariable=self.xy_table)
        self.xy_comports.grid(row=0, column=0)
        self.xy_comports.bind("<<ComboboxSelected>>", lambda e: self.xy_comports.selection_clear())
        if len(self.s.comport_list) > 0:
            # self.xy_comports['value'] = self.s.comport_list[0]
            self.xy_comports.set(self.s.comport_list[0])

        self.connect_xy_button = ttk.Button(xytableframe, text='Connect XY-table', command=self.open_xytable_window)
        self.connect_xy_button.grid(row=1, column=0, sticky=W, pady=5)
        if self.s.xy_connected:
            self.connect_xy_button['state'] = DISABLED

        # Camera
        # row 1 --> ### column 1
        cameraframe = ttk.LabelFrame(frame, text="Camera ", padding="10 10 10 10")
        cameraframe.grid(column=1, row=1, sticky=(N, W, E, S))

        self.connect_camera_button = ttk.Button(cameraframe, text='Connect camera', command=self.connect_camera)
        self.connect_camera_button.grid(row=0, column=0, sticky=W, pady=5)
        if self.s.cam_connected:
            self.connect_camera_button['state'] = DISABLED

        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def select_folder(self):
        self.s.safe_path = fd.askdirectory(title="Select data folder", mustexist=TRUE)
        self.safe_path_lbl['text'] = self.s.safe_path

    def upd_wp_nr(self):
        self.s.nr_wp = self.wpnr.get()
        # print(self.s.nr_wp)

    def upd_wp_type(self):
        self.s.wp_type = self.wptype.get()
        # print(self.s.wp_type)

    def upd_prj_name(self):
        self.s.project_name = str(self.prj_name.get())
        # print(self.s.project_name)

    def upd_sp_name(self):
        self.s.sample_name = str(self.sp_name.get())
        # print(self.s.sample_name)

    def upd_prjfn_add_check(self):
        self.s.prj_fn_add = self.prj_fn_add.get()
        print(self.prj_fn_add)
        print(self.s.prj_fn_add)

    def validate_entry(self, newval):
        # allow only alphanumeric character, _ and - and not empty
        return re.match("^[a-zA-Z0-9_-]*$", newval) is not None

    def connect_camera(self):
        self.s.cam = Camera(self.s)
        self.s.cam.initialize()
        print(self.s.cam.error)
        if self.s.cam.error == 0:
            self.s.cam_connected = True
            self.connect_camera_button['state'] = DISABLED
            self.connect_camera_button['text'] = "Camera connected"
        elif self.s.cam.error == -60:
            messagebox.showinfo("Communication failure", "Camera detected but cannot connect.\n\n"
                                                         "Is it in use by another program, or mounted?")
        else:
            messagebox.showerror("Connection failure", "Cannot connect to the camera.")

    def open_xytable_window(self):

        answer = messagebox.askyesno("Connect XY-table",
                                     "Home the holder\n(x=0mm and y=0mm) \n\n\n"
                                     "!! BEFORE !!  you connect.\n\n"
                                     "Incorrect homing will damage the table!\n\n"
                                     "Did you home the XY table?\n\n")
        if answer:
            self.s.ser, succes = self.s.open_serial_connection()
            if succes:
                self.connect_xy_button['state'] = DISABLED
                self.connect_xy_button['text'] = "XY-table connected"
                print(self.s.xy_connected)


class Camera():
    error = None
    cam = None
    def __init__(self,settings):
        self.s = settings

    def initialize(self):
        self.error, self.cam = gp.gp_camera_new()
        self.error = gp.gp_camera_init(self.cam)


    def event_text(self, event_type):

        if event_type == gp.GP_EVENT_CAPTURE_COMPLETE:
            return "Capture Complete"
        elif event_type == gp.GP_EVENT_FILE_ADDED:
            return "File Added"
        elif event_type == gp.GP_EVENT_FOLDER_ADDED:
            return "Folder Added"
        elif event_type == gp.GP_EVENT_TIMEOUT:
            return "Timeout"
        else:
            return "Unknown Event"

    # def empty_cam_cue(self, camera):
    def empty_cam_cue(self):

        # empty the camera event queue (necessary to prevent camera interface lockups)
        typ, data = self.cam.wait_for_event(200)
        # typ, data = camera.wait_for_event(200)
        while typ != gp.GP_EVENT_TIMEOUT:

            # print("Event: %s, data: %s" % (event_text(typ), data))

            if typ == gp.GP_EVENT_FILE_ADDED:
                fn = os.path.join(data.folder, data.name)
                print("New file: %s" % fn)
            # self.download_file(fn)

            # try to grab another event
            # typ, data = camera.wait_for_event(1)
            typ, data = self.cam.wait_for_event(1)

    def capture_and_get(self):
        pic = self.cam.capture(gp.GP_CAPTURE_IMAGE)
        file = self.cam.file_get(pic.folder, pic.name, gp.GP_FILE_TYPE_NORMAL)
        return file

    def file_get(self, pic):
        file = self.cam.file_get(pic.folder, pic.name, gp.GP_FILE_TYPE_NORMAL)
        return file

    def calc_movement_delay(self, x, y, f):
        """ based on calibration of actual movement time (see settings) xy in mm en speed(F) in mm/min/1.4 """
        if x > y:
            maxd = x
        else:
            maxd = y
        mm_sec = f / self.s.xy_f_corr_fact / 60
        mov_tm = maxd / mm_sec
        # add (2-3) seconds for shaking movement to stabilize, and round up to the nearest second
        mov_tm = mov_tm + self.s.cam_capture_delay
        return mov_tm


class Wellplate:

    def __init__(self, parent, settings):
        # reference the settings object
        self.s = settings
        # create the folderstructure if it does not yet exist
        self.s.create_safe_path()

        self.pbval = 0
        self.maxcap = None
        self.pbmax = None
        self.wp_coords = None
        self.wp_type = self.s.wp_type
        self.nr_wp = self.s.nr_wp
        self.project_name = self.s.project_name
        self.sample_name = self.s.sample_name
        self.project_sample_path = self.s.project_sample_path
        self.caps_perwp = None
        self.nr_crops = None
        self.plate_start_nr = 1

        self.frame = ttk.Frame(parent, padding="10 10 10 10")
        self.frame.grid(column=0, row=0, sticky=(N, W, E, S))

        self.pb = ttk.Progressbar(self.frame, orient=HORIZONTAL, length=400, mode='determinate', maximum=self.pbmax)
        self.pb['value'] = 0
        self.pb.grid(row=2, column=0, sticky=W)

        self.strstp_button = Button(self.frame, text='Start imaging', command=self.start)
        self.strstp_button.grid(row=3, column=0, sticky=W, pady=5)

        self.wellpic_list = self.create_empty_wellpic_list()
        self.update_wp_grid(self.wellpic_list)


    def start(self):

        if not self.s.cam_connected or not self.s.xy_connected:
            messagebox.showerror("connection error", "XY-table and/or camera not connected\n"
                                                     "Cannot continue.")
        else:

            self.pbval = 0
            self.pb['value'] = self.pbval
            self.strstp_button.configure(text='Stop', command=self.stop)

            global interrupt
            interrupt = False

            # store some vars locally to make operation safe for changes in settings tab
            self.wp_type = self.s.wp_type
            self.nr_wp = self.s.nr_wp
            self.project_name = self.s.project_name
            self.sample_name = self.s.sample_name
            self.project_sample_path = os.path.join(self.s.safe_path, self.project_name, self.sample_name)

            # # update the picture grid with empty pictures
            # self.wellpic_list = self.create_empty_wellpic_list()
            # self.update_wp_grid(self.wellpic_list)

            # create the folders
            self.s.create_project_sample_path()

            if self.wp_type == 6:
                self.maxcap = int(self.s.caps_perwp_6w * self.s.nr_wp)
                self.pb['maximum'] = self.maxcap
                self.wp_coords = self.s.xy_6w_coords
                self.caps_perwp = self.s.caps_perwp_6w
                self.nr_crops = self.s.nr_crops_6w

            elif self.wp_type == 12:
                self.maxcap = int(self.s.caps_perwp_12w * self.s.nr_wp)
                self.pb['maximum'] = self.maxcap
                self.wp_coords = self.s.xy_12w_coords
                self.caps_perwp = self.s.caps_perwp_12w
                self.nr_crops = self.s.nr_crops_12w

            elif self.wp_type == 24:
                self.maxcap = int(self.s.caps_perwp_24w * self.s.nr_wp)
                self.pb['maximum'] = self.maxcap
                self.wp_coords = self.s.xy_24w_coords
                self.caps_perwp = self.s.caps_perwp_24w
                self.nr_crops = self.s.nr_crops_24w

            elif self.wp_type == 48:
                self.maxcap = int(self.s.caps_perwp_48w * self.s.nr_wp)
                self.pb['maximum'] = self.maxcap
                self.wp_coords = self.s.xy_48w_coords
                self.caps_perwp = self.s.caps_perwp_48w
                self.nr_crops = self.s.nr_crops_48w

            if self.s.append_files:
                self.plate_start_nr += self.s.check_max_existing_plate_nr()

            print("wptype: " + str(self.s.wp_type))
            print("nrwp: " + str(self.s.nr_wp))
            print("maxcap: " + str(self.maxcap))
            print(self.s.sample_name)
            # invoke the capturenext function via root.after to allow the eventloop to update the interface
            self.toggle_tab_state("disabled")
            root.after(1, self.capture_next)

    def stop(self):

        self.strstp_button.configure(text='Start imaging', command=self.start)
        self.update_wp_grid(self.wellpic_list)
        global interrupt
        interrupt = True
        self.pb['value'] = 0
        self.home_xy()
        self.toggle_tab_state("normal")

    def capture_next(self, nextcap=0):

        global interrupt
        if interrupt:
            # home the table
            self.home_xy()
            self.toggle_tab_state("normal")
            return

        if nextcap < self.maxcap:
            self.pbval += 1
            self.pb['value'] = self.pbval
            x = self.wp_coords[nextcap][0]
            y = self.wp_coords[nextcap][1]
            # root.after(1000)
            print("nextcap: " + str(nextcap) + " xy" + str(x) + " " + str(y))
            self.move_and_capture(x, y, self.s.xy_f_speed)
            self.crop_save_wells(nextcap, self.plate_start_nr)

        else:
            self.pb['value'] = self.pbmax
            print("nextcap: " + str(nextcap))
            self.strstp_button.configure(text='Start imaging', command=self.start)
            # home the xy table
            self.home_xy()
            # ser.write(bytes("G28\n", 'utf-8'))
            self.update_wp_grid(self.wellpic_list)
            interrupt = True
            self.toggle_tab_state("normal")
            return

        root.after(1, lambda: self.capture_next(nextcap + 1))

    def home_xy(self):
        self.s.ser.write(bytes("G28\n", 'utf-8'))

    def move_and_capture(self, x, y, f):

        self.goto_position(x, y, f)
        time.sleep(self.s.cam.calc_movement_delay(x, y, f))
        self.capture_image("temp_cap.jpg")
        # self.crop_save_wells_old(1, 12)
        # take the pic

    def crop_save_wells(self, capnr, plate_start=1):

        temp_image = cv2.imread(os.path.join(self.s.safe_temp_path, "temp_cap.jpg"))
        temp_image = cv2.rotate(temp_image, cv2.ROTATE_180)

        if self.wp_type == 6:
            well_labels = ["A1", "A2", "A3",
                           "B1", "B2", "B3"]
            wp_nr_str = "plate_" + str(int(capnr / self.caps_perwp) + plate_start).zfill(2)

            # crop
            well_nr = capnr % self.caps_perwp
            crop = temp_image[2300:5200, 800:3700]
            save_fn = wp_nr_str + "_" + well_labels[well_nr] + ".jpg"
            # add project en sample name to the filename if checked
            if self.s.prj_fn_add:
                save_fn = self.s.project_name + "_" + self.s.sample_name + "_" + save_fn
            cv2.imwrite(os.path.join(self.project_sample_path, save_fn), crop)
            wp_thumb = cv2.resize(crop, [100, 100], cv2.INTER_NEAREST)
            cv2.imwrite(os.path.join(self.s.safe_temp_path, save_fn), wp_thumb)
            self.wellpic_list[capnr] = os.path.join(self.s.safe_temp_path, save_fn)

        if self.wp_type == 12:
            well_labels = ["A1", "A2", "A3", "A4",
                           "B1", "B2", "B3", "B4",
                           "C1", "C2", "C3", "C4"]
            wp_nr_str = "plate_" + str(int(capnr / self.caps_perwp) + plate_start).zfill(2)

            # crop 1
            well_nr = (capnr % self.caps_perwp) * 2
            picnr = capnr * 2
            crop = temp_image[2760:4610, 575:2425]
            save_fn = wp_nr_str + "_" + well_labels[well_nr] + ".jpg"
            # add project en sample name to the filename if checked
            if self.s.prj_fn_add:
                save_fn = self.s.project_name + "_" + self.s.sample_name + "_" + save_fn
            cv2.imwrite(os.path.join(self.project_sample_path, save_fn), crop)
            wp_thumb = cv2.resize(crop, [75, 75], cv2.INTER_NEAREST)
            cv2.imwrite(os.path.join(self.s.safe_temp_path, save_fn), wp_thumb)
            self.wellpic_list[picnr] = os.path.join(self.s.safe_temp_path, save_fn)

            print("crop1 len: " + str(len(self.wellpic_list)) + " picnr: " + str(picnr))

            # crop 2
            well_nr = (capnr % self.caps_perwp) * 2 + 1
            picnr = capnr * 2 + 1
            crop = temp_image[2760:4610, 2425:4275]
            save_fn = wp_nr_str + "_" + well_labels[well_nr] + ".jpg"
            # add project en sample name to the filename if checked
            if self.s.prj_fn_add:
                save_fn = self.s.project_name + "_" + self.s.sample_name + "_" + save_fn
            cv2.imwrite(os.path.join(self.project_sample_path, save_fn), crop)
            wp_thumb = cv2.resize(crop, [75, 75], cv2.INTER_NEAREST)
            cv2.imwrite(os.path.join(self.s.safe_temp_path, save_fn), wp_thumb)
            self.wellpic_list[picnr] = os.path.join(self.s.safe_temp_path, save_fn)
            print("crop2 len: " + str(len(self.wellpic_list)) + " picnr: " + str(picnr))

        if self.wp_type == 24:
            # TODO quickfix, very unelegant way of generating the labels. fix later when there is time.
            well_labels = ["A1", "A2", "B1", "B2", "A3", "A4", "B3", "B4", "A5", "A6", "B5", "B6",
                           "C1", "C2", "D1", "D2", "C3", "C4", "D3", "D4", "C5", "C6", "D5", "D6",
                           "A1", "A2", "B1", "B2", "A3", "A4", "B3", "B4", "A5", "A6", "B5", "B6",
                           "C1", "C2", "D1", "D2", "C3", "C4", "D3", "D4", "C5", "C6", "D5", "D6",
                           "A1", "A2", "B1", "B2", "A3", "A4", "B3", "B4", "A5", "A6", "B5", "B6",
                           "C1", "C2", "D1", "D2", "C3", "C4", "D3", "D4", "C5", "C6", "D5", "D6",
                           "A1", "A2", "B1", "B2", "A3", "A4", "B3", "B4", "A5", "A6", "B5", "B6",
                           "C1", "C2", "D1", "D2", "C3", "C4", "D3", "D4", "C5", "C6", "D5", "D6"]

            pic_pos_lst = [0, 1, 6, 7, 2, 3, 8, 9, 4, 5, 10, 11, 12, 13, 18, 19, 14, 15, 20, 21, 16, 17, 22, 23,
                           24, 25, 30, 31, 26, 27, 32, 33, 28, 29, 34, 35, 36, 37, 42, 43, 38, 39, 44, 45, 40, 41, 46,
                           47,
                           48, 49, 54, 55, 50, 51, 56, 57, 52, 53, 58, 59, 60, 61, 66, 67, 62, 63, 68, 69, 64, 65, 70,
                           71,
                           72, 73, 78, 79, 74, 75, 80, 81, 76, 77, 82, 83, 84, 85, 90, 91, 86, 87, 92, 93, 88, 89, 94,
                           95]

            wp_nr_str = "plate_" + str(int(capnr / self.caps_perwp) + plate_start).zfill(2)

            for cropnr in range(4):
                pos = capnr * 4 + cropnr
                gridpos = pic_pos_lst[pos]
                well_lbl = well_labels[pos]

                print("cropnr: " + str(cropnr) + ", capnr: " + str(capnr) + ", pos: " + str(pos) + ", gridpos: " + str(
                    gridpos))

                if cropnr == 0:
                    # B/D - 1/3/5
                    # crop = temp_image[2350:3700, 1000:2350]
                    crop = temp_image[2350:3700, 950:2300]
                elif cropnr == 1:
                    # B/D - 2/4/6
                    # crop = temp_image[2350:3700, 2350:3700]
                    crop = temp_image[2350:3700, 2300:3650]
                elif cropnr == 2:
                    # A/C - 1/3/5
                    # crop = temp_image[3700:5050, 1000:2350]
                    crop = temp_image[3700:5050, 950:2300]
                elif cropnr == 3:
                    # A/C - 2/4/6
                    # crop = temp_image[3700:5050, 2350:3700]
                    crop = temp_image[3700:5050, 2300:3650]

                save_fn = wp_nr_str + "_" + well_lbl + ".jpg"
                # add project en sample name to the filename if checked
                if self.s.prj_fn_add:
                    save_fn = self.s.project_name + "_" + self.s.sample_name + "_" + save_fn
                cv2.imwrite(os.path.join(self.project_sample_path, save_fn), crop)
                wp_thumb = cv2.resize(crop, [50, 50], cv2.INTER_NEAREST)
                cv2.imwrite(os.path.join(self.s.safe_temp_path, save_fn), wp_thumb)
                self.wellpic_list[gridpos] = os.path.join(self.s.safe_temp_path, save_fn)
                # print("crop len: " + str(len(self.wellpic_list)) + " picnr: " + str(gridpos), )
            root.after(1)

    def create_empty_wellpic_list(self):

        wellpic_list = list()
        wellctr = self.s.nr_wp * self.s.wp_type

        for i in range(wellctr):
            if self.wp_type == 6:
                wellpic_list.append("assets/wp/wp6_emptywell.png")
            elif self.wp_type == 12:
                wellpic_list.append("assets/wp/wp12_emptywell.png")
            elif self.wp_type == 24:
                wellpic_list.append("assets/wp/wp24_emptywell.png")
            elif self.wp_type == 48:
                wellpic_list.append("assets/wp/wp48_emptywell.png")

        return wellpic_list

    def update_wp_grid(self, wellpic_list):
        pic_ctr = 0
        wp_layout = ttk.Frame(self.frame, padding="10 3 3 10")
        wp_layout.grid(column=0, row=1, sticky=(N, W, E, S))
        root.update_idletasks()

        if self.wp_type == 6:
            rows = ["A", "B"]
            cols = ["1", "2", "3"]
        elif self.wp_type == 12:
            rows = ["A", "B", "C"]
            cols = ["1", "2", "3", " 4"]
        elif self.wp_type == 24:
            rows = ["A", "B", "C", "D"]
            cols = ["1", "2", "3", " 4", "5", "6"]
        elif self.wp_type == 48:
            rows = ["A", "B", "C", "D", "E", "F"]
            cols = ["1", "2", "3", "4", "5", "6", "7", "8"]

        wp_lc = ttk.Frame(wp_layout, padding="3 10 10 3")
        wp_rc = ttk.Frame(wp_layout, padding="3 10 10 3")
        wp_lc.grid(column=0, row=0, sticky=(N, W, E, S))
        wp_rc.grid(column=2, row=0, sticky=(N, W, E, S))

        r = 0
        c = 0
        for p in range(self.nr_wp):
            if p < 2:
                gFrame = wp_lc
            else:
                gFrame = wp_rc

            # label plates
            plate_string = "position: " + str(p + 1)
            ttk.Label(gFrame, text=plate_string).grid(row=r, column=c, pady=10)
            # r += 1
            # row header with column titles
            c1 = 1
            for col in cols:
                ttk.Label(gFrame, text=col).grid(row=r, column=c1)
                c1 += 1
            r += 1
            for row in rows:
                # header
                ttk.Label(gFrame, text=row).grid(row=r, column=c)
                c += 1
                for col in cols:
                    fname = wellpic_list[pic_ctr]
                    pimg = ImageTk.PhotoImage(Image.open(fname))
                    label = ttk.Label(gFrame, image=pimg)
                    label.image = pimg
                    label.grid(row=r, column=c)
                    pic_ctr += 1
                    # print("## pictr: " + str(pic_ctr) + " " + fname)
                    c += 1
                c = 0
                r += 1

    def goto_position(self, x, y, f):

        x_coord = str(x)
        y_coord = str(y)
        f_val = str(f)
        gcode = 'G0 X' + x_coord + ' Y' + y_coord + ' F' + f_val + '\n'
        # write out gcode to xytabel serial connection
        # ser.write(bytes(gcode, 'utf-8'))
        self.s.ser.write(bytes(gcode, 'utf-8'))
        print(gcode)

    def capture_image(self, picname):
        # take te picture
        file = self.s.cam.capture_and_get()
        file.save(os.path.join(self.s.safe_temp_path, picname))

        # trick to empty the camera cue before nextaction (see github thread from entangle devloper .....).
        # Prevents camera crashes.
        self.s.cam.empty_cam_cue()

    def toggle_tab_state(self, tabstate="normal"):
        tabs = self.frame.master.master.tabs()
        self.frame.master.master.tab(tabs[0], state=tabstate)
        # do not toggle well plate tab 1
        self.frame.master.master.tab(tabs[2], state=tabstate)
        self.frame.master.master.tab(tabs[3], state=tabstate)
        self.frame.master.master.tab(tabs[4], state=tabstate)


class Stickytrap:

    def __init__(self, parent, settings):
        #cv2.ocl.setUseOpenCL(False)  # disable opencl to prevent errors
        # reference the settings object
        self.s = settings
        # create the folderstructure if it does not yet exist
        self.s.create_safe_path()
        self.pbval = 0
        self.maxcap = 5  # 4 pict without overlap, 5 up to ~30 mm overlap
        self.overlap = 20  # (value in mm overlap of pictures)

        self.pbmax = self.maxcap

        self.stthumb_list = self.create_empty_st_list()
        self.stpic_list = []
        self.qr = ""

        self.frame = ttk.Frame(parent, padding="10 10 10 10")
        self.frame.grid(column=0, row=0, sticky=(N, W, E, S))
        #ttk.Label(self.frame, text="blaat").grid(row=0, column=0)

        self.pb = ttk.Progressbar(self.frame, orient=HORIZONTAL, length=400, mode='determinate', maximum=self.pbmax)
        self.pb['value'] = 0
        self.pb.grid(row=2, column=0, sticky=W)

        self.strstp_button = Button(self.frame, text='Start imaging', command=self.start)
        self.strstp_button.grid(row=3, column=0, sticky=W, pady=5)

        self.update_st_grid()
        self.ctr = 0

    def start(self):
        if not self.s.cam_connected or not self.s.xy_connected:
            messagebox.showerror("connection error", "XY-table and/or camera not connected\n"
                                                     "Cannot continue.")
        else:

            self.pbval = 0
            self.pb['value'] = self.pbval
            self.strstp_button.configure(text='Stop', command=self.stop)
            self.stpic_list.clear()
            self.stthumb_list.clear()

            global interrupt
            interrupt = False

            # create the folders
            self.s.create_project_sample_path()
            self.ctr = 0
            # invoke the capturenext function via root.after to allow the eventloop to update the interface
            self.toggle_tab_state("disabled")
            root.after(1, self.capture_next)


    def stop(self):

        self.strstp_button.configure(text='Start imaging', command=self.start)
        self.update_st_grid()
        global interrupt
        interrupt = True
        self.pb['value'] = 0
        self.home_xy()
        self.toggle_tab_state("normal")

    def capture_next(self, nextcap=0):

        global interrupt
        if interrupt:
            # home the table
            self.home_xy()
            self.toggle_tab_state("normal")
            return

        if nextcap < self.maxcap:
            self.pbval += 1
            self.pb['value'] = self.pbval
            x = self.s.xy_st_coords[nextcap][0]
            y = self.s.xy_st_coords[nextcap][1]
            if self.overlap > 0:
                y -= self.overlap * nextcap

            # root.after(1000)
            print("nextcap: " + str(nextcap) + " xy" + str(x) + " " + str(y))
            tempfn = "temp_st_pos_" + str(nextcap).zfill(2) + ".jpg"
            self.move_and_capture(x, y, self.s.xy_f_speed, tempfn)
            self.crop_save_temp_st(self.ctr, tempfn)
            self.ctr += 1

        else:
            self.save_images()
            self.pb['value'] = self.pbmax
            print("nextcap: " + str(nextcap))
            self.strstp_button.configure(text='Start imaging', command=self.start)
            # home the xy table
            self.home_xy()
            self.update_st_grid()
            #self.stitch_st()
            interrupt = True
            self.toggle_tab_state("normal")
            return

        root.after(1, lambda: self.capture_next(nextcap + 1))

    def home_xy(self):
        self.s.ser.write(bytes("G28\n", 'utf-8'))

    def move_and_capture(self, x, y, f, tempfn):
        self.goto_position(x, y, f)
        time.sleep(self.s.cam.calc_movement_delay(x, y, f))
        self.capture_image(tempfn)
        # self.crop_save_wells_old(1, 12)
        # take the pic

    def crop_save_temp_st(self, capnr, tempfn):

        pos_str = "st_pos_" + str(capnr).zfill(2) + ".jpg"
        temp_image = cv2.imread(os.path.join(self.s.safe_temp_path, tempfn))
        temp_image = cv2.rotate(temp_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        qr = self.detect_qr(temp_image)
        if qr != "":
            self.qr = qr
            print("qr-code detected: " + self.qr)

        #crop = temp_image[2300:5200, 800:3700]
        crop = temp_image
        save_fn = pos_str + ".jpg"
            # add project en sample name to the filename if checked

        #cv2.imwrite(os.path.join(self.s.project_sample_path, save_fn), crop)
        self.stpic_list.append(os.path.join(self.s.safe_temp_path, tempfn))
        st_thumb = cv2.resize(crop, [300, 200], cv2.INTER_NEAREST)
        st_thumb = cv2.rotate(st_thumb, cv2.ROTATE_90_COUNTERCLOCKWISE)
        cv2.imwrite(os.path.join(self.s.safe_temp_path, "thumb_" + save_fn), st_thumb)
        self.stthumb_list.append(os.path.join(self.s.safe_temp_path, "thumb_" + save_fn))

    def save_images(self):

        save_fn = ""
        if self.s.prj_fn_add:
            save_fn = self.s.project_name + "_" + self.s.sample_name + "_"
        if self.qr != "":
            save_fn = save_fn + self.qr + "_"

        for i in range(self.maxcap):
            pos_str = "st_pos_" + str(i).zfill(2)
            temp_fn = "temp_" + pos_str + ".jpg"
            save2_fn = save_fn + pos_str + ".jpg"
            os.rename(os.path.join(self.s.safe_temp_path, temp_fn),
                      os.path.join(self.s.project_sample_path, save2_fn))

    def detect_qr(self, img):

        detect = cv2.QRCodeDetector()
        val, pts, st_code = detect.detectAndDecode(img)
        print(val)
        return val

    def stitch_st(self):

        stitcher = cv2.Stitcher.create(cv2.STITCHER_SCANS)
        images = []

        for each in self.stpic_list:
            image = cv2.imread(each)
            images.append(image)
        (status, stitched) = stitcher.stitch(image)

        # if the status is '0', then OpenCV successfully performed image
        # stitching
        if status == 0:
            # write the output stitched image to disk
            #cv2.imwrite("stitch.jpg", stitched)
            # display the output stitched image to our screen
            stitched = cv2.resize(stitched, [375, 1000], cv2.INTER_NEAREST)
            cv2.imshow("Stitched", stitched)
            cv2.waitKey()
        # otherwise the stitching failed, likely due to not enough keypoints)
        # being detected
        else:
            print("[INFO] image stitching failed ({})".format(status))


    def create_empty_st_list(self):
        stthumb_list = list()
        stthumb_list.append("assets/st/empty_1_h250px.png")
        stthumb_list.append("assets/st/empty_2_h250px.png")
        stthumb_list.append("assets/st/empty_3_h250px.png")
        stthumb_list.append("assets/st/empty_4_h250px.png")

        return stthumb_list

    def update_st_grid(self):
        pic_ctr = 0
        st_layout = ttk.Frame(self.frame, padding="10 10 10 10")
        st_layout.grid(column=0, row=0, sticky=(N, W, E, S))
        root.update_idletasks()

        c = 0
        for pic in self.stthumb_list:
            # label plates
            #plate_string = "postion: " + str(i + 1)
            #ttk.Label(wp_layout, text=plate_string).grid(row=r, column=c, pady=10)
            # r += 1
            # row header with column titles
                        # header
            ttk.Label(st_layout, text=str(c)).grid(row=0, column=c)
            fname = self.stthumb_list[c]
            pimg = ImageTk.PhotoImage(Image.open(fname))
            label = ttk.Label(st_layout, image=pimg)
            label.image = pimg
            label.grid(row=1, column=c)
            c += 1

    def goto_position(self, x, y, f):

        x_coord = str(x)
        y_coord = str(y)
        f_val = str(f)
        gcode = 'G0 X' + x_coord + ' Y' + y_coord + ' F' + f_val + '\n'
        # write out gcode to xytabel serial connection
        # ser.write(bytes(gcode, 'utf-8'))
        self.s.ser.write(bytes(gcode, 'utf-8'))
        print(gcode)

    def capture_image(self, picname):
        # take te picture
        file = self.s.cam.capture_and_get()
        file.save(os.path.join(self.s.safe_temp_path, picname))

        # trick to empty the camera cue before nextaction (see github thread from entangle devloper .....).
        # Prevents camera crashes.
        self.s.cam.empty_cam_cue()

    def set_overlap(self, overlap):
        self.overlap = overlap


    def toggle_tab_state(self, tabstate="normal"):
        tabs = self.frame.master.master.tabs()
        self.frame.master.master.tab(tabs[0], state=tabstate)
        self.frame.master.master.tab(tabs[1], state=tabstate)
        # do not toggle well plate tab 2
        self.frame.master.master.tab(tabs[3], state=tabstate)
        self.frame.master.master.tab(tabs[4], state=tabstate)

class Move:

    def __init__(self, parent, settings):

        self.s = settings

        moveframe = ttk.Frame(parent, padding="3 3 3 3")
        moveframe.grid(column=0, row=0, sticky=(N, W, E, S))

        # Grid row 0
        self.num_x = StringVar()
        self.num_y = StringVar()
        self.scale_x_lbl = ttk.Label(moveframe)
        self.scale_y_lbl = ttk.Label(moveframe)
        self.scale_y_lbl.grid(column=0, row=0, sticky=W)
        self.scale_x_lbl.grid(column=1, row=0, sticky=W)

        # Grid row 1
        self.x = ttk.Scale(
            moveframe, orient=HORIZONTAL, length=self.s.xy_x_max,
            from_=0.0, to=self.s.xy_x_max, variable=self.num_x,
            command=self.update_scale_x_lbl)
        self.y = ttk.Scale(
            moveframe, orient=VERTICAL, length=self.s.xy_y_max,
            from_=0.0, to=self.s.xy_y_max, variable=self.num_y,
            command=self.update_scale_y_lbl, )
        self.y.grid(column=0, row=1)
        self.x.grid(column=1, row=1, sticky=NW)
        self.y.set(0)
        self.x.set(0)

        self.console = Text(moveframe, bg='black', fg='white', width=40)
        self.console.grid(row=1, column=3, rowspan=10)
        self.console.insert(0.0, '>>> G Code >')
        self.console_line = 1.0

        # Grid row 5
        # home button
        self.home_button = Button(moveframe, text='home', command=self.home_axis)
        self.home_button.grid(row=5, column=0, sticky=W)

        self.go_button = Button(moveframe, text='GO', command=self.goto_position)
        self.go_button.grid(row=5, column=2, sticky=E)

        # Grid row 7
        for child in moveframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def update_scale_y_lbl(self, val):
        val = float(val)
        val = round(val, 1)
        val = str(val)
        self.scale_y_lbl['text'] = "y-axis: " + val + " mm"

    def update_scale_x_lbl(self, val):
        val = float(val)
        val = round(val, 1)
        val = str(val)
        self.scale_x_lbl['text'] = "x-axis at: " + val + " mm"

    def home_axis(self):
        if not self.s.xy_connected:
            messagebox.showerror("connection error", "XY-table not connected\n"
                                                     "Cannot continue.")
        else:
            self.print_gcode('G28\n')
            self.x.set(value=0.0)
            self.y.set(value=0.0)

    def goto_position(self):

        if not self.s.xy_connected:
            messagebox.showerror("connection error", "XY-table not connected\n"
                                                     "Cannot continue.")
        else:
            x_coord = str(round(float(self.num_x.get()), 1))
            y_coord = str(round(float(self.num_y.get()), 1))
            self.print_gcode('G1 X' + x_coord + ' Y' + y_coord + ' F' + str(self.s.xy_f_speed) + '\n')

    def print_gcode(self, gcode):
        self.console.insert(self.console_line, gcode)
        self.console.yview_pickplace("end")
        # ser.write(bytes(gcode, 'utf-8'))
        self.s.ser.write(bytes(gcode, 'utf-8'))
        print(gcode)
        print(bytes(gcode, 'utf-8'))
        self.console_line += 1


class Help:

    def __init__(self, parent):
        frame = ttk.Frame(parent, padding="20 20 20 20")
        frame.grid(column=0, row=0, sticky=(N, W, E, S))

        ttk.Label(frame, text="Taskforce Kleine Biodiversiteit\n\n"
                              "Lectorate Bees and Biodiversity\n"
                              "Van Hall Larenstein University of applied sciences\n\n"
                              "For now you are on your own ;-)\n"
                              "If you really need help try the readme").grid(row=0, column=0, sticky=NW)
        link1 = ttk.Label(frame, text="https://github.com/Taskforce-Biodiversity/InsectImager#readme ")
        link1.grid(row=1, column=0, sticky=NW)
        link1.bind("<Button-1>", lambda e: self.open_url("https://github.com/Taskforce-Biodiversity/InsectImager#readme"))
        link2 = ttk.Label(frame, text="https://github.com/Taskforce-Biodiversity/InsectImager/issues")
        link2.grid(row=2, column=0, sticky=(W, E))
        link2.bind("<Button-1>", lambda e: self.open_url("https://github.com/Taskforce-Biodiversity/InsectImager/issues "))

        fname = "assets/tf_kbd_gst.jpg"
        pimg = ImageTk.PhotoImage(Image.open(fname))
        imglabel = ttk.Label(frame, image=pimg)
        imglabel.image = pimg
        imglabel.grid(row=0, column=1, rowspan=3)

    def open_url(self, url):
        webbrowser.open_new_tab(url)


if __name__ == '__main__':
    try:
        root = Tk()
        Main(root)
        interrupt = False

    finally:
        print("bye")
