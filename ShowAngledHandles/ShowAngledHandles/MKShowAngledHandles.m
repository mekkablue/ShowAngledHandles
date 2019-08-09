//
//  ShowAngledHandles.m
//  ShowAngledHandles
//
//  Created by Georg Seifert on 26.07.19.
//  Copyright © 2019 mekkablue. All rights reserved.
//

#import "MKShowAngledHandles.h"
#import <GlyphsCore/GSComponent.h>
#import <GlyphsCore/GSFilterPlugin.h>
#import <GlyphsCore/GSFont.h>
#import <GlyphsCore/GSFontMaster.h>
#import <GlyphsCore/GSGlyph.h>
#import <GlyphsCore/GSLayer.h>
#import <GlyphsCore/GSNode.h>
#import <GlyphsCore/GSPath.h>
#import <GlyphsCore/GSPathSegment.h>
#import <GlyphsCore/GSWindowControllerProtocol.h>
#import <GlyphsCore/GlyphsFilterProtocol.h>

// #import "GSEditViewController.h"
// #import "GSWindowController.h"
#import <GlyphsCore/GSGeometrieHelper.h>

CGFloat angleBetweenPoints(NSPoint firstPoint, NSPoint secondPoint) {
	/*
	Returns the angle (in degrees) of the straight line between firstPoint and secondPoint,
	0 degrees being the second point to the right of first point.
	firstPoint, secondPoint: must be NSPoint or GSNode
	*/
	CGFloat xDiff = secondPoint.x - firstPoint.x;
	CGFloat yDiff = secondPoint.y - firstPoint.y;
	return DEG(atan2(yDiff, xDiff));
}

@implementation MKShowAngledHandles {
	NSViewController<GSGlyphEditViewControllerProtocol> *_editViewController;
}

- (id)init {
	self = [super init];
	if (self) {
		// do stuff
	}
	return self;
}

- (void)loadPlugin {
	NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
	[defaults registerDefaults:@{@"com.mekkablue.ShowAngledHandles.keyboardShortcut": @"y",
								 @"com.mekkablue.ShowAngledHandles.zeroHandles": @YES,
								 @"com.mekkablue.ShowAngledHandles.almostStraightLines": @YES,
								 @"com.mekkablue.ShowAngledHandles.laserBeams": @YES,
								 @"com.mekkablue.ShowAngledHandles.duplicatePaths": @YES,
								 @"com.mekkablue.ShowAngledHandles.onlyShowCloseToStraightHandles": @NO}];
}

- (NSUInteger)interfaceVersion {
	// Distinguishes the API verison the plugin was built for. Return 1.
	return 1;
}

- (NSString *)title {
	return NSLocalizedStringFromTableInBundle(@"Angled Handles", nil, [NSBundle bundleForClass:[self class]], @"");
}

- (NSString *)keyEquivalent {
	return [[NSUserDefaults standardUserDefaults] objectForKey:@"com.mekkablue.ShowAngledHandles.keyboardShortcut"];
}

- (int)modifierMask {
	return NSEventModifierFlagCommand;
}

- (void)drawForegroundForLayer:(GSLayer *)layer {
	// Whatever you draw here will be displayed IN FRONT OF the paths.
	// To get an NSBezierPath from a GSPath, use the bezierPath method:
	//  [[myPath bezierPath] fill];
	// You can apply that to a full layer at once:
	// [myLayer bezierPath];	   # all closed paths
	// [myLayer openBezierPath];   # all open paths

	if ([self conditionsAreMetForDrawing]) {

		// mark angled handles:
		[self drawAngledHandles:layer];

		// mark duplicate path segments:
		NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
		if ([defaults boolForKey:@"com.mekkablue.ShowAngledHandles.duplicatePaths"]) {
			[self markDuplicateSegments:layer];
		}
	}
}

- (void)drawBackgroundForLayer:(GSLayer *)layer options:(NSDictionary *)options {
	if ([self conditionsAreMetForDrawing]) {
		CGFloat zoomedHandleSize = [self zoomedHandleSize];

		NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
		// mark slanted lines:
		if ([defaults boolForKey:@"com.mekkablue.ShowAngledHandles.almostStraightLines"]) {
			[self markNonStraightLines:layer scaledLineWidth:zoomedHandleSize * 0.7];
		}

		// mark crossed BCPs:
		if ([defaults boolForKey:@"com.mekkablue.ShowAngledHandles.laserBeams"]) {
			[self markCrossedHandles:layer zoomFactor:[self getScale]];
		}
		// mark zero handles:
		if ([defaults boolForKey:@"com.mekkablue.ShowAngledHandles.zeroHandles"]) {
			[self markZeroHandles:layer handleSize:zoomedHandleSize * 2];
		}
	}
}

- (void)drawBackgroundForInactiveLayer:(GSLayer *)Layer {
	// Whatever you draw here will be displayed behind the paths, but for inactive masters.
}

- (float)getScale {
	// [self getScale]; returns the current scale factor of the Edit View UI.
	// Divide any scalable size by this value in order to keep the same apparent pixel size.

	if (_editViewController) {
		return [[_editViewController graphicView] scale];
	}
	else {
		return 1.0;
	}
}

- (void)setController:(NSViewController<GSGlyphEditViewControllerProtocol> *)Controller {
	// Use [self controller]; as object for the current view controller.
	_editViewController = Controller;
}

- (BOOL)conditionsAreMetForDrawing {
	/*
	Don't activate if text or pan (hand) tool are active.
	*/
	NSObject<GSWindowControllerProtocol> *currentController = (NSObject<GSWindowControllerProtocol> *)[[[_editViewController view] window] windowController];
	if (currentController) {
		id tool = [currentController toolDrawDelegate];
		BOOL textToolIsActive = [tool isKindOfClass:NSClassFromString(@"GlyphsToolText")];
		BOOL handToolIsActive = [tool isKindOfClass:NSClassFromString(@"GlyphsToolHand")];
		if (!textToolIsActive && !handToolIsActive) {
			return YES;
		}
	}
	return NO;
}

- (CGFloat)zoomedHandleSize {
	/*
	Returns the proper handle size according to user settings:
	Glyphs > Preferences > User Preferences > Handle Size
	*/
	int handleSizeIndex = (int)[[NSUserDefaults standardUserDefaults] integerForKey:@"GSHandleSize"];

	static int handleSizes[3] = {5, 8, 12};
	CGFloat handleSize = handleSizes[handleSizeIndex] / pow([self getScale], 0.9); // scaled diameter
	return handleSize;
}

- (void)drawAngledHandles:(GSLayer *)thisLayer {
	/*
	Marks all BCPs on thisLayer that are not straight.
	*/
	[[NSColor colorWithCalibratedRed:1.0 green:0.1 blue:0.1 alpha:0.6] set];
	BOOL onlyShowCloseToStraightHandles = [[NSUserDefaults standardUserDefaults] boolForKey:@"com.mekkablue.ShowAngledHandles.onlyShowCloseToStraightHandles"];
	for (GSPath *thisPath in thisLayer.paths) {
		GSNode *prevNode = [thisPath.nodes lastObject];
		int nodeIndex = 0;
		for (GSNode *thisNode in thisPath.nodes) {
			if (thisNode.type == OFFCURVE) { // BCP
				// determine other node for angle measurement:
				GSNode *nextNode = [thisPath nodeAtIndex:nodeIndex + 1];
				GSNode *otherNode = nil;
				if (prevNode.type != OFFCURVE) {
					otherNode = prevNode;
				}
				else if (nextNode.type != OFFCURVE) {
					otherNode = nextNode;
				}
				if (otherNode) {
					if ((thisNode.position.x - otherNode.position.x) * (thisNode.position.y - otherNode.position.y) != 0.0) {
						if (!onlyShowCloseToStraightHandles) {
							[self drawHandleForNode:thisNode];
						}
						else {
							CGFloat angle = fabs(fmodf(angleBetweenPoints(thisNode.position, otherNode.position), 90.0));
							CGFloat diffX = fabs(thisNode.position.x - otherNode.position.x);
							CGFloat diffY = fabs(thisNode.position.y - otherNode.position.y);
							BOOL almostStraight = diffX <= 2.0 || diffY <= 2.0 || angle < 8.0 || angle > 82.0;
							if (almostStraight) {
								[self drawHandleForNode:thisNode];
							}
						}
					}
				}
			}
			nodeIndex++;
			prevNode = thisNode;
		}
	}
}

- (void)drawHandleForNode:(GSNode *)node {
	/*
	Draws a BCP dot in the correct size.
	*/
	// calculate handle size:
	CGFloat handleSize = [self zoomedHandleSize];

	// offcurves are a little smaller:
	if (node.type == OFFCURVE) {
		handleSize *= 0.8;
	}
	// selected handles are a little bigger:
	if ([[[node layer] selection] containsObject:node]) {
		handleSize *= 1.45;
	}
	// draw disc inside a rectangle around point position:
	NSBezierPath *dot = [self roundDotForPoint:node.position handleSize:handleSize];
	[dot fill];
}

- (NSBezierPath *)roundDotForPoint:(NSPoint)thisPoint handleSize:(CGFloat)markerWidth {
	/*
	Returns a circle with thisRadius around thisPoint.
	*/
	NSRect myRect = NSMakeRect(
		thisPoint.x - markerWidth * 0.5, thisPoint.y - markerWidth * 0.5, // origin
		markerWidth, markerWidth										  // size
	);
	return [NSBezierPath bezierPathWithOvalInRect:myRect];
}

- (void)drawCrossForPoint:(NSPoint)thisPoint firstOnCurve:(NSPoint)firstOnCurve secondOnCurve:(NSPoint)secondOnCurve zoomFactor:(CGFloat)zoomFactor smoothHandle:(BOOL)smoothHandle {
	/*
	Draws a laser beam and an intersection cross for handles that are too long,
	or a dotted indicator line for max handles.
	*/
	// arms (beams):
	NSBezierPath *arms = [NSBezierPath new];
	[arms moveToPoint:thisPoint];
	[arms lineToPoint:firstOnCurve];
	[arms moveToPoint:thisPoint];
	[arms lineToPoint:secondOnCurve];
	[arms setLineCapStyle:NSRoundLineCapStyle];
	[arms setLineWidth:1.0 / zoomFactor];
	if (smoothHandle) {
		CGFloat dash[2] = {2.0 / zoomFactor, 3.0 / zoomFactor};
		[arms setLineDash:dash count:2 phase:0];
		[[NSColor grayColor] set];
	}
	else {
		[[NSColor yellowColor] set];
	}
	[arms stroke];

	// cross (intersection):
	if (!smoothHandle) {
		[[NSColor orangeColor] set];
		CGFloat offset = 10.0;
		CGFloat leftX = thisPoint.x - offset / zoomFactor;
		CGFloat rightX = thisPoint.x + offset / zoomFactor;
		CGFloat lowerY = thisPoint.y - offset / zoomFactor;
		CGFloat upperY = thisPoint.y + offset / zoomFactor;
		NSBezierPath *cross = [NSBezierPath new];
		[cross moveToPoint:NSMakePoint(leftX, upperY)];
		[cross lineToPoint:NSMakePoint(rightX, lowerY)];
		[cross moveToPoint:NSMakePoint(leftX, lowerY)];
		[cross lineToPoint:NSMakePoint(rightX, upperY)];
		[cross setLineCapStyle:NSRoundLineCapStyle];
		[cross setLineWidth:1.0 / zoomFactor];
		[cross stroke];
	}
}

- (void)markNonStraightLines:(GSLayer *)thisLayer scaledLineWidth:(CGFloat)scaledLineWidth {
	/*
	Draws an indicator for nonstraight lines.
	Opacity depends on deviation from straight (h/v) position.
	*/
	for (GSPath *thisPath in thisLayer.paths) {
		GSNode *prevNode = [thisPath.nodes lastObject];
		for (GSNode *thisNode in thisPath.nodes) {
			if (thisNode.type != OFFCURVE) { // on-curve

				if (prevNode && prevNode.type != OFFCURVE) {
					CGFloat unstraightness = fabs(thisNode.position.x - prevNode.position.x);
					CGFloat unstraightnessY = fabs(thisNode.position.y - prevNode.position.y);
					if (unstraightness > unstraightnessY) {
						unstraightness = unstraightnessY;
					}
					if (unstraightness > 0.1 && unstraightness < 20.0) {
						CGFloat opacity = 3.0 / unstraightness;
						if (opacity > 1.0) {
							opacity = 1.0;
						}
						[[NSColor colorWithCalibratedRed:1.0 green:0.5 blue:0.0 alpha:opacity] set];
						NSBezierPath *lineMarker = [NSBezierPath new];
						[lineMarker moveToPoint:prevNode.position];
						[lineMarker lineToPoint:thisNode.position];
						[lineMarker setLineCapStyle:NSRoundLineCapStyle];
						[lineMarker setLineWidth:scaledLineWidth];
						[lineMarker stroke];
					}
				}
			}
			prevNode = thisNode;
		}
	}
}

- (void)markDuplicateSegments:(GSLayer *)thisLayer {
	/*
	Collect identical segments and mark them.
	*/
	CGFloat zoomFactor = [self getScale];
	NSMutableArray<GSPathSegment *> *segments = [NSMutableArray new];
	for (GSPath *path in thisLayer.paths) {
		[segments addObjectsFromArray:[path pathSegments]];
	}

	NSMutableArray *duplicates = [NSMutableArray new];
	for (int idx = 0; idx < [segments count]; idx++) {
		GSPathSegment *s1 = segments[idx];
		for (int jdx = idx + 1; jdx < [segments count]; jdx++) {
			GSPathSegment *s2 = segments[jdx];
			if ([s1 isEqualToSegment:s2]) {
				[duplicates addObject:s1];
			}
		}
	}
	if ([duplicates count] > 0) {
		NSBezierPath *duplicateMarker = [NSBezierPath new];
		for (GSPathSegment *segment in duplicates) {
			[duplicateMarker moveToPoint:[segment pointAtIndex:0]];

			if (segment->count == 2) {
				[duplicateMarker lineToPoint:[segment pointAtIndex:1]];
			}
			else {
				[duplicateMarker curveToPoint:[segment pointAtIndex:3] controlPoint1:[segment pointAtIndex:1] controlPoint2:[segment pointAtIndex:2]];
			}
		}
		[[NSColor purpleColor] set];
		[duplicateMarker setLineWidth:3.0 / zoomFactor];
		[duplicateMarker stroke];

		[[NSColor yellowColor] set];
		[duplicateMarker setLineWidth:2.0 / zoomFactor];
		CGFloat dash[2] = {4.0 / zoomFactor, 6.0 / zoomFactor};
		[duplicateMarker setLineDash:dash count:2 phase:2.0 / zoomFactor];
		[duplicateMarker stroke];
	}
}

- (void)markCrossedHandles:(GSLayer *)thisLayer zoomFactor:(CGFloat)zoomFactor {
	/*
	Marks crossed handles.
	*/
	for (GSPath *thisPath in thisLayer.paths) {
		int nodeIndex = -1;
		for (GSNode *thisNode in thisPath.nodes) {
			nodeIndex++;
			if (thisNode.type == CURVE) {
				NSPoint pointA = thisNode.position;
				NSPoint pointB = [thisPath nodeAtIndex:nodeIndex - 1].position;
				NSPoint pointC = [thisPath nodeAtIndex:nodeIndex - 2].position;
				NSPoint pointD = [thisPath nodeAtIndex:nodeIndex - 3].position;
				NSPoint intersection = GSIntersectLineLineUnlimited(pointA, pointB, pointC, pointD);
				if (intersection.x < NSNotFound) {
					CGFloat tAB;
					GSNearestPointOnLine(intersection, pointA, pointB, &tAB);
					CGFloat tDC;
					GSNearestPointOnLine(intersection, pointD, pointC, &tDC);
					if (tAB <= 1.001 && tAB >= 0) {
						BOOL smooth = GSPointsEqual(intersection, pointB, 0.001) && tDC >= 0.999;
						[self drawCrossForPoint:intersection firstOnCurve:pointA secondOnCurve:pointD zoomFactor:zoomFactor smoothHandle:smooth];
					}
					else if (tDC <= 1.001 && tDC >= 0) {
						BOOL smooth = GSPointsEqual(intersection, pointC, 0.001) && tAB >= 0.999;
						[self drawCrossForPoint:intersection firstOnCurve:pointA secondOnCurve:pointD zoomFactor:zoomFactor smoothHandle:smooth];
					}
				}
			}
		}
	}
}

- (void)markZeroHandles:(GSLayer *)thisLayer handleSize:(int)handleSize {
	/*
	Marks all BCPs that are retracted into the nearest oncurve point.
	*/
	[[NSColor colorWithCalibratedRed:0.7 green:0.1 blue:0.9 alpha:0.7] set];
	NSBezierPath *purpleCircles = [NSBezierPath new];

	for (GSPath *thisPath in thisLayer.paths) {
		GSNode *prevNode = [thisPath.nodes lastObject];
		for (GSNode *thisNode in thisPath.nodes) {
			if (((thisNode.type == OFFCURVE && prevNode.type != OFFCURVE) ||
				 (thisNode.type != OFFCURVE && prevNode.type == OFFCURVE)) &&
				GSPointsEqual(thisNode.position, prevNode.position, 0.01)) {
				NSBezierPath *handleDot = [self roundDotForPoint:thisNode.position handleSize:handleSize];
				[purpleCircles appendBezierPath:handleDot];
			}
			prevNode = thisNode;
		}
	}
	[purpleCircles fill];
}

- (void)conditionalContextMenus:(NSMenu *)menu {
	/*
	Builds contextual menus for plug-in options.
	*/

	NSBundle *bundle = [NSBundle bundleForClass:[self class]];
	NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];

	NSMenuItem *item = [[NSMenuItem alloc] initWithTitle:NSLocalizedStringFromTableInBundle(@"‘Show Angled Handles’ Options:", nil, bundle, @"") action:nil keyEquivalent:@""];
	[menu addItem:item];

	item = [[NSMenuItem alloc] initWithTitle:NSLocalizedStringFromTableInBundle(@"Zero Handles", nil, bundle, @"") action:@selector(toggleZeroHandles:) keyEquivalent:@""];
	item.target = self;
	[item setState:[defaults boolForKey:@"com.mekkablue.ShowAngledHandles.zeroHandles"]];
	[menu addItem:item];

	item = [[NSMenuItem alloc] initWithTitle:NSLocalizedStringFromTableInBundle(@"Almost Straight Lines", nil, bundle, @"") action:@selector(toggleAlmostStraightLines:) keyEquivalent:@""];
	item.target = self;
	[item setState:[defaults boolForKey:@"com.mekkablue.ShowAngledHandles.almostStraightLines"]];
	[menu addItem:item];

	item = [[NSMenuItem alloc] initWithTitle:NSLocalizedStringFromTableInBundle(@"Laser Beams", nil, bundle, @"") action:@selector(toggleLaserBeams:) keyEquivalent:@""];
	item.target = self;
	[item setState:[defaults boolForKey:@"com.mekkablue.ShowAngledHandles.laserBeams"]];
	[menu addItem:item];

	item = [[NSMenuItem alloc] initWithTitle:NSLocalizedStringFromTableInBundle(@"Duplicate Path Segments", nil, bundle, @"") action:@selector(toggleDuplicatePaths:) keyEquivalent:@""];
	item.target = self;
	[item setState:[defaults boolForKey:@"com.mekkablue.ShowAngledHandles.duplicatePaths"]];
	[menu addItem:item];

	item = [[NSMenuItem alloc] initWithTitle:NSLocalizedStringFromTableInBundle(@"Only Mark Handles if they are Almost Straight", nil, bundle, @"") action:@selector(toggleOnlyCloseHandles:) keyEquivalent:@""];
	item.target = self;
	[item setState:[defaults boolForKey:@"com.mekkablue.ShowAngledHandles.onlyShowCloseToStraightHandles"]];
	[menu addItem:item];
}

- (void)toggleOnlyCloseHandles:(id)sender {
	[self toggleSetting:@"onlyShowCloseToStraightHandles"];
}

- (void)toggleZeroHandles:(id)sender {
	[self toggleSetting:@"zeroHandles"];
}

- (void)toggleAlmostStraightLines:(id)sender {
	[self toggleSetting:@"almostStraightLines"];
}

- (void)toggleLaserBeams:(id)sender {
	[self toggleSetting:@"laserBeams"];
}

- (void)toggleDuplicatePaths:(id)sender {
	[self toggleSetting:@"duplicatePaths"];
}

- (void)toggleSetting:(NSString *)prefName {
	NSString *pref = [@"com.mekkablue.ShowAngledHandles." stringByAppendingString:prefName];
	NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
	[defaults setBool:![defaults boolForKey:pref] forKey:pref];
}

- (void)addMenuItemsForEvent:(NSEvent *)event toMenu:(NSMenu *)contextMenu {
	NSMenuItem *newSeparator = [NSMenuItem separatorItem];
	[contextMenu addItem:newSeparator];

	[self conditionalContextMenus:contextMenu];
}

@end
