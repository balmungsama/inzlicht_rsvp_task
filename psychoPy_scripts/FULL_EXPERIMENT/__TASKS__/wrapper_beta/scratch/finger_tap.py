# ==============================================================================
# TODO
# ==============================================================================
#
# - [x] (RSVP) Announce the beginning of a new block.
# - [ ] Check if over-writing files

# ==============================================================================
# IMPORT PACKAGES
# ==============================================================================

from __future__ import absolute_import, division
from psychopy import locale_setup, sound, gui, visual, core, data, event, logging, clock
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
from pygame import sndarray
import numpy as np  # whole numpy lib is available, prepend 'np.'
import random       # allow the random selection of items from a list
import os           # handy system and path functions
import sys          # to get file system encoding
import csv          # to do the file saving
import arrow        # to get the date
import string       # get the alphabet
import pandas as pd
import time

# ==============================================================================
# DEFAULT PREFERENCES
# ==============================================================================

# define global variables
global expInfo
global colFont
global sendTTL

# taskName
taskName = "Relaxation Task Battery"

# task settings

nRuns  = 2
nTasks = 2

audioTracks = {"mm": "stimuli/audio_mm.wav", 
               "sr": "stimuli/audio_sr.wav"}

# psychopy settings
DEBUG               = False
sendTTL             = False
parallelPortAddress = 61368
monitor             = 'testMonitor'
refreshRate         = 60 # (Hz)

# text and background colours
colFont      = 'white'                    # font colour (rgb space)
colBkgd      = 'black'                    # background colour (rgb space)
colTest      = 'red'                      # background colour for when sendTTL = False (rgb space)

# expInfo defaults
expInfo         = {u'participant': u'10'}

# ==============================================================================
# TTL Classes & Functions
# ==============================================================================

class ttl_tap():
  def __init__(self, key, condition):
    super(ttl_tap, self).__init__(key, condition)

    if self.condition == 'practice':
      self.ttl = 10

    # send the TTL
    # super(ttl_tap, self).send_ttl(self.ttl)

class ttl_rsvp():
  
  task    = 'rsvp'
  respNum = 0

  present_base       = 10
  
  response_base      = 100
  responseXrespNum   = 10

  accuracy_indicator = 1
  accuracy_base      = 200
  accuracyXrespNum   = 10
  
  def __init__(self, nTargets, sepLen, sendTTL):
    self.nTargets = nTargets
    self.sepLen   = sepLen
    self.sendTTL  = sendTTL
  
  def cond_ttl(self):
    return int(self.sepLen)

  def resp_ttl(self, stimulus, key):
    self.respNum += 1
    self.stimulus = stimulus
    
    if 'num_' in key:
      key = key.split("_")[1]
    self.key = key
    
    if self.stimulus == 'mask':
      self.accuracy = 0
    elif self.stimulus == self.key:
      self.accuracy = 1
    else:
      self.accuracy = 0

    # TTL indicating participant response
    self.respTTL = self.responseXrespNum + (self.respNum * self.responseXrespNum) + int(self.key)
    self.respTTL = int(self.respTTL)

    # TTL indicating participant accuracy
    if stimulus == 'mask':
      self.accTTL = self.accuracy_base + (self.respNum * self.accuracyXrespNum) + 0
    else:
      self.accTTL = self.accuracy_base + (self.respNum * self.accuracyXrespNum) + int(self.accuracy)

    # send the TTL
    # super(ttl_rsvp, self).send_ttl(sendTTL)

def send_ttl(ttl, sendTTL):
  if sendTTL:
    port.setData(int(ttl))
  else:
    print "TTL: {}".format(str(ttl))

# ==============================================================================
# Support Functions
# ==============================================================================

def forceQuit():
  if sendTTL:
    port.setData(int(255))
  # os.remove("tmp_stimuli.csv")
  core.quit()

def pauseExperiment():
  time.sleep(15)
  event.clearEvents(eventType='keyboard')

  
def checkSubjID(subjID):
  try:
    subjID = int(subjID)
  except:
    raise TypeError('Please make sure the participant ID is an integer')
  if subjID <= 1000:
    raise ValueError('The participant ID must be greater than 1000.')
  return subjID

def getCondition(subjID):
  conditions = ['mm', 'sr']
  try:
    subjID = int(subjID)
  except:
    raise TypeError("Subject ID must be entered in the form of an integer.")

  if subjID % 2 == 0:
    subjCond = 1 # TODO: add subjCond to documentation
  else:
    subjCond = 0
  subjCond = conditions[subjCond]
  return subjCond

def getOrder(subjID):
  allOrders = np.matrix([[0, 1, 0, 1],
                         [0, 1, 1, 0],
                         [1, 0, 0, 1],
                         [1, 0, 1, 0]])
  try:
    subjID    = int(subjID)
  except:
    raise TypeError("Subject ID must be entered in the form of an integer.")
  subjID    = float(subjID - 1000)
  subjID    = int(round(subjID/2)) - 1
  subjOrder = subjID % 4
  subjOrder = allOrders[subjOrder]
  return subjOrder

def listToPD(inData, colnames):
  # sanity checks to make sure data is properly formatted.
  if isinstance(colnames, str):
    colnames = [colnames]
  if not isinstance(colnames, list):
    raise TypeError("Column names must be either in 'str' or 'list' format.")

  if not isinstance(inData, list):
    raise TypeError('Input data must be in list format.')
  # put the data into a pandas dataframe
  outData = {}
  for colNm in range(len(colnames)):
    outData[colnames[colNm]] = inData[colNm]
  outData = pd.DataFrame(outData)
  return outData

def dispText(inText, template, advKeys = ['space'], nmText = 'templateTxt'):  
  # check the advKeys to make sure they're in list format
  if isinstance(advKeys, str):
    advKeys = [advKeys]
  elif not isinstance(advKeys, list):
    raise TypeError("The advKeys used in %s must be either a 'str or a 'list'." % inspect.stack()[0][3]) 
  
  # clear the keyboard
  event.clearEvents(eventType='keyboard')

  # prepare to start routie "instructions"
  instructText      = template
  instructText.text = inText
  instructText.name = nmText

  continueRoutine = True

  # start instructions routine
  instructText.setAutoDraw(True)
  while continueRoutine:
    # check for the 'next' keyboard shortcut
    if len(advKeys) > 1:
      if event.getKeys(keyList=advKeys[0], modifiers=advKeys[1:]):
        continueRoutine = False
    elif len(advKeys) == 1:
      if event.getKeys(keyList=advKeys[0]):
        continueRoutine = False
    if continueRoutine:
      win.flip()

  instructText.setAutoDraw(False)

# ==============================================================================
# Finger-Tapping Functions
# ==============================================================================

def tap_task(durTask=240, durPractice = 10, gap=0.6, key='space', practice_ttl=10, task_ttl=100, audioFile = 'stimuli/tick.wav'):
  # make sure the specified key is a valid option
  if not isinstance(key, str):
    raise TypeError("The specfied key must be entered in 'str' format.")

  # make sure the file exists
  if not os.path.isfile(audioFile):
    raise ValueError("The specified audio file '%s' does not exist." % audioFile)

  # clear the kayboard
  event.clearEvents(eventType='keyboard')

  durTask         = durTask + durPractice

  rt_list         = []
  tap_cond_list   = []

  crosshair       = templateTxt
  crosshair.text  = '+'
  crosshair.name  = 'crosshair'
  
  continueRoutine = True
  tick_status     = False

  tick_Clock      = core.Clock()
  rt_Clock        = core.Clock()

  if durPractice > 0:
    tick = sound.Sound(audioFile, secs=0.1)
    tick.setVolume(1)
    tick.setSound(audioFile, secs=0.1)
    
    tick_timer = core.CountdownTimer()
    tick_timer.reset()

  win.callOnFlip(send_ttl, 1, sendTTL)
  win.flip()

  rt_Clock.reset()
  while continueRoutine:
    crosshair.setAutoDraw(True)

    # check if practice time
    if (tick_Clock.getTime() <= durPractice) and (durPractice > 0):
      if tick_timer.getTime() < 0 or not tick_status:
        tick_status = True
        tick.play()
        win.callOnFlip(tick_timer.add, gap)
      # detect keypress
      theseKeys = event.getKeys(keyList=[key])
      if key in theseKeys:
        win.callOnFlip(rt_list.append, rt_Clock.getTime())
        win.callOnFlip(tap_cond_list.append, 'practice')
        win.callOnFlip(rt_Clock.reset)
        if sendTTL:
          win.callOnFlip(port.setData, int(practice_ttl))
        else:
          print "TTL {}".format(int(practice_ttl))
    elif tick_Clock.getTime() <= durTask:
      # detect keypress
      theseKeys = event.getKeys(keyList=[key])
      if key in theseKeys:
        win.callOnFlip(rt_list.append, rt_Clock.getTime())
        win.callOnFlip(tap_cond_list.append, 'PRESS')
        win.callOnFlip(rt_Clock.reset)
        if sendTTL:
          win.callOnFlip(port.setData, int(task_ttl))
        else:
          print "TTL {}".format(int(task_ttl))
    else:
      crosshair.setAutoDraw(False)
      continueRoutine=False
    
    win.flip()
  
  tick.stop()
  win.callOnFlip(send_ttl, 255, sendTTL)
  win.flip()

  return [rt_list, tap_cond_list]

# ==============================================================================
# RSVP Functions
# ==============================================================================

def rsvp_trial_setup(task_params, nTargets, sepLen):

  # get number of stimuli in this trial
  nStim     = np.random.choice(task_params['stimuli']['nStim'])
  trialStim = np.random.choice(list(task_params['stimuli']['charPool']), size=nStim)
  trialCond = ["distractor" for __ in range(nStim)]

  if nTargets == 2:
    # position of the t1 stimulus
    t1_position = range(nStim - sepLen - 1)
    t1_position = np.random.choice(t1_position)

    # position of the t2 stimulus
    t2_position = t1_position + sepLen + 1

    # put the numbers in place
    trialStim[t1_position] = np.random.choice(task_params['stimuli']['tarPool'])
    trialStim[t2_position] = np.random.choice(task_params['stimuli']['tarPool'])

    # add the condition labels
    trialCond[t1_position] = 'target'
    trialCond[t2_position] = 'target'
    
    # determine if the mask should be put in, and put it in if yes
    trialMask = np.random.random() < task_params['targetSpecs']['maskProb'][nTargets]
    if trialMask:
      mask_position  = np.random.choice(range(nStim))
      while mask_position == t1_position or mask_position == t2_position:
        mask_position  = np.random.choice(range(nStim))
      trialStim[mask_position] = ' '
      trialCond[mask_position] = 'mask'
    
  elif nTargets == 1:
    t1_position   = range(nStim - sepLen - 1)
    t1_position   = np.random.choice(t1_position)
    mask_position = t1_position + sepLen + 1

    # add to the stimuli list
    trialStim[t1_position]   = np.random.choice(task_params['stimuli']['tarPool'])
    trialStim[mask_position] = ' '

    # add to the condition list
    trialCond[t1_position]   = 'target'
    trialCond[mask_position] = 'mask'
    
  else:
    raise ValueError('nTargets must be either 1 or 2.')

  # organize the stimuli into a dictionary
  trialInfo              = {}
  trialInfo['stimuli']   = trialStim
  trialInfo['condition'] = trialCond
  trialInfo['nTargets']  = nTargets
  trialInfo['sepLen']    = sepLen

  # return the stimuli
  return trialInfo

def rsvp_task(nBlocks    = 2, 
              stimDur    = 0.05,                                          # duration of stimulus presentation in seconds (0.05)
              maskDur    = 0.034,                                         # duration of the mask in seconds (0.034)
              respWait   = 1,                                             # duration (s) between stimulus presentation & response query
              itiDur     = 0.75,                                          # duration of the ITI in seconds (0.75)
              fontSz     = 0.5,                                           # font size for the stimuli (starts at .1)
              nTargets   = [1,2],                                         # number of targets present in each trial
              sepLen     = {1:[4,8] , 2:[4,8]},                           # number of trials seperating targets 
              nTrials    = {4:72, 8:192},                                 # number of trials of each sepLen entry, in respective order
              nStim      = range(15,19),                                  # number of stimuli present in each trial 
              maskProb   = {1:0, 2:0.2},                                  # probability of a mask occuring spontaneously in each trial
              charPool   = string.ascii_uppercase,                        # pool from which to draw the distractor stimuli
              tarPool    = ["1", "2", "3", "4", "5", "6", "7", "8", "9"], # pool from which to draw targets
              keyPool    = ["1", "2", "3", "4", "5", "6", "7", "8", "9",  # pool of keys to choose from
                            "num_1", "num_2", "num_3", "num_4", "num_5", "num_6", "num_7", "num_8", "num_9"]
              ):
  """
  The total number of trials in each block (assuming nSepTrials is specified) 
    will be equal to:
                        
                        sum(nSepTrials) * nTargets
  """
  
  # clear the keyboard
  event.clearEvents(eventType='keyboard')
  
  # setup condition preferences (task_params) as a dictionary
  task_params={}
  task_params['nBlocks'] = nBlocks
  task_params['fontSz']  = fontSz
  task_params['stimuli'] = {
    'charPool' : charPool,
    'tarPool'  : tarPool,
    'keyPool'  : keyPool,
    'nStim'    : nStim
    }
  task_params['timing']  = {
    'stimDur' : stimDur,
    'maskDur' : maskDur,
    'itiDur'  : itiDur,
    'respWait': respWait
  }
  task_params['targetSpecs'] = {
    'nTargets' : nTargets,
    'maskProb' : maskProb,
    'sepLen'   : sepLen,
    'nTrials'  : nTrials
    }

  # set up the dictionary containing TTL definitions
  ttl_library={}
  ttl_library['end_present'] = 254

  # text to display when participants respond
  askNumber_txt      = templateTxt
  askNumber_txt.name = 'askNumber'

  # set up the countdown timers
  stim_timer = core.CountdownTimer(task_params['timing']['stimDur' ])
  mask_timer = core.CountdownTimer(task_params['timing']['maskDur' ])
  wait_timer = core.CountdownTimer(task_params['timing']['respWait'])

  # looping through blocks
  for block in range(nBlocks):

    # add a break in between blocks
    breakText = 'Take a quick break.\n\nPress SPACE to begin block %s.' % str(block + 1)
    if block > 0:
      dispText(breakText, template=templateTxt,nmText='break')
      time_gap()

    # create pool of trial types to choose from
    trialList={}
    trialList['targets'] = []
    trialList['sep']     = []
    for nn in task_params['targetSpecs']['nTargets']:
      for ss in task_params['targetSpecs']['sepLen'][nn]:
        target_list = [nn for __ in range(task_params['targetSpecs']['nTrials'][ss]) ]
        sep_list    = [ss for __ in range(task_params['targetSpecs']['nTrials'][ss]) ]
        # add them into the dictionary defining trials from which to sample
        trialList['targets'] += target_list
        trialList['sep'    ] += sep_list
    
    # announce that the block is ready to begin

  
    # looping through trials
    numTrials_block=len(trialList['sep'])
    for trialNum in range(numTrials_block):
      time_gap(gapDur=0.75)
      
      tmp_select = random.choice(range(len(trialList['sep'])))

      # get the parameters for this trial
      tmp_nTargets = trialList['targets'].pop(tmp_select)
      tmp_sepLen   = trialList['sep'    ].pop(tmp_select)

      # define the stimuli to show in this trial
      trialInfo = rsvp_trial_setup(task_params=task_params, nTargets=tmp_nTargets, sepLen=tmp_sepLen)

      # create template for stimulus
      stimulus_text      = templateTxt
      stimulus_text.name = 'stimulus'

      # loop through each stimulus in trialStim
      targetLog = []
      rsvp_signal = ttl_rsvp(tmp_nTargets, tmp_sepLen, sendTTL)

      # call on flip tp indicate number of seperating trials
      win.callOnFlip(send_ttl, tmp_sepLen, sendTTL)
      for stim in range(len(trialInfo['stimuli'])):

        # prepare the stimulus to be displayed
        stimulus_text.text = trialInfo['stimuli'][stim]

        if stimulus_text.text in task_params['stimuli']['charPool']:
          tmp_condition = 'distractor'
        elif stimulus_text.text in task_params['stimuli']['tarPool']:
          tmp_condition = 'target'
          targetLog.append(stimulus_text.text)
        elif stimulus_text.text == ' ':
          tmp_condition = 'mask'

        tmp_row = pd.DataFrame({'Block'    : [block + 1]          , 
                                'Trial'    : [trialNum + 1]       , 
                                'nTargets' : [tmp_nTargets]       ,
                                'Sep'      : [tmp_sepLen]         ,
                                'Iter'     : [stim + 1]           , 
                                'Cond'     : [tmp_condition]      , 
                                'Stim'     : [stimulus_text.text] ,
                                'Resp'     : [' ']                ,
                                'Acc'      : [' ']               },
                              columns=['Block','Trial','nTargets','Sep','Iter','Cond','Stim','Resp','Acc'])
        
        try:
          rsvp_dataFrame = rsvp_dataFrame.append(tmp_row, ignore_index=True)
        except:
          rsvp_dataFrame = tmp_row

        # Shown the stimulus
        stim_timer.reset()
        win.callOnFlip(stimulus_text.setAutoDraw, True)
        if tmp_condition == 'target':
          win.callOnFlip(send_ttl, (len(targetLog) * 10) + int(stimulus_text.text), sendTTL)
        while stim_timer.getTime() > 0:
          win.flip()
        win.callOnFlip(stimulus_text.setAutoDraw, False)

        # get the mask ready
        mask_text = templateTxt
        mask_text.text = ' '

        # show the mask
        mask_timer.reset()
        win.callOnFlip(mask_text.setAutoDraw, True)
        while mask_timer.getTime() > 0:
          win.flip()
        win.callOnFlip(mask_text.setAutoDraw, False)
      
      win.callOnFlip(send_ttl, ttl_library['end_present'], sendTTL)
      win.flip()

      if tmp_nTargets == 1:
        targetLog.append('mask')

      print rsvp_dataFrame

      # wait to present the participant with the number query
      waitContinue = True
      wait_timer.reset()
      while waitContinue:
        win.flip()
        if wait_timer.getTime() < 0:
          waitContinue = False

      # ask participant what numbers they saw
      respContinue = True

      # set text to ask people which numbers they saw
      askNumber_txt.text = 'Which numbers did you see?'
      askNumber_txt.setAutoDraw(True)

      # clear keyboard responses that occured before the text appeared
      event.clearEvents(eventType='keyboard')
      
      respLog      = []
      while respContinue:
        # prepare to record responses
        theseKeys = event.getKeys(keyList=task_params['stimuli']['keyPool'])
        if len(theseKeys) > 0:
          respLog.append(theseKeys[0])

          # send the ttl
          rsvp_signal.resp_ttl(targetLog[len(respLog)-1], theseKeys[0])
          win.callOnFlip(send_ttl, rsvp_signal.accTTL, sendTTL=sendTTL)

        if len(respLog) == 2:
          respContinue = False
        
        win.flip()
      
      # add the responses to the pd.DataFrame
      for resp in range(len(respLog)):
        try:
          if respLog[resp] == targetLog[resp]:
            temp_accuracy = 1
          else:
            temp_accuracy = 0
        except:
          temp_accuracy = 0
        tmp_resp_row = pd.DataFrame({'Block'    : [' ']           , 
                                     'Trial'    : [' ']           , 
                                     'nTargets' : [' ']           ,
                                     'Sep'      : [' ']           ,
                                     'Iter'     : [' ']           , 
                                     'Cond'     : [' ']           , 
                                     'Stim'     : [' ']           ,
                                     'Resp'     : [respLog[resp]] ,
                                     'Acc'      : [temp_accuracy]},
                                    columns=['Block','Trial','nTargets','Sep','Iter','Cond','Stim','Resp','Acc'])
        rsvp_dataFrame = rsvp_dataFrame.append(tmp_resp_row, ignore_index=False)
      
      askNumber_txt.setAutoDraw(False) # stop drawing the query once they've responded
  
  # signal the end of the experiment
  send_ttl(255, sendTTL)
  
  # return the rsvp_dataFrame
  return rsvp_dataFrame

# ==============================================================================
# Auditory Intervention task
# ==============================================================================

def audio_task(filePath, audioVol=1):
  if not isinstance(filePath, str):
    raise TypeError("The specfied key must be entered in 'str' format.")
  if not os.path.isfile(filePath):
    raise ValueError("The specified file does not exist.")

  # clear the keyboard
  event.clearEvents(eventType='keyboard')

  # start timers
  routineTimer = core.CountdownTimer()

  # cache the audio file
  soundFile = sound.Sound(filePath, secs=-1)
  soundFile.setVolume(audioVol)

  # set the "Stay Still" instructions
  stayStill      = templateTxt
  stayStill.text = 'Please keep relatively still while still following the directions.'
  stayStill.name = 'stayStill'
  
  win.callOnFlip(send_ttl, 1, sendTTL)
  win.flip()
  
  routineTimer.reset()
  routineTimer.add(soundFile.getDuration()) 
  
  # play the sound
  soundFile.play()
  stayStill.setAutoDraw(True)
  
  while routineTimer.getTime() > 0:
    win.flip()
  
  # send the task
  win.callOnFlip(send_ttl, 255, sendTTL)
  soundFile.stop()
  stayStill.setAutoDraw(False)

  del soundFile
  
  win.flip()

# ==============================================================================
# Time-Gap function
# ==============================================================================

def time_gap(gapDur=1):
  gap_remaining = core.CountdownTimer(gapDur)
  gap_remaining.reset()
  while gap_remaining.getTime() > 0:
    win.flip()

# ==============================================================================
# Get participant information
# ==============================================================================

dlg = gui.DlgFromDict(dictionary=expInfo, title=taskName)
if dlg.OK == False:
    core.quit()  # user pressed cancel
expInfo['date'] = arrow.now().format('YYYY_MM_DD')

checkSubjID(expInfo['participant'])
expInfo['task'] = taskName

# ==============================================================================
# Experiment Setup
# ==============================================================================

# expInfo setup
expInfo['frameRate'] = refreshRate

# check if sending TTLs or debugging
if not sendTTL or DEBUG:
  colBkgd = colTest

# prepare TTL ports
if sendTTL:
    from psychopy import parallel
    port = parallel.ParallelPort(address = parallelPortAddress)
    port.setData(0) #make sure all pins are low

win = visual.Window(
  fullscr      = False, 
  allowGUI     = True, 
  allowStencil = False,
  monitor      = monitor,
  color        = colBkgd, 
  colorSpace   = 'rgb',
  useFBO       = True)
win.mouseVisible = False

# ==============================================================================
# Global Key events (e.g., forcequit)
# ==============================================================================

event.globalKeys.add(key='escape', modifiers=['shift']           , func=forceQuit      , name='forceQuit')
event.globalKeys.add(key='escape', modifiers=['shift', 'numlock'], func=forceQuit      , name='forceQuit')
event.globalKeys.add(key='t'     , modifiers=['ctrl']            , func=pauseExperiment, name='pauseExperiment')
event.globalKeys.add(key='t'     , modifiers=['ctrl' , 'numlock'], func=pauseExperiment, name='pauseExperiment')

# ==============================================================================
# Templates to modify
# ==============================================================================

templateTxt = visual.TextStim(
  win        = win,
  name       = 'template',
  text       = u'Lorem Ipsum',
  font       = u'Arial',
  height     = 0.1,
  color      = colFont, 
  opacity    = 1
  )

# ==============================================================================
# Get subject order and group (MM or SR)
# ==============================================================================

subj_order =     getOrder(expInfo['participant'])
subj_group = getCondition(expInfo['participant'])

print subj_order[0]

# ==============================================================================
# Running the task
# ==============================================================================

taskCount = 0
for run in range(nRuns):
  
  # the auditory intervention
  if run > 0:
    dispText(inText='audio plays now', template=templateTxt, nmText='audio instructions')
    audio_task(audioTracks[subj_group])
    time_gap()

  for task in range(nTasks):

    taskInd=subj_order[0,taskCount]

    if taskInd==0:
      # rsvp task 
      dispText('RSVP, bitch.', template = templateTxt, nmText = 'rsvp instructions')
      rsvp_data = rsvp_task(nTrials={4:1, 8:1}) #, 

      # make csv file name
      rsvp_outputFile = "_".join(['TAP', expInfo['participant'], 'run'+str(run), expInfo['date']])
      rsvp_outputFile = rsvp_outputFile + '.csv'
      rsvp_outputFile = os.path.join('data', rsvp_outputFile)

      # save the csv file
      rsvp_data.to_csv(path_or_buf=rsvp_outputFile)

      time_gap()
    elif taskInd==1:
      # finger-tapping task
      dispText('SURPRISE, MUTHAFUCKA!', template = templateTxt, nmText = 'tap instructions')
      tap_data = tap_task(durTask=2)
      tap_data = listToPD(tap_data, ['RT', 'condition']) 

      # make csv file name
      tap_outputFile = "_".join(['TAP', expInfo['participant'], 'run'+str(run), expInfo['date']])
      tap_outputFile = tap_outputFile + '.csv'
      tap_outputFile = os.path.join('data', tap_outputFile)

      # save the csv file
      tap_data.to_csv(path_or_buf=tap_outputFile)

      time_gap()
    
    # increment the index
    taskCount += 1

# thank them for coming in
dispText('Thank you for participating.', template=templateTxt, nmText="thanks")

# ==============================================================================
# RSVP Task
# ==============================================================================

# ==============================================================================
# Close the Window
# ==============================================================================

# close the window and quit PsychoPy
win.close()
# core.quit()