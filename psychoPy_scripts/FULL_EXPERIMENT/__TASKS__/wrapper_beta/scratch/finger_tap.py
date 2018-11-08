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
import os    # handy system and path functions
import sys   # to get file system encoding
import csv   # to do the file saving
import arrow # to get the date
import string
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
      if tick_timer.getTime() < 1e-5 or not tick_status:
        tick_status = True
        tick.play()
        tick_timer.add(gap)
      # detect keypress
      theseKeys = event.getKeys(keyList=[key])
      if key in theseKeys:
        rt_list.append(rt_Clock.getTime())
        tap_cond_list.append('practice')
        rt_Clock.reset()
        if sendTTL:
          port.setData(int(practice_ttl))
        else:
          print "TTL {}".format(int(practice_ttl))
    elif tick_Clock.getTime() <= durTask:
      # detect keypress
      theseKeys = event.getKeys(keyList=[key])
      if key in theseKeys:
        rt_list.append(rt_Clock.getTime())
        tap_cond_list.append('PRESS')
        rt_Clock.reset()
        if sendTTL:
          port.setData(int(task_ttl))
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

def rsvpTrial(cond_prefs, nBlocks=2, stim_dur=0.05, iti_dur=0.75, fontSzStim=0.5):
  """
  The 'cond_prefs' input should contain the following fields:
    
    nTargets: an integer or list of integers indicating how many targets should 
        appear in each trial.
    
    sepLen: An integer or list of integers indicating how many targets 
        seperate T1 from T2 stimuli. Will be random if left out.
    
    nSepTrials: Number of trials for each listed seperation.

    nTrials: Number of trials. Will be ignored if nSepTrials is given. 
        If nSepTrials is left out but more than one seperation length if 
        specified, trials will be assigned to each seperation length randomly.

    The total number of trials in each block (assuming nSepTrials is specified) 
    will be equal to:
                        
                        sum(nSepTrials) * nTargets
  """



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