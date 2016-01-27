# encoding: utf-8

###########################################################################################################
#
#
#	Reporter Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#
#
###########################################################################################################


from GlyphsPlugins import *

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


class ShowAngledHandles(ReporterPlugin):

	def settings(self):
		self.menuName = Glyphs.localize({'en': 'Angled Handles', 'de': u'Schräge Anfasser'})
		self.keyboardShortcut = "y"
		self.keyboardShortcutModifier = NSCommandKeyMask
		
	def foreground(self, layer):
		HandleSize = self.getHandleSize()
		Scale = self.getScale()
		zoomedHandleSize = HandleSize / Scale
		
		# mark angled handles:
		NSColor.colorWithCalibratedRed_green_blue_alpha_( 0.9, 0.1, 0.1, 0.7 ).set()
		redCircles = NSBezierPath.alloc().init()
		listOfAngledHandles = self.getListOfAngledHandles( layer )
		for thisPoint in listOfAngledHandles:
			redCircles.appendBezierPath_( self.roundDotForPoint( thisPoint, zoomedHandleSize ) )
		redCircles.fill()
		
		# mark duplicate paths:
		self.markDuplicatePaths( layer, Scale )
	
	def background(self, layer):
		HandleSize = self.getHandleSize()
		scale = self.getScale()
		zoomedHandleSize = HandleSize / scale
		
		# mark slanted lines:
		self.markNonStraightLines( layer, zoomedHandleSize )
		
		# mark crossed BCPs:
		self.markCrossedHandles( layer, scale )
		
		# mark zero handles:
		NSColor.colorWithCalibratedRed_green_blue_alpha_( 0.7, 0.1, 0.9, 0.7 ).set()
		purpleCircles = NSBezierPath.alloc().init()
		listOfZeroHandles = self.getListOfZeroHandles( layer )
		for thisPoint in listOfZeroHandles:
			purpleCircles.appendBezierPath_( self.roundDotForPoint( thisPoint, zoomedHandleSize*2 ) )
		purpleCircles.fill()
		
		
	def roundDotForPoint( self, thisPoint, markerWidth ):
		"""
		Returns a circle with thisRadius around thisPoint.
		"""
		myRect = NSRect( ( thisPoint.x - markerWidth * 0.5, thisPoint.y - markerWidth * 0.5 ), ( markerWidth, markerWidth ) )
		return NSBezierPath.bezierPathWithOvalInRect_(myRect)
		
	def drawCrossForPoint( self, thisPoint, firstOnCurve, secondOnCurve, zoomFactor ):
		"""
		Returns a circle with thisRadius around thisPoint.
		"""
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

	def getListOfHandleCrossings( self, thisLayer ):
		"""
		Returns a list of NSPoints where handles cross.
		"""
		returnList = []
		
		for thisPath in thisLayer.paths:
			theseNodes = thisPath.nodes
			pathLength = len( theseNodes )
			for thisNodeIndex in range(pathLength):
				if theseNodes[thisNodeIndex].type == GSCURVE: #GSCURVE
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
			
	def getListOfAngledHandles( self, thisLayer ):
		"""
		Returns a list of all BCPs on thisLayer that are not straight.
		"""
		returnList = []
	
		for thisPath in thisLayer.paths:
			for i in range( len( thisPath.nodes )):
				thisNode = thisPath.nodes[ i ]
			
				if thisNode.type == GSOFFCURVE: # BCP
					prevNode = thisPath.nodes[ i-1 ]
					nextNode = thisPath.nodes[ i+1 ]
				
					if prevNode and prevNode.type != GSOFFCURVE:
						if ( thisNode.x - prevNode.x ) * ( thisNode.y - prevNode.y ) != 0.0:
							returnList.append( thisNode )
					elif nextNode and nextNode.type != GSOFFCURVE:
						if ( thisNode.x - nextNode.x ) * ( thisNode.y - nextNode.y ) != 0.0:
							returnList.append( thisNode )
						
		return returnList

	def getIndexListOfDuplicatePaths( self, thisLayer ):
		"""
		Returns a list of GSPaths that are exact duplicates of another.
		"""
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
			
	def markNonStraightLines( self, thisLayer, scaledLineWidth ):
		"""Draws NSBezierPaths for nonstraight lines."""
		for thisPath in thisLayer.paths:
			for i in range( len( thisPath.nodes )):
				thisNode = thisPath.nodes[ i ]
				if thisNode.type != GSOFFCURVE: # on-curve
					prevNode = thisPath.nodes[ i-1 ]
					if prevNode and prevNode.type != GSOFFCURVE:
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
							myOnscreenLine = myLine.bezierPath
							myOnscreenLine.setLineCapStyle_( NSButtLineCapStyle )
							myOnscreenLine.setLineWidth_( scaledLineWidth )
							myOnscreenLine.stroke()
	
	def markDuplicatePaths( self, thisLayer, zoomFactor ):
		"""Marks Duplicate Paths"""
		listOfIndexes = self.getIndexListOfDuplicatePaths( thisLayer )
		if listOfIndexes:
			duplicateMarker = NSBezierPath.alloc().init()
			
			for thisIndex in listOfIndexes:
				duplicatePathBezier = thisLayer.paths[thisIndex].bezierPath
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
			
	def markCrossedHandles( self, thisLayer, zoomFactor ):
		"""Marks crossed handles"""
		NSBezierPath.setDefaultLineWidth_( 1.0 / zoomFactor )
		for theseThreePoints in self.getListOfHandleCrossings( thisLayer ):
			intersectionPoint = theseThreePoints[0]
			firstOnCurve = theseThreePoints[1]
			secondOnCurve = theseThreePoints[2]
			self.drawCrossForPoint( intersectionPoint, firstOnCurve, secondOnCurve, zoomFactor )
	
	def getListOfZeroHandles(self, thisLayer):
		"""Returns a list of all BCPs that are retracted into the neares oncurve point."""
		returnList = []
		for thisPath in thisLayer.paths:
			for i in range(len(thisPath.nodes)):
				thisNode = thisPath.nodes[i]
				if thisNode.type == GSOFFCURVE:
					prevNode = thisPath.nodes[ i-1 ]
					nextNode = thisPath.nodes[ i+1 ]
					if prevNode.type != GSOFFCURVE:
						if prevNode.position == thisNode.position:
							returnList.append( thisNode )
					elif nextNode.type != GSOFFCURVE:
						if nextNode.position == thisNode.position:
							returnList.append( thisNode )
		return returnList
	
	def getListOfAngledHandles( self, thisLayer ):
		"""
		Returns a list of all BCPs on thisLayer that are not straight.
		"""
		returnList = []
		for thisPath in thisLayer.paths:
			for i in range( len( thisPath.nodes )):
				thisNode = thisPath.nodes[ i ]
				if thisNode.type == GSSOFFCURVE # BCP
					prevNode = thisPath.nodes[ i-1 ]
					nextNode = thisPath.nodes[ i+1 ]
					if prevNode.type != GSOFFCURVE:
						if ( thisNode.x - prevNode.x ) * ( thisNode.y - prevNode.y ) != 0.0:
							returnList.append( thisNode )
					elif nextNode.type != GSOFFCURVE:
						if ( thisNode.x - nextNode.x ) * ( thisNode.y - nextNode.y ) != 0.0:
							returnList.append( thisNode )
		return returnList

