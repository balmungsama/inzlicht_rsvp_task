# ==============================================================================
# TODO: Section
# ==============================================================================
# [ ] add lines to accept input of subjID
# [ ] fix call function to properly call the psychoPy scripts
# [ ] make function version of psychoPy scripts to better accept arguments

# ==============================================================================
# Import packages
# ==============================================================================

from psychopy import gui
from subprocess import call
import numpy as np
import os

# ==============================================================================
# Pyhton Environment to run tasks
# ==============================================================================

pyEnv = 'C:\\Program Files (x86)\\PsychoPy2\\python.exe'

import blink_rsvp #, finger_tap, somatic_relaxation_mm, somatic_relaxation_sr

# ==============================================================================
# Define Functions
# ==============================================================================

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
  for run in range(1,nRuns+1):
    for task in range(nTasks):
      currentTask = subjOrder[:,taskCount]
      currentTask = currentTask.item(0)
      if task == 0:
        blink_rsvp.blink_rsvp_TASK(expInfo, run + 1, sendTTL)
      if task == 1:
        print('this is where the tapping goes')
      taskCount += 1
    runCount += 1
    if run != nRuns:
      print "break time!"

runExperiment(False)