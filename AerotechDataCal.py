# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 09:12:26 2024

@author: tbates
"""
import tkinter as tk
from tkinter import messagebox, font
import automation1 as a1
import os
import sys

class data_and_cal():
    '''
    This script will import values from A1 to use to populate Aerotech Standard Cal and data files
    
    Parameters
    ----------
    num_readings : int
        The number of readings to take that will then be averaged for a final reading.
    dwell : int
        The amount of time for the stage to settle before taking data.
    step_size : int
        Distance to travel for each reading.
    travel : int
        Total travel of the stage being tested.
    '''
    
    def __init__(self,test_type,sys_serial,st_serial,current_date,current_time,axis,stage_type,drive,step_size,for_pos_fbk,rev_pos_fbk,forward,reverse,temp,units,oper,**kwargs):
        '''
        Defines parameters to run data_and_cal class.

        Parameters
        ----------
        num_readings : int
            The number of readings to take that will then be averaged for a final reading.
        dwell : int
            The amount of time for the stage to settle before taking data.
        step_size : int
            Distance to travel for each reading.
        travel : int
            Total travel of the stage being tested.

        Returns
        -------
        None.

        '''
        self.test_type = test_type
        self.sys_serial = sys_serial
        self.st_serial = st_serial
        self.current_date = current_date
        self.current_time = current_time
        self.axis = axis
        self.stage_type = stage_type
        self.drive = drive
        self.step_size = step_size
        self.for_pos_fbk = for_pos_fbk
        self.rev_pos_fbk = rev_pos_fbk
        self.forward = forward
        self.reverse = reverse
        self.temp = temp
        self.units = units
        self.oper = oper
        
        self.col_axis = kwargs.get('col_axis', None)
        self.speed = kwargs.get('speed', None)
        self.is_cal = kwargs.get('is_cal', None)
        self.data = kwargs.get('data', None)
        self.file_path = kwargs.get('file_path', None)
        
        #Window for error messageboxes
        self.root=tk.Tk()
        self.root.withdraw()
        
    def a1_data_file(self,controller : a1.Controller):

        self.sys_serial = str(self.sys_serial)
        self.start_path = ('O:/')
        self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)

        self.controller = controller
        #convert string list to float
        self.forward = [str(i) for i in self.forward]
        self.reverse = [str(i) for i in self.reverse]
        
        if self.drive == 'Automation1':
            #Set up status item configuration to get "enabled" and "homed" status.
            status_item_configuration = a1.StatusItemConfiguration()
            status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
            status_item_configuration.axis.add(a1.AxisStatusItem.DriveStatus, self.axis)
            status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, self.axis)
            results = self.controller.runtime.status.get_status_items(status_item_configuration)
            
            self.speed = self.controller.runtime.parameters.axes[self.axis].motion.maxjogspeed.value
            self.rollovercounts = self.controller.runtime.parameters.axes[self.axis].motion.rollovercounts.value
            axis_status = int(results.axis.get(a1.AxisStatusItem.AxisStatus, self.axis).value)
            self.is_cal = (axis_status & a1.AxisStatus.CalibrationEnabled1D) == a1.AxisStatus.CalibrationEnabled1D
            self.counts = self.controller.runtime.parameters.axes[self.axis].units.countsperunit.value
            homesetup_dec_val = int(self.controller.runtime.parameters.axes[self.axis].homing.homesetup.value)
            if homesetup_dec_val & 0x1:
                self.home_dir = 'CW'
            else:
                self.home_dir = 'CCW'
            self.home_offset = self.controller.runtime.parameters.axes[self.axis].homing.homeoffset.value
            self.axis_num = self.controller.runtime.parameters.axes[self.axis].axis_index
            
            if self.is_cal:
                self.data_cal = '1'
            else:
                self.data_cal = '0'
        
        if self.test_type == 'Bidirectional':
            data_test_type = '1'
        else:
            data_test_type = '0'
        
        #Filepath to data file
        if self.is_cal:
            self.data_file_path = self.folder_path + '/TestData/' + str(self.sys_serial) + '-' + str(self.axis) + '/Verification'
            os.makedirs(self.data_file_path,exist_ok=True)
            self.data_file_name = self.data_file_path + '/' + str(self.sys_serial) + '-' + str(self.axis) + '_Verification.dat'
        else:
            self.data_file_path = self.folder_path + '/TestData/' + str(self.sys_serial) + '-' + str(self.axis) + '/Accuracy'
            os.makedirs(self.data_file_path,exist_ok=True)
            self.data_file_name = self.data_file_path + '/' + str(self.sys_serial) + '-' + str(self.axis) + '_Accuracy.dat'
        
        with open(self.data_file_name, 'w') as f:
            f.write(
                'JobName : ' + str(self.sys_serial) + '\n'
                'DateTime : ' + str(self.current_date) + ' ' + str(self.current_time) + '\n'
                'OperatorName : ' + str(self.oper) + '\n'
                'LaserID : \n'
                'StageLabel : ' + str(self.stage_type) + '\n'
                'Calibrated : ' + str(self.data_cal) + '\n'
                'MasterStartPosition : \n'
                'ControllerVerison : ' + str(self.drive) + '\n'
                'Iterations : 1\n'
                'BiDirectional : ' + str(data_test_type) + '\n'
                'EncoderDirection : 1\n'
                'ConversionFactor : 1\n'
                'BacklashDistance : 0\n'
                'CountsPerUnit : ' + str(self.counts) + '\n'
                'TestType : Accuracy\n'
                'OpticLocation : DEFAULT\n'
                'Payload : OPTICS\n'
                'CalibrationFile : None\n'
                'HomePositionSet : 0\n'
                'TestOrientation : Horizontal\n'
                'MotionDirection : 1\n'
                'AmplifierType : CP Rev(B) @ 10 Amps\n'
                'MoveVelocity : ' + str(self.speed) + '\n'
                'MoveAcceleration : 3.33\n'
                'DriveFeedbackType : Encoder Multiplier\n'
                'DriveEncoderMultiplier : 570\n'
                'FirmwareVersion : 5.6.1.8\n'
                'StageSerialNumber : ' + str(self.st_serial) + '\n'
                '\n'
                'Calibration File Settings\n'
                'AxisIndex : ' + str(self.axis_num) + '\n'
                'StepSize : ' + str(self.step_size) + '\n'
                'HomeDirection : ' + str(self.home_dir) + '\n'
                'HomeOffset : ' + str(self.home_offset) + '\n'
                'LimitToLimitDistance : 0\n'
                'RolloverCounts : ' + str(self.rollovercounts) + '\n'
                'MotionDirection : 1\n'
                'EncoderFamily : I\n'
                '\n'
                'Ignored\n'
                '\n'
                'Position     ' + str(self.col_axis) + 'Data     Temperature\n'
                ':START\n'
                
                )
            combined_data = []
            combined_fbk = []
            data_list = []

            #Flip reverse data lists to match forward
            reverse = self.reverse[::-1]
            rev_pos_fbk = self.rev_pos_fbk[::-1]

            if self.test_type == 'Bidirectional':
                for i in self.forward:
                    combined_data.append(i)
                for i in reverse:
                    combined_data.append(i)
                for i in self.for_pos_fbk:
                    combined_fbk.append(i)
                for i in rev_pos_fbk:
                    combined_fbk.append(i)
                    
            else:
                for i in self.forward:
                    combined_data.append(i)
                for i in self.for_pos_fbk:
                    combined_fbk.append(i)

            if self.units == 'deg':
                combined_fbk = [round(float(i), 3) for i in combined_fbk]
                combined_data = [round(float(i), 3) for i in combined_data]
            else:
                combined_fbk = [round(float(i), 12) for i in combined_fbk]
                combined_data = [round(float(i), 12) for i in combined_data]
            
            combined_fbk = [str(i) for i in combined_fbk]
            combined_data = [str(i) for i in combined_data]

            for i,e in zip(combined_fbk,combined_data):
                data_list.append(i)
                data_list.append(e)

            data_count = 0
            line_data = []
            for data in data_list:
                line_data.append(str(data) + '     ')
                data_count += 1
                if data_count == 2:
                    f.write(' '.join(line_data) + str(self.temp) + '\n')
                    line_data = []
                    data_count = 0
                    
    def data_file(self):
        self.sys_serial = str(self.sys_serial)
        self.start_path = ('O:/')
        self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)
        #convert string list to float
        self.forward = [str(i) for i in self.forward]
        self.reverse = [str(i) for i in self.reverse]
        
        #Filepath to cal file
        if self.is_cal == 1:
            self.data_file_path = self.folder_path + '/TestData/' + str(self.sys_serial) + '-' + str(self.axis) + '/Verification'
            os.makedirs(self.data_file_path,exist_ok=True)
            self.data_file_name = self.data_file_path + '/' + str(self.sys_serial) + '-' + str(self.axis) + '_Verification.dat'
        else:
            self.data_file_path = self.folder_path + '/TestData/' + str(self.sys_serial) + '-' + str(self.axis) + '/Accuracy'
            os.makedirs(self.data_file_path,exist_ok=True)
            self.data_file_name = self.data_file_path + '/' + str(self.sys_serial) + '-' + str(self.axis) + '_Accuracy.dat'

        if self.is_cal == 0:
            self.data_file_box()
        if self.is_cal == 1:
            data_file_path = self.folder_path + '/TestData/' + str(self.sys_serial) + '-' + str(self.axis) + '/Accuracy'
            acc_data_file_name = data_file_path + '/' + str(self.sys_serial) + '-' + str(self.axis) + '_Accuracy.dat'
            with open(acc_data_file_name, 'r') as file:
                lines = file.readlines()
                for num, line in enumerate(lines):
                    if "CountsPerUnit" in line:
                        counts = line.split(":")
                        self.counts = float(counts[1].strip())
                    if "AxisIndex" in line:
                        self.axis_num = line.split(":")[1].strip()
                    if "HomeDirection" in line:
                        self.home_dir = line.split(":")[1].strip()
                    if "HomeOffset" in line:
                        self.home_offset = line.split(":")[1].strip()
                    if "RolloverCounts" in line:
                        self.rollovercounts = line.split(":")[1].strip()
            
        if self.test_type == 'Bidirectional':
            data_test_type = '1'
        else:
            data_test_type = '0'

        if self.is_cal == 1:
            self.data_cal = '1'
        else:
            self.data_cal = '0'
            
        with open(self.data_file_name, 'w') as f:
            f.write(
                'JobName : ' + str(self.sys_serial) + '\n'
                'DateTime : ' + str(self.current_date) + ' ' + str(self.current_time) + '\n'
                'OperatorName : ' + str(self.oper) + '\n'
                'LaserID : \n'
                'StageLabel : ' + str(self.stage_type) + '\n'
                'Calibrated : ' + str(self.data_cal) + '\n'
                'MasterStartPosition : \n'
                'ControllerVerison : ' + str(self.drive) + '\n'
                'Iterations : 1\n'
                'BiDirectional : ' + str(data_test_type) + '\n'
                'EncoderDirection : 1\n'
                'ConversionFactor : 1\n'
                'BacklashDistance : 0\n'
                'CountsPerUnit : ' + str(self.counts) + '\n'
                'TestType : Accuracy\n'
                'OpticLocation : DEFAULT\n'
                'Payload : OPTICS\n'
                'CalibrationFile : None\n'
                'HomePositionSet : 0\n'
                'TestOrientation : Horizontal\n'
                'MotionDirection : 1\n'
                'AmplifierType : CP Rev(B) @ 10 Amps\n'
                'MoveVelocity : ' + str(self.speed) + '\n'
                'MoveAcceleration : 3.33\n'
                'DriveFeedbackType : Encoder Multiplier\n'
                'DriveEncoderMultiplier : 570\n'
                'FirmwareVersion : 5.6.1.8\n'
                'StageSerialNumber : ' + str(self.st_serial) + '\n'
                '\n'
                'Calibration File Settings\n'
                'AxisIndex : ' + str(self.axis_num) + '\n'
                'StepSize : ' + str(self.step_size) + '\n'
                'HomeDirection : ' + str(self.home_dir) + '\n'
                'HomeOffset : ' + str(self.home_offset) + '\n'
                'LimitToLimitDistance : 0\n'
                'RolloverCounts : ' + str(self.rollovercounts) + '\n'
                'MotionDirection : 1\n'
                'EncoderFamily : I\n'
                '\n'
                'Ignored\n'
                '\n'
                'Position     ' + str(self.col_axis) + 'Data     Temperature\n'
                ':START\n'
                
                )
            combined_data = []
            combined_fbk = []
            data_list = []
            
            #Flip reverse data lists to match forward
            reverse = self.reverse[::-1]
            rev_pos_fbk = self.rev_pos_fbk[::-1]

            
            if self.test_type == 'Bidirectional':
                for i in self.forward:
                    combined_data.append(i)
                for i in reverse:
                    combined_data.append(i)
                for i in self.for_pos_fbk:
                    combined_fbk.append(i)
                for i in rev_pos_fbk:
                    combined_fbk.append(i)
                    
            else:
                for i in self.forward:
                    combined_data.append(i)
                for i in self.for_pos_fbk:
                    combined_fbk.append(i)
           
            if self.units == 'deg':
                combined_fbk = [round(float(i), 3) for i in combined_fbk]
                combined_data = [round(float(i), 3) for i in combined_data]
            else:
                combined_fbk = [round(float(i), 12) for i in combined_fbk]
                combined_data = [round(float(i), 12) for i in combined_data]
            for i,e in zip(combined_fbk,combined_data):
                data_list.append(i)
                data_list.append(e)

            combined_fbk = [str(i) for i in combined_fbk]
            combined_data = [str(i) for i in combined_data]

            data_count = 0
            line_data = []
            for data in data_list:
                line_data.append(str(data) + '     ')
                data_count += 1
                if data_count == 2:
                    f.write(' '.join(line_data) + str(self.temp) + '\n')
                    line_data = []
                    data_count = 0
                    
    def make_cal_file(self):
        self.sys_serial = str(self.sys_serial)
        self.start_path = ('O:/')
        self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)
        #Filepath to cal file
        self.cal_file_path = self.folder_path + '/Customer Files/CalFiles'
        self.file_name = self.cal_file_path + '/' + str(self.sys_serial) + '-' + str(self.axis) + '.cal'
        
        if self.data == 1:
            with open(self.file_path, 'r') as file:
                lines = file.readlines()
                for num, line in enumerate(lines):
                    if "CountsPerUnit" in line:
                        counts = line.split(":")
                        self.counts = float(counts[1].strip())
                    if "AxisIndex" in line:
                        self.axis_num = line.split(":")[1].strip()
                    if "HomeDirection" in line:
                        self.home_dir = line.split(":")[1].strip()
                    if "HomeOffset" in line:
                        self.home_offset = line.split(":")[1].strip()
        # Flip signs of elements in the lists
        try:
            cal_data = [-x for x in self.forward]  # Using list comprehension to multiply each element by -1
        except:
            #convert string list to float and set proper direction sense
            self.forward = [float(x) for x in self.forward]
            cal_data = [-x for x in self.forward]  # Using list comprehension to multiply each element by -1
            if self.units == 'deg':
                cal_data = [round(i,3) for i in cal_data]
            else:
                cal_data = [round(i,14) for i in cal_data]
            
        cal_data = [str(i) for i in cal_data]
        
        if self.units != 'deg':
            corunit = 'PRIMARY'
        else:
            corunit = 'PRIMARY/3600'
                
        if self.stage_type[0:3] == 'HEX':
            line_items = []
            with open(self.file_name, 'w') as f:#Writes the corrections to a text file titiled with the serial number and saves it in the folder selected. Format as follows
                f.write(
                    '[' + str(self.axis) + 'CAL' + ']\n'
                    '//Step Size in deg, correction in arc-sec\n'
                    'StepSize=' + str(self.step_size) + '\n'
                    'Correction = '
                    )   
                for data in cal_data:
                    line_items.append(str(data) + ' ')
                    f.write(' '.join(line_items))
            messagebox.showinfo('Verify Cal File', 'Copy contents of file into "...EngOnly/Hexapod/SO-1-1-kpMeasurements.txt"')
        #Automation 1 controller - using API to populate cal table       
        elif self.drive == 'Automation1':
            self.axis_num += 1
            line_items = []
            data_per_line = 6
            data_count = 0
            
            with open(self.file_name, 'w') as f:#Writes the corrections to a text file titiled with the serial number and saves it in the folder selected. Format as follows
                f.write(
                    '**************************************************************************\n'
                    ';***************          Aerotech Axis Calibration           **************\n'
                    ';Axis System Serial Number: ' + str(self.sys_serial) + '-' + str(self.axis) + '\n'
                    ';Axis Stage Serial Number: ' + str(self.st_serial) + '\n'
                    ';Date Tested: ' + str(self.current_date) + ' ' + str(self.current_time) + '\n'
                    ';Optic Location: Default\n'
                    ';Payload: None\n'
                    ';Average Air Temperature (°C): ' + str(self.temp) + '\n'
                    ';CountsPerUnit Parameter: ' + str(self.counts) + '\n'
                    ';***************************************************************************\n'
                    ':START ' + str(self.axis_num) + ' SAMPLEDIST= ' + str(self.step_size) + ' POSUNIT=PRIMARY CORUNIT='+ str(corunit) + '\n'
                    ':START HOMEDIRECTION= ' + str(self.home_dir) + ' HOMEOFFSET= ' + str(self.home_offset) + '\n'
                    )  
                for data in cal_data:
                    line_items.append(str(data) + '        ')
                    data_count += 1
                    if data_count == data_per_line:
                        f.write(' '.join(line_items) + '\n')
                        line_items = []
                        data_count = 0
                if data_count < data_per_line:
                    f.write(' '.join(line_items) + '\n')
                f.write(':END')
            
        elif self.drive != 'Automation1':
            #A3200, Ensemble, or Soloist
            line_items = []
            data_per_line = 6
            data_count = 0
            
            with open(self.file_name, 'w') as f:#Writes the corrections to a text file titiled with the serial number and saves it in the folder selected. Format as follows
                f.write(
                    '**************************************************************************\n'
                    ';***************          Aerotech Axis Calibration           **************\n'
                    ';Axis System Serial Number: ' + str(self.sys_serial) + '-' + str(self.axis) + '\n'
                    ';Axis Stage Serial Number: ' + str(self.st_serial) + '\n'
                    ';Date Tested: ' + str(self.current_date) + ' ' + str(self.current_time) + '\n'
                    ';Optic Location: Default\n'
                    ';Payload: None\n'
                    ';Average Air Temperature (°C): ' + str(self.temp) + '\n'
                    ';CountsPerUnit Parameter: ' + str(self.counts) + '\n'
                    ';***************************************************************************\n'
                    ':START ' + str(self.axis_num) + ' SAMPLEDIST=' + str(self.step_size) + ' POSUNIT=PRIMARY CORUNIT='+ str(corunit) + '\n'
                    ':START HOMEDIRECTION=' + str(self.home_dir) + ' HOMEOFFSET=' + str(self.home_offset) + '\n'
                    )   
                for data in cal_data:
                    line_items.append(str(data) + '        ')
                    data_count += 1
                    if data_count == data_per_line:
                        f.write(' '.join(line_items) + '\n')
                        line_items = []
                        data_count = 0
                if data_count < data_per_line:
                    f.write(' '.join(line_items) + '\n')
                f.write(':END')
        messagebox.showinfo('Verify Cal File', 'Load cal file and re-run program to verify.')    
        
    def data_file_box(self):
        df = tk.Toplevel(self.root)
        df.title('Generate Data File')
        
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        
        if self.drive != "Automation1":
            home_dir = ["CW","CCW"]
            
            home_dir_menu = tk.StringVar(df)
            home_dir_menu.set(home_dir[1])
            
            label = tk.Label(df, text="Input relevant data file information",bg='white',font=custom_font)
            label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)    
            
            label0 = tk.Label(df, text="Axis Number:",bg='white',font=custom_font)
            label0.grid(row=1,column=0,columnspan=2,padx=10,pady=5)
            entry0 = tk.Entry(df)
            entry0.insert(0, '1')
            entry0.grid(row=2,column=0,columnspan=2,padx=10,pady=5)
            
            label2 = tk.Label(df, text="Home Direction:",bg='white',font=custom_font)
            label2.grid(row=3,column=0,columnspan=2,padx=10,pady=5)
            dropdown = tk.OptionMenu(df, home_dir_menu, *home_dir)
            dropdown.grid(row=4,column=0,columnspan=2,padx=10,pady=5)
            
            label1 = tk.Label(df, text="Home Offset:",bg='white',font=custom_font)
            label1.grid(row=5,column=0,columnspan=2,padx=10,pady=5)
            entry1 = tk.Entry(df)
            entry1.insert(0, '0')
            entry1.grid(row=6,column=0,columnspan=2,padx=10,pady=5)
            
            label3 = tk.Label(df, text="Counts Per Unit:",bg='white',font=custom_font)
            label3.grid(row=7,column=0,columnspan=2,padx=10,pady=5)
            entry2 = tk.Entry(df)
            entry2.insert(0, '0')
            entry2.grid(row=8,column=0,columnspan=2,padx=10,pady=5)
            
            label4 = tk.Label(df, text="Rollover Counts:",bg='white',font=custom_font)
            label4.grid(row=9,column=0,columnspan=2,padx=10,pady=5)
            entry3 = tk.Entry(df)
            entry3.insert(0, '0')
            entry3.grid(row=10,column=0,columnspan=2,padx=10,pady=5)
            
            label5 = tk.Label(df, text="speed:",bg='white',font=custom_font)
            label5.grid(row=11,column=0,columnspan=2,padx=10,pady=5)
            entry4 = tk.Entry(df)
            entry4.insert(0, '0')
            entry4.grid(row=12,column=0,columnspan=2,padx=10,pady=5)
            
            def on_ok():
                self.home_dir = home_dir_menu.get()
                self.axis_num = entry0.get()
                self.home_offset = entry1.get()
                self.counts = entry2.get()
                self.rollovercounts = entry3.get()
                self.speed = entry4.get()
                df.result = 'OK'
                df.destroy()  # Destroy the window
            
            # Define a function to handle "Cancel" button click
            def on_cancel():
                df.result = "Cancel"  # Set custom result attribute
                df.destroy()  # Destroy the window
                
            button_ok = tk.Button(df, text="OK",width=10,height=2, command=on_ok)
            button_ok.grid(row=13,column=0,padx=10,pady=10)
            
            button_cancel = tk.Button(df, text="Cancel",width=10,height=2,command=on_cancel)
            button_cancel.grid(row=13,column=1,padx=10,pady=10)
            
            height_padding = 125
            width_padding = 40
            #width = max(label.winfo_reqwidth(),label0.winfo_reqwidth(),label0.winfo_reqwidth(),label0.winfo_reqwidth(),label0.winfo_reqwidth())
            #height = (label.winfo_reqheight() + label0.winfo_reqheight() + label1.winfo_reqheight() + label2.winfo_reqheight() + label3.winfo_reqheight() + button_ok.winfo_reqheight())
            
            width = max(widget.winfo_reqwidth() for widget in df.winfo_children())
            height = sum(widget.winfo_reqheight() for widget in df.winfo_children())
            df_width = width + width_padding
            df_height = height + height_padding
            x_offset = 100
            y_offset = 200
            df.geometry(f"{df_width}x{df_height}+{x_offset}+{y_offset}")
            df.configure(bg='white')
            
        df.focus_set()  # Set focus to the new window
        
        df.result = None
        
        df.wait_window()  # Wait for the window to be destroyed
        
        return df.result