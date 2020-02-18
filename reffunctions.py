# -*- coding: utf-8 -*-
"""
/***************************************************************************
ReferenceFunctions
                                 A QGIS plugin
 Provide field calculator function for Reference to other layers/features
 based on Nathan Woodrow work:
 http://nathanw.net/2012/11/10/user-defined-expression-functions-for-qgis/
                              -------------------
        begin                : 2014-09-20
        copyright            : (C) 2014 by enrico ferreguti
        email                : enricofer@gmail.com
        updated by SIGMOÉ    : 2020-02-18
        email                : em at sigmoe dot fr
        copyright 2          : 2020 (C) etienne moro
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtSql import *
try:
    from qgis.PyQt.QtWidgets import *
except:
    pass
#from qgis.core import *
import qgis
from qgis.utils import iface,qgsfunction
from qgis.core import QgsGeometry,QgsExpression,QgsMapLayer,QgsFeatureRequest
# Import the code for the dialog
from .reffunctionsdialog import refFunctionsDialog
import os.path
import sys


def _getLayerSet():
        try:    #qgis 2
            return {layer.name():layer for layer in iface.legendInterface().layers()}
        except: #qgis 3
            return {layer.name():layer for layer in qgis.core.QgsProject.instance().mapLayers().values()}



@qgsfunction(4, "Reference", register=False)
def dbvalue(values, feature, parent):
    """
        Retrieve first target_field value from target_layer when condition_field is equal to condition_value
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">dbvalue(</span>
        <span class="argument">target_layer, target_field, condition_field, condition_value</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>the name of a field of target_layer that returns the value, for example 'myTargetField'. In case of multiple results only the first is retrieved. If target_field = '$geometry', geometry value is retrieved</td></tr>
        <tr><td class="argument">condition_field</td><td>name of the field used for the condition, for example 'myKeyField'.</td></tr>
        <tr><td class="argument">condition_value</td><td>specific value that should be found to consider the object. Note that the value need to have the same type as condition_field</td></tr>
        </table></div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>dbvalue('myLayer','myTargetField','myKeyField',value)</code></li>
        </ul></div>
        <h4>Notes</h4>
        <div class="notes">The example function is similar to dbquery('myLayer','myTargetField','myKeyField =value') but is significantly faster for large database.
        </div>
    """
    dbg = debug()
    dbg.out("evaluating dbvalue")
    targetLayerName = values[0]
    targetFieldName = values[1]
    keyFieldName = values[2]
    contentCondition = values[3]
    #layerSet = {layer.name():layer for layer in iface.legendInterface().layers()}
    layerSet = _getLayerSet()
    if not (targetLayerName in layerSet.keys()):
        parent.setEvalErrorString("Error: invalid targetLayerName")
        return

    #if not targetLayerName in iface.legendInterface().layers():
    #    parent.setEvalErrorString("error: targetLayer not present")
    #iface = QgsInterface.instance()
    res = None
    for feat in layerSet[targetLayerName].getFeatures():
        if feat.attribute(keyFieldName) == contentCondition:
            if targetFieldName == "$geometry":
                res = feat.geometry().asWkt()
            else:
                try:
                    res = feat.attribute(targetFieldName)
                except:
                    parent.setEvalErrorString("Error: invalid targetFieldName")
                    return
    return res

@qgsfunction(3, "Reference", register=False, usesgeometry=True)
def dbvaluebyid(values, feature, parent):
    """
        Retrieve the target_field value from target_layer using internal feature_id
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">dbvaluebyid(</span>
        <span class="argument">target_layer, target_field, feature_id</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>the name of a field of target_layer that returns the value, for example 'myTargetField'. If target_field = '$geometry', geometry value is retrieved</td></tr>
        <tr><td class="argument">feature_id</td><td>an integer number reference to internal feature ID</td></tr>
        </table></div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>dbvaluebyid('myLayer','myTargetField',112)</code></li>
        </ul></div>
    """
    dbg = debug()
    dbg.out("evaluating dbvalue")
    targetLayerName = values[0]
    targetFieldName = values[1]
    targetFeatureId = values[2]
    #layerSet = {layer.name():layer for layer in iface.legendInterface().layers()}
    layerSet = _getLayerSet()
    if not (targetLayerName in layerSet.keys()):
        parent.setEvalErrorString("Error: invalid targetLayerName")
        return

    #if not targetLayerName in iface.legendInterface().layers():
    #    parent.setEvalErrorString("error: targetLayer not present")
    #iface = QgsInterface.instance()
    for name,layer in layerSet.items():
        if name == targetLayerName:
            try:
                targetFeatureIter = layer.getFeatures(QgsFeatureRequest(targetFeatureId))
                for targetFeature in targetFeatureIter:
                    pass
            except:
                parent.setEvalErrorString("Error: invalid targetFeatureIndex")
                return
            if targetFieldName == "$geometry":
                res = targetFeature.geometry().asWkt()
            else:
                try:
                    res = targetFeature.attribute(targetFieldName)
                except:
                    parent.setEvalErrorString("Error: invalid targetFieldName")
                    return
    return res



@qgsfunction(3, "Reference", register=False)
def dbquery(values, feature, parent):
    """
        Retrieve first target_field value from target_layer when where_clause is true
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">dbquery(</span>
        <span class="argument">target_layer, target_field, where_clause</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when source feature contains target feature, for example 'myField'.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        </td></tr>
        <tr><td class="argument">where_clause</td><td>a valid expression string without double quotes to identify fields, for example 'field1 > 1 and field2 = "foo"' </td></tr>
        </table>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>dbquery('myLayer','myField','field1 > 1 and field2 = "foo"')</code></li>
        <li><code>dbquery('myLayer','$geometry','field1 > 1 and field2 = "foo"')</code></li>
        </ul></div>
    """
    targetLayerName = values[0].replace('"','')
    targetFieldName = values[1].replace('"','')
    whereClause = values[2].replace('"','')
    layerSet = _getLayerSet()
    if not (targetLayerName in layerSet.keys()):
        parent.setEvalErrorString("Error: invalid targetLayerName")
        return
    dbg=debug()
    dbg.out("evaluating dbquery")

    for layerName, iterLayer in layerSet.items():
        if layerName == targetLayerName:
            exp = QgsExpression(whereClause)
            exp.prepare(iterLayer.dataProvider().fields())
            for feat in iterLayer.getFeatures():
                if exp.evaluate(feature):
                    if targetFieldName == "$geometry":
                        return feat.geometry().asWkt()
                    else:
                        try:
                            return feat.attribute(targetFieldName)
                        except:
                            parent.setEvalErrorString("Error: invalid targetField")


@qgsfunction(2, "Reference", register=False)
def dbsql(values, feature, parent):
    """
        Retrieve results from SQL query
        <h4>Syntax</h4>
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">dbsql(</span>
        <span class="argument">connection_name,sql_query</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">connection_name</td><td>the name of a currently registered database connection, for example 'myConnection'.</td></tr>
        <tr><td class="argument">sql_query</td><td>a valid sql query string (where clause), for example 'field1 > 1 and field2 = "foo"'</td></tr>
        </table>
        </div>
        <h4>Examples</h4>
        <div class="examples"><ul>
        <li><code>dbsql('myLayer','myField','field1 > 1 and field2 = "foo"')</code></li>
        <li><code>dbsql('myLayer','$geometry','field1 > 1 and field2 = "foo"')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating dbsql")
    connectionName = values[0]
    sqlQuery = values[1].replace('""','@#@')
    sqlQuery = sqlQuery.replace('"',"'")
    sqlQuery = sqlQuery.replace('@#@','"')
    conn = SQLconnection(connectionName)
    if conn.lastError()=="":
        res = conn.submitQuery(sqlQuery)
        dbg.out(conn.lastError())
        if conn.lastError()=="":
            if res!=[]:
                if len(res)>1 or len(res[0])>1:
                    parent.setEvalErrorString("Error: multiple results")
                else:
                    return res[0][0]
            else:
                parent.setEvalErrorString("Error: null query result")
        else:
            parent.setEvalErrorString("Error: invalid query\n"+conn.lastError())
    else:
        parent.setEvalErrorString("Error: invalid connection")

@qgsfunction(1, "Reference", register=False, usesgeometry=True)
def geomRedef(values, feature, parent):
    """
        Redefine the current feature geometry with a new WKT geometry
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomredef(</span>
        <span class="argument">WKTgeometry</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">WKTgeometry</td><td>a valid WKT geometry provided by expression commands </td></tr>
        </table>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomredef('POLYGON((602793.98 6414014.88,....))')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("self redefine geometry")
    targetGeometry = values[0]
    if iface.mapCanvas().currentLayer().isEditable():
        try:
            iface.mapCanvas().currentLayer().changeGeometry(feature.id(), targetGeometry)
            #iface.mapCanvas().currentLayer().updateExtents()
            #iface.mapCanvas().currentLayer().setCacheImage(None)
            iface.mapCanvas().currentLayer().triggerRepaint()
            #feature.setGeometry(targetGeometry)
            return 1
        except:
            parent.setEvalErrorString("Error: geometry is not valid")
            return 0

@qgsfunction(1, "Reference", register=False)
def xx(values, feature, parent):
    """
        Return the coordinate x of the given point geometry

        <h4>Syntax</h4>
        <p>dbsql(<i>geometry</i>)</p>

        <h4>Arguments</h4>
        <p><i>  geometry</i> &rarr; a valid geometry provided by expression commands 'myGeometry'.<br></p>

        <h4>Example</h4>
        <p><!-- Show examples of function.-->
             geomRedef('myLayer','myField','field1 > 1 and field2 = "foo"') <br>
             dbquery('myLayer','$geometry','field1 > 1 and field2 = "foo"') <br></p>

        </p>
    """
    dbg=debug()
    dbg.out("xx")
    pass

@qgsfunction(1, "Transformation", register=False)
def canvaswidth(values, feature, parent):
    """
        Return the width of the current canvas (in pixels or map units)
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">canvas_width(</span>
        <span class="argument">unit</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">unit</td><td>the unit in which the size is returned ('pixels' or 'mapunits')</td></tr>
        </table>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>canvas_width('mapunits')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("CanvasWidth")
    mapCanvas = iface.mapCanvas()
    if values[0]=='pixels':
        res = iface.mapCanvas().mapRenderer().width()
    elif values[0]=='mapunits':
        res = iface.mapCanvas().mapRenderer().width()*iface.mapCanvas().mapRenderer().mapUnitsPerPixel ()
    elif values[0]=='mm':
        pass
    try:
        return res
    except:
        parent.setEvalErrorString("error: argument not valid")


@qgsfunction(1, "Transformation", register=False)
def canvasheight(values, feature, parent):
    """
        Return the height of the current canvas (in pixels or map units)
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">canvas_height(</span>
        <span class="argument">unit</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">unit</td><td>the unit in which the size is returned ('pixels' or 'mapunits')</td></tr>
        </table>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>canvas_height('mapunits')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("CanvasHeight")
    mapCanvas = iface.mapCanvas()
    if values[0]=='pixels':
        res = iface.mapCanvas().mapRenderer().height()
    elif values[0]=='mapunits':
        res = iface.mapCanvas().mapRenderer().height()*iface.mapCanvas().mapRenderer().mapUnitsPerPixel ()
    elif values[0]=='mm':
        pass
    try:
        return res
    except:
        parent.setEvalErrorString("error: argument not valid")

@qgsfunction(0, "Transformation", register=False, usesgeometry=True)
def canvasx(values, feature, parent):
    """
        Return the height of the current canvas (in pixels or map units)
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">canvas_height(</span>
        <span class="argument">unit</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">unit</td><td>the unit in which the size is returned ('pixels' or 'mapunits')</td></tr>
        </table>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>canvas_height('mapunits')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("canvasx")
    if iface.mapCanvas().mapRenderer().extent().intersects(feature.geometry().boundingBox()):
        leftX = iface.mapCanvas().mapRenderer().extent().xMinimum()
        featX = feature.geometry().pointOnSurface ().boundingBox().xMinimum()
        dbg.out(leftX)
        dbg.out(featX)
        canvasX = round ((featX-leftX)/iface.mapCanvas().mapRenderer().mapUnitsPerPixel())
        return canvasX
    else:
        return

@qgsfunction(0, "Transformation", register=False, usesgeometry=True)
def canvasy(values, feature, parent):
    """
        Return the height of the current canvas (in pixels or map units)
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">canvas_height(</span>
        <span class="argument">unit</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">unit</td><td>the unit in which the size is returned ('pixels' or 'mapunits')</td></tr>
        </table>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>canvas_height('mapunits')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("canvasy")
    if iface.mapCanvas().mapRenderer().extent().intersects(feature.geometry().boundingBox()):
        bottomY = iface.mapCanvas().mapRenderer().extent().yMinimum()
        featY = feature.geometry().pointOnSurface ().boundingBox().yMinimum()
        dbg.out(bottomY)
        dbg.out(featY)
        canvasY = round ((featY-bottomY)/iface.mapCanvas().mapRenderer().mapUnitsPerPixel())
        return canvasY
    else:
        return


@qgsfunction(1, "Reference", register=False)
def WKTcentroid(values, feature, parent):
    """
        Return the center of mass of the given geometry
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">WKTcentroid(</span>
        <span class="argument">WKTgeometry</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">WKTgeometry</td><td>a valid WKT geometry provided by expression commands </td></tr>
        </table>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>WKTcentroid('POLYGON((602793.98 6414014.88,....))')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("centroid")
    ArgGeometry = QgsGeometry().fromWkt(values[0])
    try:
        return ArgGeometry.centroid().asWkt()
    except:
        parent.setEvalErrorString("error: WKT geometry not valid")
        return


@qgsfunction(1, "Reference", register=False)
def WKTpointonsurface(values, feature, parent):
    """
        Return the point within the given geometry
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">WKTpointonsurface(</span>
        <span class="argument">WKTgeometry</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">WKTgeometry</td><td>a valid WKT geometry provided by expression commands </td></tr>
        </table>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>WKTpointonsurface('POLYGON((602793.98 6414014.88,....))')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("centroid")
    ArgGeometry = QgsGeometry().fromWkt(values[0])
    try:
        return ArgGeometry.pointOnSurface().asWkt()
    except:
        parent.setEvalErrorString("error: WKT geometry not valid")
        return

@qgsfunction(1, "Reference", register=False)
def WKTlength(values, feature, parent):
    """
        Return the length of the given geometry
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">WKTlength(</span>
        <span class="argument">WKTgeometry</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">WKTgeometry</td><td>a valid WKT geometry provided by expression commands </td></tr>
        </table>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>WKTlength('LINESTRING(602793.98 6414014.88,....)')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("length")
    ArgGeometry = QgsGeometry().fromWkt(values[0])
    try:
        return ArgGeometry.length()
    except:
        parent.setEvalErrorString("error: WKT geometry not valid")
        return

@qgsfunction(1, "Reference", register=False)
def WKTarea(values, feature, parent):
    """
        Return the area of the given geometry
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">WKTarea(</span>
        <span class="argument">WKTgeometry</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">WKTgeometry</td><td>a valid WKT geometry provided by expression commands </td></tr>
        </table>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>WKTarea('POLYGON((602793.98 6414014.88,....))')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("area")
    ArgGeometry = QgsGeometry().fromWkt(values[0])
    try:
        print(ArgGeometry.asWkt() )
        return ArgGeometry.area()
    except:
        #parent.setEvalErrorString("error: WKT geometry not valid")
        return None

@qgsfunction(2, "Reference", register=False, usesgeometry=True)
def geomnearest(values, feature, parent):
    """
        Retrieve target_field value from the nearest feature in target_layer
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomnearest(</span>
        <span class="argument">target_layer, target_field</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when target feature is the nearest from source feature, for example 'myField'.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        <br/>If target_field is equal to '$id' the feature id of target feature will be retrieved.
        <br/>If target_field is equal to '$distance' the calculated distance between source and target features will be returned.</td></tr>
        </table>
        <i>Number of feature tested is limited to 100000 to avoid time wasting loops</i>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomnearest('targetLayer','TargetField')</code></li>
        <li><code>geomnearest('targetLayer','$geometry')</code></li>
        <li><code>geomnearest('targetLayer','$id')</code></li>
        <li><code>geomnearest('targetLayer','$distance')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating geomnearest")
    targetLayerName = values[0]
    targetFieldName = values[1]
    dmin = sys.float_info.max
    actualGeom = feature.geometry()
    layerSet = _getLayerSet()
    if not targetLayerName in layerSet.keys():
        parent.setEvalErrorString("error: targetLayer not present")
        return
    count = 0
    for name, layer in layerSet.items():
        if layer != iface.mapCanvas().currentLayer() and layer.type() == QgsMapLayer.VectorLayer and (targetLayerName == '' or layer.name() == targetLayerName ):
            dbg.out(layer.name())
            iter = layer.getFeatures()
            for feat in iter:
                dtest = actualGeom.distance(feat.geometry())
                count += 1
                if count < 100000:
                    if dtest<dmin:
                        dmin = dtest
                        if targetFieldName=="$geometry":
                            dminRes = feat.geometry().asWkt()
                        elif targetFieldName=="$distance":
                            dminRes = dmin
                        elif targetFieldName=="$id":
                            dminRes = feat.id()
                        else:
                            try:
                                dminRes = feat.attribute(targetFieldName)
                            except:
                                parent.setEvalErrorString("error: targetFieldName not present")
                                return
                else:
                    parent.setEvalErrorString("error: too many features to compare")
    dbg.out("DMIN")
    dbg.out(dmin)
    if count > 0:
        try:
            return dminRes
        except:
            return -1
    else:
        parent.setEvalErrorString("error: no features to compare")


@qgsfunction(3, "Reference", register=False, usesgeometry=True)
def geomdistance(values, feature, parent):
    """
        Retrieve target_field value from feature in target_layer if target feature is in distance
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomdistance(</span>
        <span class="argument">target_layer, target_field, distance</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when target feature is the nearest from source feature, for example 'myField'.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        <br/>If target_field is equal to '$id' the feature id of target feature will be retrieved.
        <br/>If target_field is equal to '$distance' the calculated distance between source and target features will be returned.</td></tr>
        <tr><td class="argument">distance</td><td>the maximum distance from feature to be considered.</td></tr>
        </table>
        <i>Number of feature tested is limited to 100000 to avoid time wasting loops</i>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomdistance('targetLayer','TargetField',100)</code></li>
        <li><code>geomdistance('targetLayer','$geometry',100)</code></li>
        <li><code>geomdistance('targetLayer','$id',100)</li>
        <li><code>geomdistance('targetLayer','$distance',100)</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating geomdistance")
    targetLayerName = values[0]
    targetFieldName = values[1]
    distanceCheck = values[2]
    dmin = sys.float_info.max
    actualGeom = feature.geometry()
    layerSet = _getLayerSet()
    if not targetLayerName in layerSet.keys():
        parent.setEvalErrorString("error: targetLayer not present")
        return
    count = 0
    for name,layer in layerSet.items():
        if layer != iface.mapCanvas().currentLayer() and layer.type() == QgsMapLayer.VectorLayer and (targetLayerName == '' or layer.name() == targetLayerName ):
            dbg.out(layer.name())
            iter = layer.getFeatures()
            for feat in iter:
                dtest = actualGeom.distance(feat.geometry())
                count += 1
                if count < 100000:
                    if dtest<dmin and dtest<=distanceCheck:
                        dmin = dtest
                        if targetFieldName=="$geometry":
                            dminRes = feat.geometry().asWkt()
                        elif targetFieldName=="$distance":
                            dminRes = dmin
                        elif targetFieldName=="$id":
                            dminRes = feat.id()
                        else:
                            try:
                                dminRes = feat.attribute(targetFieldName)
                            except:
                                parent.setEvalErrorString("error: targetFieldName not present")
                                return
                else:
                    parent.setEvalErrorString("error: too many features to compare")
    dbg.out("DMIN")
    dbg.out(dmin)
    if count > 0:
        try:
            return dminRes
        except:
            return -1
    else:
        parent.setEvalErrorString("error: no features to compare")
        

# Update Sigmoé
# Main function used by all the geom... functions
def geomsteval(values, feature, parent, predic, dbg):
    targetLayerName = values[0]
    targetFieldName = values[1]
    #layerSet = {layer.name():layer for layer in iface.legendInterface().layers()}
    layerSet = _getLayerSet()
    if not (targetLayerName in layerSet.keys()):
        parent.setEvalErrorString("error: targetLayer not present")
        return
    dbg.out(layerSet)
    dbg.out(layerSet[targetLayerName].id())
    if layerSet[targetLayerName].type() != QgsMapLayer.VectorLayer:
        parent.setEvalErrorString("error: targetLayer is not a vector layer")
        return
    count = 0
    dminRes = ""
    dminResLst = []
    for feat in layerSet[targetLayerName].getFeatures():
        count += 1
        if count < 100000:
            if eval("feature.geometry()." + predic + "(feat.geometry())"):
                if targetFieldName=="$geometry":
                    dminRes = feat.geometry().asWkt()
                elif targetFieldName=="$id":
                    dminRes = feat.id()
                else:
                    try:
                        # Case of concatenation of several attribute values
                        if "+" in targetFieldName:
                            fld_names = targetFieldName.split("+")
                            nw_val = ""
                            for fld_name in fld_names:
                                if feat.attribute(fld_name):
                                    nw_val += str(feat.attribute(fld_name)) + " "
                            nw_val = nw_val[:-1]
                        else:
                            nw_val = feat.attribute(targetFieldName)
                        if nw_val not in dminResLst:
                            if dminRes != "":
                                dminRes = str(dminRes) + " | " + str(nw_val)
                            else:
                                dminRes = nw_val
                            dminResLst.append(nw_val)
                    except:
                        parent.setEvalErrorString("error: targetFieldName not present")
                        return None
        else:
            parent.setEvalErrorString("error: too many features to compare")
    if count > 0:
        try:
            return dminRes
        except:
            return None
    else:
        parent.setEvalErrorString("error: no features to compare")
        return None

# Updated Sigmoé
@qgsfunction(2, "Reference", register=False,usesgeometry=True)
def geomwithin(values, feature, parent):
    """
        Retrieve target_field value when source feature is within feature in target_layer.
        If more than one object found, return a unique value composed of the value of each object separated by | (list of unique values).
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomwithin(</span>
        <span class="argument">target_layer, target_field</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when source feature is within target feature, for example 'myField'.
        <br/>If target_field contains the name of several fields separated by +, the result is the concatenation of the result value of each field.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        <br/>If target_field is equal to '$id' the feature id of target feature will be retrieved.</td></tr>
        </table>
        <i>Number of feature tested is limited to 100000 to avoid time wasting loops</i>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomwithin('targetLayer','TargetField')</code></li>
        <li><code>geomwithin('targetLayer','TargetField1+TargetField12')</code></li>
        <li><code>geomwithin('targetLayer','$geometry')</code></li>
        <li><code>geomwithin('targetLayer','$id')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating geomwithin")
    return geomsteval(values, feature, parent, "within", dbg)


# Updated Sigmoé
@qgsfunction(2, "Reference", register=False,usesgeometry=True)
def geomtouches(values, feature, parent):
    """
        Retrieve target_field value when source feature touches feature in target_layer.
        If more than one object found, return a unique value composed of the value of each object separated by | (list of unique values).
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomtouches(</span>
        <span class="argument">target_layer, target_field</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when source feature touches target feature, for example 'myField'.
        <br/>If target_field contains the name of several fields separated by +, the result is the concatenation of the result value of each field.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        <br/>If target_field is equal to '$id' the feature id of target feature will be retrieved.</td></tr>
        </table>
        <i>Number of feature tested is limited to 100000 to avoid time wasting loops</i>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomtouches('targetLayer','TargetField')</code></li>
        <li><code>geomtouches('targetLayer','TargetField1+TargetField12')</code></li>
        <li><code>geomtouches('targetLayer','$geometry')</code></li>
        <li><code>geomtouches('targetLayer','$id')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating geomtouches")
    return geomsteval(values, feature, parent, "touches", dbg)
        

# Updated Sigmoé
@qgsfunction(2, "Reference", register=False,usesgeometry=True)
def geomintersects(values, feature, parent):
    """
        Retrieve target_field value when source feature intersects feature in target_layer. If more than one object found, return a unique value composed of the value of each object separated by | (list of unique values).
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomintersects(</span>
        <span class="argument">target_layer, target_field</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when source feature intersects target feature, for example 'myField'.
        <br/>If target_field contains the name of several fields separated by +, the result is the concatenation of the result value of each field.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        <br/>If target_field is equal to '$id' the feature id of target feature will be retrieved.</td></tr>
        </table>
        <i>Number of feature tested is limited to 100000 to avoid time wasting loops</i>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomintersects('targetLayer','TargetField')</code></li>
        <li><code>geomintersects('targetLayer','TargetField1+TargetField12')</code></li>
        <li><code>geomintersects('targetLayer','$geometry')</code></li>
        <li><code>geomintersects('targetLayer','$id')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating geomintersects")
    return geomsteval(values, feature, parent, "intersects", dbg)


# Updated Sigmoé
@qgsfunction(2, "Reference", register=False, usesgeometry=True)
def geomcontains(values, feature, parent):
    """
        Retrieve target_field value when source feature contains feature in target_layer. If more than one object found, return a unique value composed of the value of each object separated by | (list of unique values).
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomcontains(</span>
        <span class="argument">target_layer, target_field</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when source feature contains target feature, for example 'myField'.
        <br/>If target_field contains the name of several fields separated by +, the result is the concatenation of the result value of each field.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        <br/>If target_field is equal to '$id' the feature id of target feature will be retrieved.</td></tr>
        </table>
        <i>Number of feature tested is limited to 100000 to avoid time wasting loops</i>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomcontains('targetLayer','TargetField')</code></li>
        <li><code>geomcontains('targetLayer','TargetField1+TargetField12')</code></li>
        <li><code>geomcontains('targetLayer','$geometry')</code></li>
        <li><code>geomcontains('targetLayer','$id')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating geomcontains")
    return geomsteval(values, feature, parent, "contains", dbg)
    

# Updated Sigmoé
@qgsfunction(2, "Reference", register=False,usesgeometry=True)
def geomdisjoint(values, feature, parent):
    """
        Retrieve target_field value when source feature is disjoint from target feature in target_layer. If more than one object found, return a unique value composed of the value of each object separated by | (list of unique values).
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomdisjoint(</span>
        <span class="argument">target_layer, target_field</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when source feature is disjoint from target feature, for example 'myField'.
        <br/>If target_field contains the name of several fields separated by +, the result is the concatenation of the result value of each field.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        <br/>If target_field is equal to '$id' the feature id of target feature will be retrieved.</td></tr>
        </table>
        <i>Number of feature tested is limited to 100000 to avoid time wasting loops</i>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomdisjoint('Parcels','Id')</code></li>
        <li><code>geomdisjoint('Parcels','section+number')</code></li>
        <li><code>geomdisjoint('Buildings','$geometry')</code></li>
        <li><code>geomdisjoint('Buildings','$id')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating geomdisjoint")
    return geomsteval(values, feature, parent, "disjoint", dbg)
    
        
# Updated Sigmoé
@qgsfunction(2, "Reference", register=False,usesgeometry=True)
def geomequals(values, feature, parent):
    """
        Retrieve target_field value when source feature is equal (same geometry) to feature in target_layer. If more than one object found, return a unique value composed of the value of each object separated by | (list of unique values).
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomequals(</span>
        <span class="argument">target_layer, target_field</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when source feature is equal to target feature, for example 'myField'.
        <br/>If target_field contains the name of several fields separated by +, the result is the concatenation of the result value of each field.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        <br/>If target_field is equal to '$id' the feature id of target feature will be retrieved.</td></tr>
        </table>
        <i>Number of feature tested is limited to 100000 to avoid time wasting loops</i>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomequals('targetLayer','TargetField')</code></li>
        li><code>geomequals('targetLayer','TargetField1+TargetField12')</code></li>
        <li><code>geomequals('targetLayer','$geometry')</code></li>
        <li><code>geomequals('targetLayer','$id')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating geomcontains")
    return geomsteval(values, feature, parent, "equals", dbg)


# Updated Sigmoé
@qgsfunction(2, "Reference", register=False,usesgeometry=True)
def geomoverlaps(values, feature, parent):
    """
        Retrieve target_field value when source feature overlaps feature in target_layer. If more than one object found, return a unique value composed of the value of each object separated by | (list of unique values).
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomoverlaps(</span>
        <span class="argument">target_layer, target_field</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when source feature overlaps target feature, for example 'myField'.
        <br/>If target_field contains the name of several fields separated by +, the result is the concatenation of the result value of each field.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        <br/>If target_field is equal to '$id' the feature id of target feature will be retrieved.</td></tr>
        </table>
        <i>Number of feature tested is limited to 100000 to avoid time wasting loops</i>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomoverlaps('targetLayer','TargetField')</code></li>
        <li><code>geomoverlaps('targetLayer','TargetField1+TargetField12')</code></li>
        <li><code>geomoverlaps('targetLayer','$geometry')</code></li>
        <li><code>geomoverlaps('targetLayer','$id')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating geomcontains")
    return geomsteval(values, feature, parent, "overlaps", dbg)
    

# Updated Sigmoé
@qgsfunction(2, "Reference", register=False,usesgeometry=True)
def geomcrosses(values, feature, parent):
    """
        Retrieve target_field value when source feature crosses feature in target_layer. If more than one object found, return a unique value composed of the value of each object separated by | (list of unique values).
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">geomcrosses(</span>
        <span class="argument">target_layer, target_field</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>the name of a currently loaded layer, for example 'myLayer'.</td></tr>
        <tr><td class="argument">target_field</td><td>a field in target_layer we want as result when source feature crosses target feature, for example 'myField'.
        <br/>If target_field contains the name of several fields separated by +, the result is the concatenation of the result value of each field.
        <br/>If target_field is equal to '$geometry' the WKT geometry of target feature will be retrieved.
        <br/>If target_field is equal to '$id' the feature id of target feature will be retrieved.</td></tr>
        </table>
        <i>Number of feature tested is limited to 100000 to avoid time wasting loops</i>
        </div>
        <h4>Examples</h4>
        <!-- Show examples of function.-->
        <div class="examples"><ul>
        <li><code>geomcrosses('targetLayer','TargetField')</code></li>
        <li><code>geomcrosses('targetLayer','TargetField1+TargetField12')</code></li>
        <li><code>geomcrosses('targetLayer','$geometry')</code></li>
        <li><code>geomcrosses('targetLayer','$id')</code></li>
        </ul></div>
    """
    dbg=debug()
    dbg.out("evaluating geomcrosses")
    return geomsteval(values, feature, parent, "crosses", dbg)      
        

# Updated Sigmoé
# Main function used by ...geom_count functions
def stgeomcounteval(values, feature, parent, predic):
    DEBUG = False
    try:    #qgis 3
        if DEBUG : print('feat geom ',feature.geometry().asPolygon(), feature.geometry().area(), feature.hasGeometry())
    except: #qgis 2
        if DEBUG : print('feat geom ', feature.geometry())
    
    targetLayerName = values[0]
    #targetFieldName = values[1]
    
    if feature.geometry() is not None:        
        #layerSet = {layer.name():layer for layer in iface.legendInterface().layers()}
        layerSet = _getLayerSet()
        
        
        if not (targetLayerName in layerSet.keys()):
            parent.setEvalErrorString("error: targetLayer not present")
            return
        if layerSet[targetLayerName].type() != qgis.core.QgsMapLayer.VectorLayer:
            parent.setEvalErrorString("error: targetLayer is not a vector layer")
            return
            
        count = 0
        
        request = qgis.core.QgsFeatureRequest()
        request.setFilterRect(feature.geometry().boundingBox())
        for feat in layerSet[targetLayerName].getFeatures(request):
            if eval("feat.geometry()."+ predic + "(feature.geometry())"):
                count += 1
        if DEBUG : print('feat ',feature.id(),'count',count)
        return count
        
    else:
        return False

        
# Updated Sigmoé
@qgsfunction(args=1, group="Reference",register = False, usesgeometry=True)
def intersecting_geom_count(values, feature, parent):
    """
        Get the count of the features in target_layer that intersect the source feature
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">intersecting_geom_count(</span>
        <span class="argument">'target_layer'</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>name of the target layer, for example 'Trees'.</td></tr>
        </table></div>
        <h4>Examples</h4>
        <!-- Show example of function.-->
        <div class="examples"><ul>
        <li><code>intersecting_geom_count('Trees')</code> &rarr; <code>126</code></li>
        </ul></div>
    """ 
    
    return stgeomcounteval(values, feature, parent, "intersects")
            

@qgsfunction(args=1, group='Reference',register = False, usesgeometry=True)
def within_geom_count(values, feature, parent):
    """
        Get the count of the features in target_layer that are within the source feature
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">within_geom_count(</span>
        <span class="argument">'target_layer'</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>name of the target layer, for example 'Trees'.</td></tr>
        </table></div>
        <h4>Examples</h4>
        <!-- Show example of function.-->
        <div class="examples"><ul>
        <li><code>within_geom_count('Trees')</code> &rarr; <code>126</code></li>
        </ul></div>
    """ 
    
    return stgeomcounteval(values, feature, parent, "within")
        
@qgsfunction(args=1, group='Reference',register = False, usesgeometry=True)
def overlapping_geom_count(values, feature, parent):
    """
        Get the count of the features in target_layer overlaping the source feature
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">overlapping_geom_count(</span>
        <span class="argument">'target_layer'</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>name of the target layer, for example 'Trees'.</td></tr>
        </table></div>
        <h4>Examples</h4>
        <!-- Show example of function.-->
        <div class="examples"><ul>
        <li><code>overlapping_geom_count('Trees')</code> &rarr; <code>126</code></li>
        </ul></div>
    """ 
    
    return stgeomcounteval(values, feature, parent, "overlaps")

            

@qgsfunction(args=1, group='Reference',register = False, usesgeometry=True)
def equaling_geom_count(values, feature, parent):
    """
        Get the count of the features in target_layer that are equals (same geometry) to the source feature
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">equaling_geom_count(</span>
        <span class="argument">'target_layer'</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>name of the target layer, for example 'Trees'.</td></tr>
        </table></div>
        <h4>Examples</h4>
        <!-- Show example of function.-->
        <div class="examples"><ul>
        <li><code>equaling_geom_count('Trees')</code> &rarr; <code>126</code></li>
        </ul></div>
    """ 
    
    return stgeomcounteval(values, feature, parent, "isGeosEqual")  
            
            
# Updated Sigmoé
# Main function used by ...geom_sum functions
def stgeomsumeval(values, feature, parent, predic):
    DEBUG = False
    
    try:    #qgis 3
        if DEBUG : print('feat geom ',feature.geometry().asPolygon(), feature.geometry().area(), feature.hasGeometry())
    except: #qgis 2
        if DEBUG : print('feat geom ', feature.geometry())
    
    targetLayerName = values[0]
    targetFieldName = values[1]
    
    if feature.geometry() is not None:
        #layerSet = {layer.name():layer for layer in iface.legendInterface().layers()}
        layerSet = _getLayerSet()
            
        if not (targetLayerName in layerSet.keys()):
            parent.setEvalErrorString("error: targetLayer not present")
            return
        if layerSet[targetLayerName].type() != qgis.core.QgsMapLayer.VectorLayer:
            parent.setEvalErrorString("error: targetLayer is not a vector layer")
            return
            
        count = 0.0
        
        request = qgis.core.QgsFeatureRequest()
        request.setFilterRect(feature.geometry().boundingBox())
        for feat in layerSet[targetLayerName].getFeatures(request):
            if eval("feat.geometry()." + predic + "(feature.geometry())"):
                try:
                    count += float(feat[targetFieldName])
                except:
                    #case feat[targetFieldName] is null or string....
                    pass
        if DEBUG : print('feat ',feature.id(),'count',count)
        return count
        
    else:
        return False



@qgsfunction(args=2, group="Reference",register = False, usesgeometry=True)
def intersecting_geom_sum(values, feature, parent):
    """
        Return the sum of the field_to_sum values of the objects in the target_layer that intersect the source feature
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">intersecting_geom_sum(</span>
        <span class="argument">'target_layer', 'field_to_sum'</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>name of the target layer, for example 'Roads'.</td></tr>
        <tr><td class="argument">field_to_sum</td><td>name of the field to sum, for example 'Roadlength'</td></tr>
        </table></div>
        <h4>Examples</h4>
        <!-- Show example of function.-->
        <div class="examples"><ul>
        <li><code>intersecting_geom_sum('Roads','Roadlength')</code> &rarr; <code>12569.63</code></li>
        </ul></div>
    """ 
    
    return stgeomsumeval(values, feature, parent, "intersects")
        
        

@qgsfunction(args=2, group='Reference',register = False, usesgeometry=True)
def within_geom_sum(values, feature, parent):
    """
        Return the sum of the field_to_sum values of the objects in the target_layer that are within the source feature
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">within_geom_sum(</span>
        <span class="argument">'target_layer', 'field_to_sum'</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>name of the target layer, for example 'Roads'.</td></tr>
        <tr><td class="argument">field_to_sum</td><td>name of the field to sum, for example 'Roadlength'</td></tr>
        </table></div>
        <h4>Examples</h4>
        <!-- Show example of function.-->
        <div class="examples"><ul>
        <li><code>within_geom_sum('Roads','Roadlength')</code> &rarr; <code>12569.63</code></li>
        </ul></div>
    """ 
    
    return stgeomsumeval(values, feature, parent, "within")
        

@qgsfunction(args=2, group='Reference',register = False, usesgeometry=True)
def overlapping_geom_sum(values, feature, parent):
    """
        Return the sum of the field_to_sum values of the objects in the target_layer overlapping the source feature
        <h4>Syntax</h4>
        <div class="syntax"><code>
        <span class="functionname">overlapping_geom_sum(</span>
        <span class="argument">'target_layer', 'field_to_sum'</span>
        <span class="functionname">)</span>
        </code></div>
        <h4>Arguments</h4>
        <div class="arguments">
        <table>
        <tr><td class="argument">target_layer</td><td>name of the target layer, for example 'Roads'.</td></tr>
        <tr><td class="argument">field_to_sum</td><td>name of the field to sum, for example 'Roadlength'</td></tr>
        </table></div>
        <h4>Examples</h4>
        <!-- Show example of function.-->
        <div class="examples"><ul>
        <li><code>overlapping_geom_sum('Roads','Roadlength')</code> &rarr; <code>12569.63</code></li>
        </ul></div>
    """ 
    
    return stgeomsumeval(values, feature, parent, "overlaps")

        
        
        
        
class debug:

    def __init__(self):
        self.debug = None

    def out(self,string):
        if self.debug:
            print(string)

class SQLconnection:

    def __init__(self,conn):
        self.dbg = debug()
        s = QSettings()
        s.beginGroup("PostgreSQL/connections/"+conn)
        currentKeys = s.childKeys()
        self.PSQLDatabase=s.value("database", "" )
        self.PSQLHost=s.value("host", "" )
        self.PSQLUsername=s.value("username", "" )
        self.PSQLPassword=s.value("password", "" )
        self.PSQLPort=s.value("port", "" )
        self.PSQLService=s.value("service", "" )
        s.endGroup()
        self.db = QSqlDatabase.addDatabase("QPSQL")
        self.db.setHostName(self.PSQLHost)
        self.db.setPort(int(self.PSQLPort))
        self.db.setDatabaseName(self.PSQLDatabase)
        self.db.setUserName(self.PSQLUsername)
        self.db.setPassword(self.PSQLPassword)
        ok = self.db.open()
        if not ok:
            self.error = "Database Error: %s" % self.db.lastError().text()
            #QMessageBox.information(None, "DB ERROR:", error)
        else:
            self.error=""

    def submitQuery(self,sql):
        query = QSqlQuery(self.db)
        query.exec_(sql)
        self.dbg.out(sql)
        rows= []
        self.dbg.out("SQL RESULT:")
        self.dbg.out(query.lastError().type())
        self.dbg.out(query.lastError().text())
        if query.lastError().type() != QSqlError.NoError:
            self.error = "Database Error: %s" % query.lastError().text()
            #QMessageBox.information(None, "SQL ERROR:", resultQuery)
        else:
            self.error = ""
            while (query.next()):
                fields=[]
                count = 0
                #query.value(count)
                for k in range(0,query.record().count()):
                    try:
                        fields.append(unicode(query.value(k), errors='replace'))
                    except TypeError:
                        fields.append(query.value(k))
                    except AttributeError:
                        fields.append(str(query.value(k)))
                rows += [fields]
        self.dbg.out(rows)
        return rows

    def lastError(self):
        return self.error

class refFunctions:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        self.dbg = debug()
        self.dlg = refFunctionsDialog()

        # Create the dialog (after translation) and keep reference
        #self.dlg = refFunctionDialog()


    def initGui(self):
        self.dbg.out("initGui")
        QgsExpression.registerFunction(dbvalue)
        QgsExpression.registerFunction(dbvaluebyid)
        QgsExpression.registerFunction(dbquery)
        QgsExpression.registerFunction(dbsql)
        QgsExpression.registerFunction(WKTarea)
        QgsExpression.registerFunction(WKTcentroid)
        QgsExpression.registerFunction(WKTpointonsurface)
        QgsExpression.registerFunction(WKTlength)
        QgsExpression.registerFunction(geomRedef)
        QgsExpression.registerFunction(geomnearest)
        QgsExpression.registerFunction(geomdistance)
        QgsExpression.registerFunction(geomwithin)
        QgsExpression.registerFunction(geomcontains)
        QgsExpression.registerFunction(geomcrosses)
        QgsExpression.registerFunction(geomdisjoint)
        QgsExpression.registerFunction(geomequals)
        QgsExpression.registerFunction(geomintersects)
        QgsExpression.registerFunction(geomoverlaps)
        QgsExpression.registerFunction(geomtouches)
        QgsExpression.registerFunction(canvaswidth)
        QgsExpression.registerFunction(canvasheight)
        QgsExpression.registerFunction(canvasx)
        QgsExpression.registerFunction(canvasy)
        
        QgsExpression.registerFunction(intersecting_geom_count)
        QgsExpression.registerFunction(within_geom_count)
        QgsExpression.registerFunction(overlapping_geom_count)
        QgsExpression.registerFunction(intersecting_geom_sum)
        QgsExpression.registerFunction(within_geom_sum)
        QgsExpression.registerFunction(overlapping_geom_sum)
        
        QgsExpression.registerFunction(equaling_geom_count)
        
        icon_path = os.path.join(self.plugin_dir,"icon.png")
        # map tool action
        self.action = QAction(QIcon(icon_path),"refFunctions", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&refFunctions", self.action)


    def unload(self):
        QgsExpression.unregisterFunction('dbvalue')
        QgsExpression.unregisterFunction('dbvaluebyid')
        QgsExpression.unregisterFunction('dbquery')
        QgsExpression.unregisterFunction('dbsql')
        QgsExpression.unregisterFunction('WKTarea')
        QgsExpression.unregisterFunction('WKTcentroid')
        QgsExpression.unregisterFunction('WKTpointonsurface')
        QgsExpression.unregisterFunction('WKTlength')
        QgsExpression.unregisterFunction('geomRedef')
        QgsExpression.unregisterFunction('geomnearest')
        QgsExpression.unregisterFunction('geomdistance')
        QgsExpression.unregisterFunction('geomwithin')
        QgsExpression.unregisterFunction('geomcontains')
        QgsExpression.unregisterFunction('geomcrosses')
        QgsExpression.unregisterFunction('geomdisjoint')
        QgsExpression.unregisterFunction('geomequals')
        QgsExpression.unregisterFunction('geomintersects')
        QgsExpression.unregisterFunction('geomoverlaps')
        QgsExpression.unregisterFunction('geomtouches')
        QgsExpression.unregisterFunction('canvaswidth')
        QgsExpression.unregisterFunction('canvasheight')
        QgsExpression.unregisterFunction('canvasx')
        QgsExpression.unregisterFunction('canvasy')
        
        QgsExpression.unregisterFunction('intersecting_geom_count')
        QgsExpression.unregisterFunction('within_geom_count')
        QgsExpression.unregisterFunction('overlapping_geom_count')
        QgsExpression.unregisterFunction('intersecting_geom_sum')
        QgsExpression.unregisterFunction('within_geom_sum')
        QgsExpression.unregisterFunction('overlapping_geom_sum')
        
        QgsExpression.unregisterFunction('equaling_geom_count')
        
        self.iface.removePluginMenu(u"&refFunctions", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        self.dlg.show()
