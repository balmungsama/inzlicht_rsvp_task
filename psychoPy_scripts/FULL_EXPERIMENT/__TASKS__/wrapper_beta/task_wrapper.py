# ==============================================================================
# TODO: Section
# ==============================================================================
# [ ] add lines to accept input of subjID
# [ ] fix call function to properly call the psychoPy scripts
# [ ] make function version of psychoPy scripts to better accept arguments

# ==============================================================================
# Import packages
# ==============================================================================

from psychopy import gui, event, core
from subprocess import call
import numpy as np
import os

import blink_rsvp, finger_tap #, somatic_relaxation_mm, somatic_relaxation_sr

# ==============================================================================
# Pyhton Environment to run tasks
# ==============================================================================

pyEnv = 'C:\\Program Files (x86)\\PsychoPy2\\python.exe'

# ==============================================================================
# INTERVENTION FILES
# ==============================================================================

audioFiles = [
  'stimuli/body_scan_long_norm.ogg',
  'stimuli/Newcastle Hospitals - unknown album - 00 - Progressive Muscle Relaxation - Male Voice.ogg'
]

# ==============================================================================
# Define Functions
# ==============================================================================

def forceQuit(sendTTL):
    if sendTTL:
        port.setData(int(255))
    os.remove("tmp_stimuli.csv")
    core.quit()

def checkSubjID(subjID):
  try:
    subjID = int(subjID)
  except:
    raise TypeError('Please make sure the participant ID is an integer')
  if subjID <= 1000:
    raise ValueError('The participant ID must be greater than 1000.')
  return subjID

def getCondition(subjID):
  # conditions = ['mm', 'sr']
  if int(subjID) % 2 == 0:
    subjCond = 1 # TODO: add subjCond to documentation
  else:
    subjCond = 0
  return subjCond

def getOrder(subjID):
  allOrders = np.matrix([[0, 1, 0, 1],
                         [0, 1, 1, 0],
                         [1, 0, 0, 1],
                         [1, 0, 1, 0]])
  subjID    = float(subjID - 1000)
  subjID    = int(round(subjID/2)) - 1
  subjOrder = subjID % 4
  subjOrder = allOrders[subjOrder]
  return subjOrder

def runExperiment(sendTTL):
  event.globalKeys.clear()
  event.globalKeys.add(key='escape', modifiers=['shift']           , func=forceQuit, func_args = [sendTTL], name='forcequit')
  event.globalKeys.add(key='escape', modifiers=['shift', 'numlock'], func=forceQuit, func_args = [sendTTL], name='forcequit')

  nTasks  = 2
  nRuns   = 2
  expName = u'John Task Battery' 
  expInfo = {u'participant': u'10'}
  dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)
  if dlg.OK == False:
      core.quit()  # user pressed cancel
  subjID    = checkSubjID(expInfo['participant'])
  subjCond  = getCondition(subjID)
  subjOrder = getOrder(subjID)
  runCount  = 0
  taskCount = 0

  expStatus = False
  for run in range(1,nRuns+1):
    for task in range(nTasks):
      currentTask = subjOrder[:,taskCount]
      currentTask = currentTask.item(0)
      print "the current task is " + str(currentTask)
      if currentTask == 0:
        blink_rsvp.blink_rsvp(expInfo, run, expStatus, sendTTL)
      if currentTask == 1:
        finger_tap.finger_tap(expInfo, run, expStatus, sendTTL)
      expStatus = True
      taskCount += 1
    runCount += 1
    if run != nRuns:
      print "INTERVENTION!"
  
  win.close()
  core.quit() # quit the experiment

# ==============================================================================
# RUN EXPERIMENT
# ==============================================================================

runExperiment(False)