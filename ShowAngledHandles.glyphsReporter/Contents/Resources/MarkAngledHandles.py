#!/usr/bin/env python
# encoding: utf-8

"""
Copyright 2013 Rainer Erich Scheichelbauer (@mekkablue).
Based on a Template by Georg Seifert (@schriftgestalt).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0
"""

import objc
from Foundation import *
from AppKit import *
import sys, os, re

MainBundle = NSBundle.mainBundle()
path = MainBundle.bundlePath()+"/Contents/Scripts"
if not path in sys.path:
	sys.path.append(path)

import GlyphsApp

GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

class AngledHandlesReporter ( NSObject, GlyphsReporterProtocol ):
	
	def init( self ):
		return self
	
	def title( self ):
		"""
		This is the title of the trigger as it appears in the menu in combination with 'Show'.
		"""
		return "Angled Handles"
		
	def interfaceVersion( self ):
		"""
		Must return 1.
		"""
		try:
			return 1
		except Exception as e:
			self.logToConsole( "interfaceVersion: %s" % str(e) )
		
	def keyEquivalent( self ):
		"""
		The key for the keyboard shortcut.
		Set modifier keys in modifierMask() further below.
		Pretty tricky to find a shortcut that is not taken yet, be careful.
		If you are not sure, use 'return None', to let the users set their own shortcuts in System Prefs.
		"""
		try:
			return "y"
		except Exception as e:
			self.logToConsole( "keyEquivalent: %s" % str(e) )
		
	def modifierMask( self ):
		"""
		Use any combination of these to determine the modifier keys for your default shortcut:
		return NSShiftKeyMask | NSControlKeyMask | NSCommandKeyMask | NSAlternateKeyMask
		Or: return 0. Must return something.
		"""
		try:
			return NSCommandKeyMask
		except Exception as e:
			self.logToConsole( "modifierMask: %s" % str(e) )
		
	def getListOfNodesToBeMarked( self, thisLayer ):
		"""
		Returns a list of all BCPs on thisLayer that are not straight.
		"""
		try:
			returnList = []
		
			for thisPath in thisLayer.paths:
				for i in range( len( thisPath.nodes )):
					thisNode = thisPath.nodes[ i ]
				
					if thisNode.type == 65: # BCP
						prevNode = thisPath.nodes[ i-1 ]
						nextNode = thisPath.nodes[ i+1 ]
					
						if prevNode.type != 65:
							if ( thisNode.x - prevNode.x ) * ( thisNode.y - prevNode.y ) != 0.0:
								returnList.append( thisNode )
						elif nextNode.type != 65:
							if ( thisNode.x - nextNode.x ) * ( thisNode.y - nextNode.y ) != 0.0:
								returnList.append( thisNode )
							
			return returnList
		except Exception as e:
			self.logToConsole( "getListOfNodesToBeMarked: %s" % str(e) )
		
	def markerForPoint( self, thisPoint, markerWidth ):
		"""
		Returns a circle with thisRadius around thisPoint.
		"""
		try:
			myRect = NSRect( ( thisPoint.x - markerWidth * 0.5, thisPoint.y - markerWidth * 0.5 ), ( markerWidth, markerWidth ) )
			return NSBezierPath.bezierPathWithOvalInRect_(myRect)
		except Exception as e:
			self.logToConsole( "markerForPoint: %s" % str(e) )
		
	def getScale( self ):
		"""
		Returns the current scale factor of the Edit View UI.
		Divide any scalable size by this value in order to keep the same pixel size.
		"""
		try:
			return self.controller.graphicView().scale()
		except:
			self.logToConsole( "getScale error: Scale defaulting to 1.0. %s" % str(e) )
			return 1.0
	
	def getHandleSize( self ):
		"""
		Returns the current handle size as set in user preferences.
		"""
		try:
			Selected = NSUserDefaults.standardUserDefaults().integerForKey_( "GSHandleSize" )
			if Selected == 0:
				return 5.0
			elif Selected == 2:
				return 10.0
			else:
				return 7.0 # Regular
		except Exception as e:
			self.logToConsole( "getHandleSize: HandleSize defaulting to 7.0. %s" % str(e) )
			return 7.0
		
	def drawForegroundForLayer_( self, Layer ):
		"""
		Whatever you draw here will be displayed IN FRONT OF the paths.
		"""
		try:
			HandleSize = self.getHandleSize()
			Scale = self.getScale() 
			NSColor.colorWithCalibratedRed_green_blue_alpha_( 0.9, 0.1, 0.1, 0.7 ).set()
			
			redCircles = NSBezierPath.alloc().init()
			for thisPoint in self.getListOfNodesToBeMarked( Layer ):
				redCircles.appendBezierPath_( self.markerForPoint( thisPoint, HandleSize / Scale ) )
				
			redCircles.fill()
		except Exception as e:
			self.logToConsole( "drawForegroundForLayer_: %s" % str(e) )
			
	def drawBackgroundForLayer_( self, Layer ):
		"""
		Whatever you draw here will be displayed BEHIND the paths.
		"""
		pass
		
	def drawBackgroundForInactiveLayer_( self, Layer ):
		"""
		Whatever you draw here will be displayed behind the paths, but for inactive masters.
		"""
		pass
		
	def setController_( self, Controller ):
		"""
		Use self.controller as object for the current view controller.
		"""
		try:
			self.controller = Controller
		except Exception as e:
			self.logToConsole( "setController_: Could not set controller. %s" % str(e) )

	def logToConsole( self, message ):
		"""
		The variable message will be passed to Console.app.
		Use self.logToConsole("bla bla") for debugging.
		"""
		myLog = "Show %s plugin:\n%s" % ( self.title(), message )
		NSLog( myLog )
