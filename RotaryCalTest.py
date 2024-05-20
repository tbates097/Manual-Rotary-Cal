# -*- coding: utf-8 -*-
"""
Created on Mon Apr 15 11:21:16 2024

@author: tbates
"""

import automation1 as a1
import sys
import tkinter as tk
from tkinter import messagebox, font, filedialog
import time
import math
import datetime
from RS232 import collimator
from AerotechDataCal import data_and_cal
from AerotechPDF import aerotech_PDF


class rotary_cal():
    '''
    Program to execute an accuracy and calibration test for a rotary stage that cannot be mounted in the Rotary Calibrator. 
    This program will automate motion of the test and master axis and collect autocollimator data.
    It will then post-process and make plots with a calibration file.
    
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

    def __init__(self,axis,num_readings,dwell,step_size,travel,units,dia,test_type,sys_serial,st_serial,comments,temp,start_pos,drive,stage_type,oper,**kwargs):
        '''
        Defines parameters to run rotary calibration test.

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
        self.axis = axis
        self.num_readings = num_readings
        self.dwell = dwell
        self.step_size = step_size
        self.travel = travel
        self.units = units
        self.dia = dia
        self.test_type = test_type
        self.sys_serial = sys_serial
        self.st_serial = st_serial
        self.comments = comments
        self.temp = temp
        self.start_pos = start_pos
        self.drive = drive
        self.stage_type = stage_type
        self.oper = oper
        
        self.is_cal = kwargs.get('is_cal', None)
        self.col_axis = kwargs.get('col_axis', None)
        
        #Window for error messageboxes
        self.root=tk.Tk()
        self.root.withdraw()
        
    def a1_test(self,controller : a1.Controller):
        self.controller = controller
        self.Xdir = []
        self.Ydir = []
        self.raw_for_pos = []
        self.raw_rev_pos = []
        self.raw_forward = []
        self.raw_reverse = []
        
        self.data = 0
        
        global col_reading
        col_reading = collimator(self.num_readings,self.dwell)
        
        #Set up status item configuration to get "enabled" and "homed" status.
        status_item_configuration = a1.StatusItemConfiguration()
        status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.DriveStatus, self.axis)
        status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, self.axis)
        results = self.controller.runtime.status.get_status_items(status_item_configuration)
        
        #Variables for motion
        self.dir_step = 0.0555555
        self.speed = self.controller.runtime.parameters.axes[self.axis].motion.maxjogspeed.value
        
        #Calculate travels if in linear units
        if self.units == 'mm':
            self.radius = self.dia / 2
            self.step_size = (self.step_size / 360) * ((2 * math.pi) * (self.radius))
            self.travel = (self.travel / 360) * ((2 * math.pi) * (self.radius))
            self.dir_step = (self.dir_step / 360) * ((2 * math.pi) * (self.radius))
            self.start_pos = (self.start_pos / 360) * ((2 * math.pi) * (self.radius))
        if self.units == 'in':
            self.radius = self.dia / 2
            self.step_size = ((self.step_size / 360) * ((2 * math.pi) * (self.radius))) / 25.4
            self.travel = ((self.travel / 360) * ((2 * math.pi) * (self.radius))) / 25.4
            self.dir_step = ((self.dir_step / 360) * ((2 * math.pi) * (self.radius))) / 25.4
            self.start_pos = ((self.start_pos / 360) * ((2 * math.pi) * (self.radius))) / 25.4
        
        #Check to see if axis is enabled.
        drive_status = int(results.axis.get(a1.AxisStatusItem.DriveStatus, self.axis).value)
        is_enabled = (drive_status & a1.DriveStatus.Enabled) == a1.DriveStatus.Enabled
        if is_enabled == False:
            #Enable if not enabled.
            self.controller.runtime.commands.motion.enable((self.axis))
        
        #Check to see if axis is homed.
        axis_status = int(results.axis.get(a1.AxisStatusItem.AxisStatus, self.axis).value)
        is_homed = (axis_status & a1.AxisStatus.Homed) == a1.AxisStatus.Homed
        if is_homed == False:
            #Home if not homed.
            self.controller.runtime.commands.motion.home((self.axis))
        
        #Move to start position
        pos_fbk = round(results.axis.get(a1.AxisStatusItem.PositionFeedback, self.axis).value,6)
        
        #Move to zero to zero collimator
        self.controller.runtime.commands.motion.moveabsolute([self.axis], [0],[self.speed])
        time.sleep(abs(pos_fbk / self.speed))
        
        #Ask user to align the ultradex to the Autocollimator while the stage is at home.
        align = self.open_message_box()
        if align == "OK":
            time.sleep(2)
            self.dir_sense()
        if align == "Cancel":
            tk.messagebox.showerror('Abort','Test Stopped')
            

    def dir_sense(self):
        #Check direction sense
        self.controller.runtime.commands.motion.moveincremental([self.axis], [self.dir_step], [self.speed])
        
        Xavg,Yavg = col_reading.collimator_reading()
        self.Xdir.append(Xavg)
        self.Ydir.append(Yavg)
        time.sleep(3)

        self.controller.runtime.commands.motion.moveabsolute([self.axis], [self.start_pos], [self.speed])
        time.sleep(1)
        
        if self.Xdir > self.Ydir:
            self.col_axis = 'X'
        else:
            self.col_axis = 'Y'
        
        self.test_loop()
        
    def a1_test_loop(self):
        if pos_fbk != self.start_pos:
            self.controller.runtime.commands.motion.moveabsolute([self.axis], [self.start_pos], [self.speed])
            time.sleep((abs(pos_fbk - self.start_pos)/self.speed) + 3)
            
        #Establish a step count for while loop.
        self.num_points = (self.travel / self.step_size)
        if self.test_type == "Bidirectional":
            self.num_points = (self.num_points * 2)
        self.test_points = 0
        
        #Establish a counter for the move execution
        self.test_distance = 0
        
        if self.test_type == 'Unidirectional':
        #Execute a loop to iterate through the forward run.
            
            while self.test_points <= (self.num_points):

                response = self.open_data_box()
                
                if response == "OK":
                    #Calls to function that reads collimator data and appends to the end of a new list
                    Xavg,Yavg = col_reading.collimator_reading()
                    
                    #Set up status item configuration to get "enabled" and "homed" status.
                    status_item_configuration = a1.StatusItemConfiguration()
                    status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
                    results = self.controller.runtime.status.get_status_items(status_item_configuration)
                    #Gets the position feedback of the stage and adds it to a list
                    self.pos_fbk = round(results.axis.get(a1.AxisStatusItem.PositionFeedback, self.axis).value,6)

                    #Appends the collimator average readings to a list for plotting data
                    if abs(self.Xdir[0]) > abs(self.Ydir[0]):
                        self.raw_forward.append(Xavg)
                    else:
                        self.raw_forward.append(Yavg)
                    self.raw_for_pos.append(self.pos_fbk)
                        
                    if self.test_points < (self.num_points):
                        self.controller.runtime.commands.motion.moveincremental([self.axis],[self.step_size],[self.speed])
                        time.sleep((self.step_size / self.speed) + 3)

                if response == "Cancel":
                    tk.messagebox.showerror('Abort', 'Test Stopped')
                    break

                #Increment counter for while loop
                self.test_points += 1 
                    
        if self.test_type == 'Bidirectional':
        #Execute a loop to iterate through the forward run.
            while self.test_points <= (self.num_points / 2):
  
                response = self.open_data_box()
                   
                if response == "OK":
                    #Calls to function that reads collimator data and appends to the end of a new list
                    Xavg,Yavg = col_reading.collimator_reading()
                       
                    #Set up status item configuration to get "enabled" and "homed" status.
                    status_item_configuration = a1.StatusItemConfiguration()
                    status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
                    results = self.controller.runtime.status.get_status_items(status_item_configuration)
                    #Gets the position feedback of the stage and adds it to a list
                    self.pos_fbk = round(results.axis.get(a1.AxisStatusItem.PositionFeedback, self.axis).value,6)
                       
                    #Appends the collimator average readings to a list    
                    if abs(self.Xdir[0]) > abs(self.Ydir[0]):
                        self.raw_forward.append(Xavg)
                    else:
                        self.raw_forward.append(Yavg)
                    self.raw_for_pos.append(self.pos_fbk)      
                       
                    if self.test_points < (self.num_points / 2):
                        self.controller.runtime.commands.motion.moveincremental([self.axis],[self.step_size],[self.speed])
                        time.sleep((self.step_size / self.speed) + 3)
                
                if response == "Cancel":
                    tk.messagebox.showerror('Abort', 'Test Stopped')
                    self.test_points = 0
                    self.pos_fbk = 0
                    break
                
                #Increment counter for while loop
                self.test_points += 1 
                
            #execute over travel
            if self.units != 'deg':
                end_point = round(self.travel,4) + round(self.start_pos,4)
                pos_fbk = round(self.pos_fbk,4)
            else:
                end_point = round(self.travel,0) + round(self.start_pos,0)
                pos_fbk = round(self.pos_fbk,0)
            if pos_fbk == end_point:

                self.controller.runtime.commands.motion.moveincremental([self.axis],[self.dir_step],[self.speed])
                time.sleep(0.5)
                self.controller.runtime.commands.motion.moveincremental([self.axis],[self.dir_step * -1],[self.speed])
                time.sleep(3)
                    
                response = self.open_data_box()
                        
                if response == "OK":
                    #Calls to function that reads collimator data and appends to the end of a new list
                    Xavg,Yavg = col_reading.collimator_reading()
                        
                    #Set up status item configuration to get "enabled" and "homed" status.
                    status_item_configuration = a1.StatusItemConfiguration()
                    status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
                    results = self.controller.runtime.status.get_status_items(status_item_configuration)
                    #Gets the position feedback of the stage and adds it to a list
                    self.pos_fbk = round(results.axis.get(a1.AxisStatusItem.PositionFeedback, self.axis).value,6)
                        
                    if abs(self.Xdir[0]) > abs(self.Ydir[0]):
                        self.raw_reverse.append(Xavg)
                    else:
                        self.raw_reverse.append(Yavg)
                    self.raw_rev_pos.append(self.pos_fbk)
                    
                    self.controller.runtime.commands.motion.moveincremental([self.axis],[(self.step_size) * -1],[self.speed])
                    time.sleep((self.step_size / self.speed) + 3)
                
                if response == "Cancel":
                    tk.messagebox.showerror('Abort', 'Test Stopped')
                    self.test_points = 0
                    self.pos_fbk = 0
                    pass
                
            #Increment counter for while loop
            #self.test_points += 1
                
            while self.num_points / 2 < self.test_points <= self.num_points:

                response = self.open_data_box()
                    
                if response == "OK":
                    #Calls to function that reads collimator data and appends to the end of a new list
                    Xavg,Yavg = col_reading.collimator_reading()
                        
                    #Set up status item configuration to get "enabled" and "homed" status.
                    status_item_configuration = a1.StatusItemConfiguration()
                    status_item_configuration.axis.add(a1.AxisStatusItem.PositionFeedback, self.axis)
                    results = self.controller.runtime.status.get_status_items(status_item_configuration)
                    #Gets the position feedback of the stage and adds it to a list
                    self.pos_fbk = round(results.axis.get(a1.AxisStatusItem.PositionFeedback, self.axis).value,6)
                        
                    if abs(self.Xdir[0]) > abs(self.Ydir[0]):
                        self.raw_reverse.append(Xavg)
                    else:
                        self.raw_reverse.append(Yavg)
                    self.raw_rev_pos.append(self.pos_fbk)
                    
                    if self.num_points / 2 < self.test_points < self.num_points:
                        self.controller.runtime.commands.motion.moveincremental([self.axis],[(self.step_size) * -1],[self.speed])
                        time.sleep((self.step_size / self.speed) + 3)
                        
                    self.test_distance += self.step_size     
                        
                #Increment counter for while loop
                self.test_points += 1
                    
            if self.test_type == 'Bidirectional':        
                if self.units != 'deg':
                    end_point = round(self.travel,4) + round(self.start_pos,4)
                    pos_fbk = round(self.pos_fbk,4)
                else:
                    end_point = round(self.travel,0) + round(self.start_pos,0)
                    pos_fbk = round(self.pos_fbk,0)
            else:
                if self.units != 'deg':
                    end_point = round(self.start_pos,4)
                    pos_fbk = round(self.pos_fbk,4)
                else:
                    end_point = round(self.start_pos,0)
                    pos_fbk = round(self.pos_fbk,0)
                    
            if pos_fbk == end_point:
                self.setup_data()
            else:
                pass
            
    def a1_setup_data(self):
        #convert string list to float and set proper direction sense
        self.raw_forward = [float(i) for i in self.raw_forward]
        self.raw_reverse = [float(i) for i in self.raw_reverse]
        
        if abs(self.Xdir[0]) > abs(self.Ydir[0]):
            if self.Xdir[0] < 0:
                self.raw_forward = [-x for x in self.raw_forward]
                self.raw_reverse = [-x for x in self.raw_reverse]

        if abs(self.Xdir[0]) < abs(self.Ydir[0]):
            if self.Ydir[0] < 0:        
                self.raw_forward = [-y for y in self.raw_forward]
                self.raw_reverse = [-y for y in self.raw_reverse]

        if self.units != "deg":
            self.convert()
        else:
            self.for_pos_fbk = []
            for i in self.raw_for_pos:
                self.for_pos_fbk.append(i)
            self.rev_pos_fbk = []
            for i in self.raw_rev_pos:
                self.rev_pos_fbk.append(i)
            self.forward = []
            for i in self.raw_forward:
                self.forward.append(i)
            self.reverse = []
            for i in self.raw_reverse:
                self.reverse.append(i)   
            self.post_process()

    def test(self):
        self.raw_for_pos = []
        self.raw_rev_pos = []
        self.raw_forward = []
        self.raw_reverse = []
        
        self.data = 0
        
        #Calculate travels if in linear units
        if self.units == 'mm':
            self.radius = self.dia / 2
            self.travel = (self.travel / 360) * ((2 * math.pi) * (self.radius))
            self.step_size = (self.step_size / 360) * ((2 * math.pi) * (self.radius))
            self.start_pos = (self.start_pos / 360) * ((2 * math.pi) * (self.radius))
        if self.units == 'in':
            self.radius = self.dia / 2
            self.travel = (self.travel / 360) * ((2 * math.pi) * (self.radius)) / 25.4
            self.step_size = ((self.step_size / 360) * ((2 * math.pi) * (self.radius))) / 25.4
            self.start_pos = ((self.start_pos / 360) * ((2 * math.pi) * (self.radius))) / 25.4
        
        global col_reading
        col_reading = collimator(self.num_readings,self.dwell)
        
        #self.col_axis = self.open_manual_box()

        #Ask user to align the ultradex to the Autocollimator while the stage is at home.
        align = self.open_message_box()
        if align == "OK":
            time.sleep(2)
            self.test_loop()
        else:
            messagebox.showinfo('Abort','Test Stopped')
        
    def test_loop(self):
        #Establish a step count for while loop.
        self.num_points = (self.travel / self.step_size)
        if self.test_type == "Bidirectional":
            self.num_points = (self.num_points * 2)
        self.test_points = 0

        #Establish a counter for the move execution
        self.test_distance = 0    
        
        if self.test_type == 'Unidirectional':
        #Execute a loop to iterate through the forward run.
            
            while self.test_points <= (self.num_points):

                response = self.manual_data_box()
                
                if response == "OK":
                    #Calls to function that reads collimator data and appends to the end of a new list
                    Xavg,Yavg = col_reading.collimator_reading()
                    
                    #Appends the collimator average readings to a list
                    if self.col_axis == 'X':
                        self.raw_forward.append(Xavg)
                    else:
                        self.raw_forward.append(Yavg)
                    
                    self.pos_fbk = self.test_distance + self.step_size
                    self.raw_for_pos.append((self.pos_fbk - self.step_size))
                
                if response == "Cancel":
                    tk.messagebox.showerror('Abort', 'Test Stopped')
                    break
                
                #Increment counter for while loop
                self.test_points += 1 
                self.test_distance += self.step_size
                    
        if self.test_type == 'Bidirectional':
        #Execute a loop to iterate through the forward run.
            while self.test_points <= (self.num_points / 2):

                response = self.manual_data_box()
                   
                if response == "OK":
                    #Calls to function that reads collimator data and appends to the end of a new list
                    Xavg,Yavg = col_reading.collimator_reading()
                       
                    #Appends the collimator average readings to a list
                    if self.col_axis == 'X':
                        self.raw_forward.append(Xavg)
                    else:
                        self.raw_forward.append(Yavg)
                    
                    self.pos_fbk = self.test_distance + self.step_size
                    self.raw_for_pos.append((self.pos_fbk - self.step_size))
                
                if response == "Cancel":
                    tk.messagebox.showerror('Abort', 'Test Stopped')
                    self.pos_fbk = 0
                    break    
                
                #Increment counter for while loop
                if self.test_points <= (self.num_points / 2):
                    self.test_points += 1 
                if self.test_points <= (self.num_points / 2):
                    self.test_distance += self.step_size
                    
            #execute over travel
            if self.pos_fbk == self.travel + self.step_size:

                messagebox.showerror('Over Travel','Execute an over-travel move and press OK')
                
                response = self.manual_data_box()
                        
                if response == "OK":
                    #Calls to function that reads collimator data and appends to the end of a new list
                    Xavg,Yavg = col_reading.collimator_reading()
                        
                    if self.col_axis == 'X':
                        self.raw_reverse.append(Xavg)
                    else:
                        self.raw_reverse.append(Yavg)
                    self.pos_fbk = self.pos_fbk - self.step_size
                    self.raw_rev_pos.append(self.pos_fbk)
                
                if response == "Cancel":
                    tk.messagebox.showerror('Abort', 'Test Stopped')
                    self.test_points = 0
                    pass
                
            self.test_distance -= self.step_size
                
            while self.num_points / 2 < self.test_points <= self.num_points:

                response = self.manual_data_box()
                    
                if response == "OK":
                    #Calls to function that reads collimator data and appends to the end of a new list
                    Xavg,Yavg = col_reading.collimator_reading()
                        
                    if self.col_axis == 'X':
                        self.raw_reverse.append(Xavg)
                    else:
                        self.raw_reverse.append(Yavg)
                    
                    self.pos_fbk = self.pos_fbk - self.step_size
                    self.raw_rev_pos.append(self.pos_fbk)
                
                if response == "Cancel":
                    tk.messagebox.showerror('Abort', 'Test Stopped')
                    self.pos_fbk = 0
                    break        
                
                #Increment counter for while loop
                self.test_points += 1
                if self.num_points / 2 < self.test_points <= self.num_points:
                    self.test_distance -= self.step_size
                    
        if self.test_points == self.num_points + 1:
            self.setup_data()
        else:
            pass
        
    def setup_data(self):        
        #convert string list to float and set proper direction sense
        self.raw_forward = [float(i) for i in self.raw_forward]
        self.raw_reverse = [float(i) for i in self.raw_reverse]

        if self.units != "deg":
            self.convert()
        else:
            self.for_pos_fbk = []
            for i in self.raw_for_pos:
                self.for_pos_fbk.append(i)
            self.rev_pos_fbk = []
            for i in self.raw_rev_pos:
                self.rev_pos_fbk.append(i)
            self.forward = []
            for i in self.raw_forward:
                self.forward.append(i)
            self.reverse = []
            for i in self.raw_reverse:
                self.reverse.append(i)
            self.post_process()
        
    def import_data(self):
        self.for_pos_fbk = []
        self.rev_pos_fbk = []
        self.forward = []
        self.reverse = []
        #Ask user to navigate to the data file
        self.file_path = filedialog.askopenfilename(title="Select Data File")
        if self.file_path:
            self.data = 1
            with open(self.file_path, 'r') as file:
                lines = file.readlines()
                for num, line in enumerate(lines):
                    if "Calibrated" in line:
                        self.is_cal = line.split(":")[1].strip()
                        print(self.is_cal)
                    if line.startswith(':START'):
                        line = file.readline()
                        lines = lines[num+1:]
                        break
                data_list = []
                for line in lines:
                    values = line.strip().split()
                    
                    if len(values) >= 2:
                        data_list.append((values[0],values[1]))
                        
                if self.test_type == 'Bidirectional':
                    for i, data in enumerate(data_list):
                        if i < len(data_list) / 2:
                            self.for_pos_fbk.append(data[0])
                            self.forward.append(data[1])
                        else:
                            self.rev_pos_fbk.append(data[0])
                            self.reverse.append(data[1])
                            
                    self.for_pos_fbk = [float(i) for i in self.for_pos_fbk]
                    self.rev_pos_fbk = [float(i) for i in self.rev_pos_fbk]
                    self.forward = [float(i) for i in self.forward]
                    self.reverse = [float(i) for i in self.reverse]
                else:
                    for data in data_list:
                        self.for_pos_fbk.append(data[0])
                        self.forward.append(data[1])
                        
                    self.for_pos_fbk = [float(i) for i in self.for_pos_fbk]
                    self.forward = [float(i) for i in self.forward]
                    
            self.post_process()
        
        else:
            messagebox.showerror("Abort", "No file selected.")
          
    def convert(self):
        self.for_pos_fbk = []
        self.rev_pos_fbk = []
        self.forward = []
        self.reverse = []
        
        if self.units == "mm":
            # Convert diameter to radius
            radius = self.dia / 2
            
            # Convert arcseconds to radians
            arcsec_to_rad = math.pi / 180 / 3600
            
            for i in self.raw_forward:
                # Convert angular measurements (arcseconds) to radians
                angle_i_rad = float(i) * arcsec_to_rad
                    
                # Calculate arc lengths using radius and converted angles
                arc_length_i = radius * angle_i_rad
                    
                # Append arc lengths to result lists
                self.forward.append(arc_length_i)
            
            for i in self.raw_for_pos:
                self.for_pos_fbk.append(i)
            
            if self.test_type == "Bidirectional":
                for i in self.raw_reverse:
                    # Convert angular measurements (arcseconds) to radians
                    angle_i_rad = float(i) * arcsec_to_rad
                        
                    # Calculate arc lengths using radius and converted angles
                    arc_length_i = radius * angle_i_rad
                        
                    # Append arc lengths to result lists
                    self.reverse.append(arc_length_i)
                 
                for i in self.raw_rev_pos:
                    self.rev_pos_fbk.append(i)
            
        if self.units == "in":
            # Convert diameter to radius
            radius = self.dia / 2
            
            # Convert arcseconds to radians
            arcsec_to_rad = math.pi / 180 / 3600
            
            for i in self.raw_forward:
                # Convert angular measurements (arcseconds) to radians
                angle_i_rad = float(i) * arcsec_to_rad
                
                # Calculate arc lengths using radius and converted angles
                arc_length_i = (radius * angle_i_rad) / 25.4
                
                # Append arc lengths to result lists
                self.forward.append(arc_length_i)
                
            for i in self.raw_for_pos:
                self.for_pos_fbk.append(i)
                
            if self.test_type == "Bidirectional":
                for i in self.raw_reverse:
                    # Convert angular measurements (arcseconds) to radians
                    angle_i_rad = float(i) * arcsec_to_rad
                    
                    # Calculate arc lengths using radius and converted angles
                    arc_length_i = (radius * angle_i_rad) / 25.4
                    
                    # Append arc lengths to result lists
                    self.reverse.append(arc_length_i)
                    
                for i in self.raw_rev_pos:
                    self.rev_pos_fbk.append(i)
   
        self.post_process()
    
    def post_process(self):
        global data,cal
        
        self.current_date = datetime.date.today()
        self.current_time = datetime.datetime.now().time()
        
        #Create and empty list for repeat data
        rep = []
        rep = []
        
        #Flip reverse data lists to match forward
        self.reverse = self.reverse[::-1]
        self.rev_pos_fbk = self.rev_pos_fbk[::-1]
        
        #Calculate min max of forward and reverse runs
        if self.test_type == "Bidirectional":
            self.max = float(max(*self.forward,*self.reverse))
            self.min = float(min(*self.forward,*self.reverse))
            
            #Calculate repeatability
            for i, e in zip(self.forward,self.reverse):
                diff = abs(i) - abs(e)
                rep.append(diff)
    
            #Get repeatability
            self.rep = abs(max(rep))

        else:
            #Get pk to pk accuracy result
            self.max = float(max(self.forward))
            self.min = float(min(self.forward))
            
        #Get accuracy
        self.pk_pk = (abs(self.max)) + (abs(self.min))
        print('First',self.is_cal)
        if self.drive == 'Automation1' and self.data == 0:
            #Set up status item configuration to get "Calibrated" status.
            status_item_configuration = a1.StatusItemConfiguration()
            status_item_configuration.axis.add(a1.AxisStatusItem.DriveStatus, self.axis)
            status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, self.axis)
            results = self.controller.runtime.status.get_status_items(status_item_configuration)
            
            self.rollovercounts = self.controller.runtime.parameters.axes[self.axis].motion.rollovercounts.value
            axis_status = int(results.axis.get(a1.AxisStatusItem.AxisStatus, self.axis).value)
            self.is_cal = (axis_status & a1.AxisStatus.CalibrationEnabled1D) == a1.AxisStatus.CalibrationEnabled1D
            
            if self.is_cal:
                self.is_cal = 1
            else:
                self.is_cal = 0
                
            data_file = data_and_cal(
                self.test_type,
                self.sys_serial,
                self.st_serial,
                self.current_date,
                self.current_time,
                self.axis,
                self.stage_type,
                self.drive,
                self.step_size,
                self.for_pos_fbk,
                self.rev_pos_fbk,
                self.forward,
                self.reverse,
                self.temp,
                self.units,
                self.oper,
                col_axis = self.col_axis,
                speed = self.speed
                )
            
            data_file.a1_data_file(self.controller)
        elif self.drive != 'Automation1' and self.data == 0:
            print('second',self.is_cal)
            #Call to data file creation
            data_file = data_and_cal(
                self.test_type,
                self.sys_serial,
                self.st_serial,
                self.current_date,
                self.current_time,
                self.axis,
                self.stage_type,
                self.drive,
                self.step_size,
                self.for_pos_fbk,
                self.rev_pos_fbk,
                self.forward,
                self.reverse,
                self.temp,
                self.units,
                self.oper,
                col_axis = self.col_axis,
                is_cal = self.is_cal
                )
            
            data_file.data_file()
            
        if self.test_type == 'Bidirectional': 
            gen_pdf = aerotech_PDF(
                self.test_type,
                self.sys_serial,
                self.st_serial,
                self.current_date,
                self.current_time,
                self.axis,
                self.stage_type,
                self.drive,
                self.step_size,
                self.for_pos_fbk,
                self.rev_pos_fbk,
                self.forward,
                self.reverse,
                self.temp,
                self.units,
                self.dia,
                self.pk_pk,
                self.is_cal,
                self.comments,
                self.travel,
                self.start_pos,
                self.oper,
                rep = self.rep,
                data = self.data
                )
        else:

            gen_pdf = aerotech_PDF(
                self.test_type,
                self.sys_serial,
                self.st_serial,
                self.current_date,
                self.current_time,
                self.axis,
                self.stage_type,
                self.drive,
                self.step_size,
                self.for_pos_fbk,
                self.rev_pos_fbk,
                self.forward,
                self.reverse,
                self.temp,
                self.units,
                self.dia,
                self.pk_pk,
                self.is_cal,
                self.comments,
                self.travel,
                self.start_pos,
                self.oper,
                data = self.data
                )
          
        if self.data == 0:
            gen_pdf.rotary_pdf()
    
        #PDF for importing data only        
        if self.data == 1:
            gen_pdf.rotary_pdf()

            data_file = data_and_cal(
                self.test_type,
                self.sys_serial,
                self.st_serial,
                self.current_date,
                self.current_time,
                self.axis,
                self.stage_type,
                self.drive,
                self.step_size,
                self.for_pos_fbk,
                self.rev_pos_fbk,
                self.forward,
                self.reverse,
                self.temp,
                self.units,
                self.oper,
                data = self.data,
                file_path = self.file_path
                )
        print('third',self.is_cal)
        if self.is_cal == 1:
            messagebox.showinfo('Test Complete','Test Is Complete')

        else:    
            self.cal = self.open_cal_box()
            
            if self.cal == 'OK':
                #Call to cal file creation
                data_file.make_cal_file()
            else:
                messagebox.showinfo('Test Complete','Test Is Complete')


    def open_data_box(self):
        take_data = tk.Toplevel(self.root)
        take_data.title('Take Data')
        take_data.configure(bg='white')
        
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        
        label = tk.Label(take_data, text="Index Ultradex and click OK To Take Data",bg='white',font=custom_font)
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
            
        def on_ok():
            take_data.result = "OK"  # Set custom result attribute
            take_data.destroy()  # Destroy the window
        
        # Define a function to handle "Cancel" button click
        def on_cancel():
            take_data.result = "Cancel"  # Set custom result attribute
            take_data.destroy()  # Destroy the window
            self.root.focus_set()  # Set focus back to the root window
            return "Cancel"  # Return the result immediately

        
        button_ok = tk.Button(take_data, text="OK",width=10,height=2, command=on_ok)
        button_ok.grid(row=1,column=0,padx=10,pady=10)
        
        button_cancel = tk.Button(take_data, text="Cancel",width=10,height=2,command=on_cancel)
        button_cancel.grid(row=1,column=1,padx=10,pady=10)
        
        padding = 40
        width = label.winfo_reqwidth()
        height = label.winfo_reqheight() + button_ok.winfo_reqheight()
        
        take_data_width = width + padding
        take_data_height = height + padding
        x_offset = 100
        y_offset = 200
        take_data.geometry(f"{take_data_width}x{take_data_height}+{x_offset}+{y_offset}")
        take_data.configure(bg='white')
        
        take_data.focus_set()  # Set focus to the new window
        
        take_data.result = None
        
        take_data.wait_window()  # Wait for the window to be destroyed
        
        return take_data.result
    
    def manual_data_box(self):
        manual_data = tk.Toplevel(self.root)
        manual_data.title('Take Manual Data')
        
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        
        label = tk.Label(manual_data, text="Index Stage To " + str(self.test_distance) + " Then Click OK To Take Data",bg='white',font=custom_font)
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
        
        def on_ok():
            manual_data.result = "OK"  # Set custom result attribute
            manual_data.destroy()  # Destroy the window
        
        # Define a function to handle "Cancel" button click
        def on_cancel():
            manual_data.result = "Cancel"  # Set custom result attribute
            manual_data.destroy()  # Destroy the window
            self.root.focus_set()  # Set focus back to the root window
            return "Cancel"  # Return the result immediately
        
        button_ok = tk.Button(manual_data, text="OK",width=10,height=2, command=on_ok)
        button_ok.grid(row=1,column=0,padx=10,pady=10)
        
        button_cancel = tk.Button(manual_data, text="Cancel",width=10,height=2,command=on_cancel)
        button_cancel.grid(row=1,column=1,padx=10,pady=10)
        
        padding = 40
        width = label.winfo_reqwidth()
        height = label.winfo_reqheight() + button_ok.winfo_reqheight()
        
        manual_data_width = width + padding
        manual_data_height = height + padding
        x_offset = 100
        y_offset = 200
        manual_data.geometry(f"{manual_data_width}x{manual_data_height}+{x_offset}+{y_offset}")
        manual_data.configure(bg='white')
        
        manual_data.focus_set()  # Set focus to the new window
        
        manual_data.result = None
        
        manual_data.wait_window()  # Wait for the window to be destroyed
        
        return manual_data.result
        
    def open_message_box(self):
        align = tk.Toplevel(self.root)
        align.title('Setup')
        align.configure(bg='white')
        
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        if self.drive == 'Automation1':
            label = tk.Label(align, text="Align Ultradex and manually zero Autocollimator",bg='white',font=custom_font)
            label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
        else:
            label = tk.Label(align, text="Home Axis. Align Ultradex and manually zero Autocollimator",bg='white',font=custom_font)
            label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
        def on_ok():
            align.result = "OK"  # Set custom result attribute
            align.destroy()  # Destroy the window
        
        # Define a function to handle "Cancel" button click
        def on_cancel():
            align.result = "Cancel"  # Set custom result attribute
            align.destroy()  # Destroy the window
            align.destroy()  # Destroy the window
            self.root.focus_set()  # Set focus back to the root window
            return "Cancel"  # Return the result immediately
        
        button_ok = tk.Button(align, text="OK",width=10,height=2, command=on_ok)
        button_ok.grid(row=1,column=0,padx=10,pady=10)
        
        button_cancel = tk.Button(align, text="Cancel",width=10,height=2,command=on_cancel)
        button_cancel.grid(row=1,column=1,padx=10,pady=10)
        
        padding = 40
        width = label.winfo_reqwidth()
        height = label.winfo_reqheight() + button_ok.winfo_reqheight()
        
        align_width = width + padding
        align_height = height + padding
        x_offset = 100
        y_offset = 200
        align.geometry(f"{align_width}x{align_height}+{x_offset}+{y_offset}")
        align.configure(bg='white')
        
        align.focus_set()  # Set focus to the new window
        
        align.result = None
        
        align.wait_window()  # Wait for the window to be destroyed
        
        return align.result    
    
    def open_manual_box(self):
        axis = tk.Toplevel(self.root)
        axis.title('Select Collimator Axis')
        
        col_axis = ["X","Y"]
        cal_status = ["Yes", "No"]
        
        col_axis_menu = tk.StringVar(axis)
        col_axis_menu.set(col_axis[0])
        
        cal_status_menu = tk.StringVar(axis)
        cal_status_menu.set(cal_status[0])
        
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        
        label1 = tk.Label(axis, text="Autocollimator Axis:",bg='white',font=custom_font)
        label1.grid(row=0,column=0,columnspan=2,padx=10,pady=5)
        dropdown = tk.OptionMenu(axis, col_axis_menu, *col_axis)
        dropdown.grid(row=1,column=0,columnspan=2,padx=10,pady=5)
        dropdown.configure(bg='white',width=5,height=1)
        
        def on_ok():
            axis.result = col_axis_menu.get()
            axis.destroy()  # Destroy the window
        
        button_ok = tk.Button(axis, text="OK",width=10,height=2, command=on_ok)
        button_ok.grid(row=4,column=0,columnspan=2,padx=10,pady=10)
        
        height_padding = 60
        width_padding = 20
        width = label1.winfo_reqwidth()
        height = sum(widget.winfo_reqheight() for widget in axis.winfo_children())
        #label1.winfo_reqheight() + dropdown.winfo_reqheight() + label2.winfo_reqheight() + dropdown1.winfo_reqheight() + button_ok.winfo_reqheight()
        axis_width = width + width_padding
        axis_height = height + height_padding
        x_offset = 100
        y_offset = 200
        axis.geometry(f"{axis_width}x{axis_height}+{x_offset}+{y_offset}")
        axis.configure(bg='white')
        
        axis.focus_set()  # Set focus to the new window
        
        axis.result = None
        
        axis.wait_window()  # Wait for the window to be destroyed
        
        return axis.result
    
    def open_pdf_box(self):
        pdf = tk.Toplevel(self.root)
        pdf.title('Generate PDF')
        
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        
        label = tk.Label(pdf, text="Would you like to make a PDF?",bg='white',font=custom_font)
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=10) 
        
        def on_ok():
            pdf.result = 'OK'
            pdf.destroy()  # Destroy the window
        
        # Define a function to handle "Cancel" button click
        def on_cancel():
            pdf.result = "Cancel"  # Set custom result attribute
            messagebox.showerror("Abort", "Test Stopped.")
            pdf.destroy()  # Destroy the window
            pdf.destroy()  # Destroy the window
            self.root.focus_set()  # Set focus back to the root window
            return "Cancel"  # Return the result immediately
        
        button_ok = tk.Button(pdf, text="Yes",width=10,height=2, command=on_ok)
        button_ok.grid(row=2,column=0,padx=10,pady=10)
        
        button_cancel = tk.Button(pdf, text="Cancel",width=10,height=2,command=on_cancel)
        button_cancel.grid(row=2,column=1,padx=10,pady=10)
        
        padding = 40
        width = label.winfo_reqwidth()
        height = label.winfo_reqheight() + button_ok.winfo_reqheight()
        
        pdf_width = width + padding
        pdf_height = height + padding
        x_offset = 100
        y_offset = 200
        pdf.geometry(f"{pdf_width}x{pdf_height}+{x_offset}+{y_offset}")
        pdf.configure(bg='white')
        
        pdf.focus_set()  # Set focus to the new window
        
        pdf.result = None
        
        pdf.wait_window()  # Wait for the window to be destroyed
        
        return pdf.result
    
    def open_cal_box(self):
        cal = tk.Toplevel(self.root)
        cal.title('Generate Cal File')
        
        custom_font = font.Font(family="Times New Roman", size=12, weight="bold", slant="italic")
        
        label = tk.Label(cal, text="Are you generating a cal file?",bg='white',font=custom_font)
        label.grid(row=0, column=0, columnspan=2, padx=20, pady=10)
        
        def on_ok():
            cal.result = 'OK'
            cal.destroy()  # Destroy the window
        
        # Define a function to handle "Cancel" button click
        def on_cancel():
            cal.result = "Cancel"  # Set custom result attribute
            cal.destroy()  # Destroy the window
            cal.destroy()  # Destroy the window
            self.root.focus_set()  # Set focus back to the root window
            return "Cancel"  # Return the result immediately
            
        button_ok = tk.Button(cal, text="Yes",width=10,height=2, command=on_ok)
        button_ok.grid(row=2,column=0,padx=10,pady=10)
        
        button_cancel = tk.Button(cal, text="No",width=10,height=2,command=on_cancel)
        button_cancel.grid(row=2,column=1,padx=10,pady=10)
        
        padding = 40
        width = label.winfo_reqwidth()
        height = label.winfo_reqheight() + button_ok.winfo_reqheight()
        
        cal_width = width + padding
        cal_height = height + padding
        x_offset = 100
        y_offset = 200
        cal.geometry(f"{cal_width}x{cal_height}+{x_offset}+{y_offset}")
        cal.configure(bg='white')
            
        cal.focus_set()  # Set focus to the new window
        
        cal.result = None
        
        cal.wait_window()  # Wait for the window to be destroyed
        
        return cal.result
    
    def run(self):
        self.root.mainloop()
        