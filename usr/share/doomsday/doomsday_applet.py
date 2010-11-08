#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       countdown.py
#       
#       Copyright 2010 Tommy Brunn <tommy.brunn@gmail.com>
#       
#       Permission is hereby granted, free of charge, to any person obtaining a copy
#       of this software and associated documentation files (the "Software"), to deal
#       in the Software without restriction, including without limitation the rights
#       to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#       copies of the Software, and to permit persons to whom the Software is
#       furnished to do so, subject to the following conditions:
#
#       The above copyright notice and this permission notice shall be included in
#       all copies or substantial portions of the Software.
#
#       THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#       IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#       FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#       AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#       LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#       OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#       THE SOFTWARE.
#
#       I sincerely apologize for how ugly the following code is.

import os, sys
import pygtk
pygtk.require('2.0')
import gtk, gobject
import gnomeapplet

import ConfigParser

from datetime import datetime
from time import sleep
from math import floor
from math import ceil

class DoomsdayApplet(gnomeapplet.Applet):
	def __init__(self, applet, iid):
		
		#get the config file
		self.config = ConfigParser.ConfigParser()
		if os.getenv("XDG_CONFIG_HOME"):
			_config_dir = os.getenv("XDG_CONFIG_HOME")
		else:
			_config_dir = os.path.join(os.getenv("HOME"), ".config")
			_config_dir = os.path.join(_config_dir, "doomsday")
		
		if not os.path.exists(_config_dir):
			os.makedirs(_config_dir)
			
		self.configfile = os.path.join(_config_dir, "config.ini")
		
		self.applet = applet		
		
		#Initialize gtk.Builder and load our glade file
		self.builder = gtk.Builder()
		self.builder.add_from_file( os.path.join( os.path.abspath( os.path.dirname(sys.argv[0]) ), "ui.xml" ) )
		
		#get the objects we need from the glade file
		self.about = self.builder.get_object("aboutdialog")
		self.dateselect = self.builder.get_object("dateselect")
		
		#Create the label for our countdown
		self.label = gtk.Label()
		self.label.set_text("Click to add date")
		
		#We need to create an EventBox, because gtk.Image can't handle events
		self.eventbox = gtk.EventBox()
		self.eventbox.add(self.label)
		
		#Add a button release event to our EventBox
		self.eventbox.set_events(gtk.gdk.BUTTON_PRESS_MASK)
		
		#Add a helpful tooltip
		self.eventbox.set_tooltip_text("Drop a file here to upload")
		
		#Connect the signals with the callbacks
		self.builder.connect_signals(self)
		self.eventbox.connect("button_press_event", self.on_eventbox_clicked)
		self.eventbox.connect("destroy", gtk.main_quit)
		
		#Get the checkbutton
		self.checkbutton = self.builder.get_object("enablealarm")
		
		#Get the spinners and calendar
		self.hourspin = self.builder.get_object("hourspin")
		self.minutespin = self.builder.get_object("minutespin")
		self.secondspin = self.builder.get_object("secondspin")
		self.calendar = self.builder.get_object("calendar")
		
		## create a configuration file if it doesn't exist. If it does,
		## import the values appropriately
		self.config.read("self.configfile")
		self.read_config()
		
		
		#Create the menu
		self.create_menu(self.applet)
		
		#Add the eventbox to the applet
		self.applet.add(self.eventbox)
		self.applet.show_all()
		
		if self.checkbutton.get_active():
			self.update_countdown()
			gobject.timeout_add(30*1000, self.update_countdown)
		
	def set_target(self, year, month, day, hour, minute, second):
		"""Sets the date target to count down to."""
		try:
			self.target = self.target.replace(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
			print("New target is "+str(self.target))
		except AttributeError:
			self.target = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
	
	def on_enablealarm_toggled(self, obj):
		if obj.get_active():
			date = self.calendar.get_date()
			#Add one to the month because the calendar and the datetime
			#object count the months differently.
			self.set_target(date[0], self.get_month(), date[2], int(self.hourspin.get_value()), int(self.minutespin.get_value()), int(self.secondspin.get_value()))
			self.update_countdown()
			gobject.timeout_add(30*1000, self.update_countdown)
		else:
			self.label.set_text("Click to add date")
			
	def get_month(self):			
		return self.calendar.get_date()[1]+1
			
	def update_countdown(self):
		"""Updates the label if necessary, or notifies the user if the
		date has been reached."""
		
		# If the checkbutton isn't checked, do nothing.
		if not self.checkbutton.get_active():
			return False
		
		# If the checkbutton is checked, but the date has passed, let
		# the user know.
		if self.target < datetime.now():
			return self.reached_target()
		
		weeks, days, hours, minutes, seconds = self.calculate_remaining_time(self.target)
		
		s = ""

		if weeks > 0:
			s += str(int(weeks))+" week"
			if weeks > 1:
				s+="s"
		
		if days > 0:
			if weeks > 0:
				s +=", "
			s += str(int(days))+" day"
			if days > 1:
				s+="s"
		
		if hours > 0:
			if weeks > 0 or days > 0:
				s+=", "
			s += str(int(hours))+" hour"
			if hours > 1:
				s+="s"
		
		if minutes > 0:
			if weeks > 0 or days > 0 or hours > 0:
				s+=", "
			s += str(int(minutes))+" minute"
			if minutes > 1:
				 s+="s"
		
		if weeks == 0 and days == 0 and hours == 0 and minutes == 0:
			   s += str(int(seconds))+ " second"
			   if seconds > 1:
				   s+="s"
		
		self.label.set_text(s)
		return True
		
	def reached_target(self):
		self.label.set_text("Date reached!")
		return False
		
	def calculate_remaining_time(self, target):
		"""Returns remaining time in weeks, days, hours and minutes.
		Takes a datetime object as an argument."""
		diff = target-datetime.now()
		weeks = int(floor(diff.days/7))
		days = int(floor(diff.days-weeks*7))
		hours = int(floor(diff.seconds/60/60))
		minutes = int(floor(diff.seconds/60-hours*60))
		seconds = int(floor(diff.seconds-hours*60*60-minutes*60))
		
		return weeks, days, hours, minutes, seconds
	
	def create_menu(self, applet):
		xml="""<popup name="button3">
<menuitem name="dateset" 
          verb="SetDate" 
          label="_Set target date"/>
<menuitem name="ItemAbout" 
          verb="About" 
          label="_About" 
          pixtype="stock" 
          pixname="gtk-about"/>
</popup>"""
		
		verbs = [("About", self.show_about), ("SetDate", self.show_dateselect)]
		applet.setup_menu(xml, verbs, None)
		
	def on_eventbox_clicked(self, obj, label, *data):
		'''Callback for when someone clicks on the applet'''
		if label.button == 1:
			self.show_dateselect(obj, label)
			
	def show_dateselect(self, obj, label, *data):
		self.dateselect.show()
		
	def on_dateselect_close(self, widget, *data):
		'''Updates and stores values when the dateselect window is closed.'''
		date = self.calendar.get_date()
		self.set_target(date[0], self.get_month(), date[2], int(self.hourspin.get_value()), int(self.minutespin.get_value()), int(self.secondspin.get_value()))
		self.write_config()
		self.dateselect.hide()
		self.on_enablealarm_toggled(self.checkbutton)
		return True
		
	def show_about(self, obj, label, *data):
		#Create our About window
		self.about.show()
		
	def on_aboutdialog_close(self, widget, *data):
		self.about.hide()
		return True #Prevents the window from being destroyed if the X button was clicked
		
	def config_section_map(self, section):
		'''Method for fetching and setting options in an ini file.'''
		dict1 = {}
		options = self.config.options(section)
		for option in options:
			try:
				dict1[option] = self.config.get(section, option)
				if dict1[option] == -1:
					DebugPrint("skip: %s" % option)
			except:
				print("exception on %s!" % option)
				dict1[option] = ""
		return dict1
		
	def read_config(self):
		'''Reads the configuration file. Creates one if necessary.'''
		
		if not os.path.isfile(self.configfile):
			self.create_config()
			return
		
		# This only reads it into memory. It doesnt' actually set the
		# values.
		self.config.read(self.configfile)

		# Contrary to the information in the pygtk docs, checkbuttons 
		# only seem to take 1 or 0, not boolean values.
		if self.config_section_map("TargetSettings")["enabled"]:
			self.checkbutton.set_active(1)
		else:
			self.checkbutton.set_active(0)

		self.hourspin.set_value(float(self.config_section_map("TargetSettings")["hour"]))
		self.minutespin.set_value(float(self.config_section_map("TargetSettings")["minute"]))
		self.secondspin.set_value(float(self.config_section_map("TargetSettings")["second"]))
		
		# Because of the inconsistency between the calendar and the
		# datetime object, we have to futz about a little with the values.
		month = int(self.config_section_map("TargetSettings")["month"])
		if month == 12:
			month = 0
		else:
			month-=1
		
		self.calendar.select_month(month, int(self.config_section_map("TargetSettings")["year"]))
		self.calendar.select_day(int(self.config_section_map("TargetSettings")["day"]))
		
		self.set_target(int(self.config_section_map("TargetSettings")["year"]), int(self.config_section_map("TargetSettings")["month"]), int(self.config_section_map("TargetSettings")["day"]), int(self.config_section_map("TargetSettings")["hour"]), int(self.config_section_map("TargetSettings")["minute"]), int(self.config_section_map("TargetSettings")["second"]))
		
	def write_config(self):
		'''Updates the configuration file.'''
		cfgfile = open(self.configfile, "w")
		
		self.config.set("TargetSettings", "enabled", str(self.checkbutton.get_active()))
		self.config.set("TargetSettings", "hour", int(self.hourspin.get_value()))
		self.config.set("TargetSettings", "minute", int(self.minutespin.get_value()))
		self.config.set("TargetSettings", "second", int(self.secondspin.get_value()))
		
		date = self.calendar.get_date()
		
		self.config.set("TargetSettings", "year", date[0])
		self.config.set("TargetSettings", "month", self.get_month())
		self.config.set("TargetSettings", "day", date[2])

		self.config.write(cfgfile)
		cfgfile.close()
		
	def create_config(self):
		'''Creates a configuration file at ~/.config/doomsday/config.ini'''
		
		cfgfile = open(self.configfile, "w")
		self.config.add_section("TargetSettings")
		now = datetime.now()
		self.config.set("TargetSettings", "enabled", 'False')
		self.config.set("TargetSettings", "hour", now.hour)
		self.config.set("TargetSettings", "minute", now.minute)
		self.config.set("TargetSettings", "second", now.second)
		
		self.config.set("TargetSettings", "year", now.year)
		self.config.set("TargetSettings", "month", now.month)
		self.config.set("TargetSettings", "day", now.day)

		self.config.write(cfgfile)
		cfgfile.close()

def applet_factory(applet, iid):
	DoomsdayApplet(applet, iid)
	return gtk.TRUE
	
if __name__ == '__main__':
	print("Starting factory")
	if len(sys.argv) > 1 and sys.argv[1] == '-d': # debugging
		mainWindow = gtk.Window()
		mainWindow.set_title('Applet window')
		mainWindow.connect('destroy', gtk.main_quit)
		applet = gnomeapplet.Applet()
		applet_factory(applet, None)
		applet.reparent(mainWindow)
		mainWindow.show_all()
		gtk.main()
		sys.exit()
	else:
		gnomeapplet.bonobo_factory("OAFIID:Doomsday_Factory", gnomeapplet.Applet.__gtype__, "Countdown to date and time", "0.1", applet_factory)

