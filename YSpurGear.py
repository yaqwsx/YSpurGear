#Author-Jan Mrázek
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback

def newPoint(x, y, z):
    return adsk.core.Point3D.create(x, y, z)
    
def newPointD(origin, x, y):
    sketch = origin.parentSketch
    point = sketch.sketchPoints.add(adsk.core.Point3D.create(1, 1, 0))
    dimensionh = sketch.sketchDimensions.addDistanceDimension(
        origin,
        point,
        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
        newPoint(1, 0, 0))
    dimensionh.parameter.expression = x
    dimensionv = sketch.sketchDimensions.addDistanceDimension(
        origin,
        point,
        adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
        newPoint(1, 0, 0))
    dimensionv.parameter.expression = y
    return point
    
def newLine(sketch, start, end):
    return sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)

def newLineD(sketch, start, end):
    line = sketch.sketchCurves.sketchLines.addByTwoPoints(start, end)
    
    try:
        direction = start.vectorTo(end)
    except AttributeError:
        start = start.geometry
        direction = start.vectorTo(end)
    normal = direction.copy()
    normal.x = -direction.y
    normal.y = direction.x
    normal.normalize()
    normal.scaleBy(1)
    
    dimension = sketch.sketchDimensions.addDistanceDimension(
        line.startSketchPoint,
        line.endSketchPoint,
        adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
        newPoint(start.x + direction.x / 2 + normal.x, start.y + direction.y / 2 + normal.y, 0))
    return line, dimension
    
def newCircle(sketch, center, diameter):
    return sketch.sketchCurves.sketchCircles.addByCenterRadius(center, diameter)
    
def newCircleD(sketch, center, diameter):
    circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(center, diameter)
    try:
        center.x
    except AttributeError:
        center = center.geometry
    dimension = sketch.sketchDimensions.addDiameterDimension(circle,
        newPoint(center.x, center.y + diameter, center.z))
    return circle, dimension
    
def dumpLength(sketch, length, name=None):
    l, d = newLineD(sketch, newPoint(0, 0, 0), newPoint(1, 0, 0))
    print("Dimension name: " + d.parameter.name + ", formula: " + length)
    d.parameter.expression = length
    if name:
        print(name + " = " + str(d.parameter.value) + d.parameter.unit)
    else:
        print("value: " + str(d.parameter.value))
    
def dumpAngle(sketch, angle, name=None):
    a = newLine(sketch, newPoint(0, 0, 0), newPoint(1, 0, 0))
    b = newLine(sketch, a.startSketchPoint, newPoint(1, 1, 0))
    d = sketch.sketchDimensions.addAngularDimension(a, b, newPoint (2, 0.5, 0))
    print("Dimension name: " + d.parameter.name + ", formula: " + angle)
    d.parameter.expression = angle
    if name:
        print(name + " = " + str(d.parameter.value) + d.parameter.unit)
    else:
        print("value: " + str(d.parameter.value))
    
def makeHorizontal(line):
    line.parentSketch.geometricConstraints.addHorizontal(line)
    
def makeVertical(line):
    line.parentSketch.geometricConstraints.addVertical(line)
    
def makeCoincident(a, b):
    a.parentSketch.geometricConstraints.addCoincident(a, b)
    
def makePerpendicular(a, b):
    a.parentSketch.geometricConstraints.addPerpendicular(a, b)
    
def makeEqual(a, b):
    a.parentSketch.geometricConstraints.addEqual(a, b)
    
def makeCollinear(a, b):
    a.parentSketch.geometricConstraints.addCollinear(a, b)
    
def makeSymmetric(a, b, m):
    a.parentSketch.geometricConstraints.addSymmetry(a, b, m)

def splineTroughPoints(sketch, pointSet):
    spline = sketch.sketchCurves.sketchFittedSplines.add(pointSet)
    for i in range(pointSet.count):
        makeCoincident(pointSet.item(i), spline.fitPoints.item(i))
    return spline    
        
def mirrorSpline(mirror, spline):
    sketch = spline.parentSketch
    pointSet = adsk.core.ObjectCollection.create()
    for i in range(spline.fitPoints.count):
        point = sketch.sketchPoints.add(adsk.core.Point3D.create(0, 0, 0))
        makeSymmetric(point, spline.fitPoints.item(i), mirror)
        pointSet.add(point)
    return splineTroughPoints(sketch, pointSet)
    

def drawParameters(sketch, compOrigin):
    origin = sketch.project(compOrigin).item(0)
    teethCountLine, teethCount = newLineD(sketch,
        origin,
        newPoint(0, 1, 0)) # 10 teeth
    makeVertical(teethCountLine);
    teethCount.parameter.name = "teethCount_" + teethCount.parameter.name
    moduleLine, module = newLineD(sketch,
        origin,
        newPoint(0.1, 0, 0))
    makeHorizontal(moduleLine)
    module.parameter.name = "module_" + module.parameter.name
    pressureAngleLine = newLine(sketch,
        origin,
        newPoint(1, 1, 0))
    pressureAngle = sketch.sketchDimensions.addAngularDimension(
        pressureAngleLine,
        moduleLine,
        newPoint(1, 1, 0))
    pressureAngle.parameter.expression = "20 deg"
    pressureAngle.parameter.name = "pressureAngle_" + pressureAngle.parameter.name
    thicknessLine, thickness = newLineD(
        sketch,
        origin,
        newPoint(0, -0.5, 0)) # 5mm
    makeHorizontal(thicknessLine)
    thickness.parameter.name = "thickness_" + thickness.parameter.name
    helixAngleLine = newLine(
        sketch,
        origin,
        newPoint(1, -1, 0))
    helixAngle = sketch.sketchDimensions.addAngularDimension(
        helixAngleLine,
        moduleLine,
        newPoint(1, -0.5, 0))
    helixAngle.parameter.expression = "30 deg"
    helixAngle.parameter.name = "helixAngle_" + helixAngle.parameter.name
    return origin, teethCount, module, pressureAngle, thickness, helixAngle
    
def drawStock(sketch, compOrigin, teethCount, module, pressureAngle):
    origin = sketch.project(compOrigin).item(0)
    
    pitchCircle, pitchCircleD = newCircleD(sketch, origin, 1)
    pitchCircleD.parameter.name = "pitchCircle_" + pitchCircleD.parameter.name
    pitchCircle.isConstruction = True
    addendum, addendumD = newCircleD(sketch, origin, 1.5)
    addendumD.parameter.name = "addendum_" + addendumD.parameter.name
    dedendum, dedendumD = newCircleD(sketch, origin, 0.5)
    dedendumD.parameter.name = "dedendum_" + dedendumD.parameter.name
    dedendum.isConstruction = True
    baseCircle, baseCircleD = newCircleD(sketch, origin, 0.8)
    baseCircle.isConstruction = True
    
    pitchCircleD.parameter.expression = "{} * {} / 1mm".format(teethCount, module)
    addendumD.parameter.expression = "{p} + 2 * {m}".format(p=pitchCircleD.parameter.name, m=module)
    dedendumD.parameter.expression = "{p} - 2 * 1.25 * {m}".format(p=pitchCircleD.parameter.name, m=module)
    baseCircleD.parameter.expression = "{p} * cos({a})".format(p=pitchCircleD.parameter.name, a=pressureAngle)
    
    return pitchCircleD, addendum, addendumD, dedendumD, baseCircleD
    
def drawTrochoidal(origin, teethCount, module, pressureAngle, offset, segments):
    # formula taken from https://engineering.stackexchange.com/questions/13852/involute-gear-curve-when-root-diameter-falls-below-base-diameter/13868
    r = "({n} * {module} / 2mm)".format(n=teethCount, module=module)
    x0 = "(-1.25 * {module})".format(module=module)
    y0 = "(PI * {module}/4 - 1.25 * {module} * tan({pressureAngle}))".format(module=module, pressureAngle=pressureAngle)
    pointSet = adsk.core.ObjectCollection.create()
    for i in range(segments + 1):
        t = "(-{y0}/{r}+({i} * 360mm)/({segments}*{teethCount}))".format(**locals())
        x = "(({r} + {x0}) * cos({t}) + ({r} * {t} / 180 * PI + {y0}) * sin({t}))".format(**locals())
        y = "(-({r} + {x0}) * sin({t}) + ({r} * {t} / 180 * PI + {y0}) * cos({t}))".format(**locals())
        p = newPointD(
            origin,
            #"({r} + {x0}) * cos({t}) + ({r} * {t} / 180 * PI + {y0}) * sin({t})".format(**locals()),
            #"-({r} + {x0}) * sin({t}) + ({r} * {t} / 180 * PI + {y0}) * cos({t})".format(**locals()))
            "cos({offset}) * {x} - sin({offset}) * {y}".format(**locals()),
            "sin({offset}) * {x} + cos({offset}) * {y}".format(**locals()))
        pointSet.add(p)
    spline = origin.parentSketch.sketchCurves.sketchFittedSplines.add(pointSet)
    for i in range(pointSet.count):
        makeCoincident(pointSet.item(i), spline.fitPoints.item(i))
    return spline
            
def drawInvolute(origin, teethCount, module, pressureAngle, pitchDia, baseDia, addendumDia, offset, segments):
    # formula taken from https://thebloughs.net/involute-gear-generation-in-solidworks/
    pitchAngle = "(1 / {teethCount} * 1 deg * 360 mm)".format(**locals())
    alpha = "(sqrt((({pitchDia}/1mm) ^ 2 - ({baseDia} / 1mm) ^ 2)) / {baseDia} * 1mm * 180 / PI * 1 deg - {pressureAngle})".format(**locals())
    beta = "({pitchAngle} / 4 - {alpha} + {offset})".format(**locals())
    phi = "(2 * sqrt(({addendumDia} / 2mm) ^ 2 - ({baseDia} / 2mm) ^ 2) / {baseDia} * 1mm * 180deg / PI)".format(**locals())
    pointSet = adsk.core.ObjectCollection.create()
    for i in range(segments + 1):
        t = "({i} * {phi} / {segments})".format(**locals())
        p = newPointD(
            origin,
            "{baseDia} / 2 * (cos({t} + {beta}) + {t} / 180deg * PI * sin({t} + {beta}))".format(**locals()),
            "{baseDia} / 2 * (sin({t} + {beta}) - {t} / 180deg * PI * cos({t} + {beta}))".format(**locals()))
        pointSet.add(p)
    spline = origin.parentSketch.sketchCurves.sketchFittedSplines.add(pointSet)
    for i in range(pointSet.count):
        makeCoincident(pointSet.item(i), spline.fitPoints.item(i))
    return spline
    
def drawTooth(sketch, origin, teethCount, module, pressureAngle, offset):
    print("offset: " + str(offset))
    stockOrigin = sketch.project(origin).item(0)
    pitchDia, addendumCirc, addendum, dedendum, baseDia = drawStock(
        sketch,
        origin,
        teethCount,
        module,
        pressureAngle)
    involute = drawInvolute(
        stockOrigin,
        teethCount,
        module,
        pressureAngle,
        pitchDia.parameter.name,
        baseDia.parameter.name,
        addendum.parameter.name,
        offset,
        10)
    trachoidal = drawTrochoidal(
        stockOrigin,
        teethCount,
        module,
        pressureAngle,
        offset,
        10)
        
    if offset == 0 or offset == "0":
        mirrorLine = newLine(sketch, stockOrigin, newPoint(2, 0, 0))
        makeHorizontal(mirrorLine)
    else:
        horizontalLine = newLine(sketch, stockOrigin, newPoint(2, 0, 0))
        makeHorizontal(horizontalLine)
        horizontalLine.isConstruciton = True
        mirrorLine = newLine(sketch, stockOrigin, newPoint(2, 2, 0))
        dim = sketch.sketchDimensions.addAngularDimension(
            horizontalLine,
            mirrorLine,
            newPoint(3, 2, 0))
        dim.parameter.expression = offset
    mirrorLine.isConstruction = True
    involute2 = mirrorSpline(mirrorLine, involute)
    trachoidal2 = mirrorSpline(mirrorLine, trachoidal)
    
    tArc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(stockOrigin, trachoidal2.startSketchPoint, 1)
    makeCoincident(tArc.endSketchPoint, trachoidal.startSketchPoint)
    
    newLine(sketch, stockOrigin, involute.startSketchPoint)
    newLine(sketch, stockOrigin, involute2.startSketchPoint)
        
    pitchAngle = "(1 / {teethCount} * 1 deg * 360 mm / 2)".format(teethCount=teethCount)
    fenceA = newLine(sketch, stockOrigin, newPoint(1, 1, 0))
    fenceAD = sketch.sketchDimensions.addAngularDimension(fenceA, mirrorLine, newPoint (1, 0.85, 0))
    fenceAD.parameter.expression = pitchAngle
    makeCoincident(fenceA.endSketchPoint, addendumCirc)
    fenceB = newLine(sketch, stockOrigin, newPoint(1, -1, 0))
    fenceBD = sketch.sketchDimensions.addAngularDimension(fenceB, mirrorLine, newPoint (1, -0.85, 0))
    fenceBD.parameter.expression = fenceAD.parameter.name
    makeCoincident(fenceB.endSketchPoint, addendumCirc)

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        rootComp = design.activeComponent 
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        
        parameters = sketches.add(xyPlane)
        parameters.name = "parameters"
        origin, teethCount, module, pressureAngle, thickness, helixAngle = drawParameters(
            parameters,
            rootComp.originConstructionPoint)
        parameters.isLightBulbOn = False
        
        bottom = sketches.add(xyPlane)
        bottom.name = "bottom"
        drawTooth(bottom,
                  origin,
                  teethCount.parameter.name,
                  module.parameter.name,
                  pressureAngle.parameter.name,
                  0)
        
        # Create top face plane
        planes = rootComp.constructionPlanes
        planeInput = planes.createInput()
        offsetValue = adsk.core.ValueInput.createByString(thickness.parameter.name)
        planeInput.setByOffset(xyPlane, offsetValue)
        topFacePlane = planes.add(planeInput)
        topFacePlane.name = "topFace"
        
        top = sketches.add(topFacePlane)
        top.name = "top"
        drawTooth(top,
                  origin,
                  teethCount.parameter.name,
                  module.parameter.name,
                  pressureAngle.parameter.name, 
                  "(360deg / (tan(90deg-{helixAngle})*PI*{module}*{teethCount} / 1mm) * {thickness})".format(
                      thickness=thickness.parameter.name,
                      helixAngle=helixAngle.parameter.name,
                      module=module.parameter.name,
                      teethCount=teethCount.parameter.name))

    except:
        print('Failed:\n{}'.format(traceback.format_exc()))
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
