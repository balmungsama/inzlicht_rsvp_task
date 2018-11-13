# ==============================================================================
# TODO
# ==============================================================================
#
# - [ ] (RSVP) Announce the beginning of a new block.

# ==============================================================================
# IMPORT PACKAGES
# ==============================================================================

from __future__ import absolute_import, division
from psychopy import locale_setup, sound, gui, visual, core, data, event, logging, clock
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)
import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle
from time import sleep
import os     # handy system and path functions
import sys    # to get file system encoding
import csv    # to do the file saving
import arrow  # to get the date
import string # get the alphabet
import pandas as pd

# ==============================================================================
# DEFAULT PREFERENCES
# ==============================================================================

# define global variables
global expInfo
global colFont
global sendTTL

# taskName
taskName = "John's Battery"

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

# task settings
durTask      = 5#240                        # duration of the main task
durPractice  = 10                         # duration of the metronome practice
tickGap      = 0.6                        # time in seconds seperating each metronome strike
tickKey      = 'space'                    # key to press to record during the tapping task
tickSound    = 'stimuli/clock-tick1.wav'  # file path to the ticking sound file

# expInfo defaults
expInfo         = {u'participant': u'10'}

# ==============================================================================
# Finger-Tapping Functions
# ==============================================================================

def forceQuit():
  if sendTTL:
    port.setData(int(255))
  # os.remove("tmp_stimuli.csv")
  core.quit()

def checkSubjID(subjID):
  try:
    subjID = int(subjID)
  except:
    raise TypeError('Please make sure the participant ID is an integer')
  if subjID <= 1000:
    raise ValueError('The participant ID must be greater than 1000.')
  return subjID
    
def prepData(inData, colnames):
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
  print outData
  outData = pd.DataFrame(outData)
  return outData

def writeData(rtData, colnames, outputDir = 'data'):
  # Prepare the data for writing to a csv
  outData = prepData(rtData, colnames)
  
  if not os.path.isdir(outputDir):
    os.mkdir(outputDir)
  outputFile = "_".join([expInfo['task'], expInfo['participant'], expInfo['date']])
  outputFile = outputFile + '.csv'
  outputFile = os.path.join('data', outputFile)

  outData.to_csv(path_or_buf=outputFile)

def dispText(inText, template, advKeys = ['space'], nmText = 'templateTxt'):  
  # check the advKeys to make sure they're in list format
  if isinstance(advKeys, str):
    advKeys = [advKeys]
  elif not isinstance(advKeys, list):
    raise TypeError("The advKeys used in %s must be either a 'str or a 'list'." % inspect.stack()[0][3]) 

  # prepare to start routie "instructions"
  instructText      = template
  instructText.text = inText
  instructText.name = nmText

  continueRoutine = True

  while continueRoutine:
    # start instructions routine
    instructText.setAutoDraw(True)

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

def detectPress(durTask=240, durPractice = 10, gap=0.6, key='space', practice_ttl=10, task_ttl=100, audioFile = 'stimuli/clock-tick1.wav'):
  # make sure the specified key is a valid option
  if not isinstance(key, str):
    raise TypeError("The specfied key must be entered in 'str' format.")

  # make sure the file exists
  if not os.path.isfile(audioFile):
    raise ValueError("The specified audio file '%s' does not exist." % audioFile)

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
  return [rt_list, tap_cond_list]

# ==============================================================================
# RSVP Functions
# ==============================================================================

def rsvp_trial_setup(task_params, nTargets, sepLen):

  # get number of stimuli in this trial
  nStim     = np.random.choice(task_params['stimuli']['nStim'])
  trialStim = np.random.choice(list(task_params['stimuli']['tarPool']), size=nStim)

  if nTargets == 2:
    # position of the t1 stimulus
    t1_position = range(nStim - sepLen - 1)
    t1_position = np.random.choice(t1_position)

    # position of the t2 stimulus
    t2_position = t1_position + sepLen + 1

    # put the numbers in place
    trialStim[t1_position] = str(np.random.choice(task_params['stimuli']['tarPool']))
    trialStim[t2_position] = str(np.random.choice(task_params['stimuli']['tarPool']))
    
    # determine if the mask should be put in, and put it in if yes
    trialMask = np.random.random() < task_params['targetSpecs']['maskProb'][nTargets]
    if trialMask:
      mask_position  = np.random.choice(range(nStim))
      while mask_position == t1_position or mask_position == t2_position:
        mask_position  = np.random.choice(range(nStim))
      trialStim[mask_position] = ' '
    
  elif nTargets == 1:
    t1_position   = range(nStim - sepLen - 1)
    t1_position   = np.random.choice(t1_position)
    mask_position = t1_position + sepLen + 1

    trialStim[t1_position]   = str(np.random.choice(task_params['stimuli']['tarPool']))
    trialStim[mask_position] = ' '
    
  else:
    raise ValueError('nTargets must be either 1 or 2.')

  # return the stimuli
  return trialStim

def rsvp_task(nBlocks    = 2, 
              stimDur    = 0.05,                          # duration of stimulus presentation in seconds (0.05)
              maskDur    = 0.034,                         # duration of the mask in seconds (0.034)
              respWait   = 1,                             # duration (s) between stimulus presentation & response query
              itiDur     = 0.75,                          # duration of the ITI in seconds (0.75)
              fontSz     = 0.5,                           # font size for the stimuli (starts at .1)
              nTargets   = [1,2],                         # number of targets present in each trial
              sepLen     = {1:[4,8] , 2:[4,8]},           # number of trials seperating targets 
              nTrials    = {4:72, 8:192},                 # number of trials of each sepLen entry, in respective order
              nStim      = range(15,19),                  # number of stimuli present in each trial 
              maskProb   = {1:0, 2:0.2},                  # probability of a mask occuring spontaneously in each trial
              charPool   = string.ascii_uppercase,        # pool from which to draw the distractor stimuli
              tarPool    = range(1,10)
              ):
  """
  The total number of trials in each block (assuming nSepTrials is specified) 
    will be equal to:
                        
                        sum(nSepTrials) * nTargets
  """
  
  # setup condition preferences (task_params) as a dictionary
  task_params={}
  task_params['nBlocks'] = nBlocks
  task_params['fontSz']  = fontSz
  task_params['stimuli'] = {
    'charPool' : charPool,
    'tarPool'  : tarPool,
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

  # text to display when participants respond
  numberQuery_text      = templateTxt
  numberQuery_text.text = 'Which numbers did you see?'
  numberQuery_text.name = 'Number Query'

  # set up the countdown timers
  stim_timer = core.CountdownTimer(task_params['stimDur' ])
  mask_timer = core.CountdownTimer(task_params['maskDur' ])
  wait_timer = core.CountdownTimer(task_params['respWait'])

  # looping through blocks
  for block in range(nBlocks):
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
    for __ in range(numTrials_block):
      tmp_select = random.choice(range(len(trialList['sep'])))

      # get the parameters for this trial
      tmp_nTargets = trialList['targets'].pop(tmp_select)
      tmp_sepLen   = trialList['sep'    ].pop(tmp_select)

      # get the mask ready
      mask_text = templateTxt
      mask_text.text = ' '

      # define the stimuli to show in this trial
      trialStim = rsvp_trial_setup(task_params=task_params, nTargets=tmp_nTargets, sepLen=tmp_sepLen)

      # loop through each stimulus in trialStim
      for stim in trialStim:
        # prepare the stimulus to be displayed
        stimulus_text      = templateTxt
        stimulus_text.text = stimulus_text
        stimulus_text.name = 'stimulus'
        win.flip()

        # Shown the stimulus
        stim_timer.reset()
        while stim_timer.getTime() > 0:
          stimulus_text.autoDraw(True)
          win.flip()
        stimulus_text.autoDraw(False)

        # show the mask
        mask_timer.reset()
        while mask_timer.getTime() > 0:
          mask_text.autoDraw(True)
          win.flip()
        mask_text.autoDraw(False)
      
      # wait to present the participant with the number query
      waitContinue = True
      wait_timer.reset()
      while waitContinue:
        if wait_timer.getTime < 0:
          waitContinue = False

      # ask participant what numbers they saw
      respLog = []
      respContinue = True
      while respContinue:
        numberQuery_text.autoDraw(True)

        # prepare to record responses
        theseKeys = event.getKeys(keyList=task_params['stimuli']['tarPool'])
        if len(theseKeys) > 0:
          respLog.append(theseKeys[0])

        if len(theseKeys) == 2:
          respContinue=False
        
        win.flip()
      numberQuery_text.autoDraw(False) # stop drawing the query once they've responded



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
  fullscr      = True, 
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

event.globalKeys.add(key='escape', modifiers=['shift']           , func=forceQuit, name='forceQuit')
event.globalKeys.add(key='escape', modifiers=['shift', 'numlock'], func=forceQuit, name='forceQuit')

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
# Finger-Tapping Task
# ==============================================================================

# show the instructions
dispText('SURPRISE, MUTHAFUCKA!', template = templateTxt, nmText = 'instructions')

# start the ticking
rt_list = detectPress(durTask=durTask, durPractice = durPractice, gap=tickGap, key=tickKey, audioFile = tickSound)

# write the data to a csv file
writeData(rt_list, ['RT', 'condition'])

# ==============================================================================
# RSVP Task
# ==============================================================================

# ==============================================================================
# Close the Window
# ==============================================================================

# close the window and quit PsychoPy
win.close()
# core.quit()