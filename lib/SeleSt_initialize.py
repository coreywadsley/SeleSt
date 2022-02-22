"""
Selective Stopping (SeleSt) task

    SeleSt_initialize
        Information that can change from session to session is initialized in this script
        
    See the SeleSt.py script for general information on the task
"""

# Import required modules
import os
from psychopy import visual, core, gui, data
from psychopy.hardware import keyboard
import serial
import numpy as np
import array
import json

# Create Experiment class
#   Contains both general and advanced settings in dictionaries that are presented in GUIs.
#   A tool tip for each option is accessible by hovering the mouse over the input area.
#   You can make changes to the default values by altering the code below, or by creating a specific Experiment class
#   that is called in SeleSt.py, e.g., Experiment_debug.
class Experiment():
    def __init__(self,_thisDir):        
        # Create dictionary with general task information (this dictionary will be exported to a .txt file if save data is selected)
        self.taskInfo = {
            'Experiment name': 'x', # name of experiment (included in filename)
            'Participant ID': 0, # ID of participant (included in filename)
            'Age (years)': 0, # age of participant
            'Sex': ['-','F','M', 'Non-binary', 'Prefer not to say'], # sex of participant
            'Handedness': ['Right-handed','Left-handed','Mixed-handed'], # handedness of participant
            'Paradigm': ['ARI','SST'], # use anticipatory response inhibition (ARI) or stop-signal task (SST) paradigm (NOTE: default option can be changed by switching order of array)
            'Response mode': ['Wait-and-press','Hold-and-release'], # option to run task in wait-and-press (trials start automatically) or hold-and-release (trials self-initiated by holding response keys) modes
            'Include practice?': True, # include instructions and practice go-only & go/stop block
            'Save data?': True, # option to save task data
            'Import trials?': False, # option to import file containing trial information as opposed to the options in general settings
            'File path': _thisDir, # file path to folder containing trials file to import
            'File name': 'trials_1.xlsx', # name of the file to import
            'Change general settings?': False} # option to change general settings via GUI
        dlg=gui.DlgFromDict(dictionary=self.taskInfo, title='SeleSt', # Create GUI for taskInfo dictionary w/ tool tips
            order = ('Experiment name', 'Participant ID', 'Age (years)', 'Sex', 'Handedness', 'Paradigm', 'Response mode', 'Include practice?', 'Save data?', 'Import trials?', 'File path', 'File name', 'Change general settings?'),
            tip={'Experiment name': 'Input name of experiment which will included in data file name',
                 'Participant ID': 'Input ID of participant that will be included in data file name',
                 'Paradigm': 'Select whether to use anticipatory response inhibition (ARI) or stop-signal task (SST) task',
                 'Response mode': 'Select if trials should be initiated automatically (wait-and-press) or self-initiated by participant (hold-and-release)',
                 'Include practice?': 'Select this to include instructions and practice blocks for the task',
                 'Import trials?': 'Select this if you would like to import a trials file (NOTE: this will override randomisation)',
                 'File path': 'File path to folder containing trials file to import',
                 'File name': 'File name of trials file to be imported',
                 'Change general settings?': 'Select this if you would like to change general settings of the task'})
        if dlg.OK == False: core.quit()
        self.taskInfo['date'] = data.getDateStr() # add timestamp (will be included in data filename)
        # Create dictionary with general task settings        
        self.genSettings = {
            'Monitor name': 'testMonitor', # name of monitor (see https://www.psychopy.org/builder/builderMonitors.html for more info)
            'Full-screen?': True, # option to run task in full-screen or borderless window
            'Use response box?': False, # option to enable external response box
            'Trial-by-trial feedback?': True, # option to present trial-by-trial feedback
            'n practice go trials': 36, # number of go trials to include in practice go-only block
            'n go trials per block': 24,
            'n stop-both trials per block': 4,
            'n stop-left trials per block': 4,
            'n stop-right trials per block': 4,
            'n blocks': 12, # number of blocks to repeat the above trial arrangement over
            'n forced go trials': 3, # number of go trials to force at the start of each block
            'Staircase stop-signal delays?': True, # option to use staircased SSDs, SSDs will be fixed if not selected
            'Stop-signal delay step-size (ms)': 50, # step size to change stop-signal delay by if staircasing is enabled
            'Change advanced settings?':False} # option to change advanced settings via GUI              
        if self.taskInfo['Change general settings?']:
            dlg=gui.DlgFromDict(dictionary=self.genSettings, title='SeleSt (general settings)', # Create GUI for expInfo dictionary w/ tool tips
                order = ('Monitor name', 'Full-screen?', 'Use response box?', 'Trial-by-trial feedback?', 'n practice go trials', 'n go trials per block', 'n stop-both trials per block', 'n stop-left trials per block', 'n stop-right trials per block', 'n blocks', 'n forced go trials', 'Staircase stop-signal delays?', 'Stop-signal delay step-size (ms)', 'Change advanced settings?'),
                tip = {
                     'Monitor name': 'Input name of the monitor being used to present the task (see Monitor Centre for more info)',
                     'Full-screen?': 'Select this if you would like to run the task in full-screen mode (recommended for data collection)',
                     'Use response box?': 'Select this if you would like to use an external response box',
                     'Trial-by-trial feedback?': 'Select this if you would like to present trial-by-trial feedback',
                     'n practice go trials': 'Number of go trials to include in practice go-only block',
                     'n blocks': 'Set the number of blocks to repeat the trials across (NOTE: if importing trials the number of trials will be divided by n blocks; e.g., 100 trials, 10 blocks = 10 blocks x 10 trials)',
                     'n forced go trials': 'Input the number of go trials you would like to force at the start of each block',
                     'Staircase stop-signal delays?': 'Select this to staircase stop-signal delays to achieve a 50% stopping success for each stop trial type',
                     'Stop-signal delay step-size (ms)': 'Enter size to increase/decrease stop-signal delay during staircasing',
                     'Change advanced settings?': 'Select this if you would like to change any of the advanced settings'})
            if dlg.OK ==False: core.quit() # user pressed cancel

        # Create dictionary with advanced task settings (default settings dependent on paradigm)
        if self.taskInfo['Paradigm'] == 'ARI': # default settings for ARI
            Defaults = {'Target time (ms)': 800, 'Trial length (s)': 1.5, 'Fixed delay length (s)': 0.5, 'Stop-both time (ms)': 600, 'Stop-left time (ms)': 550, 'Stop-right time (ms)': 550, 'Lower stop-limit (ms)': 150, 'Upper stop-limit (ms)': 50, 'Positional stop signal': False, 'Target position': 0.8, 'Stimulus size (cm)': 15}
        elif self.taskInfo['Paradigm'] == 'SST': # default settings for SST
            Defaults = {'Target time (ms)': 300, 'Trial length (s)': 1.5, 'Fixed delay length (s)': 1, 'Stop-both time (ms)': 300, 'Stop-left time (ms)': 250, 'Stop-right time (ms)': 250, 'Lower stop-limit (ms)': 150, 'Upper stop-limit (ms)': 50, 'Positional stop signal': False, 'Target position': 0.8, 'Stimulus size (cm)': 5}        
        self.advSettings = {
            'Send serial trigger at trial onset?': False, # option to send serial trigger at trial onset (NOTE: a compatible serial device will need to be set up before this works)
            'Left response key': 'n', # response key for left stimulus
            'Right response key': 'm', # response key for right stimulus
            'Target time (ms)': Defaults['Target time (ms)'], # ARI ONLY: target time for responses
            'Trial length (s)': Defaults['Trial length (s)'], # Length of trial
            'Intertrial interval (s)': 1.5, # Length of intertrial interval
            'Fixed rise delay?': False, # option to use fixed rise delay, if false, random uniform delay is used (ARI: 0.5 - 1 s, SST: 1 -2 s)
            'Fixed delay length (s)': Defaults['Fixed delay length (s)'], # length of fixed rise delay if option is enabled
            'Stop-both time (ms)': Defaults['Stop-both time (ms)'], # starting SSD for stop-both trials
            'Stop-left time (ms)': Defaults['Stop-left time (ms)'],
            'Stop-right time (ms)': Defaults['Stop-right time (ms)'],
            'Lower stop-limit (ms)': Defaults['Lower stop-limit (ms)'], # time relative to trial onset that the bars should not stop before'
            'Upper stop-limit (ms)': Defaults['Upper stop-limit (ms)'], # time relative to target time that the bars should not stop after (e.g. 800 ms target, 150 ms upper stop-limit = 650 ms stopping limit)
            'Positional stop signal': Defaults['Positional stop signal'], # ARI ONLY: option to use positional stop-signal (cessation of bar rising)
            'Stimulus size (cm)': Defaults['Stimulus size (cm)'], # size of the left and right stimuli (ARI = height of bars, SST = height of triangles)
            'Target position': Defaults['Target position'], # ARI ONLY: position of target lines as proportion of total bar height
            'Cue color': 'black', # colour of cues (ARI = target lines, SST = outline of triangle)
            'Go color': 'black', # colour of go signal (ARI = filling bar, SST = filling of triangle)
            'Stop color': 'cyan', # colour of stop signal (same as above)
            'Background color': 'grey' # colour of background
            }        
        if self.genSettings['Change advanced settings?']:
            dlg=gui.DlgFromDict(dictionary=self.advSettings, title='SeleSt (Advanced settings)', # Create GUI for advExpInfo dictionary if advanced option was selected
                order = ('Send serial trigger at trial onset?', 'Left response key', 'Right response key', 'Target time (ms)', 'Trial length (s)', 'Intertrial interval (s)', 'Fixed rise delay?', 'Fixed delay length (s)', 'Stop-both time (ms)', 'Stop-left time (ms)', 'Stop-right time (ms)', 'Lower stop-limit (ms)', 'Upper stop-limit (ms)', 'Positional stop signal', 'Target position', 'Stimulus size (cm)', 'Background color', 'Cue color', 'Go color', 'Stop color'),
                tip = {
                     'Send serial trigger at trial onset?': 'Select this if you would like to send a trigger at trial onset (NOTE: a serial device must be set up for this to work)',
                     'Target time (ms)': 'Input the desired target response time (NOTE: keep in mind that trial length needs to be adjusted to allow for complete filling if target time is extended too far)',
                     'Trial length (s)': 'Input desired trial length (NOTE FOR ARI: this should be at least the length of total time it takes for both bars to fill)',
                     'Intertrial interval (s)': 'Input the desired intertrial interval (ITI)',
                     'Fixed rise delay?': 'If selected, each trial will begin with a fixed rise delay (length below). If unselected, each trial will begin with a variable rise delay (ARI: 500 - 1000 ms, SST: 1000 - 2000 ms).',
                     'Fixed delay length (s)': 'Length of fixed delay (if selected) you would like to use at the start of each trial',
                     'Lower stop-limit (ms)': 'Time relative to trial onset that the bars should not stop before',
                     'Upper stop-limit (ms)': 'Time relative to target time that the bars should not stop after (e.g. 800 ms target, 150 ms upper stop-limit = 650 ms stopping limit)',
                     'Positional stop signal': 'ARI ONLY: Present stop signal as cessation of rising bars, if not, change color of filling bar',
                     'Stimulus size (cm)': 'Size of the left and right stimuli (ARI = height of bars, SST = height of triangles)',
                     'Target position': 'ARI ONLY: Input where you would like the target lines to be positioned as proportion of total bar height (e.g. 0.8 equates to 80% of bar height/filling time)',
                     'Cue color': 'Input name of desired color of the cue (ARI = target lines, SST = triangle outline)',
                     'Go color': 'Input name of desired color of the go signal (ARI = filling bar, SST = triangle filling)',
                     'Stop color': 'Input name of desired color of the stop signal (ARI = filling bar, SST = triangle filling)',
                     'Background color': 'Input name of desired color of the background (for list of possible colors see https://www.w3schools.com/Colors/colors_names.asp )'})
        if dlg.OK==False: core.quit()
        
        # Set up the window in which we will present stimuli
        self.win = visual.Window(
            fullscr=self.genSettings['Full-screen?'],
            winType='pyglet',
            monitor=self.genSettings['Monitor name'],
            color=self.advSettings['Background color'],
            blendMode='avg',
            allowGUI=False,
            units = 'cm',
            size = [1200, 1200],
            screen = 0)
        
        # Measure the monitors refresh rate
        self.taskInfo['frameRate'] = self.win.getActualFrameRate()
        self.frameRate = self.taskInfo['frameRate']
        if self.frameRate != None:
            self.frameDur = 1.0 / round(self.frameRate) * 1000
        else:
            self.frameDur = 1.0 / 60.0 * 1000 # could not measure, so guess
        print('Monitor frame rate is %s Hz' %(round(self.taskInfo['frameRate'],0))) # print out useful info on frame rate & duration for the interested user
        print('Frame duration is %s ms' %round(self.frameDur,1))        
        
        # Here you can implement code to operate an external response box. 
        # The keyboard will be used if no response box is selected.
        if self.genSettings['Use response box?'] == True:
            # e.g.
            #self.rb = buttonbox.Buttonbox()    # example buttonbox from RuSocSci
            #self.L_resp_key = 'E'
            #self.R_resp_key = 'A'
            if self.taskInfo['Response mode'] == 'Hold-and-release':
                pass
            pass
        else:
            self.rb = keyboard.Keyboard()  # use input rom keyboard
            self.L_resp_key = self.advSettings['Left response key']
            self.R_resp_key = self.advSettings['Right response key']        
                    
        # Here you can set up a serial device (e.g. to send trigger at trial onset)
        if self.advSettings['Send serial trigger at trial onset?'] == True:    
            # e.g.
            #self.ser = serial.Serial('COM8', 9600, timeout=0)
            #line = ser.readline()
            pass

        # Create clocks to monitor trial duration and trial times
        self.globalClock = core.Clock() # to track total time of experiment
        self.trialClock = core.Clock() # to track time on a trial-by-trial basis
        self.holdClock = core.Clock() # to track press time when waiting for key press in hold and release

        # SAVE DATA
        # Check if a "data" folder exists in this directory, and make one if not.
        if not os.path.exists(_thisDir + os.sep +'data/'):
            print('Data folder did not exist, making one in current directory')
            os.makedirs(_thisDir + os.sep +'data/')
        if self.taskInfo['Save data?'] == True: # only save if option is selected
            self.Output = _thisDir + os.sep + u'data/SeleSt_%s_%s_%s' % (self.taskInfo['Participant ID'],
                self.taskInfo['Experiment name'], self.taskInfo['date']) # create output file to store behavioural data
            with open(self.Output+'.txt', 'a') as b: # create file w/ headers
                b.write('block trial startTime trialName trialType stopTime L_press R_press L_targetTime R_targetTime L_RT R_RT\n')
            taskInfo_output = _thisDir + os.sep + u'data/SeleSt_%s_%s_%s_taskInfo.txt' % (self.taskInfo['Participant ID'],
                self.taskInfo['Experiment name'], self.taskInfo['date']) # create output file to store taskInfo dictionary                       
            with open(taskInfo_output, 'w') as convert_file:
                 convert_file.write(json.dumps(self.taskInfo)) # save taskInfo dictionary            

        # INSTRUCTIONS        
        # Load instructions depending on selected paradigm
        # Instructions can be modified by replacing the associated .png for each instruction (see SeleSt_intrusctions.ppt for instruction slides)
        if self.taskInfo['Paradigm'] == 'ARI':
            self.instr_1_go = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-1-go_ARI.png')
            self.instr_2_points = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-2-points_ARI.png')
            self.instr_3_stop = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-3-stop_ARI.png')
        elif self.taskInfo['Paradigm'] == 'SST':
            self.instr_1_go = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-1-go_SST.png')
            self.instr_2_points = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-2-points_SST.png')
            self.instr_3_stop = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-3-stop_SST.png')     
        self.instr_4_task = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-4-task.png') 
        self.instr_5_taskEnd = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-5-taskEnd.png')                       
        if self.taskInfo['Include practice?'] == True: # markers to keep track of practice if option is selected
            self.practiceGo = True
            self.practiceStop = True
        else: # don't practice if option is disabled
            self.practiceGo = False
            self.practiceStop = False

# Create Stimuli class
#   Generates stimuli that will be presented during the task
class Stimuli:
    def __init__(self, exp):
        
        # Create stimuli for SST
        if exp.taskInfo['Paradigm'] == 'SST':
            self.L_cue = visual.Polygon(exp.win, edges=3, fillColor=None, lineWidth=5, lineColor=exp.advSettings['Cue color'], opacity=1, units='cm', size=[exp.advSettings['Stimulus size (cm)'],0.6*exp.advSettings['Stimulus size (cm)']], ori=-90, pos=[-1,0])
            self.L_stim = visual.Polygon(exp.win, edges=3, fillColor=exp.advSettings['Go color'], lineWidth=5, lineColor=exp.advSettings['Cue color'], opacity=1, units='cm', size=[exp.advSettings['Stimulus size (cm)'],0.6*exp.advSettings['Stimulus size (cm)']], ori=-90, pos=[-1,0])
            self.R_cue = visual.Polygon(exp.win, edges=3, fillColor=None, lineWidth=5, lineColor=exp.advSettings['Cue color'], opacity=1, units='cm', size=[exp.advSettings['Stimulus size (cm)'],0.6*exp.advSettings['Stimulus size (cm)']], ori=90, pos=[1,0])
            self.R_stim = visual.Polygon(exp.win, edges=3, fillColor=exp.advSettings['Go color'], lineWidth=5, lineColor=exp.advSettings['Cue color'], opacity=1, units='cm', size=[exp.advSettings['Stimulus size (cm)'],0.6*exp.advSettings['Stimulus size (cm)']], ori=90, pos=[1,0])
        
        # Create stimuli for ARI
        elif exp.taskInfo['Paradigm'] == 'ARI':
            # Do some calculations for size of bars and target lines
            barWidth = 1.5 # width of each bar in cm
            self.barTop = exp.advSettings['Stimulus size (cm)']/2 # location of top of the bar
            vert1Width = 0-(barWidth/2) # location of left side of bar
            vert2Width = (barWidth/2) # location of right side of bar
            self.L_emptyVert = [(vert1Width+-1.5,0-self.barTop), (vert1Width+-1.5,0-self.barTop+.01), 
                    (vert2Width+-1.5,0-self.barTop+.01), (vert2Width+-1.5,0-self.barTop)] # vertices of empty L bar
            self.L_fullVert = [(vert1Width+-1.5,0-self.barTop),(vert1Width+-1.5,self.barTop),
                    (vert2Width+-1.5,self.barTop),(vert2Width+-1.5,0-self.barTop)] # vertices of full L bar
            self.R_emptyVert = [(vert1Width+3,0-self.barTop), (vert1Width+3,0-self.barTop+.01), 
                    (vert2Width+0,0-self.barTop+.01), (vert2Width+0,0-self.barTop)] # vertices of empty R bar
            self.R_fullVert = [(vert1Width+3,0-self.barTop),(vert1Width+3,self.barTop),
                    (vert2Width+0,self.barTop),(vert2Width+0,0-self.barTop)] # vertices of full R bar
            self.L_emptyStim = visual.ShapeStim(exp.win, vertices=self.L_fullVert, fillColor='white', lineWidth=0, opacity=1, units='cm') # create empty L bar
            self.R_emptyStim = visual.ShapeStim(exp.win, vertices=self.R_fullVert, fillColor='white', lineWidth=0, opacity=1, units='cm') # create empty R bar
            TargetLineWidth = 5.5 # width of target lines
            TargetPos = (exp.advSettings['Target position']*exp.advSettings['Stimulus size (cm)'])-exp.advSettings['Stimulus size (cm)']/2 # set target to target position                       
            # Create stimuli (filling bars and target lines)
            self.L_cue = visual.Line(exp.win, lineColor = exp.advSettings['Cue color'], start=[0-(TargetLineWidth/2),TargetPos],end=[TargetLineWidth/2-3,TargetPos], lineWidth=10) # L target line
            self.L_stim = visual.ShapeStim(exp.win, fillColor=exp.advSettings['Go color'], lineWidth=0, opacity=1, units='cm', vertices=self.L_emptyVert) # L filling bar
            self.R_cue = visual.Line(exp.win, lineColor = exp.advSettings['Cue color'], start=[0-(TargetLineWidth/2)+3,TargetPos],end=[TargetLineWidth/2,TargetPos], lineWidth=10) # R target line
            self.R_stim = visual.ShapeStim(exp.win, fillColor=exp.advSettings['Go color'], lineWidth=0, opacity=1, units='cm', vertices=self.R_emptyVert) # R filling bar

# Create Trials class
#   Generates trials that will be presented during the task based on settings or imported file, and
#   initiates counters and settings for trial number, scores, and target RTs
class Trials:
    def __init__(self,exp):
        if exp.taskInfo['Import trials?'] == True: # import trials from conditions file
            self.trialList = data.importConditions(exp.taskInfo['File path'] + exp.taskInfo['File name'])
            self.blockTrials = np.array_split(self.trialList,exp.genSettings['n blocks'])
        else:
            nGoTrials = [1] * exp.genSettings['n go trials per block'] # set number of go and stop trials
            nStopBothTrials = [2] * exp.genSettings['n stop-both trials per block']
            nStopLeftTrials = [3] * exp.genSettings['n stop-left trials per block']
            nStopRightTrials = [4] * exp.genSettings['n stop-right trials per block']
            self.trialList = nGoTrials + nStopBothTrials + nStopLeftTrials + nStopRightTrials
        # Insert practice routine if option is selected
        if exp.taskInfo['Include practice?'] == True:
            exp.genSettings['n blocks'] = exp.genSettings['n blocks'] + 2 # add an additional block if practice trials have been selected
        self.blockList = [1] * exp.genSettings['n blocks'] # create list of blocks (NOTE: this can be used in the future to set block types)
        
        # Set up counters for block and trial number
        self.blockCount = 0
        self.trialCount = 0               
        # Set score values
        self.totalScore = 0
        self.blockScore = 0
        self.prevBlockScore = '-'
        self.trialScore = 0         
        self.lowScore = 25
        self.midScore = 50
        self.highScore = 100
        # Set target RTs
        if exp.taskInfo['Paradigm'] == 'ARI':
            self.lowTarget = 75
            self.midTarget = 50
            self.highTarget = 25
        elif exp.taskInfo['Paradigm'] == 'SST':
            self.lowTarget = 500
            self.midTarget = 400
            self.highTarget = 300            

        # # Create arrays of len('n blocks') for use in plotting block data for feedback
        # BlockCountArray = np.array([])
        # for i in range(1,exp.genSettings['n blocks']+1):
        #     self.BlockCountArray = np.append(BlockCountArray, [i], axis = 0)    
        # BlockScoreArray = np.array([])
        # for i in range(1,exp.genSettings['n blocks']+1):
        #     self.BlockScoreArray = np.append(BlockScoreArray, [0], axis = 0)
 
# Create SSD class
#   Generates information for stop trials based on selected settings
class SSD:
    def __init__(self,exp):
        # Set up initial stop-signal delays within an array
            # For example, stop-both trials are set to the first value (0) within the array.
            # Additional stop-times for different conditions (e.g. reac vs proac) can be included by adding additional variables to the array.
        self.stopTimeArray = array.array('i', [0, exp.advSettings['Stop-both time (ms)'],exp.advSettings['Stop-left time (ms)'],exp.advSettings['Stop-right time (ms)']]) # array to store stopTimes (NOTE: can append stop time for additional staircases)
        self.strcaseTime = exp.genSettings['Stop-signal delay step-size (ms)'] # set desired increment for staircase
    
"""
MODIFIED CLASSES CAN BE INSERTED BELOW
    e.g., Experiment_debug
    This allows for quick switching between experiments without having to change the settings within the code.
"""

class Experiment_debug():
    def __init__(self,_thisDir):
        # Create dictionary with general task information (this dictionary will be exported to a .txt file if save data is selected)
        self.taskInfo = {
            'Experiment name': 'x', # name of experiment (included in filename)
            'Participant ID': 0, # ID of participant (included in filename)
            'Age (years)': 0, # age of participant
            'Sex': ['-','F','M','Prefer not to say'], # sex of participant
            'Handedness': ['Right-handed','Left-handed','Ambidextrous'], # handedness of participant
            'Paradigm': ['ARI','SST'], # use anticipatory response inhibition (ARI) or stop-signal task (SST) paradigm (NOTE: default option can be changed by switching order of array)
            'Response mode': ['Wait-and-press','Hold-and-release'], # option to run task in wait-and-press (trials start automatically) or hold-and-release (trials self-initiated by holding response keys) modes
            'Include practice?': True, # include instructions and practice go-only & go/stop block
            'Save data?': False, # option to save task data
            'Import trials?': False, # option to import file containing trial information as opposed to the options in general settings
            'File path': _thisDir, # file path to folder containing trials file to import
            'File name': 'trials_1.xlsx', # name of the file to import
            'Change general settings?': False} # option to change general settings via GUI
        dlg=gui.DlgFromDict(dictionary=self.taskInfo, title='SeleSt', # Create GUI for taskInfo dictionary w/ tool tips
            order = ('Experiment name', 'Participant ID', 'Age (years)', 'Sex', 'Handedness', 'Paradigm', 'Response mode', 'Include practice?', 'Save data?', 'Import trials?', 'File path', 'File name', 'Change general settings?'),
            tip={'Experiment name': 'Input name of experiment which will included in data file name',
                 'Participant ID': 'Input ID of participant that will be included in data file name',
                 'Paradigm': 'Select whether to use anticipatory response inhibition (ARI) or stop-signal task (SST) task',
                 'Response mode': 'Select if trials should be initiated automatically (wait-and-press) or self-initiated by participant (hold-and-release)',
                 'Include practice?': 'Select this to include instructions and practice blocks for the task',
                 'Import trials?': 'Select this if you would like to import a trials file (NOTE: this will override randomisation)',
                 'File path': 'File path to folder containing trials file to import',
                 'File name': 'File name of trials file to be imported',
                 'Change general settings?': 'Select this if you would like to change general settings of the task'})
        if dlg.OK == False: core.quit()
        self.taskInfo['date'] = data.getDateStr() # add timestamp (will be included in data filename)
        # Create dictionary with general task settings        
        self.genSettings = {
            'Monitor name': 'dell_laptop', # name of monitor (see https://www.psychopy.org/builder/builderMonitors.html for more info)
            'Full-screen?': True, # option to run task in full-screen or borderless window
            'Use response box?': False, # option to enable external response box
            'Trial-by-trial feedback?': True, # option to present trial-by-trial feedback
            'n practice go trials': 4, # number of go trials to include in practice go-only block
            'n go trials per block': 2,
            'n stop-both trials per block': 2,
            'n stop-left trials per block': 0,
            'n stop-right trials per block': 0,
            'n blocks': 2, # number of blocks to repeat the above trial arrangement over
            'n forced go trials': 1, # number of go trials to force at the start of every block
            'Staircase stop-signal delays?': True, 
            'Stop-signal delay step-size (ms)': 50, # step size to change stop-signal delay by if staircasing is enabled
            'Change advanced settings?':False} # option to change advanced settings via GUI              
        if self.taskInfo['Change general settings?']:
            dlg=gui.DlgFromDict(dictionary=self.genSettings, title='SeleSt (general settings)', # Create GUI for expInfo dictionary w/ tool tips
                order = ('Monitor name', 'Full-screen?', 'Use response box?', 'Trial-by-trial feedback?', 'n practice go trials', 'n go trials per block', 'n stop-both trials per block', 'n stop-left trials per block', 'n stop-right trials per block', 'n blocks', 'n forced go trials', 'Staircase stop-signal delays?', 'Stop-signal delay step-size (ms)', 'Change advanced settings?'),
                tip = {
                     'Monitor name': 'Input name of the monitor being used to present the task (see Monitor Centre for more info)',
                     'Full-screen?': 'Select this if you would like to run the task in full-screen mode (recommended for data collection)',
                     'Use response box?': 'Select this if you would like to use an external response box',
                     'Trial-by-trial feedback?': 'Select this if you would like to present trial-by-trial feedback',
                     'n practice go trials': 'Number of go trials to include in practice go-only block',
                     'n blocks': 'Set the number of blocks to repeat the trials across (NOTE: if importing trials the number of trials will be divided by n blocks; e.g., 100 trials, 10 blocks = 10 blocks x 10 trials)',
                     'n forced go trials': 'Input the number of go trials you would like to force at the start of each block',
                     'Staircase stop-signal delays?': 'Select this to staircase stop-signal delays to achieve a 50% stopping success for each stop trial type',
                     'Stop-signal delay step-size (ms)': 'Enter size to increase/decrease stop-signal delay during staircasing',
                     'Change advanced settings?': 'Select this if you would like to change any of the advanced settings'})
            if dlg.OK ==False: core.quit() # user pressed cancel

        # Create dictionary with advanced task settings (default settings dependent on paradigm)
        if self.taskInfo['Paradigm'] == 'ARI': # default settings for ARI
            Defaults = {'Target time (ms)': 800, 'Trial length (s)': 1.5, 'Fixed delay length (s)': 0.5, 'Stop-both time (ms)': 600, 'Stop-left time (ms)': 550, 'Stop-right time (ms)': 550, 'Lower stop-limit (ms)': 150, 'Upper stop-limit (ms)': 50, 'Positional stop signal': False, 'Target position': 0.8, 'Stimulus size (cm)': 15}
        elif self.taskInfo['Paradigm'] == 'SST': # default settings for SST
            Defaults = {'Target time (ms)': 300, 'Trial length (s)': 1.5, 'Fixed delay length (s)': 1, 'Stop-both time (ms)': 300, 'Stop-left time (ms)': 250, 'Stop-right time (ms)': 250, 'Lower stop-limit (ms)': 150, 'Upper stop-limit (ms)': 50, 'Positional stop signal': False, 'Target position': 0.8, 'Stimulus size (cm)': 5}        
        self.advSettings = {
            'Send serial trigger at trial onset?': False, # option to send serial trigger at trial onset (NOTE: a compatible serial device will need to be set up before this works)
            'Left response key': 'left', # response key for left stimulus
            'Right response key': 'right', # response key for right stimulus
            'Target time (ms)': Defaults['Target time (ms)'], # ARI ONLY: target time for responses
            'Trial length (s)': Defaults['Trial length (s)'], # Length of trial
            'Intertrial interval (s)': 1.5,
            'Fixed rise delay?': False, # option to use fixed rise delay, if false, random uniform delay is used (ARI: 0.5 - 1 s, SST: 1 -2 s)
            'Fixed delay length (s)': Defaults['Fixed delay length (s)'], # length of fixed rise delay if option is enabled
            'Stop-both time (ms)': Defaults['Stop-both time (ms)'],
            'Stop-left time (ms)': Defaults['Stop-left time (ms)'],
            'Stop-right time (ms)': Defaults['Stop-right time (ms)'],
            'Lower stop-limit (ms)': Defaults['Lower stop-limit (ms)'],
            'Upper stop-limit (ms)': Defaults['Upper stop-limit (ms)'],
            'Positional stop signal': Defaults['Positional stop signal'], # option 
            'Stimulus size (cm)': Defaults['Stimulus size (cm)'], # size of the left and right stimuli (ARI = height of bars, SST = height of triangles)
            'Target position': Defaults['Target position'], # ARI only: position of target lines as proportion of total bar height
            'Cue color': 'black', # colour of cues (ARI = target lines, SST = outline of triangle)
            'Go color': 'black', # colour of go signal (ARI = filling bar, SST = filling of triangle)
            'Stop color': 'cyan', # colour of stop signal (same as above)
            'Background color': 'grey' # colour of background
            }        
        if self.genSettings['Change advanced settings?']:
            dlg=gui.DlgFromDict(dictionary=self.advSettings, title='SeleSt (Advanced settings)', # Create GUI for advExpInfo dictionary if advanced option was selected
                order = ('Send serial trigger at trial onset?', 'Left response key', 'Right response key', 'Target time (ms)', 'Trial length (s)', 'Intertrial interval (s)', 'Fixed rise delay?', 'Fixed delay length (s)', 'Stop-both time (ms)', 'Stop-left time (ms)', 'Stop-right time (ms)', 'Lower stop-limit (ms)', 'Upper stop-limit (ms)', 'Positional stop signal', 'Target position', 'Stimulus size (cm)', 'Background color', 'Cue color', 'Go color', 'Stop color'),
                tip = {
                     'Send serial trigger at trial onset?': 'Select this if you would like to send a trigger at trial onset (NOTE: a serial device must be set up for this to work)',
                     'Target time (ms)': 'Input the desired target response time (NOTE: keep in mind that trial length needs to be adjusted to allow for complete filling if target time is extended too far)',
                     'Trial length (s)': 'Input desired trial length (NOTE FOR ARI: this should be at least the length of total time it takes for both bars to fill)',
                     'Intertrial interval (s)': 'Input the desired intertrial interval (ITI)',
                     'Fixed rise delay?': 'If selected, each trial will begin with a fixed rise delay (length below). If unselected, each trial will begin with a variable rise delay (ARI: 500 - 1000 ms, SST: 1000 - 2000 ms).',
                     'Fixed delay length (s)': 'Length of fixed delay (if selected) you would like to use at the start of each trial',
                     'Lower stop-limit (ms)': 'Time relative to trial onset that the bars should not stop before',
                     'Upper stop-limit (ms)': 'Time relative to target time that the bars should not stop after (e.g. 800 ms target, 150 ms upper stop-limit = 650 ms stopping limit)',
                     'Positional stop signal': 'ARI ONLY: Present stop signal as cessation of rising bars, if not, change color of filling bar',
                     'Stimulus size (cm)': 'Size of the left and right stimuli (ARI = height of bars, SST = height of triangles)',
                     'Target position': 'ARI ONLY: Input where you would like the target lines to be positioned as proportion of total bar height (e.g. 0.8 equates to 80% of bar height/filling time)',
                     'Cue color': 'Input name of desired color of the cue (ARI = target lines, SST = triangle outline)',
                     'Go color': 'Input name of desired color of the go signal (ARI = filling bar, SST = triangle filling)',
                     'Stop color': 'Input name of desired color of the stop signal (ARI = bar filling, SST = triangle filling)',
                     'Background color': 'Input name of desired color of the background (for list of possible colors see https://www.w3schools.com/Colors/colors_names.asp )'})
        if dlg.OK==False: core.quit()
        
        # Set up the window in which we will present stimuli
        self.win = visual.Window(
            fullscr=self.genSettings['Full-screen?'],
            winType='pyglet',
            monitor=self.genSettings['Monitor name'],
            color=self.advSettings['Background color'],
            blendMode='avg',
            allowGUI=False,
            units = 'cm',
            size = [1200, 1200],
            screen=1)
        
        # Measure the monitors refresh rate
        self.taskInfo['frameRate'] = self.win.getActualFrameRate()
        self.frameRate = self.taskInfo['frameRate']
        if self.frameRate != None:
            self.frameDur = 1.0 / round(self.frameRate) * 1000
        else:
            self.frameDur = 1.0 / 60.0 * 1000 # could not measure, so guess
        print('Monitor frame rate is %s Hz' %(round(self.taskInfo['frameRate'],0))) # print out useful info on frame rate & duration for the interested user
        print('Frame duration is %s ms' %round(self.frameDur,1))        
        
        # Here you can implement code to operate an external response box. 
        # The keyboard will be used if no response box is selected.
        if self.genSettings['Use response box?'] == True:
            # e.g.
            #self.rb = buttonbox.Buttonbox()    # example buttonbox from RuSocSci
            #self.L_resp_key = 'E'
            #self.R_resp_key = 'A'
            if self.genSettings['Response mode'] == 'Hold-and-release':
                pass
            pass
        else:
            self.rb = keyboard.Keyboard()  # use input rom keyboard
            self.L_resp_key = self.advSettings['Left response key']
            self.R_resp_key = self.advSettings['Right response key']        
                    
        # Here you can set up a serial device (e.g. to send trigger at trial onset)
        if self.advSettings['Send serial trigger at trial onset?'] == True:    
            # e.g.
            #self.ser = serial.Serial('COM8', 9600, timeout=0)
            #line = ser.readline()
            pass

        # Create clocks to monitor trial duration and trial times
        self.globalClock = core.Clock() # to track total time of experiment
        self.trialClock = core.Clock() # to track time on a trial-by-trial basis
        self.holdClock = core.Clock() # to track press time when waiting for key press in hold and release

        # SAVE DATA
        # Check if a "data" folder exists in this directory, and make one if not.
        if not os.path.exists(_thisDir + os.sep +'data/'):
            print('Data folder did not exist, making one in current directory')
            os.makedirs(_thisDir + os.sep +'data/')
        if self.taskInfo['Save data?'] == True: # only save if option is selected
            self.Output = _thisDir + os.sep + u'data/SeleSt_%s_%s_%s' % (self.taskInfo['Participant ID'],
                self.taskInfo['Experiment name'], self.taskInfo['date']) # create output file to store behavioural data.
            with open(self.Output+'.txt', 'a') as b: # create file w/ headers
                b.write('block trial startTime trialName trialType stopTime L_press R_press L_targetTime R_targetTime L_RT R_RT\n')
            taskInfo_output = _thisDir + os.sep + u'data/SeleSt_%s_%s_%s_taskInfo.txt' % (self.taskInfo['Participant ID'],
                self.taskInfo['Experiment name'], self.taskInfo['date']) # create output file to store taskInfo dictionary                       
            with open(taskInfo_output, 'w') as convert_file:
                 convert_file.write(json.dumps(self.taskInfo)) # save taskInfo dictionary            

        # INSTRUCTIONS        
        # Load instructions depending on selected paradigm
        # Instructions can be modified by replacing the associated .png for each instruction (see SeleSt_intrusctions.ppt for instruction slides)
        if self.taskInfo['Paradigm'] == 'ARI':
            self.instr_1_go = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-1-go_ARI.png')
            self.instr_2_points = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-2-points_ARI.png')
            self.instr_3_stop = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-3-stop_ARI.png')
        elif self.taskInfo['Paradigm'] == 'SST':
            self.instr_1_go = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-1-go_SST.png')
            self.instr_2_points = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-2-points_SST.png')
            self.instr_3_stop = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-3-stop_SST.png')     
        self.instr_4_task = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-4-task.png') 
        self.instr_5_taskEnd = visual.ImageStim(self.win, image=_thisDir+'/instructions/instr-5-taskEnd.png')                   
        if self.taskInfo['Include practice?'] == True: # markers to keep track of practice if option is selected
            self.practiceGo = True
            self.practiceStop = True
        else: # don't practice if option is disabled
            self.practiceGo = False
            self.practiceStop = False