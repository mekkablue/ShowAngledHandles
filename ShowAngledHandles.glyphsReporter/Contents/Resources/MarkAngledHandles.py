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
path = MainBundle.bundlePath() + "/Contents/Scripts"
if not path in sys.path:
	sys.path.append( path )

import GlyphsApp
GlyphsReporterProtocol = objc.protocolNamed( "GlyphsReporter" )

def subtractPoints( point1, point2 ):
	"""Returns point2 - point1."""
	try:
		return NSPoint( point2.x - point1.x, point2.y - point1.y )
	except Exception as e:
		print "subtractPoints subroutine:", str(e)
		return None

def intersectionWithNSPoints( pointA, pointB, pointC, pointD ):
	"""
	Returns an NSPoint of the intersection AB with CD.
	Or False if there is no intersection
	"""
	try:
		x1, y1 = pointA.x, pointA.y
		x2, y2 = pointB.x, pointB.y
		x3, y3 = pointC.x, pointC.y
		x4, y4 = pointD.x, pointD.y
		
		try:
			slope12 = ( float(y2) - float(y1) ) / ( float(x2) - float(x1) )
		except:
			# division by zero if vertical
			slope12 = None
			
		try:
			slope34 = ( float(y4) - float(y3) ) / ( float(x4) - float(x3) )
		except:
			# division by zero if vertical
			slope34 = None
		
		if slope12 == slope34:
			# parallel, no intersection
			return None
		elif slope12 is None:
			# first line is vertical
			x = x1
			y = slope34 * ( x - x3 ) + y3
		elif slope34 is None:
			# second line is vertical
			x = x3
			y = slope12 * ( x - x1 ) + y1
		else:
			# both lines have an angle
			x = ( slope12 * x1 - y1 - slope34 * x3 + y3 ) / ( slope12 - slope34 )
			y = slope12 * ( x - x1 ) + y1
			
		return NSPoint( x, y )
		
	except Exception as e:
		print "intersectionWithNSPoints subroutine:", str(e)
		return None

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
	
	def roundDotForPoint( self, thisPoint, markerWidth ):
		"""
		Returns a circle with thisRadius around thisPoint.
		"""
		try:
			myRect = NSRect( ( thisPoint.x - markerWidth * 0.5, thisPoint.y - markerWidth * 0.5 ), ( markerWidth, markerWidth ) )
			return NSBezierPath.bezierPathWithOvalInRect_(myRect)
		except Exception as e:
			self.logToConsole( "roundDotForPoint: %s" % str(e) )

	def drawCrossForPoint( self, thisPoint, firstOnCurve, secondOnCurve, zoomFactor ):
		"""
		Returns a circle with thisRadius around thisPoint.
		"""
		try:
			offset = 10.0
			leftX  = thisPoint.x - offset / zoomFactor
			rightX = thisPoint.x + offset / zoomFactor
			lowerY = thisPoint.y - offset / zoomFactor
			upperY = thisPoint.y + offset / zoomFactor
			
			# arms
			NSColor.yellowColor().set()
			NSBezierPath.strokeLineFromPoint_toPoint_( thisPoint, firstOnCurve )
			NSBezierPath.strokeLineFromPoint_toPoint_( thisPoint, secondOnCurve )
			
			# cross
			NSColor.orangeColor().set()
			NSBezierPath.strokeLineFromPoint_toPoint_( NSPoint(leftX,upperY), NSPoint(rightX,lowerY) )
			NSBezierPath.strokeLineFromPoint_toPoint_( NSPoint(leftX,lowerY), NSPoint(rightX,upperY) )
		except Exception as e:
			self.logToConsole( "drawCrossForPoint: %s" % str(e) )
	
	
	def getListOfHandleCrossings( self, thisLayer ):
		"""
		Returns a list of NSPoints where handles cross.
		"""
		try:
			returnList = []
			
			for thisPath in thisLayer.paths:
				theseNodes = thisPath.nodes
				pathLength = len( theseNodes )
				for thisNodeIndex in range(pathLength):
					if theseNodes[thisNodeIndex].type == 35: #GSCURVE
						pointA = theseNodes[  thisNodeIndex    % pathLength ].position
						pointB = theseNodes[ (thisNodeIndex-1) % pathLength ].position
						pointC = theseNodes[ (thisNodeIndex-2) % pathLength ].position
						pointD = theseNodes[ (thisNodeIndex-3) % pathLength ].position
						nsRectAB = NSRect( pointA, subtractPoints( pointA, pointB ) )
						nsRectCD = NSRect( pointD, subtractPoints( pointD, pointC ) )
						rectAB = NSBezierPath.bezierPathWithRect_( nsRectAB )
						rectCD = NSBezierPath.bezierPathWithRect_( nsRectCD )
						intersection = intersectionWithNSPoints( pointA, pointB, pointC, pointD )
						if intersection:
							if rectAB.containsPoint_(intersection) or rectCD.containsPoint_(intersection):
								returnList.append( [intersection, pointA, pointD] )
								
			return returnList
		except Exception as e:
			self.logToConsole( "getListOfHandleCrossings: %s" % str(e) )
			
	def getListOfAngledHandles( self, thisLayer ):
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
					
						if prevNode and prevNode.type != 65:
							if ( thisNode.x - prevNode.x ) * ( thisNode.y - prevNode.y ) != 0.0:
								returnList.append( thisNode )
						elif nextNode and nextNode.type != 65:
							if ( thisNode.x - nextNode.x ) * ( thisNode.y - nextNode.y ) != 0.0:
								returnList.append( thisNode )
							
			return returnList
		except Exception as e:
			self.logToConsole( "getListOfAngledHandles: %s" % str(e) )

	def getIndexListOfDuplicatePaths( self, thisLayer ):
		"""
		Returns a list of GSPaths that are exact duplicates of another.
		"""
		try:
			indexesOfDuplicates = []
			numberOfPaths = len(thisLayer.paths)
			for thisPathNumber in range( numberOfPaths ):
				if thisPathNumber < (numberOfPaths - 1):
					thisPath = thisLayer.paths[thisPathNumber]
					for thatPathNumber in range( thisPathNumber + 1, numberOfPaths ):
						thatPath = thisLayer.paths[thatPathNumber]
						if thisPath.pathDict() == thatPath.pathDict():
							indexesOfDuplicates.append( thatPathNumber )
			return indexesOfDuplicates
		except Exception as e:
			self.logToConsole( "getIndexListOfDuplicatePaths: %s" % str(e) )
			
	def markNonStraightLines( self, thisLayer, scaledLineWidth ):
		"""Draws NSBezierPaths for nonstraight lines."""
		try:
			for thisPath in thisLayer.paths:
				for i in range( len( thisPath.nodes )):
					thisNode = thisPath.nodes[ i ]
				
					if thisNode.type != 65: # on-curve
						prevNode = thisPath.nodes[ i-1 ]
					
						if prevNode and prevNode.type != 65:
							unstraightness = abs( thisNode.x - prevNode.x )
							unstraightnessY = abs( thisNode.y - prevNode.y )
							if unstraightness > unstraightnessY:
								unstraightness = unstraightnessY
							if unstraightness > 0.1 and unstraightness < 20.0:
								opacity = 3.0 / unstraightness
								if not opacity <= 1.0:
									opacity = 1.0 
								NSColor.colorWithCalibratedRed_green_blue_alpha_( 1.0, 0.5, 0.0, opacity ).set()
								myLine = GSPath()
								myLine.addNode_( prevNode.copy() )
								myLine.addNode_( thisNode.copy() )
								myLine.closed = False
								myOnscreenLine = self.bezierPathComp(myLine)
								myOnscreenLine.setLineCapStyle_( NSButtLineCapStyle )
								myOnscreenLine.setLineWidth_( scaledLineWidth )
								myOnscreenLine.stroke()
		except Exception as e:
			self.logToConsole( "markNonStraightLines: %s" % str(e) )
	
	def bezierPathComp( self, thisPath ):
		try:
			return thisPath.bezierPath() # until v2.2
		except Exception as e:
			return thisPath.bezierPath # v2.3+
	
	def markDuplicatePaths( self, thisLayer, zoomFactor ):
		"""Marks Duplicate Paths"""
		try:
			listOfIndexes = self.getIndexListOfDuplicatePaths( thisLayer )
			if listOfIndexes:
				duplicateMarker = NSBezierPath.alloc().init()
				
				for thisIndex in listOfIndexes:
					duplicatePathBezier = self.bezierPathComp( thisLayer.paths[thisIndex] )
					duplicateMarker.appendBezierPath_( duplicatePathBezier )
				
				duplicateMarker.setLineCapStyle_( NSRoundLineCapStyle )
				
				NSColor.purpleColor().set()
				duplicateMarker.setLineWidth_( 3.0/zoomFactor )
				duplicateMarker.setLineDash_count_phase_( [7.0/zoomFactor, 3.0/zoomFactor], 2, 3.5/zoomFactor )
				duplicateMarker.stroke()
				
				NSColor.yellowColor().set()
				duplicateMarker.setLineWidth_( 2.0/zoomFactor )
				duplicateMarker.setLineDash_count_phase_( [4.0/zoomFactor, 6.0/zoomFactor], 2, 2.0/zoomFactor )
				duplicateMarker.stroke()
				
		except Exception as e:
			self.logToConsole( "markDuplicatePaths: %s" % str(e) )
			
	def markCrossedHandles( self, thisLayer, zoomFactor ):
		"""Marks crossed handles"""
		try:
			NSBezierPath.setDefaultLineWidth_( 1.0 / zoomFactor )
			for theseThreePoints in self.getListOfHandleCrossings( thisLayer ):
				intersectionPoint = theseThreePoints[0]
				firstOnCurve = theseThreePoints[1]
				secondOnCurve = theseThreePoints[2]
				self.drawCrossForPoint( intersectionPoint, firstOnCurve, secondOnCurve, zoomFactor )
			
		except Exception as e:
			self.logToConsole( "markCrossedHandles: %s" % str(e) )
	
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
		
	# def markerForPoint( self, thisPoint, markerWidth ):
	# 	"""
	# 	Returns a circle with thisRadius around thisPoint.
	# 	"""
	# 	try:
	# 		myRect = NSRect( ( thisPoint.x - markerWidth * 0.5, thisPoint.y - markerWidth * 0.5 ), ( markerWidth, markerWidth ) )
	# 		return NSBezierPath.bezierPathWithOvalInRect_(myRect)
	# 	except Exception as e:
	# 		self.logToConsole( "markerForPoint: %s" % str(e) )
		
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
			zoomedHandleSize = HandleSize / Scale
			
			# mark angled handles:
			NSColor.colorWithCalibratedRed_green_blue_alpha_( 0.9, 0.1, 0.1, 0.7 ).set()
			redCircles = NSBezierPath.alloc().init()
			for thisPoint in self.getListOfAngledHandles( Layer ):
				redCircles.appendBezierPath_( self.roundDotForPoint( thisPoint, zoomedHandleSize ) )
			redCircles.fill()
			
			# mark duplicate paths:
			self.markDuplicatePaths( Layer, Scale )
		except Exception as e:
			self.logToConsole( "drawForegroundForLayer_: %s" % str(e) )
	
	def drawBackgroundForLayer_( self, Layer ):
		"""
		Whatever you draw here will be displayed BEHIND the paths.
		"""
		try:
			HandleSize = self.getHandleSize()
			Scale = self.getScale()
			zoomedHandleSize = HandleSize / Scale
			
			# mark slanted lines:
			self.markNonStraightLines( Layer, zoomedHandleSize )
			
			# mark crossed BCPs:
			self.markCrossedHandles( Layer, Scale )
		except Exception as e:
			self.logToConsole( "drawBackgroundForLayer_: %s" % str(e) )
		
	def drawBackgroundForInactiveLayer_( self, Layer ):
		"""
		Whatever you draw here will be displayed behind the paths, but for inactive masters.
		"""
		try:
			pass
		except Exception as e:
			self.logToConsole( "drawBackgroundForInactiveLayer_: %s" % str(e) )
		
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
