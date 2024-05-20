# -*- coding: utf-8 -*-
"""
Created on Tue May 14 12:31:52 2024

@author: tbates
"""

import os
import numpy as np
import tkinter as tk
import math
from AerotechFormat import AerotechFormat
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

class aerotech_PDF():
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
    
    def __init__(self,test_type,sys_serial,st_serial,current_date,current_time,axis,stage_type,drive,step_size,for_pos_fbk,rev_pos_fbk,forward,reverse,temp,units,dia,pk_pk,is_cal,comments,travel,start_pos,oper,**kwargs):
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
        self.dia = dia
        self.pk_pk = pk_pk
        self.is_cal = is_cal
        self.comments = comments
        self.travel = travel
        self.start_pos = start_pos
        self.oper = oper
        
        self.rep = kwargs.get('rep', None)
        self.data = kwargs.get('data', None)
        
        #Window for error messageboxes
        self.root=tk.Tk()
        self.root.withdraw()
        
    def rotary_pdf(self):
        self.start_path = ('O:/')
        self.sys_serial = str(self.sys_serial)
        self.folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(self.start_path) for dir_name in dirs if str(self.sys_serial[0:6]) in dir_name), None)

        # This cell of the script will be used to generate a pdf in the AerotechFooter Format
        global fig
        
        #Center data about zero for plotting
        mean_forward = np.mean(self.forward)
        mean_reverse = np.mean(self.reverse)
        
        forward = self.forward - mean_forward
        reverse = self.reverse - mean_reverse
    
        
        title_font = fm.FontProperties(family='Times New Roman', size=12, weight='bold')
        label_font = fm.FontProperties(family='Times New Roman', size=10, style='italic')
        #plt.rcParams.update({'font.size': 10})
        fig, ax1, ax2, ax3, ax4 = AerotechFormat.makeTemplate()
        
        ax1 = plt.subplot2grid((19, 3),(3,0), rowspan = 8, colspan = 3,)
        plt.title('Accuracy', fontproperties=title_font)
    
        #Accuracy plot
        if self.units == 'deg':
            plt.ylabel('Accuracy (arcsec)',fontproperties=label_font)
        else:
            plt.ylabel('Accuracy ({})'.format(self.units),fontproperties=label_font)
        plt.xlabel('Position ({})'.format(self.units),fontproperties=label_font)
        if self.test_type == "Bidirectional":
            ax1.plot(self.for_pos_fbk, forward, '-b', label='Forward', marker='o')
            ax1.plot(self.for_pos_fbk, reverse, '-r', label='Reverse', marker='x')
            plt.legend(loc='upper right')
        else:
            ax1.plot(self.for_pos_fbk, forward, '-b', label='Accuracy', marker='o')
            plt.legend(loc='upper right')
    
        #Results Text Box
        if self.units == "deg":
            if self.test_type != "Bidirectional":
                ax2.text(0.02,.8, 'Accuracy: {} arcsec'.format(round(self.pk_pk,3)), color = 'black', size = 8.5)
            else:
                ax2.text(0.02,.8, 'Accuracy: {} arcsec'.format(round(self.pk_pk,3)), color = 'black', size = 8.5)
                ax2.text(0.02,.725, 'Repeat: {} arcsec'.format(round(self.rep,3)), color = 'black', size = 8.5)    
        else:
            if self.test_type != "Bidirectional":
                if self.units == 'mm':
                    radius = self.dia / 2
                    arc_length_deg = self.pk_pk / (radius)
                    arc_length_rad = arc_length_deg * (180 / math.pi)
                    pk_arc_sec = arc_length_rad * 3600
                else:
                    radius = self.dia / 2
                    radius = radius / 25.4
                    arc_length_deg = self.pk_pk / (radius)
                    arc_length_rad = arc_length_deg * (180 / math.pi)
                    pk_arc_sec = arc_length_rad * 3600
                #ax2.text(0.02,.725, '          {} {}'.format(round(self.pk_pk,6),self.units), color = 'black', size = 8.5)
                ax2.text(0.02,.8, 'Accuracy: {} arcsec ({} {})'.format(round(pk_arc_sec,3),round(self.pk_pk,8),self.units), color = 'black', size = 8.5)
            else:
                if self.units == 'mm':
                    radius = self.dia / 2
                    arc_length_deg = self.pk_pk / (radius)
                    arc_length_rad = arc_length_deg * (180 / math.pi)
                    pk_arc_sec = arc_length_rad * 3600
                    rep_deg = self.rep / (radius)
                    rep_rad = rep_deg * (180 / math.pi)
                    rep_arc_sec = rep_rad * 3600
                else:
                    radius = self.dia / 2
                    radius = radius / 25.4
                    arc_length_deg = self.pk_pk / (radius)
                    arc_length_rad = arc_length_deg * (180 / math.pi)
                    pk_arc_sec = arc_length_rad * 3600
                    rep_deg = self.rep / (radius)
                    rep_rad = rep_deg * (180 / math.pi)
                    rep_arc_sec = rep_rad * 3600
                #ax2.text(0.02,.725, '          {} {}'.format(str(round(self.pk_pk,6)),self.units), color = 'black', size = 8.5)
                ax2.text(0.02,.8, 'Accuracy: {} arcsec ({} {})'.format(round(pk_arc_sec,3),round(self.pk_pk,8),self.units), color = 'black', size = 8.5)
                #ax2.text(0.02,.725, 'Repeatability: {} {}'.format(str(round(self.rep,6)),self.units), color = 'black', size = 8.5)
                ax2.text(0.02,.725, 'Repeat: {} arcsec ({} {})'.format(round(rep_arc_sec,3),round(self.rep,8),self.units), color = 'black', size = 8.5)
        #Comments Text Box
        ax3.text(0.02, .8, 'System Serial Number: {}'.format(str(self.sys_serial) + '-' + str(self.axis)), color = 'black', size = 9)
        ax3.text(0.02, .725, 'Stage Serial Number: {}'.format(self.st_serial), color = 'black', size = 9)
        ax3.text(0.02, .65, 'Stage: {}'.format(self.stage_type),color='black',size=9)
        ax3.text(0.02, .575, 'Date: {} {}'.format(self.current_date,self.current_time), color = 'black', size= 9)
        ax3.text(0.02, .500, 'Operator: {}'.format(self.oper), color = 'black', size= 9)
        ax3.text(0.02, .275, 'Comments: {}'.format(self.comments), color = 'black', size = 10, verticalalignment = 'top')

        if self.is_cal == 1:
            is_cal = 'Calibrated'
        else:
            is_cal = 'Uncalibrated'

        #Test Conditions Text Box
        degree_sign = u'\N{DEGREE SIGN}'
        ax4.text(.02, .8, 'Temperature: {} {}C'.format(self.temp, degree_sign), color = 'black', size = 9)
        ax4.text(.02, .725, 'Calibration Status: {}'.format(is_cal),color='black',size=9)
        ax4.text(.02, .65, 'Step Size: {} {}'.format(round(self.step_size,6),self.units), color = 'black', size = 9)
        ax4.text(.02, .575, 'Travel: {} {}'.format(round(self.travel,6), self.units), color = 'black', size = 9)
        ax4.text(.02, .500, 'Start Position: {} {}'.format(self.start_pos, self.units), color = 'black', size = 9)
        if self.units != 'deg':
            ax4.text(.02, 0.425, 'Working Diameter: {} mm'.format(self.dia), color = 'black', size = 9)
        
        if is_cal == 'Calibrated':
            output_file = str(self.sys_serial + '-' + self.axis + "_Verification.pdf")
        else:
            output_file = str(self.sys_serial + '-' + self.axis + "_Accuracy.pdf")
                
        pdf_file_path = self.folder_path + '/Customer Files/Plots'
        save_file = pdf_file_path + '/' + output_file
        fig.get_figure().savefig(save_file)
    