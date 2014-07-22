"""
********************************************************************************
* Name: WMSDataset
* Author: Nathan Swain
* Created On: July 8, 2014
* Copyright: (c) Brigham Young University 2014
* License: BSD 2-Clause
********************************************************************************
"""


__all__ = ['WMSDatasetFile', 'WMSDatasetRaster']

import os
from datetime import datetime, timedelta
from zipfile import ZipFile

from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Integer, String, Float
from sqlalchemy.orm import relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase
from gsshapy.lib import parsetools as pt, wms_dataset_chunk as wdc
from gsshapy.orm.map import RasterMapFile
from gsshapy.orm.rast import RasterObject

from mapkit.RasterLoader import RasterLoader
from mapkit.RasterConverter import RasterConverter
from mapkit.sqlatypes import Raster


class WMSDatasetFile(DeclarativeBase, GsshaPyFileObjectBase):
    """
    File object for interfacing with WMS Gridded and Vector Datasets
    """
    __tablename__ = 'wms_dataset_files'

    tableName = __tablename__  #: Database tablename

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    projectFileID = Column(Integer, ForeignKey('prj_project_files.id'))  #: FK

    # Value Columns
    type = Column(Integer)  #: INTEGER
    fileExtension = Column(String, default='txt')  #: STRING
    objectType = Column(String)  #: STRING
    vectorType = Column(String)  #: STRING
    objectID = Column(Integer)  #: INTEGER
    numberData = Column(Integer)  #: INTEGER
    numberCells = Column(Integer)  #: INTEGER
    name = Column(String)  #: STRING

    # Relationship Properties
    projectFile = relationship('ProjectFile', back_populates='wmsDatasets')  #: RELATIONSHIP
    rasters = relationship('WMSDatasetRaster', back_populates='wmsDataset')  #: RELATIONSHIP

    # File Properties
    SCALAR_TYPE = 1
    VECTOR_TYPE = 0
    VALID_DATASET_TYPES = (VECTOR_TYPE, SCALAR_TYPE)

    def __init__(self):
        """
        Constructor
        """
        GsshaPyFileObjectBase.__init__(self)

    def __repr__(self):
        if self.type == self.SCALAR_TYPE:
            return '<WMSDatasetFile: Name=%s, Type=%s, objectType=%s, objectID=%s, numberData=%s, numberCells=%s, FileExtension=%s>' % (
                self.name,
                'scalar',
                self.objectType,
                self.objectID,
                self.numberData,
                self.numberCells,
                self.fileExtension)

        elif self.type == self.VECTOR_TYPE:
            return '<WMSDatasetFile: Name=%s, Type=%s, vectorType=%s, objectID=%s, numberData=%s, numberCells=%s, FileExtension=%s>' % (
                self.name,
                'vector',
                self.vectorType,
                self.objectID,
                self.numberData,
                self.numberCells,
                self.fileExtension)
        else:
            return '<WMSDatasetFile: Name=%s, Type=%s, objectType=%s, vectorType=%s, objectID=%s, numberData=%s, numberCells=%s, FileExtension=%s>' % (
                self.name,
                self.type,
                self.objectType,
                self.vectorType,
                self.objectID,
                self.numberData,
                self.numberCells,
                self.fileExtension)

    def read(self, directory, filename, session, maskMap, spatial=False, spatialReferenceID=4236):
        """
        Read file into the database.
        """

        # Read parameter derivatives
        path = os.path.join(directory, filename)
        filename_split = filename.split('.')
        name = filename_split[0]

        # Default file extension
        extension = ''

        if len(filename_split) >= 2:
            extension = filename_split[-1]

        if os.path.isfile(path):
            # Add self to session
            session.add(self)

            # Read
            self._read(directory, filename, session, path, name, extension, spatial, spatialReferenceID, maskMap)

            # Commit to database
            self._commit(session, self.COMMIT_ERROR_MESSAGE)

        else:
            # Rollback the session if the file doesn't exist
            session.rollback()

            # Issue warning
            print 'WARNING: {0} listed in project file, but no such file exists.'.format(filename)

    def write(self, session, directory, name, maskMap):
        """
        Write from database to file.

        *session* = SQLAlchemy session object\n
        *directory* = to which directory will the files be written (e.g.: '/example/path')\n
        *name* = name of file that will be written (e.g.: 'my_project.ext')\n
        """

        # Assemble Path to file
        name_split = name.split('.')
        name = name_split[0]

        # Default extension
        extension = ''

        if len(name_split) >= 2:
            extension = name_split[-1]

        # Run name preprocessor method if present
        try:
            name = self._namePreprocessor(name)
        except:
            'DO NOTHING'

        if extension == '':
            filename = '{0}.{1}'.format(name, self.fileExtension)
        else:
            filename = '{0}.{1}'.format(name, extension)

        filePath = os.path.join(directory, filename)

        with open(filePath, 'w') as openFile:
            # Write Lines
            self._write(session=session,
                        openFile=openFile,
                        maskMap=maskMap)



    def getAsKmlGridAnimation(self, session, projectFile=None, path=None, colorRamp=None, documentName=None, alpha=1.0, noDataValue=0):
        """
        Retrieve the WMS dataset as a gridded time stamped KML string
        """
        # Prepare rasters
        timeStampedRasters = self._assembleRasterParams(projectFile, self.rasters)

        # Create a raster converter
        converter = RasterConverter(sqlAlchemyEngineOrSession=session)

        # Configure color ramp
        if isinstance(colorRamp, dict):
            converter.setCustomColorRamp(colorRamp['colors'], colorRamp['interpolatedPoints'])
        else:
            converter.setDefaultColorRamp(colorRamp)

        if documentName is None:
            documentName = self.fileExtension

        kmlString = converter.getAsKmlGridAnimation(tableName=WMSDatasetRaster.tableName,
                                                    timeStampedRasters=timeStampedRasters,
                                                    rasterIdFieldName='id',
                                                    rasterFieldName='raster',
                                                    documentName=documentName,
                                                    alpha=alpha,
                                                    noDataValue=noDataValue)

        if path:
            with open(path, 'w') as f:
                f.write(kmlString)

        return kmlString

    def getAsKmlPngAnimation(self, session, projectFile=None, path=None, colorRamp=None, documentName=None, alpha=1.0,
                             drawOrder=0, noDataValue=0, cellSize=None, resampleMethod='NearestNeighbour'):
        """
        Retrieve the WMS dataset as a PNG time stamped KMZ
        """
        # Prepare rasters
        timeStampedRasters = self._assembleRasterParams(projectFile, self.rasters)

        # Make sure the raster field is valid
        converter = RasterConverter(sqlAlchemyEngineOrSession=session)

        # Configure color ramp
        if isinstance(colorRamp, dict):
            converter.setCustomColorRamp(colorRamp['colors'], colorRamp['interpolatedPoints'])
        else:
            converter.setDefaultColorRamp(colorRamp)

        if documentName is None:
            documentName = self.fileExtension

        kmlString, binaryPngStrings = converter.getAsKmlPngAnimation(tableName=WMSDatasetRaster.tableName,
                                                                     timeStampedRasters=timeStampedRasters,
                                                                     rasterIdFieldName='id',
                                                                     rasterFieldName='raster',
                                                                     documentName=documentName,
                                                                     alpha=alpha,
                                                                     drawOrder=drawOrder,
                                                                     cellSize=cellSize,
                                                                     noDataValue=noDataValue,
                                                                     resampleMethod=resampleMethod)

        if path:
            directory = os.path.dirname(path)
            archiveName = (os.path.split(path)[1]).split('.')[0]
            kmzPath = os.path.join(directory, (archiveName + '.kmz'))

            with ZipFile(kmzPath, 'w') as kmz:
                kmz.writestr(archiveName + '.kml', kmlString)

                for index, binaryPngString in enumerate(binaryPngStrings):
                    kmz.writestr('raster{0}.png'.format(index), binaryPngString)

        return kmlString, binaryPngStrings

    def _read(self, directory, filename, session, path, name, extension, spatial, spatialReferenceID, maskMap):
        """
        WMS Dataset File Read from File Method
        """
        # Assign file extension attribute to file object
        self.fileExtension = extension

        if isinstance(maskMap, RasterMapFile) and maskMap.fileExtension == 'msk':
            # Vars from mask map
            columns = maskMap.columns
            rows = maskMap.rows
            upperLeftX = maskMap.west
            upperLeftY = maskMap.north

            # Derive the cell size (GSSHA cells are square, so it is the same in both directions)
            cellSizeX = int(abs(maskMap.west - maskMap.east) / columns)
            cellSizeY = -1 * cellSizeX

            # Dictionary of keywords/cards and parse function names
            KEYWORDS = {'DATASET': wdc.datasetHeaderChunk,
                        'TS': wdc.datasetScalarTimeStepChunk}

            # Open file and read plain text into text field
            with open(path, 'r') as f:
                chunks = pt.chunk(KEYWORDS, f)

            # Parse header chunk first
            header = wdc.datasetHeaderChunk('DATASET', chunks['DATASET'][0])

            # Parse each time step chunk and aggregate
            timeStepRasters = []

            for chunk in chunks['TS']:
                timeStepRasters.append(wdc.datasetScalarTimeStepChunk(chunk, columns, header['numberCells']))

            # Set WMS dataset file properties
            self.name = header['name']
            self.numberCells = header['numberCells']
            self.numberData = header['numberData']
            self.objectID = header['objectID']

            if header['type'] == 'BEGSCL':
                self.objectType = header['objectType']
                self.type = self.SCALAR_TYPE

            elif header['type'] == 'BEGVEC':
                self.vectorType = header['objectType']
                self.type = self.VECTOR_TYPE

            # Create WMS raster dataset files for each raster
            for timeStep, timeStepRaster in enumerate(timeStepRasters):
                # Create new WMS raster dataset file object
                wmsRasterDatasetFile = WMSDatasetRaster()

                # Set the wms dataset for this WMS raster dataset file
                wmsRasterDatasetFile.wmsDataset = self

                # Set the time step and timestamp and other properties
                wmsRasterDatasetFile.iStatus = timeStepRaster['iStatus']
                wmsRasterDatasetFile.timestamp = timeStepRaster['timestamp']
                wmsRasterDatasetFile.timeStep = timeStep + 1

                # If spatial is enabled create PostGIS rasters
                if spatial:
                    # Process the values/cell array
                    wmsRasterDatasetFile.raster = RasterLoader.makeSingleBandWKBRaster(session,
                                                                                       columns, rows,
                                                                                       upperLeftX, upperLeftY,
                                                                                       cellSizeX, cellSizeY,
                                                                                       0, 0,
                                                                                       spatialReferenceID,
                                                                                       timeStepRaster['cellArray'])

                # Otherwise, set the raster text properties
                else:
                    wmsRasterDatasetFile.rasterText = ''

            # Add current file object to the session
            session.add(self)

        else:
            print "WARNING: Could not read {0}. Mask Map must be supplied to read WMS Datasets.".format(filename)

    def _write(self, session, openFile, maskMap):
        """
        WMS Dataset File Write to File Method
        """
        # Magic numbers
        FIRST_VALUE_INDEX = 12

        # Write the header
        openFile.write('DATASET\r\n')

        if self.type == self.SCALAR_TYPE:
            openFile.write('OBJTYPE {0}\r\n'.format(self.objectType))
            openFile.write('BEGSCL\r\n')

        elif self.type == self.VECTOR_TYPE:
            openFile.write('VECTYPE {0}\r\n'.format(self.vectorType))
            openFile.write('BEGVEC\r\n')

        openFile.write('OBJID {0}\r\n'.format(self.objectID))
        openFile.write('ND {0}\r\n'.format(self.numberData))
        openFile.write('NC {0}\r\n'.format(self.numberCells))
        openFile.write('NAME {0}\r\n'.format(self.name))

        # Retrieve the mask map to use as the status rasters
        statusString = ''
        if isinstance(maskMap, RasterMapFile):
            # Convert Mask Map to GRASS ASCII Raster
            statusGrassRasterString = maskMap.getAsGrassAsciiGrid(session)

            # Split by lines
            statusValues = statusGrassRasterString.split()

            # Assemble into a string in the WMS Dataset format
            for i in range(FIRST_VALUE_INDEX, len(statusValues)):
                statusString += statusValues[i] + '\r\n'

        # Write time steps
        for timeStepRaster in self.rasters:
            # Write time step header
            openFile.write('TS {0} {1}\r\n'.format(timeStepRaster.iStatus, timeStepRaster.timestamp))

            # Write status raster (mask map) if applicable
            if timeStepRaster.iStatus == 1:
                openFile.write(statusString)

            # Write value raster
            valueString = timeStepRaster.getAsWmsDatasetString(session)

            if valueString is not None:
                openFile.write(valueString)

            else:
                print 'Not Spatial'

        # Write ending tag for the dataset
        openFile.write('ENDDS\r\n')

    def _assembleRasterParams(self, projectFile, rasters):
        # Assemble input for converter method
        timeStampedRasters = []
        startDateTime = datetime(1970, 1, 1)

        if projectFile is not None:
            # Get base time from project file if it is there
            startDate = projectFile.getCard('START_DATE')
            startTime = projectFile.getCard('START_TIME')

            if (startDate is not None) and (startTime is not None):
                startDateParts = startDate.value.split()
                startTimeParts = startTime.value.split()

                if len(startDateParts) >= 3 and len(startTimeParts) >= 2:
                    year = int(startDateParts[0])
                    month = int(startDateParts[1])
                    day = int(startDateParts[2])
                    hour = int(startTimeParts[0])
                    minute = int(startTimeParts[1])
                    startDateTime = datetime(year, month, day, hour, minute)

        for raster in rasters:
            # Create dictionary and populate
            timeStampedRaster = dict()
            timeStampedRaster['rasterId'] = raster.id

            # Calculate the delta times
            timestamp = raster.timestamp
            timestampDelta = timedelta(minutes=timestamp)

            # Create datetime objects
            timeStampedRaster['dateTime'] = startDateTime + timestampDelta

            # Add to the list
            timeStampedRasters.append(timeStampedRaster)

        return timeStampedRasters


class WMSDatasetRaster(DeclarativeBase, RasterObject):
    """
    File object for interfacing with WMS Gridded and Vector Datasets
    """
    __tablename__ = 'wms_dataset_rasters'

    # Public Table Metadata
    tableName = __tablename__  #: Database tablename
    rasterColumnName = 'raster'
    defaultNoDataValue = 0

    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)  #: PK
    datasetFileID = Column(Integer, ForeignKey('wms_dataset_files.id'))

    # Value Columns
    timeStep = Column(Integer)  #: INTEGER
    timestamp = Column(Float)  #: FLOAT
    iStatus = Column(Integer)  #: INTEGER
    rasterText = Column(String)  #: STRING
    raster = Column(Raster)  #: RASTER

    # Relationship Properties
    wmsDataset = relationship('WMSDatasetFile', back_populates='rasters')

    def __init__(self):
        """
        Constructor
        """

    def __repr__(self):
        return '<TimestampedRaster: TimeStep=%s, Timestamp=%s>' % (
            self.timeStep,
            self.timestamp)

    def getAsWmsDatasetString(self, session):
        """
        Retrieve the WMS Raster as a string in the WMS Dataset format
        """
        # Magic numbers
        FIRST_VALUE_INDEX = 12

        # Write value raster
        if type(self.raster) != type(None):
            # Convert to GRASS ASCII Raster
            valueGrassRasterString = self.getAsGrassAsciiGrid(session)

            # Split by lines
            values = valueGrassRasterString.split()

            # Assemble into string
            wmsDatasetString = ''
            for i in range(FIRST_VALUE_INDEX, len(values)):
                wmsDatasetString += '{0:.6f}\r\n'.format(float(values[i]))

            return wmsDatasetString