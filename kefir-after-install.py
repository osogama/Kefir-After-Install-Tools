#!/usr/bin/env python
#
# Kefir After Install 
#
# Version :  Alpha
# Kefir After Install by Edilson Alzemand 

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import GdkPixbuf
from gi.repository import Pango
from xml.dom import minidom
import os
import sys
import subprocess
import time
import datetime
import shutil
import urllib2
import webbrowser
import fcntl
import apt
from softwareproperties.SoftwareProperties import SoftwareProperties
import threading
import platform


def set_proc_name(newname):
    from ctypes import cdll, byref, create_string_buffer
    libc = cdll.LoadLibrary('libc.so.6')
    buff = create_string_buffer(len(newname)+1)
    buff.value = newname
    libc.prctl(15, byref(buff), 0, 0, 0)

def closeWindow(widget, event, window):
    # Close window
    widget.destroy()
    # Kill apt and dpkg if busy
    checkLocks()
    # Exit
    sys.exit()
    
def debugPrint(textToPrint):
    if verboseDebug:
      print textToPrint    
      
def setPartnerRepoActive():
    try:
      p1 = subprocess.Popen(['sed -i "/^# deb .*partner/ s/^# //" /etc/apt/sources.list'], shell=True, stdout=subprocess.PIPE)
      p2 = subprocess.Popen(['sed -i "/^# deb-src .*partner/ s/^# //" /etc/apt/sources.list'], shell=True, stdout=subprocess.PIPE)
      debugPrint("[Notice] Ubuntu Partner Repo Active")
      appendToLog("[Notice] Ubuntu Partner Repo Active")      
    except:
      debugPrint("[Error] Ubuntu Partner Repo could not be activated")
      appendToLog("[Error] Ubuntu Partner Repo could not be activated")
      
      
def checkLocks():
  # Just remove any processes busy on startup that is keeping apt cache or dpkg busy
  # Bit nasty not to check first is is locked - TODO  
  try:
	    # Try to remove locks if any nad kill processes
      p4 = subprocess.Popen(['fuser -k /var/lib/dpkg/lock'], shell=True, stdout=subprocess.PIPE)
      p5 = subprocess.Popen(['fuser -k /var/lib/apt/lists/lock'], shell=True, stdout=subprocess.PIPE)
      debugPrint("[Notice] apt and dpkg locks removed" )
      appendToLog("[Notice] apt and dpkg locks removed" )
     
  except:
      debugPrint("[Warning] Could not determine apt locks")
      appendToLog("[Warning] Could not determine apt locks")
	 

def refreshGui(delay=0.0001, wait=0.0001):
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration()
        time.sleep(wait)


def checkInternetConnection(targetUrl):
    try:
        response=urllib2.urlopen(targetUrl, timeout=4)
        debugPrint("[Notice] Internet Connection Active")
        appendToLog("[Notice] Internet Connection Active")
        return True
    except:
        debugPrint("[Error] Internet Offline")
        appendToLog("[Error] Internet Offline")
        return False
        
 
def setInstallLabel(state, selected):
    # Used as helper for on_cell_toggle and on_changed
    if state == 'installed':
      installLabel=' installed'
    if state == 'not-installed':
      installLabel='will be installed'
    if state == 'installed' and selected == True:
      installLabel='will be re-installed'
    if state == 'not-installed' and selected == False:
      installLabel='not installed'
    if state == 'error':
      installLabel='did not install correctly'
    return installLabel


def readRemoteFile(url):
    # Read contents of remote file
    try:
      wp = urllib2.urlopen(url)
      remoteContent = wp.read()
      remoteContent = remoteContent.strip()
      wp.close()
    except:
      debugPrint("[Error] Cannot read Remote Version File "+url)
      appendToLog("[Error] Cannot read Remote Version File "+url)
      remoteContent = 0 
    return remoteContent


def downloadFile(url, localdir):
    # Download to instalDir
    try:
      webFile = urllib2.urlopen(url)
      outFileName = url.split('/')[-1]
      outFile = os.path.join(localdir,outFileName)
      localFile = open(outFile, 'w')
      localFile.write(webFile.read())
      webFile.close()
      localFile.close()
    except:
      debugPrint("[Error] Cannot download file "+url)
      appendToLog("[Error] Cannot download file "+url)

  
def checkUpdate():
    # Get local list version
    try:
      fp = open(localVersionPath, 'r' )
      localVersion = fp.read()
      localVersion = localVersion.strip()
      fp.close()
    except:
      debugPrint("[Error] Cannot read Local Version File")
      appendToLog("[Error] Cannot read Local Version File")
      localVersion = 0
      
    # Get remote list version
    remoteVersion = readRemoteFile(remoteVersionPath)
      
    # Decide to update list or not
    if remoteVersion > localVersion :
      debugPrint("[Notice] Downloading software list "+remoteVersion)
      appendToLog("[Notice] Downloading software list "+remoteVersion)
      # Download new version
      downloadFile(remoteVersionPath, installDir)
      # Download new XML list
      downloadFile(remoteXmlPath, installDir)
      
      
def on_cell_toggle(cell, path, model):
    # Toggle if not busy installing
    if installStatus != 'busy' and installStatus != 'complete' :
      if path is not None:
        it = model.get_iter(path)
        # have no idea why we need to do a int here        
        getPathInt = int(path)
        itemInstallState = installStateList[getPathInt]
        
        # Set icon depending on state
        if itemInstallState == 'installed' and model[it][0] == False :
          model[it][4] = GdkPixbuf.Pixbuf.new_from_file(iconPathReinstall)
        
        if itemInstallState == 'installed' and model[it][0] == True :
          model[it][4] = GdkPixbuf.Pixbuf.new_from_file(iconPathOk)
                
        # Toggle state
        model[it][0] = not model[it][0]
        
        # Set label again because of re-install not showing on toggle
        # NB sytax different from setting label on_changed  
        installLabel = setInstallLabel(itemInstallState, model[it][0])
        # Set Progress bar text
        #label.set_text("%s %s" %(model[it][1], installLabel))
        progressBar.set_text("%s %s" %(model[it][1], installLabel))


def on_changed(selection, label):
    installLabel = 'unknown'

    # get the model and the iterator that points at the data in the model
    (model, iter) = selection.get_selected()
        
    # Sneaky syntax here compared to on_cell_toggle 
    it = int(model.get_string_from_iter(iter))

    # Get path val from iter
    #getPathInt = int(it)
    # Get installstate  
    itemInstallState = installStateList[it]
    
    # Get the label text 
    installLabel = setInstallLabel(itemInstallState, model[iter][0])

    # set the label to a new value depending on the selection
    # if not busy installing
    if installStatus != 'busy':
      #label.set_text("%s %s" %(model[iter][1], installLabel))
      progressBar.set_text("%s %s" %(model[iter][1], installLabel))
    return True
    
def pulse():
    progressBar.pulse()
    # call the function again
    return True  
    
        
def writeToFile(fileName,content,flag):
    try:
      fp = open(fileName, flag)
      fp.write(content)
      fp.close()
    except IOError:
      writeError="File Not Saved"
    except:
      writeError="File Not Saved"
      raise
    return


def appendToLog(content):
    timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    writeToFile(logFile, ('['+timeStamp+']'+' '+content+'\n'), 'a')
    return


def on_install_button_active(button, model, itemSelectCount):
    global pulseTimer
    global installStatus
    global cache
    global view
    global p1

    # set busy flag
    installStatus = 'busy'

    # Remove CANCEL button
    Gtk.Container.remove(grid, cancelButton)

    # Count items
    itemCount = len(model)
      
    # Add PPA's
    # Set progress
    progressBar.set_fraction(0.1)
    label.set_text("Installing new software sources...")
    appendToLog("Installing new software sources...")
    
   
    # Use APT module and SoftwareProperties to add-apt
    sp = SoftwareProperties()
    for listItem in range(itemCount):
      # Check which items are selected True in list column 0
      itemSelected = model[listItem][0]
      if itemSelected:
        if ppaList[listItem] != '' :
          progressBar.set_text("Adding PPA for "+model[listItem][1])
          # add-apt the python way ! taken from add-apt code
          try:
              sp.add_source_from_line(ppaList[listItem])
              debugPrint("Added PPA - %s" % ppaList[listItem])
              appendToLog("Added PPA - %s" % ppaList[listItem])
          except: 
              debugPrint("[Error] Could not add PPA - %s" % ppaList[listItem])
              appendToLog("[Error] Could not add PPA - %s" % ppaList[listItem])


    # Save new apt list  
    sp.sourceslist.save() 
    progressBar.set_fraction(0.2)

    # Add Keys 
    for listItem in range(itemCount):
      # Check which items are selected True in list column 0
      itemSelected = model[listItem][0]
      if itemSelected:
        if getAptKeyList[listItem] != '' :
          debugPrint("Name : %s" % model[listItem][1])
          debugPrint("Keys : %s" % getAptKeyList[listItem])
          progressBar.set_text("Adding software key for "+model[listItem][1])
          # Add key the bash way TODO do this differently to handle errors/timeout
          # First check type of key wget or apt-key adv
          if "recv-keys" in getAptKeyList[listItem] :
            keyType='apt-key'
          else:
            keyType='wget'
          try:
              if keyType == 'wget':
                # Just read Key URL and do the rest
                p1 = subprocess.Popen(['wget', '-O', '-', getAptKeyList[listItem]], stdout=subprocess.PIPE)
                p2 = subprocess.Popen(['apt-key', 'add', '--yes', '--quiet', '-'], stdin=p1.stdout, stdout=subprocess.PIPE)
                p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
              if keyType == 'apt-key':
                # Run command as is
                p6 = subprocess.Popen([getAptKeyList[listItem]], shell=True, stdout=subprocess.PIPE)

              debugPrint("Key added for : %s" % model[listItem][1])  
              appendToLog("Key added for : %s" % model[listItem][1])  
              debugPrint("Key status:  %s" % output)
              appendToLog("Key status:  %s" % output)
          except: 
              debugPrint("[Error] Could not add key from - %s" % getAptKeyList[listItem])  
              appendToLog("[Error] Could not add key from - %s" % getAptKeyList[listItem])  

    progressBar.set_fraction(0.3)

    # Manually write to file to add APT for DEB repos
    for listItem in range(itemCount):
      # Check which items are selected True in list column 0
      itemSelected = model[listItem][0]
      if itemSelected:
        if aptListEntryList[listItem] != '' :
          debugPrint("Name : %s" % model[listItem][1])
          debugPrint("APT : %s" % aptListEntryList[listItem])
          installTitles = installTitleList[listItem].split(' ')
          progressBar.set_text("Adding APT Repository for "+model[listItem][1])
          # write sources to file
          try:
              writeToFile(os.path.join(aptListPath, installTitles[0]+'.list'), 'deb '+aptListEntryList[listItem]+'\n', 'w')
              #writeToFile(os.path.join(aptListPath, installTitles[0]+'.list'), 'deb-src '+aptListEntryList[listItem]+'\n', 'a')
              writeToFile(os.path.join(aptListPath, installTitles[0]+'.list.save'), 'deb '+aptListEntryList[listItem]+'\w', 'w')
              #writeToFile(os.path.join(aptListPath, installTitles[0]+'.list.save'), 'deb-src '+aptListEntryList[listItem]+'\n', 'a')
              debugPrint("Added APT - %s" % aptListEntryList[listItem])
              appendToLog("Added APT - %s" % aptListEntryList[listItem])
          except: 
              debugPrint("[Error] Could not add APT - %s" % aptListEntryList[listItem])
              appendToLog("[Error] Could not add APT - %s" % aptListEntryList[listItem])
              onInstallError() 


    # Save new apt list  
    sp.sourceslist.save() 
    
    # We need to open the cache again before updating  
    progressBar.set_fraction(0.4)
    progressBar.set_text('Reading Software List...')
    debugPrint("[Progress] Open Cache...")
    appendToLog("[Progress] Open Cache...")
    
    cache.open()
   
    # Now, lets update the package list
    progressBar.set_fraction(0.5)
    progressBar.set_text('Updating Software Center...')
    debugPrint("[Progress] Cache update...")
    appendToLog("[Progress] Cache update...")
    pulseTimer = GLib.timeout_add(100, pulse)
    
    try:
        cache.update()
    except:
        appendToLog("[Warning] Cache update warnings. Not fatal - continue...")
        debugPrint("[Warning] Cache update warnings. Not fatal - continue...")

    GLib.source_remove(pulseTimer)
    
    # Now we can do the same as 'apt-get upgrade' does
    progressBar.set_fraction(0.7)
    #progressBar.set_text('Updating Software ...')
    #print "[progress] Updating Software ..."
    #cache.upgrade()
    # or we can play 'apt-get dist-upgrade'
    #cache.upgrade(True)
    # Q: Why does nothing happen?
    # A: You forgot to call commit()!
    debugPrint("[Progress] Commit Cache...")
    appendToLog("[Progress] Commit Cache...")
    progressBar.set_fraction(0.8)
    progressBar.set_text('Updating Software Center...')

    try:
        #cache.commit()
        cache.commit(aptAcquireProgress, aptInstallProgress)
        
    except:
        debugPrint("[Error] apt-get update failed")
        
    
    # Software sources added Done
    progressBar.set_fraction(1)
    progressBar.set_text('')
    label.set_text('Software sources added successfully')
    appendToLog('Software sources added successfully')

    
    
    # START installing apps one by one 

    # using itemSelectCount to do progress increments
    progInc = float(100 / itemSelectCount) / 100
    itemIncCount = 0
    
    progressBar.set_fraction(0.02)
    
    for listItem in range(itemCount):
      # Check which items are selected True in list column 0
      itemSelected = model[listItem][0]
      if itemSelected:
        # With selected items ...
        label.set_text('Installing Software '+str(itemIncCount+1)+' of '+str(itemSelectCount)+' ...')
        appendToLog('[Notice] Installing Software '+str(itemIncCount+1)+' of '+str(itemSelectCount)+' ...')
        
        # Un Install first if RE-install is selected
        if installStateList[listItem] == 'installed':
         
          progressBar.set_text("Removing "+model[listItem][1])
          # Set focus
          view.set_cursor(listItem)
          # open cache again for each install to update new packages list
          cache.open()
          # Get package list into array
          installTitles = installTitleList[listItem].split(' ')
          # mark packages for Remove
          for itemToRemove in installTitles:
            try:
                cache[itemToRemove].mark_delete()
                debugPrint("[Remove] Marked for Removal %s" % itemToRemove )
                appendToLog("[Remove] Marked for Removal %s" % itemToRemove )
            except:
                debugPrint("[Error] Packages not found for %s" % model[listItem][1] )
                appendToLog("[Error] Packages not found for %s" % model[listItem][1] )
                # TODO show install failed not done
                installError = "[Error] Packages not found for " + model[listItem][1]
  
          # Commit new cache and remove each set of packages 
          try:
              aptAcquireProgress.start()
              progressTimer = GLib.timeout_add(200, renderCellProgress, model, listItem, 'remove')
              cache.commit(aptAcquireProgress, aptInstallProgress)
              aptAcquireProgress.stop()
              GLib.source_remove(progressTimer)
              # Update icon after removal
              model[listItem][4] = GdkPixbuf.Pixbuf.new_from_file(iconPathBlank)
              debugPrint("Un-Install complete for %s" % model[listItem][1] )
              appendToLog("Un-Install complete for %s" % model[listItem][1] )
          except:
              debugPrint("[Error] Un-Install failed for %s" % model[listItem][1] )
              appendToLog("[Error] Un-Install failed for %s" % model[listItem][1] )
              installError = "[Error] Un-Install failed for " + model[listItem][1]
        
        
        
        # Run Pre-install commands
        # if item has pre-install run that now
        if preInstallList[listItem] != '' :
          progressBar.set_text("Running pre-install for "+model[listItem][1])
          # Run pre install commands the bash way TODO do this differently to handle errors/timeout
          try:
              p1 = subprocess.Popen([preInstallList[listItem]], shell=True, stdout=subprocess.PIPE)
              output = p1.communicate()[0]
              debugPrint("Running Pre install script for : %s" % model[listItem][1]) 
              debugPrint("Pre install script output:  %s" % output)
              appendToLog("Running Pre install script for : %s" % model[listItem][1]) 
              appendToLog("Pre install script output:  %s" % output)
          except: 
              debugPrint("[Error] Pre install script error : %s" % model[listItem][1]) 
              appendToLog("[Error] Pre install script error : %s" % model[listItem][1]) 
      

        # Install software item FINALLY             
        installError = ''

        # Initial cell progressbar value
        model[listItem][3] = 0      
        
        progressBar.set_text("Installing "+model[listItem][1])
        debugPrint("Installing %s" % model[listItem][1])
        appendToLog("Installing %s" % model[listItem][1])
        # Set focus
        view.set_cursor(listItem)
        # open cache again for each install to update new packages list
        cache.open()
        # Get package list into array
        installTitles = installTitleList[listItem].split(' ')
        # mark packages for install
        for itemToInstall in installTitles:
          try:
              cache[itemToInstall].mark_install()
              debugPrint("[Install] Marked for install %s" % itemToInstall )
              appendToLog("[Install] Marked for install %s" % itemToInstall )
          except:
              debugPrint("[Error] Packages not found for %s" % model[listItem][1] )
              appendToLog("[Error] Packages not found for %s" % model[listItem][1] )
              # TODO show install failed not done
              installError = "[Error] Packages not found for " + model[listItem][1]


        # Commit new cache and install each set of packages 
        try:
            #cache.upgrade()
            aptAcquireProgress.start()
            progressTimer = GLib.timeout_add(200, renderCellProgress, model, listItem, 'install')

            cache.commit(aptAcquireProgress, aptInstallProgress)

            #cache.commit()
            debugPrint("Install complete for %s" % model[listItem][1] )
            appendToLog("Install complete for %s" % model[listItem][1] )
        except:
            debugPrint("[Error] Installation failed for %s" % model[listItem][1] )
            # TODO show install failed not done
            installError = "[Error] Installation failed for " + model[listItem][1]
        
        
        # END of Install 
        
        # Run POST-install commands
        # if item has post-install run that now
        if postInstallList[listItem] != '' :
          progressBar.set_text("Running post-install for "+model[listItem][1])
          # Run post install commands the bash way TODO do this differently to handle errors/timeout
          try:
              p1 = subprocess.Popen([postInstallList[listItem]], shell=True, stdout=subprocess.PIPE)
              output = p1.communicate()[0]
              debugPrint("Running Post install script for : %s" % model[listItem][1]) 
              debugPrint("Post install script output:  %s" % output)
              appendToLog("Running Post install script for : %s" % model[listItem][1]) 
              appendToLog("Post install script output:  %s" % output)
          except: 
              debugPrint("[Error] Post install script error : %s" % model[listItem][1]) 
              appendToLog("[Error] Post install script error : %s" % model[listItem][1]) 
            
    
        # Set Cell Progress bar and deselect when done
        model[listItem][3] = 100
        model[listItem][0] = False
        GLib.source_remove(progressTimer)
        aptAcquireProgress.stop()


        time.sleep(0.1)
        refreshGui()
        time.sleep(0.1)
        
        # Check if install ok and set icon
        if installError == '':
          iconPathMod = iconPathOk
          installStateList[listItem]='installed'
        else:
          iconPathMod = iconPathError
          installStateList[listItem]='error'

          
        # Set icon
        model[listItem][4] = GdkPixbuf.Pixbuf.new_from_file(iconPathMod)

        # If selected Inc for each item as we know not how many here
        # Move progress incrementally depending on number of install items
        itemIncCount = itemIncCount + 1
        displayInc = progInc * itemIncCount

        # Update main progress bar at the end of each item install
        progressBar.set_fraction(displayInc)



    # All Done - The End -
    # Remove Timers 
    GLib.source_remove(progressTimer)
    progressBar.set_fraction(1)
    progressBar.set_text('')
    
    # Stop Spinner
    spinner.stop()
    label.set_text('Installation Complete')
    debugPrint('[END] Installation Complete')
    appendToLog('[END] Installation Complete')
    # Set focus
    view.set_cursor(0)
    # Reset installstatus
    installStatus = 'complete'
    # Remove Cancel Button and spinner
    #Gtk.Container.remove(grid, cancelButton)
    Gtk.Container.remove(grid, spinner)

    
    # Activate Install Now/Done button 
    button.set_sensitive(True)

def on_install_thread(button, model):
    global loop_thread

    # If button set active and label set to done exit
    if button.get_label() == 'Done':
       sys.exit()

    appendToLog('Install sequence initiated - Install Now')

    # Count items before we start
    itemCount = len(model)     
    # count selected items    
    itemSelectCount = 0
    for listItem in range(itemCount):
      # Check which items are selected True in list column 0
      itemSelected = model[listItem][0]
      if itemSelected:
        itemSelectCount = itemSelectCount + 1
        
    debugPrint('Number of items selected for install : %s' % str(itemSelectCount))
    appendToLog('Number of items selected for install : %s' % str(itemSelectCount))
    
    # Do nothing if no items selected
    if itemSelectCount == 0 :
      return                 
       
    # Set button and progress
    button.set_sensitive(False)
    button.set_label("Done")
    progressBar.set_fraction(0.05)
    progressBar.set_text('Installation Started')
    label.set_text("Installing new software ...")
    appendToLog("Installing new software ...")
    
    # Start Spinner
    spinner.start()

    # start the data function threaded
    loop_thread = threading.Thread(target=on_install_button_active, args=[button, model, itemSelectCount])
    #loop_thread = Process(target=on_install_button_active, args=(button, model))
    loop_thread.start()
    
    appendToLog('Install Thread started')

    # timer to sync treads every second 1000ms to get feedback to gui
    timerAsync = GLib.timeout_add(100, joinTreads)


def joinTreads():
    global loop_thread
    # Join Threads every second for 0.5 sec and relax
    loop_thread.join(timeout=0.02)
    #print "Status :", installStatus
    #if installStatus == 'quit':
    #  loop_thread.join()
    #  sys.exit()
    return True


def renderCancelDialog():
    global installStatus
    
    dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.QUESTION,
               Gtk.ButtonsType.YES_NO, appName )
    dialog.set_default_size(400, 250)
    dialog.format_secondary_text("Are you sure you would like to Cancel now ?\n")
    response = dialog.run()
    
    if response == Gtk.ResponseType.YES:
      # loop_thread.join() not needed before it is started and causes issues here
      if pulseTimer > 0 :
        GLib.source_remove(pulseTimer)
      if timerAsync > 0 :
        GLib.source_remove(timerAsync)  

      # Set EXIT flag
      installStatus = 'quit'
      
      dialog.destroy()

      # Exit
      sys.exit()
  
    elif response == Gtk.ResponseType.NO:
      debugPrint("Cancel selected - Do nothing")
      dialog.destroy()

    dialog.destroy()
    return
    
    
def renderOfflineDialog():
    dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.WARNING,
               Gtk.ButtonsType.OK, appName+' - Offline' )
    dialog.set_default_size(400, 250)
    dialog.format_secondary_text("An internet connection is required by "+appName+"\nThis application will now quit")
    response = dialog.run()
    
    if response == Gtk.ResponseType.OK:
      dialog.destroy()
      sys.exit()

    dialog.destroy()


def on_cancel_button_clicked(button):
    renderCancelDialog()

def renderCellProgress(model, path, location):
    # Get download part first
    totalBytes = aptAcquireProgress.total_bytes
    currentBytes = aptAcquireProgress.current_bytes
    # Install part
    installProgress = aptInstallProgress.percent
        
    try:
        percentDown = (currentBytes / (totalBytes * 1.0) * 100)
    except(ZeroDivisionError):
        percentDown = 0
        
    if percentDown < 100 and location == 'install':
      # while downloading show progress up to 50%
      currentProgress = (percentDown / 2)
      
    if percentDown == 100 and location == 'install':
      # from 50% on we show the install progress
      # first take a pause because installProgress still at 100 from previous instance
      if percentDown == 100 and installProgress == 100:
        time.sleep(0.3)
      currentProgress = (installProgress / 2) + 50
      
    if location == 'remove':
      # count down
      currentProgress = 100.0 - installProgress
      
    if percentDown == 0 and installProgress > 0 and location == 'install':
      # on reinstall and cache install
      progressBar.set_text("Installing "+model[path][1])
      currentProgress = installProgress

    if percentDown == 0 and installProgress == 100 and location == 'install':
      # another pause to catch up when new install starts and previous installProgress still active
      time.sleep(0.5)
      currentProgress = installProgress

    # update each list item percent ... progressbar set to half - 50%
    #currentProgress = float(aptInstallProgress.percent / 1.2)
    # Set progress bar value
    model[path][3] = int(currentProgress)
    #debugPrint("location = %s" % location)
    #debugPrint("currentBytes = %s" % currentBytes)
    #debugPrint("totalBytes = %s" % totalBytes)
    #debugPrint("percentDown = %s" % percentDown)
    #debugPrint("installProgress = %s" % str(installProgress))
    #debugPrint("[currentProgress] = %s" % currentProgress)
    return True

    
def renderStartupSplash():
    global splashWindow
    global splashProgressBar
    # Create Main window
    splashWindow = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    splashWindow.set_title( appName+' '+appVersion )
    #splashWindow.set_title( '' )
    splashWindow.set_icon(GdkPixbuf.Pixbuf.new_from_file(iconPath))
    splashWindow.set_border_width(10)
    splashWindow.connect('delete-event', closeWindow, splashWindow)

    splashWindow.set_default_size(300, 300)
    splashWindow.set_position(Gtk.WindowPosition.CENTER)
    splashWindow.set_resizable(False)
   
    # Create an logo Image
    logoImage = Gtk.Image()
    # set the content of the image as the file filename.png
    #pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(iconPath, 300, 300, True)

    logoImage.set_from_file(iconPath)
    #logoImage.set_from_pixbuf(pixbuf)

    # Create Label        
    #splashLabel = Gtk.Label()
    #splashLabel.set_text("  Checking installed software...  ")
    
    # Create progress bar
    splashProgressBar = Gtk.ProgressBar()
    splashProgressBar.set_show_text(True)
    splashProgressBar.set_ellipsize(3)
    splashProgressBar.set_fraction(0.1)
    splashProgressBar.set_text('Initialising...')


    # a grid to attach the elements
    splashGrid = Gtk.Grid()
    #splashGrid.set_column_homogeneous(True)
    #splashGrid.set_row_homogeneous(True)
    splashGrid.set_row_spacing(15)
    splashGrid.attach(logoImage, 0, 0, 1, 1)
    #splashGrid.attach(splashLabel, 0, 1, 1, 1)
    splashGrid.attach(splashProgressBar, 0, 2, 1, 1)
   
    # attach the grid to the window
    splashWindow.add(splashGrid)  

    # Show Window
    splashWindow.show_all()
    

def renderMainWindow():
    global progressBar
    global label
    global view
    global spinner
    global grid
    global cancelButton

    # Create Main window
    mainWindow = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    mainWindow.set_title( appName+' '+appVersion )
    mainWindow.set_icon(GdkPixbuf.Pixbuf.new_from_file(iconPath))
    mainWindow.set_border_width(10)
    mainWindow.connect('delete-event', closeWindow, mainWindow)

    mainWindow.set_default_size(560, 400)
    mainWindow.set_position(Gtk.WindowPosition.CENTER)
    mainWindow.set_resizable(True)

    view = Gtk.TreeView(menuItemStore)
    # Make TreeView resize vertically only
    view.set_hexpand(True)
    view.set_vexpand(True)
      
    columns = ["Select", " Title",
           " Description", " Install Progress ", " "]
     
      
    # Render menuItemStore columns
    for i in range(len(columns)):
        # Render first column as toggle
        if i == 0:
          cell = Gtk.CellRendererToggle()
          cell.connect('toggled', on_cell_toggle, menuItemStore)
          # ceate coloumn and get val from liststore col 0
          col = Gtk.TreeViewColumn(columns[i], cell, active=i)
        if i == 1 or i ==2 : 
          # cellrenderer to render the text
          cell = Gtk.CellRendererText()
          # create column
          col = Gtk.TreeViewColumn(columns[i], cell, text=i)
        # the text in the first column should be in boldface
        if i == 1:
          cell.props.weight_set=True
          cell.props.weight=Pango.Weight.BOLD
          
        # the column is created
        if i == 3:
          cell = Gtk.CellRendererProgress()
          # progress value from liststore col 3
          col = Gtk.TreeViewColumn(columns[i], cell, value=i)

        # the icon column is created
        if i == 4:
          cell = Gtk.CellRendererPixbuf()
          cell.set_fixed_size(30, -1)
          # progress value from liststore col 4
          col = Gtk.TreeViewColumn(columns[i], cell, pixbuf=i)
          col.set_min_width(30)
          #col.set_fixed_width(30)
          #col.set_expand(False)
               
        # and it is appended to the treeview
        view.append_column(col)
    
    
    
    # Create an logo Image
    #logoImage = Gtk.Image()
    # set the content of the image as the file filename.png
    #logoImage.set_from_file(iconPath)

    # Create Label        
    label = Gtk.Label()
    label.set_text("Selecione os Softwares que deseja instalar")
    
    # Create progress bar
    progressBar = Gtk.ProgressBar()
    #progressBar.set_text("")
    progressBar.set_show_text(True)
    progressBar.set_fraction(0.0)
    progressBar.set_text(' ')

    # Create Spinner
    spinner = Gtk.Spinner()

    # Create Install Button
    installButton = Gtk.Button("Instalar agora")
    installButton.connect("clicked", on_install_thread, menuItemStore)


    # Create Cancel Button
    cancelButton = Gtk.Button("_Cancelar", use_underline=True)
    cancelButton.connect("clicked", on_cancel_button_clicked)

    
    # CALLBACK for all changes item selected in select list
    view.get_selection().connect("changed", on_changed, label)

    # create scrollwindow
    scrollTree = Gtk.ScrolledWindow()
    scrollTree.set_min_content_width(560)
    scrollTree.set_min_content_height(300)
    scrollTree.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    # Put liststore view in scroll window
    scrollTree.add(view)

    # a grid to attach the elements
    grid = Gtk.Grid()
    grid.set_row_spacing(15)
    
    grid.attach(label, 0, 0, 3, 1)
    grid.attach(progressBar, 0, 1, 3, 1)
    grid.attach(scrollTree, 0, 3, 3, 1)
    grid.attach(cancelButton, 1, 4, 1, 1)
    grid.attach_next_to(spinner, cancelButton, Gtk.PositionType.LEFT, 1, 1)
    grid.attach_next_to(installButton, cancelButton, Gtk.PositionType.RIGHT, 1, 1)
 
    #grid.attach(spinner, 2, 0, 1, 1)
    #grid.attach_next_to(spinner, label, Gtk.PositionType.RIGHT, 1, 1)

    # attach the grid to the window
    mainWindow.add(grid)  

    appendToLog('Main display rendered')


    # Render Main Window
    mainWindow.show_all()


def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)
    
def checkInstall(software):

    # Convert software list into array
    software = software.split(' ')
    # Check each item and if one is missing assume not installed 
    for item in software:
      try:
          isInstalled = cache[item].is_installed # Evaluates true if git is installed
      except:
          isInstalled = False
        
      # if any item on install list is False return False
      if isInstalled == False:
        return isInstalled
        
    # if installed return True  as False would already been returned      
    return isInstalled


############################# Main Loop
#
if __name__ == "__main__":
  
  # Vars
  verboseDebug = True

  # Main Env Vars
  appName = 'Kefir After Install'
  procName = 'Kefir-after-install'
  appVersion = 'Alpha'
  userHome = os.getenv("HOME")
  timeStamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  installDir = './'
  logFile = '/var/log/kefir-after-install.log'
  lockFilePath = os.path.join('/tmp/ubuntu-after-install.lock')
  iconPath = os.path.join(installDir, 'kefir-after-install.png')
  iconPathError = os.path.join(installDir, 'lib', 'icons', 'red.svg')
  iconPathReinstall = os.path.join(installDir, 'lib', 'icons', 'orange.svg')
  iconPathOk = os.path.join(installDir, 'lib', 'icons', 'green.svg')
  iconPathBlank = os.path.join(installDir, 'lib', 'icons', 'grey.svg')
  xmlFilename = 'kefir-after-install.xml'
  xmlPath = os.path.join(installDir, xmlFilename)
  VersionFilename = ''
  localVersionPath = os.path.join(installDir, VersionFilename)
  remoteVersionDir = 'https://'
  remoteVersionPath = os.path.join(remoteVersionDir, VersionFilename)
  remoteXmlPath = os.path.join(remoteVersionDir, xmlFilename)
  aptListPath = '/etc/apt/sources.list.d/'
  # App Vars
  connectionStatus = False
  installStatus = ''
  pulseTimer = 0
  timerAsync = 0
  progressTimer = 0
  p1 = ''
  
  
  # Set running process title using libc
  set_proc_name(procName)
   
  # Lock File
  try:
      lockFile = open(lockFilePath,'w')
	    # Try to aquire lock
      fcntl.flock(lockFile, fcntl.LOCK_EX|fcntl.LOCK_NB)
      # File has not been locked before 
      fileIsLocked = False
  except:
      # File is already locked
	    fileIsLocked = True
	  
  if fileIsLocked: 
	  sys.exit('[Notice] '+procName+' instance already running or you do not have admin rights to run the program.')
	
  lockFile.write('%d\n'%os.getpid())
  lockFile.flush()

  # Start Log file after use appendToLog
  writeToFile(logFile, ('['+timeStamp+'] '+appName+' '+appVersion+' - Started'+'\n'), 'w')
  debugPrint("[Notice] Log file created")
  appendToLog("[Notice] Log file created")
  
  # Get Dist Info
  (distId, distRelease, distCodename) = platform.linux_distribution()
  debugPrint("Distribution : %s" % distId)
  appendToLog("Distribution : %s" % distId)
  debugPrint("Release : %s" % distRelease)
  appendToLog("Release : %s" % distRelease)
  debugPrint("Codename : %s" % distCodename)
  appendToLog("Codename : %s" % distCodename)


  # START Splash Screen

  renderStartupSplash()

  # need this to render splash screen at this point
  time.sleep(0.1)
  refreshGui()
  time.sleep(2)
  refreshGui()

  # Check For Locks on dpkg and apt lists and remove if needed
  splashProgressBar.set_text('Check if installers are busy...')
  splashProgressBar.set_fraction(0.2)
  checkLocks()

  # Check internet connection
  splashProgressBar.set_text('Checking internet connection...')
  splashProgressBar.set_fraction(0.3)
  refreshGui()
  if checkInternetConnection('http://ubuntu.com') == False:
      # OFFLINE
      renderOfflineDialog()
 
  # Check for list update 
  #splashProgressBar.set_text('Checking for updates...')
  #splashProgressBar.set_fraction(0.4)
  #refreshGui()
  #if checkInternetConnection('http://ubuntu.com') == True:
      # ONLINE
      #checkUpdate()
 
  # Add Partner Repo Active
  splashProgressBar.set_text('Checking software sources...')
  splashProgressBar.set_fraction(0.5)  
  refreshGui()
  setPartnerRepoActive()


  # Get APT cache progress 
  aptOpProgress = apt.progress.text.OpProgress()
  
  aptOptBaseProgress = apt.progress.base.OpProgress()
  aptAcquireProgress = apt.progress.base.AcquireProgress()
  aptInstallProgress = apt.progress.base.InstallProgress()
 
  # Create apt cache 
  splashProgressBar.set_text('Reading installed software list...')
  splashProgressBar.set_fraction(0.7)  
  refreshGui()
  #cache = apt.Cache(aptOpProgress)
  cache = apt.Cache()
  appendToLog('Apt cache created')
  
  splashProgressBar.set_fraction(0.9)
  splashProgressBar.set_text('Almost done...')
  time.sleep(0.1)
  refreshGui()
 
  # Open and read cache of all packages
  cache.open()
  appendToLog('Apt cache read')

  # Parse the XML install file
  appendToLog('Parsing XML...')

  xmldoc = minidom.parse(xmlPath)

  # Declare arrays and get xml obj
  titleList = []
  xmlTitleListObj = xmldoc.getElementsByTagName('Title') 

  descriptionList = []
  xmlDescriptionListObj = xmldoc.getElementsByTagName('Description')
  
  installTitleList = []
  xmlInstallTitleListObj = xmldoc.getElementsByTagName('InstallTitle')
  
  ppaList = []
  xmlPpaListObj = xmldoc.getElementsByTagName('PPA')
  
  getAptKeyList = []
  xmlGetAptKeyObj = xmldoc.getElementsByTagName('GetAptKey')
 
  aptListEntryList = []
  xmlAptListEntryObj = xmldoc.getElementsByTagName('AptListEntry')

  preInstallList = []
  xmlPreInstallObj = xmldoc.getElementsByTagName('PreInstall')

  postInstallList = []
  xmlPostInstallObj = xmldoc.getElementsByTagName('PostInstall')

  minVersionList = []
  xmlMinVersionObj = xmldoc.getElementsByTagName('MinVersion')

  # Declare select box bool value array and progress
  selectBox = []
  progressBox = []
  installStateList = []

  itemCount = len(xmlTitleListObj)
  item=0
  realCount = 0
  
  # Create GTK ListStore
  menuItemStore = Gtk.ListStore(bool, str, str, int, GdkPixbuf.Pixbuf)

  appendToLog('Building ListStore')

  # Copy xml obj values to build arrays for easy reference of each item
  # and build liststore for Gtk 
  for item in range(itemCount):
    # Only add items that mach Ubuntu min version requirement
    minVerItem = getText(xmlMinVersionObj[item].childNodes)
    if distRelease >= minVerItem:
      # First item is the select box value
      # Check if software is installed here for each item before setting True
      # Also set progress to 100 if installed
      titleItem = getText(xmlTitleListObj[item].childNodes)
      softwareItem = getText(xmlInstallTitleListObj[item].childNodes)
      ppaItem = getText(xmlPpaListObj[item].childNodes)
      minVerItem = getText(xmlMinVersionObj[item].childNodes)
      
      # Add * for software requiring PPA
      #if ppaItem != '' :
      #  titleItem = titleItem + ' *'
  
      # Set checkbox ON if not installed
      if checkInstall(softwareItem):
        selectBox.append(False)
        progressValue = 0
        iconPathMod = iconPathOk
        installStateList.append('installed')
        
      else:
        selectBox.append(True)
        progressValue = 0
        iconPathMod = iconPathBlank
        installStateList.append('not-installed')
  
      # Build own arrays from xml 
      titleList.append(titleItem)
      descriptionList.append(getText(xmlDescriptionListObj[item].childNodes))
      installTitleList.append(softwareItem)
      ppaList.append(ppaItem)
      getAptKeyList.append(getText(xmlGetAptKeyObj[item].childNodes))
      aptListEntryList.append(getText(xmlAptListEntryObj[item].childNodes))
      preInstallList.append(getText(xmlPreInstallObj[item].childNodes))
      postInstallList.append(getText(xmlPostInstallObj[item].childNodes))
      minVersionList.append(minVerItem)
      
      # Build Progress blank array
      progressBox.append(progressValue)
          
      # Build listStore select list array at the same time
      menuItemStore.append([selectBox[realCount], titleList[realCount], descriptionList[realCount], progressBox[realCount], GdkPixbuf.Pixbuf.new_from_file(iconPathMod)])
      # using realCount to keep track of counters in the arrays 
      # because not all items are added the count goes out
      realCount = realCount + 1
      
  appendToLog('ListStore Created')
  
  # Kill Splash Screen
  splashWindow.destroy() 


  # Render menu items
  renderMainWindow()


  # Start GTK Main
  Gtk.main()


