#Final master by Karl Mueller, MAR 29 2021
#Release candidate 1.4 improves diagnostic capabilities of the device through data logging function.
# RC1.4 now outputs Mean Sway Distance [m] and Mean Sway Velocity [m] to the logged data.

### SWE RELEASE CANDIDATE 1.4 ###

from sys import prefix
import kivy
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
import kivy.properties as kp
import math
#import winsound
import time
import threading
import csv
import os

from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRectangleFlatButton, MDFlatButton, MDRaisedButton
from kivymd.theming import ThemeManager
from kivy_garden.graph import Graph, MeshLinePlot, ScatterPlot, SmoothLinePlot, LinePlot
from kivymd.toast import toast

from client_fx import client_fx
from emailer import send_mail

from kivymd.uix.snackbar import Snackbar

from quaternionRotation import quaternion_rotation_matrix, toQuat, toEuler
import matplotlib.pyplot as plt
import numpy as np
#import beepy

from pyquaternion import Quaternion

from kivy.core.audio import SoundLoader

Window.size = (20*50, 20*50) #remove for android builds, will resize to screen automatically



app_structure = '''
#:import Graph kivy_garden.graph.Graph
#:import MeshLinePlot kivy_garden.graph.MeshLinePlot
#:import MeshStemPlot kivy_garden.graph.MeshStemPlot
#:import Snackbar kivymd.uix.snackbar.Snackbar
#:import MDDialog kivymd.uix.dialog.MDDialog

Screen:
    BoxLayout:
        orientation: 'vertical'
        MDToolbar: 
            title: 'Swe: Release Candidate 1.4'
            left_action_items: [['menu', lambda x: nav_drawer1.set_state('open')]]
            elevation: 10
        Widget:
            title: ''

    NavigationLayout:
        ScreenManager:
            id: screen_mgr1

            ConnectionScreen:
                name: 'connection_screen1'

                MDTextField:
                    id: ipAddr
                    text: f"{app.ip_in}"
                    hint_text: 'Enter IP Address'
                    helper_text: 'IP Address of Swe Product'
                    helper_text_mode: 'on_focus'
                    icon_right: 'cellphone-wireless'
                    icon_right_color: app.theme_cls.primary_color
                    pos_hint: {'center_x':0.5,'center_y':0.67}
                    size_hint_x: None
                    width: 300

                MDTextField:
                    id: portAddr
                    text: f"{app.port_in}"
                    hint_text: 'Enter Port'
                    helper_text: 'Port number of Swe product'
                    helper_text_mode: 'on_focus'
                    icon_right: 'power-plug'
                    icon_right_color: app.theme_cls.primary_color
                    pos_hint: {'center_x': 0.5, 'center_y': 0.45}
                    size_hint_x: None
                    width: 300

                MDRaisedButton:
                    id: connectButton
                    text: 'Connect to Swe'
                    pos_hint: {'center_x': 0.5, 'center_y': 0.23}
                    width: 500
                    height: 80
                    on_release: app.call_imu_data()

                MDRectangleFlatButton:
                    id: emergencyPrompt
                    text: 'Click to report fall'
                    pos_hint: {'center_x': 0.5, 'center_y': 0.075}
                    on_release: app.manualAlert()

            VisualizerScreen:
                name: 'visualizer_screen1'

                MDBoxLayout:
                    orientation: 'vertical'

                    MDLabel:
                        id: fall_indicator01
                        size_hint_y: 0.35
                        text: 'Fall detection standby'
                        size_hint_x: None
                        halign: 'center'

                    MDRectangleFlatButton:
                        id: beginGraphButton
                        text: 'Begin Plotting'
                        pos_hint: {'center_x': 0.25, 'center_y': 0.35}
                        on_release: app.livePlot()

                    MDRectangleFlatButton:
                        id: stopGraphButton
                        text: 'Stop Plotting'
                        pos_hint: {'center_x': 0.75, 'center_y': 0.35}
                        on_release: app.cancelPlot()

                    Graph:
                        id: graph01 
                        title: 'Center of Pressure Visualization'
                        xlabel: 'Position X (m)'
                        ylabel: 'Position Y (m)'
                        xmin: -.5
                        xmax: .5
                        x_ticks_major: .125
                        ymin: -.5
                        ymax: .5
                        y_ticks_major: .125
                        y_grid_label: True
                        x_grid_label: True
                        padding: 10
                        x_grid: True
                        y_grid: True

            SettingsScreen:
                name: 'settings_screen1'

                MDTextField:
                    id: usr_weight
                    text: f"{app.weight_in}"
                    hint_text: 'Enter weight in lbs'
                    helper_text: 'weight in lbs'
                    helper_text_mode: 'on_focus'
                    icon_right: 'weight-pound'
                    icon_right_color: app.theme_cls.primary_color
                    pos_hint: {'center_x':0.5,'center_y':0.5}
                    size_hint_x: None
                    width: 300

                MDTextField:
                    id: usr_height
                    text: f"{app.height_in}"
                    hint_text: 'Enter height of user [inches]'
                    helper_text: 'height in inches'
                    helper_text_mode: 'on_focus'
                    icon_right: 'human-male-height'
                    icon_right_color: app.theme_cls.primary_color
                    pos_hint: {'center_x':0.5,'center_y':0.675}
                    size_hint_x: None
                    width: 300

                MDTextField:
                    id: usr_sex
                    text: f"{app.sex_in}"
                    hint_text: 'Sex of user (m or f)'
                    helper_text: 'enter m or f'
                    helper_text_mode: 'on_focus'
                    icon_right: 'emoticon-wink'
                    icon_right_color: app.theme_cls.primary_color
                    pos_hint: {'center_x':0.5,'center_y':0.85}
                    size_hint_x: None
                    width: 300

                MDTextField:
                    id: contact01
                    text: f"{app.e_contact_in}"
                    hint_text: 'Emergency Contact Email'
                    helper_text: 'email of person to be contacted in case of fall'
                    helper_text_mode: 'on_focus'
                    icon_right: 'email'
                    icon_right_color: app.theme_cls.primary_color
                    pos_hint: {'center_x':0.5,'center_y':0.325}
                    size_hint_x: None
                    width: 300

                MDTextField:
                    id: refr_rate_field
                    text: f"{app.rate_refresh_in}"
                    hint_text: 'Refresh rate'
                    helper_text: 'refresh rate of device in Hz'
                    helper_text_mode: 'on_focus'
                    icon_right: 'cellphone-wireless'
                    icon_right_color: app.theme_cls.primary_color
                    pos_hint: {'center_x':0.5,'center_y':0.15}
                    size_hint_x: None
                    width: 300
                    on_text: 
                        Snackbar(text=f'Device refresh rate changed to {refr_rate_field.text} Hz').show()

            ConfigScreen:
                name: 'manuf_config'

                MDTextField:
                    id: g_thresh
                    text: f"{app.grav_thresh_in}"
                    hint_text: 'Fall-det Acceleration Threshold'
                    helper_text: 'value in gs (value*9.8 is acceleration)'
                    helper_text_mode: 'on_focus'
                    icon_right: ''
                    icon_right_color: app.theme_cls.primary_color
                    pos_hint: {'center_x':0.5,'center_y':0.35}
                    size_hint_x: None
                    width: 300

                MDTextField:
                    id: f_det_freq
                    text: f"{app.fall_det_rate}"
                    hint_text: 'Fall detection frequency [Hz]'
                    helper_text: 'How often the device will check for falls, more frequent=more sensitive'
                    helper_text_mode: 'on_focus'
                    icon_right: ''
                    icon_right_color: app.theme_cls.primary_color
                    pos_hint: {'center_x':0.5,'center_y':0.65}
                    size_hint_x: None
                    width: 300


        MDNavigationDrawer:
            id: nav_drawer1

            BoxLayout:
                orientation: 'vertical'
                spacing: '8dp'
                padding: '8dp'
                Image:
                    source: 'swe_logo.png'

                MDLabel:
                    text: 'Swe Technologies'
                    font_style: 'Subtitle1'
                    size_hint_y: None
                    height: self.texture_size[1]
                    color: [1, 1, 1, 1]

                MDLabel:
                    text: 'Fall Detection'
                    font_style: 'Caption'
                    size_hint_y: None
                    height: self.texture_size[1]
                    color: [1, 1, 1, 1]

                ScrollView:
                    MDList:
                        OneLineIconListItem:
                            text: 'Connectivity'
                            on_release: screen_mgr1.current ='connection_screen1'
                            IconLeftWidget:
                                icon: 'access-point'
                        OneLineIconListItem:
                            text: 'Posture Visualizer'
                            on_release: screen_mgr1.current = 'visualizer_screen1'
                            IconLeftWidget: 
                                icon: 'axis-arrow'
                        OneLineIconListItem:
                            text: 'Settings'
                            on_release: screen_mgr1.current = 'settings_screen1'
                            IconLeftWidget:
                                icon: 'cogs'
                        OneLineIconListItem:
                            text: 'Configure'
                            on_release: screen_mgr1.current = 'manuf_config'
                            IconLeftWidget:
                                icon: 'android-debug-bridge'

<ConnectionScreen>:
<VisualizerScreen>:
<SettingsScreen>:
<ConfigScreen>:
'''
class ConnectionScreen(Screen):
    pass

class VisualizerScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class ConfigScreen(Screen):
    pass

class dialog(object):
    pass

# Begin structure of app class, references above kivy structures
class sweApp(MDApp):
    

    def build(self):
        self.theme_cls.primary_palette = 'Red'
        self.theme_cls.theme_style = 'Dark'

        if os.path.isfile('DefinitiveSweRC1_3\\storedDetails\\stored_details.txt'):
            with open('DefinitiveSweRC1_3\\storedDetails\\stored_details.txt', 'r') as usr_detail:
                stored_values = usr_detail.read().split(',')
                self.ip_in = stored_values[0]
                self.port_in = stored_values[1]
                self.weight_in = stored_values[2]
                self.height_in = stored_values[3]
                self.sex_in = stored_values[4]
                self.e_contact_in = stored_values[5]
                self.rate_refresh_in = stored_values[6]
                self.grav_thresh_in = stored_values[7]
                self.fall_det_rate = stored_values[8]
        else:
            self.ip_in = '192.168.1.1'
            self.port_in = '35196'
            self.weight_in = '125'
            self.height_in = '65'
            self.sex_in = 'm'
            self.e_contact_in = 'placeholder'
            self.rate_refresh_in = '50'
            self.grav_thresh_in = '1.47'
            self.fall_det_rate = '10'

        mainscreen1 = Builder.load_string(app_structure)

        self.alertTime = 5
        self.dialog = MDDialog(title='')
        self.sensor_refresh = int(mainscreen1.ids.refr_rate_field.text) #handle for this within the imu call and plotting functions

        self.plot_init = False

        self.username = 'swe-User'

        self.weight = float(mainscreen1.ids.usr_weight.text) * 0.4536  # weight entered in kilograms
        self.height = float(mainscreen1.ids.usr_height.text) * 2.54  # height entered in centimeters
        self.sex = mainscreen1.ids.usr_sex.text

        self.sens_height = 0.49275*self.height/100 #height of device, floor to waist of user ROUGH CALC
        self.cop_tail = 25  # number of values to plot in cop plotter before overwrite

        return mainscreen1


    def switchToConnection(self, *args):
        self.root.ids.screen_mgr1.current = 'connection_screen1'


    def switchToVisualizer(self, *args):
        self.root.ids.screen_mgr1.current = 'visualizer_screen1'


    def emergencyAlert(self, *args):
        self.root.ids.fall_indicator01.text = 'FALL DETECTED!! WARNING'
        self.alertClock.cancel()
        self.dialog.dismiss()
        emerg_email = self.root.ids.contact01.text
        
        
        send_mail('sweappnotifier@gmail.com',
            emerg_email, 'sweNotify', username)
        
        Snackbar(
            text=f'ALERT >>> {emerg_email} has been notified of the fall!!! <<<',
            ).show()
        
        MDDialog(title='Notification Sent', 
            text=f'ALERT >>> {emerg_email} has been notified of the fall!!! <<<').open()


    def autoAlert(self, *args):
        self.fall_time = time.asctime()
        self.fall_time_epoch = time.time()
        self.time_session_end = time.asctime()
        self.fall_event = True
        self.countdownThread = threading.Thread(target=self.countdownAlert)
        self.alertClock = threading.Timer(self.alertTime, self.emergencyAlert)
        self.alertClock.start()
        self.countdownThread.start()


    def countdownAlert(self, *args):
        for seconds in range(2*self.alertTime + 1):
            Snackbar(
                text=f'{seconds/2} / 5 Elapsed').show()
            time.sleep(0.5)
        self.logData()  # logs the data regardless of false posiutive/negative status as thread never closes


    def fall_cancel(self, *args):
        self.alertClock.cancel()
        self.false_positive = True
        self.dialog.dismiss()

    def manualAlert(self, *args):
        self.begin_time = time.asctime()
        self.fall_time = time.asctime()
        self.fall_time_epoch = time.time()
        self.fall_event = True # assumes fall if pushed, will show false positive if cancelled
        self.false_positive = False
        self.manual_report = True

        self.alertPrompt()


    def alertPrompt(self, *args):
        emerg_cancel = MDRaisedButton(
            text='Cancel', on_press=self.fall_cancel,
                text_color=self.theme_cls.primary_color
            )
        emerg_send = MDFlatButton(
            text='Send Alert NOW!', on_press=self.emergencyAlert,
            text_color=self.theme_cls.primary_color
        )

        self.dialog = MDDialog(title='Fall Detected',
                            auto_dismiss=False,
                            text=f'You have {self.alertTime} seconds to cancel if this was a false alarm!!!',
            buttons=[emerg_cancel, emerg_send]
        )

        self.cancelPlot()
        self.dialog.open()
        self.autoAlert()



    def call_imu_data(self): #used in the button that begins imu connection
        ip_input = self.root.ids.ipAddr.text
        port_input = int(self.root.ids.portAddr.text)
        Snackbar(
            text=f'Attempting connection with {ip_input} : {port_input}... this may take some time').show()

        try:
            self.imu_instance = client_fx(2, ip_input, port_input)
            Snackbar(text=f'Connection with {ip_input} : {port_input} successful!',
                    button_text="Visualizer Screen",
                    button_callback=self.switchToVisualizer
                    ).show()
        except: 
            Snackbar(text=f'Cannot connect with {ip_input} : {port_input}... try again later').show()

        #save previous user details for next session
        qq = f'{ip_input}'
        
        to_write = f"{self.root.ids.ipAddr.text},{self.root.ids.portAddr.text},{self.root.ids.usr_weight.text},{self.root.ids.usr_height.text},{self.root.ids.usr_sex.text},{self.root.ids.contact01.text},{self.root.ids.refr_rate_field.text},{self.root.ids.g_thresh.text},{self.root.ids.f_det_freq.text}"
        
        with open('DefinitiveSweRC1_3\\storedDetails\\stored_details.txt', 'w') as new_detail:

            new_detail.write(to_write)
                            


    def imuPlotExcept(self, *args):
        self.cancelPlot()
        imuExceptionBar = Snackbar(
            text=f'Connection with IMU not established, connect Swe device first and retry',
            button_text= "ConnectionScreen",
            button_callback=self.switchToConnection
            )

        imuExceptionBar.show()


    #def beepBoop(*args):
        #beepy.beep(3)


    def updatePoints(self, *args):
        #Pull data from LIFO queue from imu instance
        try:
            self.full_imu = self.imu_instance.dq.get()

        except:
            self.imuPlotExcept()
            return

        instant_imu = self.full_imu[1:5] #need up to 4 but this is a non-inclusive slice so 5 is cropped, NOTe: 0 is time and 5+ are lin acc

        # epoch time since beg 2021
        self.c_time = instant_imu[0] - 1609477200 #Equates to time in s since beg of 2021 (roughly)

        #Requires horizontal-mount IMU, i.e. IMU same as inertial ref frame
        h_vec = np.array([0, 0, self.sens_height])
        euler = -toEuler(instant_imu)[0]
        
        correctedFrame = Quaternion(axis=(0.0, 0.0, 1.0), radians=euler)
        rotate90 = Quaternion(axis=(0.0, 0.0, 1.0), degrees=90)
        #standingFrame = Quaternion(axis=(0.0, 1.0, 0.0), degrees=-90)
        
        frameQuat = rotate90 * correctedFrame * instant_imu

        frameRotation = quaternion_rotation_matrix(frameQuat)

        s = np.dot(frameRotation, h_vec)

        world_vect = [s[0], s[1], s[2]]  
        #rotateMyWorld = quaternion_rotation_matrix(correctedFrame)
        #world_vect = np.dot(rotateMyWorld, world_vect)

        self.data_log.append(self.full_imu)
        self.cop_log.append([world_vect[0], world_vect[1]])
        self.cop.append([world_vect[0], world_vect[1]])


        if len(self.cop) >= self.cop_tail:
            self.cop = self.cop[-self.cop_tail:]

        self.current_cop = ([self.cop[-1]])

        #self.x.append(float((s[0])))
        #self.y.append(float((s[1])))
        self.a_x.append(float(self.full_imu[5]))
        self.a_y.append(float(self.full_imu[6]))
        self.a_z.append(float(self.full_imu[7]))
        self.a_svm.append(float(math.sqrt((self.a_x[-1]**2)+(self.a_y[-1]**2)+(self.a_z[-1]**2))))

        # space to proccess the fall detectionn at 10Hz
        if (time.time() - self.tt[-1]) >= (1/float(self.root.ids.f_det_freq.text)):
            if (abs(self.cop[-1][0]) >= (self.foot_lr/2) or abs(self.cop[-1][1]) >= (self.bos_w/2)):

                #if self.beeping == False:
                    #Clock.schedule_interval(self.beepBoop, .2)
                    #self.beeping = True

                if (self.a_svm[-1] > (9.81 * float(self.root.ids.g_thresh.text))):
                    self.fall_time_epoch = self.c_time
                    self.alertPrompt()
                    self.tt.append(self.c_time)
            #elif self.beeping==True:
                #Clock.unschedule(self.beepBoop)
                #self.beeping = False

        if self.plot_init == False: #run this only if graph needs initialized, creates plot objects
            self.plot_cop = SmoothLinePlot(color=[0, 1, 0, 1])
            self.plot_current_pos = ScatterPlot(color=[1, 0, 0, 1], point_size=7)
            plot_bos = ScatterPlot(color=[1, 1, 1, 1], point_size=3)
            
            self.plot_cop.points = self.cop
            self.plot_current_pos.points = self.current_cop
            plot_bos.points = self.points_bos

            self.root.ids.graph01.add_plot(self.plot_cop)
            self.root.ids.graph01.add_plot(self.plot_current_pos)
            self.root.ids.graph01.add_plot(plot_bos)

            self.plot_init = True #changes boolean to set graph as initialized and skip first code
        else:
            self.plot_cop.points = self.cop
            self.plot_current_pos.points = self.current_cop

    def livePlot(self, *args):
        self.root.ids.fall_indicator01.text = 'NOT FALLING' #indicator writes at button press to change from stanby to fall detection
        self.graph_activate = True

        self.cop = []
        self.cop_log = []
        self.data_log = []

        self.init_falldet()

        Clock.schedule_interval(self.updatePoints, 1/self.sensor_refresh)


    def init_falldet(self, *args):

        self.false_positive = False #reset false positives each graph reset
        self.fall_event = False #reset to show fall not occurred

        self.begin_time = time.asctime()

        self.manual_report = False

        self.beeping = False
        if (self.sex == "m"):
            self.r_l = 22.486 + 0.046*self.weight
            self.l_l = 23.31 + 0.034*self.weight
            self.r_w = 8.22 + 0.020*self.weight
            self.l_w = 8.40 + 0.016*self.weight
        if (self.sex == "f"):
            self.r_l = 22.62 + 0.015*self.weight
            self.l_l = 22.64 + 0.011*self.weight
            self.r_w = 8.12 + 0.007*self.weight
            self.l_w = 8.25 + 0.005*self.weight

        self.a_x = []
        self.a_y = []
        self.a_z = []
        self.a_svm = []
        self.theta = []
        self.a_gsvm = []
        self.pre_MD = []
        self.pre_SP = []

        self.foot_lr = 0.01*(self.r_l + ((self.height - 81.1)/3.4))/2
        self.foot_ll = 0.01*(self.l_l + ((self.height - 81.1)/3.4))/2
        self.s_w = 0.055
        self.bos_w = 0.01*(self.l_w + self.r_w + self.s_w)
        self.ll_corner = [-1*(self.foot_ll/2), -1*(self.bos_w/2)]
        self.lr_corner = [(self.foot_lr/2), -1*(self.bos_w/2)]
        self.ul_corner = [-1*(self.foot_ll/2), (self.bos_w/2)]
        self.ur_corner = [(self.foot_lr/2), (self.bos_w/2)]
        self.points_bos = [self.ll_corner, self.ul_corner, self.ur_corner, self.lr_corner]

        self.tt = [time.time()]


    def cancelPlot(self, *args):
        self.root.ids.fall_indicator01.text = 'Fall detection standby'
        self.time_session_end = time.asctime()
        self.logData()
        Clock.unschedule(self.updatePoints)

    def swayMetrics(self):
        i = 0
        pre_MD = []
        pre_SP = []
        while i < len(self.cop[0]):
            pre_MD.append(float(math.sqrt((self.cop[i][0]**2)+(self.cop[i][1]**2))))
            pre_SP.append(float(math.sqrt((((self.cop[i+1][0])-(self.cop[i][0]))**2)+(((self.cop[i+1][1])-(self.cop[i][1]))**2))))
            i+=1
        return pre_MD, pre_SP

    def logData(self, *args):
        
        try:
            self.fall_time = self.fall_time + 0.0
            self.fall_time_epoch = self.fall_time_epoch + 0.0
        except:
            self.fall_time = 'NULL'
            self.fall_time_epoch = 'NULL'

        print(self.fall_time_epoch)

        try:
            pre_MD, pre_SP = self.swayMetrics()
            MD = str((1/len(pre_MD))*sum(pre_MD))
            MV = str((sum(pre_SP))/(self.data_log[-1][0] - self.data_log[0][0]))

        except:
            MD, MV = 'NULL','NULL'

        headers = [
            ['PARAMS', str(self.username), 'G Threshold =>', str(
                self.root.ids.g_thresh.text), '', 'Fall Detect Frequency [Hz]', str(
                self.root.ids.f_det_freq.text), '','',''],
            ['Time_Begin', str(self.begin_time), '', 'Fall Event Recorded?', str(
                self.fall_event), '', 'False Positive?', str(self.false_positive), '', ''],
            ['Time End', str(self.time_session_end), '', 'Fall Time', str(self.fall_time), str(self.fall_time_epoch), '', '', '', ''],
            ['','','','','','','','','',''], 
            ['SWAY METRICS','','Mean Sway Distance [m]', MD, '', 'Mean Sway Velocity [m/s]', '', MV,'',''],
            ['','','','','','','','','',''],
            ['Epoch Time [s]', 'Quat_1', 'Quat_2', 'Quat_3',
                'Quat_4', 'Lin_Acc_1 [m/s^2]', 'Lin_Acc_2', 'Lin_Acc_3', 'C.O.P._x', 'C.O.P._y']]

        if self.manual_report == False:
            data_matrix = np.hstack((self.data_log, self.cop_log))
            data_matrix = data_matrix.tolist()
        else:
            pass

        filetime = self.begin_time.replace(':', '_')
        print(filetime)
        with open(f'event_recording_{filetime}.csv', 'w', newline='') as f:
            writer=csv.writer(f, delimiter=',')
            writer.writerows(headers)
            if self.manual_report == False:
                writer.writerows(data_matrix)
            else:
                pass
        
        #print(headers)
        print('Data logging completed...')
if __name__ == '__main__': #Required method to run application object when script is run
    sweApp().run()
