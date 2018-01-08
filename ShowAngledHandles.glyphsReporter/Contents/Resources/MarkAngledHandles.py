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
import sys, os, re
from GlyphsApp import OFFCURVE
from GlyphsApp.plugins import *
GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

class AngledHandlesReporter ( NSObject, GlyphsReporterProtocol ):
	
	def init( self ):
		"""
		Unless you know what you are doing, leave this at "return self".
		"""
		# Bundle = NSBundle.bundleForClass_( NSClassFromString( self.className() ));
		return self
	
	def title( self ):
		"""
		This is the title of the trigger as it appears in the menu in combination with 'Show'.
		E.g. return "Nodes" will 
		"""
		return "Angled Handles"
		
	def interfaceVersion( self ):
		"""
		Must return 1.
		"""
		return 1
		
	def groupID( self ):
		"""
		Determines the position in the toolbar if you have a toolbar icon.
		"""
		return 100
		
	def keyEquivalent( self ):
		"""
		The key for the keyboard shortcut.
		Set modifier keys in modifierMask() further below.
		Pretty tricky to find a shortcut that is not taken yet, be careful.
		If you are not sure, use 'return None', to let the users set their own shortcuts in System Prefs.
		"""
		return "y"
		
	def modifierMask( self ):
		"""
		Use any combination of these to determine the modifier keys for your default shortcut:
		return NSShiftKeyMask | NSControlKeyMask | NSCommandKeyMask | NSAlternateKeyMask
		Or: return 0. Must return something.
		"""
		return NSCommandKeyMask
		
	def logToConsole( self, message ):
		"""
		The variable message will be passed to Console.app.
		Use self.logToConsole("bla bla") for debugging.
		"""
		myLog = "Show %s plugin:\n%s" % ( self.title(), message )
		NSLog( myLog )
	
	def getListOfNodesToBeMarked( self, thisLayer ):
		"""
		Returns a list of all BCPs on thisLayer that are not straight.
		"""
		returnList = []
		
		for thisPath in thisLayer.paths:
			for i in range( len( thisPath.nodes )):
				thisNode = thisPath.nodes[ i ]
				
				if thisNode.type == 65:
					prevNode = thisPath.nodes[ i-1 ]
					nextNode = thisPath.nodes[ i+1 ]
					
					if prevNode.type != 65:
						if ( thisNode.x - prevNode.x ) * ( thisNode.y - prevNode.y ) != 0.0:
							returnList.append( thisNode )
					elif nextNode.type != 65:
						if ( thisNode.x - nextNode.x ) * ( thisNode.y - nextNode.y ) != 0.0:
							returnList.append( thisNode )
							
		return returnList
		
	def markerForPoint( self, thisPoint, markerWidth ):
		"""
		Returns a circle with thisRadius around thisPoint.
		"""
		myRect = NSRect( ( thisPoint.x - markerWidth * 0.5, thisPoint.y - markerWidth * 0.5 ), ( markerWidth, markerWidth ) )
		return NSBezierPath.bezierPathWithOvalInRect_(myRect)
		
	def getScale( self ):
		"""
		Returns the current scale factor of the Edit View UI.
		Divide any scalable size by this value in order to keep the same pixel size.
		"""
		try:
			return self.controller.graphicView().scale()
		except:
			self.logToConsole( "Scale defaulting to 1.0" )
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
		except:
			self.logToConsole( "HandleSize defaulting to 7.0" )
			return 7.0
		
	def drawForegroundForLayer_( self, Layer ):
		"""
		Whatever you draw here will be displayed IN FRONT OF the paths.
		Setting a color:
			NSColor.colorWithCalibratedRed_green_blue_alpha_( 1.0, 1.0, 1.0, 1.0 ).set() # sets RGBA values between 0.0 and 1.0
			NSColor.redColor().set() # predefined colors: blackColor, blueColor, brownColor, clearColor, cyanColor, darkGrayColor, grayColor, greenColor, lightGrayColor, magentaColor, orangeColor, purpleColor, redColor, whiteColor, yellowColor
		Drawing a path:
			myPath = NSBezierPath.alloc().init()  # initialize a path object myPath
			myPath.appendBezierPath_( subpath )   # add subpath to myPath
			myPath.fill()   # fill myPath with the current NSColor
			myPath.stroke() # stroke myPath with the current NSColor
		See:
		https://developer.apple.com/library/mac/documentation/Cocoa/Reference/ApplicationKit/Classes/NSBezierPath_Class/Reference/Reference.html
		https://developer.apple.com/library/mac/documentation/cocoa/reference/applicationkit/classes/NSColor_Class/Reference/Reference.html
		"""
		
		try:
			HandleSize = self.getHandleSize()
			Scale = self.getScale() 
			# NSColor.redColor().set()
			NSColor.colorWithCalibratedRed_green_blue_alpha_( 0.9, 0.1, 0.1, 0.7 ).set()
			
			redCircles = NSBezierPath.alloc().init()
			
			for thisPoint in self.getListOfNodesToBeMarked( Layer ):
				redCircles.appendBezierPath_( self.markerForPoint( thisPoint, HandleSize / Scale ) )
				
			redCircles.fill()
			
		except Exception as e:
			self.logToConsole( str(e) )
			
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
		self.controller = Controller
