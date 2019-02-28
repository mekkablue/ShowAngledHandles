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


import math
from GlyphsApp import OFFCURVE, GSCURVE, GSPath
from GlyphsApp.plugins import *
from AppKit import NSRoundLineCapStyle

def angleBetweenPoints( firstPoint, secondPoint ):
	"""
	Returns the angle (in degrees) of the straight line between firstPoint and secondPoint,
	0 degrees being the second point to the right of first point.
	firstPoint, secondPoint: must be NSPoint or GSNode
	"""
	xDiff = secondPoint.x - firstPoint.x
	yDiff = secondPoint.y - firstPoint.y
	return math.degrees(math.atan2(yDiff,xDiff))

def subtractPoints( point1, point2 ):
	"""
	Returns point2 - point1.
	"""
	return NSPoint( point2.x - point1.x, point2.y - point1.y )

def intersect( pointA, pointB, pointC, pointD ):
	"""
	Returns an NSPoint of the intersection AB with CD,
	or None if there is no intersection.
	pointA, pointB: NSPoints representing the first line AB,
	pointC, pointD: NSPoints representing the second line CD.
	"""
	try:
		x1, y1 = pointA
		x2, y2 = pointB
		x3, y3 = pointC
		x4, y4 = pointD
		xtop = (x4-x3)*(x2*y1-x1*y2)-(x2-x1)*(x4*y3-x3*y4)
		ytop = (y1-y2)*(x4*y3-x3*y4)-(y3-y4)*(x2*y1-x1*y2)
		divisor = (y4-y3)*(x2-x1)-(y2-y1)*(x4-x3)
		x = xtop/divisor
		y = ytop/divisor
		return NSPoint( x, y )
	except:
		return None

class ShowAngledHandles(ReporterPlugin):

	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Angled Handles',
			'de': u'Schräge Anfasser',
			'es': u'manejadores inclinados',
			'fr': u'les poignées inclinées',
			'zh': u'⚖️路径检查工具',
		})
		
		Glyphs.registerDefault("com.mekkablue.ShowAngledHandles.keyboardShortcut", "y")
		Glyphs.registerDefault("com.mekkablue.ShowAngledHandles.zeroHandles", True)
		Glyphs.registerDefault("com.mekkablue.ShowAngledHandles.almostStraightLines", True)
		Glyphs.registerDefault("com.mekkablue.ShowAngledHandles.laserBeams", True)
		Glyphs.registerDefault("com.mekkablue.ShowAngledHandles.duplicatePaths", True)
		Glyphs.registerDefault("com.mekkablue.ShowAngledHandles.onlyShowCloseToStraightHandles", False)
		
		self.keyboardShortcut = Glyphs.defaults["com.mekkablue.ShowAngledHandles.keyboardShortcut"]
		self.keyboardShortcutModifier = NSCommandKeyMask
	
	def conditionsAreMetForDrawing(self):
		"""
		Don't activate if text or pan (hand) tool are active.
		"""
		currentController = self.controller.view().window().windowController()
		if currentController:
			tool = currentController.toolDrawDelegate()
			textToolIsActive = tool.isKindOfClass_( NSClassFromString("GlyphsToolText") )
			handToolIsActive = tool.isKindOfClass_( NSClassFromString("GlyphsToolHand") )
			if not textToolIsActive and not handToolIsActive: 
				return True
		return False
	
	def foreground(self, layer):
		if self.conditionsAreMetForDrawing():
			
			# mark angled handles:
			self.drawAngledHandles( layer )
			
			# mark duplicate path segments:
			if Glyphs.defaults["com.mekkablue.ShowAngledHandles.duplicatePaths"]:
				self.markDuplicateSegments( layer, self.getScale() )
	
	def background(self, layer):
		if self.conditionsAreMetForDrawing():
			zoomedHandleSize = self.zoomedHandleSize()
			
			# mark slanted lines:
			if Glyphs.defaults["com.mekkablue.ShowAngledHandles.almostStraightLines"]:
				self.markNonStraightLines( layer, zoomedHandleSize*0.7 )
			
			# mark crossed BCPs:
			if Glyphs.defaults["com.mekkablue.ShowAngledHandles.laserBeams"]:
				self.markCrossedHandles( layer, self.getScale() )
			
			# mark zero handles:
			if Glyphs.defaults["com.mekkablue.ShowAngledHandles.zeroHandles"]:
				self.markZeroHandles( layer, zoomedHandleSize*2 )
	
	def zoomedHandleSize(self):
		"""
		Returns the proper handle size according to user settings:
		Glyphs > Preferences > User Preferences > Handle Size
		"""
		handleSizes = (5, 8, 12)
		handleSizeIndex = Glyphs.handleSize 
		handleSize = handleSizes[handleSizeIndex]*self.getScale()**-0.9 # scaled diameter
		return handleSize
	
	def drawAngledHandles(self, thisLayer):
		"""
		Marks all BCPs on thisLayer that are not straight.
		"""
		NSColor.colorWithCalibratedRed_green_blue_alpha_( 1.0, 0.1, 0.1, 0.6 ).set()
		for thisPath in thisLayer.paths:
			for thisNode in thisPath.nodes:
				if thisNode.type == OFFCURVE: # BCP
					# determine other node for angle measurement:
					otherNode = None
					if thisNode.prevNode.type != OFFCURVE:
						otherNode = thisNode.prevNode
					elif thisNode.nextNode.type != OFFCURVE:
						otherNode = thisNode.nextNode
					if otherNode:
						if ( thisNode.x - otherNode.x ) * ( thisNode.y - otherNode.y ) != 0.0:
							if not Glyphs.defaults["com.mekkablue.ShowAngledHandles.onlyShowCloseToStraightHandles"]:
								self.drawHandleForNode( thisNode )
							else:
								angle = angleBetweenPoints( thisNode, otherNode ) % 90.0
								diffX = abs(thisNode.x - otherNode.x)
								diffY = abs(thisNode.y - otherNode.y)
								almostStraight = diffX <= 2.0 or diffY <= 2.0 or angle < 8.0 or angle > 82.0
								if almostStraight:
									self.drawHandleForNode( thisNode )
	
	def drawHandleForNode(self, node):
		"""
		Draws a BCP dot in the correct size.
		"""
		# calculate handle size:
		handleSize = self.zoomedHandleSize()
		
		# offcurves are a little smaller:
		if node.type == OFFCURVE:
			handleSize *= 0.8
	
		# selected handles are a little bigger:
		if node.selected:
			handleSize *= 1.45
	
		# draw disc inside a rectangle around point position:
		dot = self.roundDotForPoint(node.position, handleSize)
		dot.fill()
	
	def roundDotForPoint( self, thisPoint, markerWidth ):
		"""
		Returns a circle with thisRadius around thisPoint.
		"""
		myRect = NSRect( 
			( thisPoint.x-markerWidth*0.5, thisPoint.y-markerWidth*0.5 ), # origin
			( markerWidth, markerWidth ), # size
		)
		return NSBezierPath.bezierPathWithOvalInRect_(myRect)
		
	def drawCrossForPoint( self, thisPoint, firstOnCurve, secondOnCurve, zoomFactor, smoothHandle=False ):
		"""
		Draws a laser beam and an intersection cross for handles that are too long, 
		or a dotted indicator line for max handles.
		"""
		# arms (beams):
		arms = NSBezierPath.bezierPath()
		arms.moveTo_(thisPoint)
		arms.lineTo_(firstOnCurve)
		arms.moveTo_(thisPoint)
		arms.lineTo_(secondOnCurve)
		arms.setLineCapStyle_(NSRoundLineCapStyle)
		arms.setLineWidth_(1.0/zoomFactor)
		if smoothHandle:
			arms.setLineDash_count_phase_( (2.0/zoomFactor, 3.0/zoomFactor), 2, 0 )
			NSColor.grayColor().set()
		else:
			NSColor.yellowColor().set()
		arms.stroke()
		
		# cross (intersection):
		if not smoothHandle:
			NSColor.orangeColor().set()
			offset = 10.0
			leftX  = thisPoint.x - offset / zoomFactor
			rightX = thisPoint.x + offset / zoomFactor
			lowerY = thisPoint.y - offset / zoomFactor
			upperY = thisPoint.y + offset / zoomFactor
			cross = NSBezierPath.bezierPath()
			cross.moveTo_(NSPoint(leftX,upperY))
			cross.lineTo_(NSPoint(rightX,lowerY))
			cross.moveTo_(NSPoint(leftX,lowerY))
			cross.lineTo_(NSPoint(rightX,upperY))
			cross.setLineCapStyle_(NSRoundLineCapStyle)
			cross.setLineWidth_(1.0/zoomFactor)
			cross.stroke()

	def markNonStraightLines( self, thisLayer, scaledLineWidth ):
		"""
		Draws an indicator for nonstraight lines.
		Opacity depends on deviation from straight (h/v) position.
		"""
		for thisPath in thisLayer.paths:
			for thisNode in thisPath.nodes:
				if thisNode.type != OFFCURVE: # on-curve
					prevNode = thisNode.prevNode
					if prevNode and prevNode.type != OFFCURVE:
						unstraightness = abs( thisNode.x - prevNode.x )
						unstraightnessY = abs( thisNode.y - prevNode.y )
						if unstraightness > unstraightnessY:
							unstraightness = unstraightnessY
						if unstraightness > 0.1 and unstraightness < 20.0:
							opacity = 3.0 / unstraightness
							if not opacity <= 1.0:
								opacity = 1.0 
							NSColor.colorWithCalibratedRed_green_blue_alpha_( 1.0, 0.5, 0.0, opacity ).set()
							lineMarker = NSBezierPath.bezierPath()
							lineMarker.moveTo_( prevNode.position )
							lineMarker.lineTo_( thisNode.position )
							lineMarker.setLineCapStyle_( NSRoundLineCapStyle )
							lineMarker.setLineWidth_( scaledLineWidth )
							lineMarker.stroke()
	
	def markDuplicateSegments(self, thisLayer, zoomFactor):
		"""
		Collect identical segments and mark them.
		"""
		segments = []
		for p in thisLayer.paths:
			for s in p.segments:
				segments.append(s)

		duplicates = []
		for i, s1 in enumerate(segments):
			for j, s2 in enumerate(segments[i+1:]):
				if s1 not in duplicates and s1 in (s2, s2[::-1]):
					duplicates.append(s1)
		
		if duplicates:
			duplicateMarker = NSBezierPath.bezierPath()
			for segment in duplicates:
				duplicateMarker.moveToPoint_(
					segment[0].pointValue(),
				)
				if len(segment) == 2:
					duplicateMarker.lineToPoint_(
						segment[1].pointValue(),
					)
				else:
					duplicateMarker.curveToPoint_controlPoint1_controlPoint2_(
						segment[3].pointValue(),
						segment[1].pointValue(),
						segment[2].pointValue(),
					)
			NSColor.purpleColor().set()
			duplicateMarker.setLineWidth_( 3.0/zoomFactor )
			duplicateMarker.stroke()
			
			NSColor.yellowColor().set()
			duplicateMarker.setLineWidth_( 2.0/zoomFactor )
			duplicateMarker.setLineDash_count_phase_( [4.0/zoomFactor, 6.0/zoomFactor], 2, 2.0/zoomFactor )
			duplicateMarker.stroke()

	def markCrossedHandles( self, thisLayer, zoomFactor ):
		"""
		Marks crossed handles.
		"""
		for thisPath in thisLayer.paths:
			for thisNode in thisPath.nodes:
				if thisNode.type == GSCURVE:
					pointA = thisNode.position
					pointB = thisNode.prevNode.position
					pointC = thisNode.prevNode.prevNode.position
					pointD = thisNode.prevNode.prevNode.prevNode.position
					handleRectAB = NSBezierPath.bezierPathWithRect_( NSRect( pointA, subtractPoints(pointA, pointB) ) )
					handleRectCD = NSBezierPath.bezierPathWithRect_( NSRect( pointD, subtractPoints(pointD, pointC) ) )
					intersection = intersect(pointA, pointB, pointC, pointD)
					if intersection:
						intersectionInAB = handleRectAB.containsPoint_(intersection)
						intersectionInCD = handleRectCD.containsPoint_(intersection)
						if intersectionInAB:
							smooth = intersection == pointB
							self.drawCrossForPoint( intersection, pointA, pointD, zoomFactor, smooth )
						elif intersectionInCD:
							smooth = intersection == pointC
							self.drawCrossForPoint( intersection, pointA, pointD, zoomFactor, smooth )
	
	def markZeroHandles(self, thisLayer, handleSize):
		"""
		Marks all BCPs that are retracted into the nearest oncurve point.
		"""
		NSColor.colorWithCalibratedRed_green_blue_alpha_( 0.7, 0.1, 0.9, 0.7 ).set()
		purpleCircles = NSBezierPath.bezierPath()
		
		for thisPath in thisLayer.paths:
			for thisNode in thisPath.nodes:
				if thisNode.type == OFFCURVE:
					retractedInPrevNode = thisNode.prevNode.type != OFFCURVE and thisNode.prevNode.position == thisNode.position
					retractedInNextNode = thisNode.nextNode.type != OFFCURVE and thisNode.nextNode.position == thisNode.position
					if retractedInNextNode or retractedInPrevNode:
						handleDot = self.roundDotForPoint( thisNode.position, handleSize )
						purpleCircles.appendBezierPath_( handleDot )
	
		purpleCircles.fill()
	
	def conditionalContextMenus(self):
		"""
		Builds contextual menus for plug-in options.
		"""
		return [
		{
			'name': Glyphs.localize({
				'en': u"‘Show Angled Handles’ Options:", 
				'de': u"Einstellungen für »Schräge Anfasser anzeigen«:", 
				'es': u"Opciones para ‘Mostrar manejadores inclinados’:", 
				'fr': u"Options pour «Montrer poignées inclinées»",
				'zh': u"路径检查工具",
			}), 
			'action': None,
		},
		{
			'name': Glyphs.localize({
				'en': u"Zero Handles", 
				'de': u"Null-Anfasser", 
				'es': u"Manejadores zero", 
				'fr': u"Poignées à zéro", 
				'zh': u"🏌️‍♀️单摇臂报错", 
			}), 
			'action': self.toggleZeroHandles,
			'state': Glyphs.defaults[ "com.mekkablue.ShowAngledHandles.zeroHandles" ],
		},
		{
			'name': Glyphs.localize({
				'en': u"Almost Straight Lines", 
				'de': u"Beinahe gerade Linien", 
				'es': u"Líneas casi ortogonales", 
				'fr': u"Lignes presque orthogonales", 
				'zh': u"🤸‍♀️非垂直路径报错", 
			}), 
			'action': self.toggleAlmostStraightLines,
			'state': Glyphs.defaults[ "com.mekkablue.ShowAngledHandles.almostStraightLines" ],
		},
		{
			'name': Glyphs.localize({
				'en': u"Laser Beams",
				'de': u"Laserstrahlen", 
				'es': u"Rayos láser",
				'fr': u"Rayons laser", 
				'zh': u"🔫摇臂过长警告", 
			}), 
			'action': self.toggleLaserBeams,
			'state': Glyphs.defaults[ "com.mekkablue.ShowAngledHandles.laserBeams" ],
		},
		{
			'name': Glyphs.localize({
				'en': u"Duplicate Path Segments",
				'de': u"Doppelte Pfadsegmente",
				'es': u"Segmentos de trazos duplicados",
				'fr': u"Segments de tracés en double", 
				'zh': u"👯‍♂️路径重叠警告", 
			}), 
			'action': self.toggleDuplicatePaths,
			'state': Glyphs.defaults[ "com.mekkablue.ShowAngledHandles.duplicatePaths" ],
		},
		{
			'name': Glyphs.localize({
				'en': u"Only Mark Handles if they are Almost Straight",
				'de': u"Anfasser nur markieren, wenn sie beinahe gerade sind",
				'es': u"Marcar manejadores sólo cuando están casi en línea recta",
				'fr': u"Indiquer seulement les poignées presque orthogonales", 
				'zh': u"⚖️接近水平或垂直摇臂警告", 
			}), 
			'action': self.toggleOnlyCloseHandles,
			'state': Glyphs.defaults[ "com.mekkablue.ShowAngledHandles.onlyShowCloseToStraightHandles" ],
		},
		]

	def toggleOnlyCloseHandles(self):
		self.toggleSetting("onlyShowCloseToStraightHandles")
	
	def toggleZeroHandles(self):
		self.toggleSetting("zeroHandles")
	
	def toggleAlmostStraightLines(self):
		self.toggleSetting("almostStraightLines")
	
	def toggleLaserBeams(self):
		self.toggleSetting("laserBeams")
	
	def toggleDuplicatePaths(self):
		self.toggleSetting("duplicatePaths")

	def toggleSetting(self, prefName):
		pref = "com.mekkablue.ShowAngledHandles.%s" % prefName
		Glyphs.defaults[pref] = not bool(Glyphs.defaults[pref])
	
	def addMenuItemsForEvent_toMenu_(self, event, contextMenu):
		if self.generalContextMenus:
			setUpMenuHelper(contextMenu, self.generalContextMenus, self)
		
		newSeparator = NSMenuItem.separatorItem()
		contextMenu.addItem_(newSeparator)
		
		contextMenus = self.conditionalContextMenus()
		if contextMenus:
			setUpMenuHelper(contextMenu, contextMenus, self)
	