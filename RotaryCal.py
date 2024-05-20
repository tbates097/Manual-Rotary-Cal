# -*- coding: utf-8 -*-
"""
Created on Thu May 16 08:40:45 2024

@author: tbates
"""
import sys

sys.path.append(r'C:\Users\tbates\Python\ManualRotaryCal')
sys.path.append(r'C:\Program Files (x86)\Aerotech\Controller Version Selector\Bin\Automation1')

import os
import tkinter as tk
from tkinter import ttk
from RotaryCalTest import rotary_cal
import automation1 as a1


def rotarycaltest():
    axis = ax.get()
    num_readings = 5
    dwell = 1
    step_size = step.get()
    travel = trav.get()
    temp = tem.get()
    start_pos = start.get()
    dia = diam.get()
    sys_serial = sys.get()
    st_serial = st.get()
    comments = comm.get()
    stage_type = st_type.get()
    oper = opName.get()
    col_axis = col.get()

    global rot_cal, controller
    
    
    if drive == 'Automation1':
        try:
            controller = a1.Controller.connect()
            controller.start()
        except:
            controller = a1.Controller.connect_usb()
            controller.start()
            
        for axis_index in range(0,1):
    
            # Create status item configuration object
            status_item_configuration = a1.StatusItemConfiguration()
                
            # Add this axis status word to object
            status_item_configuration.axis.add(a1.AxisStatusItem.AxisStatus, axis_index)
    
            # Get axis status word from controller
            result = controller.runtime.status.get_status_items(status_item_configuration)
            axis_status = int(result.axis.get(a1.AxisStatusItem.AxisStatus, axis_index).value)
    
            # Check NotVirtual bit of axis status word
            if (axis_status & 1<<13) == 0:
                controller = a1.Controller.connect_usb()
   
        rot_cal = rotary_cal(
            axis,
            num_readings, 
            dwell, 
            step_size, 
            travel, 
            units, 
            dia, 
            test_type,
            sys_serial,
            st_serial,
            comments,
            temp,
            start_pos,
            drive,
            stage_type,
            oper
            )
        rot_cal.a1_test(controller)
        rot_cal.run()
    else:
        rot_cal = rotary_cal(
            axis,
            num_readings, 
            dwell, 
            step_size, 
            travel, 
            units, 
            dia, 
            test_type,
            sys_serial,
            st_serial,
            comments,
            temp,
            start_pos,
            drive,
            stage_type,
            oper,
            is_cal = is_cal,
            col_axis = col_axis
            )
        rot_cal.test()
        rot_cal.run()

def import_data():
    global rot_cal
    
    axis = ax.get()
    num_readings = 5
    dwell = 1
    step_size = step.get()
    travel = trav.get()
    temp = tem.get()
    start_pos = start.get()
    dia = diam.get()
    sys_serial = sys.get()
    st_serial = st.get()
    comments = comm.get()
    stage_type = st_type.get()
    oper = opName.get()
    
    rot_cal = rotary_cal(
        axis,
        num_readings, 
        dwell, 
        step_size, 
        travel, 
        units, 
        dia, 
        test_type,
        sys_serial,
        st_serial,
        comments,
        temp,
        start_pos,
        drive,
        stage_type,
        oper,
        )
    rot_cal.import_data()
    rot_cal.run()

def test_type_def():
    global test_type
    if direction.get() == "uni":
        test_type = 'Unidirectional'
    elif direction.get() == "bi":
        test_type = 'Bidirectional'
    else:
        test_type = 'None'

def unit_def():
    global units
    if unit.get() == 'deg':
        diam.set('None')
        units = 'deg'
        ent_stent["state"] = tk.DISABLED
    elif unit.get() == 'mm':
        units = 'mm'
        ent_stent["state"] = tk.NORMAL
    elif unit.get() == 'in':
        units = 'in'
        ent_stent["state"] = tk.NORMAL
    else:
        units = 'None'
        ent_stent["state"] = tk.DISABLED

def drive_def():
    global drive
    global is_cal
    if cont.get() == 'a1':
        cbx_cal["state"] = tk.DISABLED
        ent_col['state'] = tk.DISABLED
        cal.set(0)
        is_cal = 0
        drive = 'Automation1'
    elif cont.get() == 'other':
        cbx_cal["state"] = tk.NORMAL
        ent_col['state'] = tk.NORMAL
        drive = 'Other'
        if cal.get() == 1:
            is_cal = 1
        else:
            is_cal = 0
    else:
        drive = 'None'

def cal_def():
    global is_cal
    if cal.get() == 1:
        is_cal = 1
    else:
        is_cal = 0

def openPlot():
    
    axis = ax.get()
    sys_serial = sys.get()
    
    start_path = ('O:/')
    folder_path = next((os.path.join(root, dir_name) for root, dirs, _ in os.walk(start_path) for dir_name in dirs if str(sys_serial[0:6]) in dir_name), None)      
    pdf_file_path = folder_path + '/Customer Files/Plots'
    print(pdf_file_path)
    
    if os.path.exists(pdf_file_path):
        output_file = str(sys_serial + '-' + axis + "_Accuracy.pdf")
        pdf = pdf_file_path + '/' + output_file
        os.startfile(pdf)

        output_file = str(sys_serial + '-' + axis + "_Verification.pdf")
        pdf = pdf_file_path + '/' + output_file
        os.startfile(pdf)
    else:
        print(f"File '{pdf_file_path}' does not exist.")

window = tk.Tk()
window.title("Manual Rotary Calibration")

window.resizable(False, False)  # This code helps to disable windows from resizing

window_height = 700
window_width = 700

screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()

x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))

window.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))


# window.geometry('700x700')
# window.eval('tk::PlaceWindow . center')
window.columnconfigure([0,1,2,3], weight=1, minsize=700/4, uniform='column')
window.rowconfigure([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21], weight=1, minsize=1)
df_row = 0
h1_row = 1
test_row = 2
h2_row = 3
axName_row = 4
ll_row = 5
ul_row = 6
ts_row = 7
filt_row = 8
eq_row = 9
eqa_row = 10
h3_row = 11
sn_row = 12
stage_row = 13
op_row = 14
cv_row = 15
ol_row = 16
pm_row = 17
col_row = 18
h4_row = 19
run_row = 20
out_row = 21


window.rowconfigure(out_row,minsize=4)

ttk.Separator(master=window,orient='horizontal').grid(row=h1_row,column=0,columnspan=4,sticky='ew')
ttk.Separator(master=window,orient='horizontal').grid(row=h2_row,column=0,columnspan=4,sticky='ew')
ttk.Separator(master=window,orient='horizontal').grid(row=h3_row,column=0,columnspan=4,sticky='ew')
ttk.Separator(master=window,orient='horizontal').grid(row=h4_row,column=0,columnspan=4,sticky='ew')

#btn_dataFile = tk.Button(
    #master=window,
    #text="Browse for Data File",
    #width=25,
    #height = 1,
    #command=browse_dataFile
#)
#btn_dataFile.grid(row=df_row,column=0,padx=5,pady=5)

#lbl_dataFile = tk.Label(
    #master=window,
    #text='',
    #anchor='w',
#)

#lbl_dataFile.grid(row=df_row,column=1,padx=5,pady=5,columnspan=3)


lbl_test = tk.Label(
    master=window,
    text="Select Test Type:",
)

lbl_test.grid(row=test_row,column=0,padx=5,pady=5)

direction = tk.StringVar(value=0)

uni_dir = tk.Radiobutton(
    master=window,
    text="Unidirectional",
    variable=direction,
    value="uni",
    command=test_type_def
)
uni_dir.grid(row=test_row,column=1,padx=5,pady=5)

bi_dir = tk.Radiobutton(
    master=window,
    text="Bidirectional",
    variable=direction,
    value="bi",
    command=test_type_def
)
bi_dir.grid(row=test_row,column=2,padx=5,pady=5)

lbl_axis = tk.Label(
    master=window,
    text="Axis Name",
    width=25,
    height=1,
)
lbl_axis.grid(row=axName_row,column=0,padx=5,pady=5)

ax = tk.StringVar(value='X')
ent_axis = tk.Entry(
    master=window,
    textvariable=ax,
    width=25,
)
ent_axis.grid(row=axName_row,column=1,padx=5,pady=5)

#lbl_gAxis = tk.Label(
    #master=window,
    #text="Gantry Follower Axis Name\n(if applicable)",
    #width=25,
    #height=2,
#)

#lbl_gAxis.grid(row=axName_row,column=2,padx=5,pady=5)

#gAxName = tk.StringVar()
#ent_gAxis = tk.Entry(
    #master=window,
    #textvariable=gAxName,
    #width=25,
#)

#ent_gAxis.grid(row=axName_row,column=3,padx=5,pady=5)


lbl_st = tk.Label(
    master=window,
    text="Starting Position (deg)",
    width=25,
    height=1,
)
lbl_st.grid(row=ll_row,column=0,padx=5,pady=5)

start = tk.DoubleVar()
ent_start_pos = tk.Entry(
    master=window,
    textvariable=start,
    width=25,
)
ent_start_pos.grid(row=ll_row,column=1,padx=5,pady=5)

lbl_travel = tk.Label(
    master=window,
    text="Total Travel (deg)",
    width=25,
    height=1,
)
lbl_travel.grid(row=ul_row,column=0,padx=5,pady=5)

trav = tk.DoubleVar(value='360')
ent_travel = tk.Entry(
    master=window,
    textvariable=trav,
    width=25,
)
ent_travel.grid(row=ul_row,column=1,padx=5,pady=5)

lbl_step_size = tk.Label(
    master=window,
    text="Step Size (deg)",
    width=25,
    height=1,
)
lbl_step_size.grid(row=ts_row,column=0,padx=5,pady=5)

step = tk.DoubleVar(value='15')
ent_step_size = tk.Entry(
    master=window,
    textvariable=step,
    width=25,
)
ent_step_size.grid(row=ts_row,column=1,padx=5,pady=5)

# lbl_sr = tk.Label(
#     master=window,
#     text="Data Sampling Rate Used (Hz)",
#     width=25,
#     height=1,
# )

# lbl_sr.grid(row=5,column=0,padx=5,pady=5)

# sampleRate = tk.StringVar()
# ent_sr = tk.Entry(
#     master=window,
#     textvariable=sampleRate,
#     width=25,
# )

# ent_sr.grid(row=5,column=1,columnspan=3,padx=5,pady=5)

lbl_units = tk.Label(
    master=window,
    text = "Units:",
)
lbl_units.grid(row=filt_row, column=0,padx=5,pady=5)

unit = tk.StringVar(value='0')
cbx_deg = tk.Radiobutton(
    master=window,
    text="Degrees",
    variable=unit,
    value='deg',
    command=unit_def
)
cbx_deg.grid(row=filt_row,column=1,padx=5,pady=5)

cbx_mm = tk.Radiobutton(
    master=window,
    text="Millimeters",
    variable=unit,
    value='mm',
    command=unit_def
)
cbx_mm.grid(row=filt_row,column=2,padx=5,pady=5)

cbx_in = tk.Radiobutton(
    master=window,
    text="Inches",
    variable=unit,
    value='in',
    command=unit_def
)
cbx_in.grid(row=filt_row,column=3,padx=5,pady=5)

lbl_stent = tk.Label(
    master=window,
    text="Stent Diameter (mm)",
    width=25,
    height=1,
)
lbl_stent.grid(row=eq_row,column=0,padx=5,pady=5)

diam = tk.StringVar(value='None')
ent_stent = tk.Entry(
    master=window,
    textvariable=diam,
    width=25,
    state=tk.DISABLED
)   
ent_stent.grid(row=eq_row,column=1,padx=5,pady=5)

lbl_drive = tk.Label(
    master=window,
    text = "Controller:",
)
lbl_drive.grid(row=eqa_row, column=0,padx=5,pady=5)

cont = tk.StringVar(value='0')

cbx_a1 = tk.Radiobutton(
    master=window,
    text="Automation1",
    variable=cont,
    value='a1',
    command=drive_def
)
cbx_a1.grid(row=eqa_row,column=1,padx=5,pady=5)

cbx_other = tk.Radiobutton(
    master=window,
    text="Other",
    variable=cont,
    value='other',
    command=drive_def
)
cbx_other.grid(row=eqa_row,column=2,padx=5,pady=5)

cal = tk.IntVar(value=0)
cbx_cal = tk.Checkbutton(
    master=window,
    text="Calibrated",
    variable=cal,
    onvalue=1,
    offvalue=0,
    state=tk.DISABLED,
    command=cal_def
)
cbx_cal.grid(row=eqa_row,column=3,padx=5,pady=5)

lbl_serial = tk.Label(
    master=window,
    text="Serial Number",
    width=25,
    height=1,
)
lbl_serial.grid(row=sn_row,column=0,padx=5,pady=5)

sys = tk.StringVar(value='"System Serial Number"')
ent_serial = tk.Entry(
    master=window,
    textvariable=sys,
    width=25,
)
ent_serial.grid(row=sn_row,column=1,columnspan=3,padx=5,pady=5)

lbl_st_serial = tk.Label(
    master=window,
    text="Stage Serial Number",
    width=25,
    height=1,
)
lbl_st_serial.grid(row=stage_row,column=0,padx=5,pady=5)

st= tk.StringVar(value='"Stage Serial Number"')
ent_st_serial = tk.Entry(
    master=window,
    textvariable=st,
    width=25,
)
ent_st_serial.grid(row=stage_row,column=1,columnspan=3,padx=5,pady=5)

lbl_op = tk.Label(
    master=window,
    text="Operator",
    width=25,
    height=1,
)
lbl_op.grid(row=op_row,column=0,padx=5,pady=5)

opName= tk.StringVar(value='"Your Initials"')
ent_op = tk.Entry(
    master=window,
    textvariable=opName,
    width=25,
)
ent_op.grid(row=op_row,column=1,columnspan=3,padx=5,pady=5)


lbl_stage = tk.Label(
    master=window,
    text="Stage Part Number",
    width=25,
    height=1,
)
lbl_stage.grid(row=cv_row,column=0,padx=5,pady=5)

st_type = tk.StringVar(value='"Enter Stage Name"')
ent_stage = tk.Entry(
    master=window,
    textvariable=st_type,
    width=25,
)
ent_stage.grid(row=cv_row,column=1,columnspan=3,padx=5,pady=5)

lbl_temp = tk.Label(
    master=window,
    text="Temp",
    width=25,
    height=1,
)
lbl_temp.grid(row=ol_row,column=0,padx=5,pady=5)

tem = tk.DoubleVar(value='20')
ent_temp = tk.Entry(
    master=window,
    textvariable=tem,
    width=25,
)
ent_temp.grid(row=ol_row,column=1,columnspan=3,padx=5,pady=5)

lbl_comments = tk.Label(
    master=window,
    text="Comments",
    width=25,
    height=1,
)
lbl_comments.grid(row=pm_row,column=0,padx=5,pady=5)

comm= tk.StringVar()
ent_comments = tk.Entry(
    master=window,
    textvariable=comm,
    width=25,
)
ent_comments.grid(row=pm_row,column=1,columnspan=3,padx=5,pady=5)

lbl_col = tk.Label(
    master=window,
    text="Collimator Axis",
    width=25,
    height=1,
)
lbl_col.grid(row=col_row,column=0,padx=5,pady=5)

col= tk.StringVar(value='"X or Y for collimator data"')
ent_col = tk.Entry(
    master=window,
    textvariable=col,
    state=tk.DISABLED,
    width=25,
)
ent_col.grid(row=col_row,column=1,columnspan=3,padx=5,pady=5)

btn_import = tk.Button(
    master=window,
    text="Import Data",
    width=30,
    height = 1,
    command=import_data
)
btn_import.grid(row=run_row,column=1,padx=5,pady=5)

lbl_import = tk.Label(
    master=window,
    text='',
    anchor='w',
)

lbl_import.grid(row=run_row,column=1,padx=5,pady=5,columnspan=3)

btn_run = tk.Button(
    master=window,
    text="Run",
    width=25,
    height = 1,
    command=rotarycaltest
)

btn_run.grid(row=run_row,column=0,padx=5,pady=5)

btn_open = tk.Button(
    master=window,
    text="Open Plot",
    width=25,
    height = 1,
    command=openPlot
)

btn_open.grid(row=run_row,column=2,padx=5,pady=5)

txt_outStr = tk.Text(master=window,
                    state=tk.DISABLED,
                     height=10,fg='white',bg='black'
    )

# outStr_scroll = tk.Scrollbar(master=window)
# txt_outStr.configure(yscrollcommand=outStr_scroll.set)
# txt_outStr.pack(side=tk.LEFT)
# outStr_scroll.config(command=txt_outStr.yview)
# outStr_scroll.pack(side=tk.RIGHT,fill=tk.Y)


txt_outStr.grid(row=out_row,column=0,padx=0,pady=5,columnspan=4)


window.mainloop()