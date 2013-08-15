'''
********************************************************************************
* Name: StormPipeNetworkModel
* Author: Nathan Swain
* Created On: May 14, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

__all__ = ['StormPipeNetworkFile', 
           'SuperLink', 
           'SuperNode',
           'Pipe',
           'SuperJunction', 
           'Connection']

import os

from sqlalchemy import ForeignKey, Column
from sqlalchemy.types import Integer, Float
from sqlalchemy.orm import  relationship

from gsshapy.orm import DeclarativeBase
from gsshapy.orm.file_base import GsshaPyFileObjectBase
from gsshapy.lib import parsetools as pt, spn_chunk as spc


    
class StormPipeNetworkFile(DeclarativeBase, GsshaPyFileObjectBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_storm_pipe_network_files'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    
    # Relationship Properties
    connections = relationship('Connection', back_populates='stormPipeNetworkFile')
    superLinks = relationship('SuperLink', back_populates='stormPipeNetworkFile')
    superJunctions = relationship('SuperJunction', back_populates='stormPipeNetworkFile')
    projectFile = relationship('ProjectFile', uselist=False, back_populates='stormPipeNetworkFile')
    
    # File Properties
    EXTENSION = 'spn'
    
    def __init__(self, directory, filename, session):
        '''
        Constructor
        '''
        GsshaPyFileObjectBase.__init__(self, directory, filename, session)
    
    def __repr__(self):
        return '<PipeNetwork: ID=%s>' %(self.id)
    
    def _readWithoutCommit(self):
        '''
        Storm Pipe Network File Read from File Method
        '''
        # Dictionary of keywords/cards and parse function names
        KEYWORDS = {'CONNECT': spc.connectChunk,
                    'SJUNC': spc.sjuncChunk,
                    'SLINK': spc.slinkChunk}
        
        sjuncs = []
        slinks = []
        connections = []
        
        # Parse file into chunks associated with keywords/cards
        with open(self.PATH, 'r') as f:
            chunks = pt.chunk(KEYWORDS, f)
            
        # Parse chunks associated with each key    
        for key, chunkList in chunks.iteritems():
            # Parse each chunk in the chunk list
            for chunk in chunkList:
                # Call chunk specific parsers for each chunk
                result = KEYWORDS[key](key, chunk)

                # Cases
                if key == 'CONNECT':
                    connections.append(result)
                elif key == 'SJUNC':
                    sjuncs.append(result)
                elif key == 'SLINK':
                    slinks.append(result)
        
        # Create GSSHAPY objects
        self._createConnection(connections)
        self._createSjunc(sjuncs)
        self._createSlink(slinks)
        
        
    def _writeToOpenFile(self, session, openFile):
        '''
        Storm Pipe Network File Write to File Method
        '''           
        # Retrieve Connection objects and write to file
        connections = self.connections
        self._writeConnections(connections=connections, 
                               fileObject=openFile)
        
        # Retrieve SuperJuntion objects and write to file
        sjuncs = self.superJunctions
        self._writeSuperJunctions(superJunctions=sjuncs,
                                  fileObject=openFile)
        
        # Retrieve SuperLink objects and write to file
        slinks = self.superLinks
        self._writeSuperLinks(superLinks=slinks,
                              fileObject=openFile)
        
        
    def _createConnection(self, connections):
        '''
        Create GSSHAPY Connection Objects Method
        '''
        
        for c in connections:
            # Create GSSHAPY Connection object
            connection = Connection(slinkNumber=c['slinkNumber'],
                                    upSjuncNumber=c['upSjunc'],
                                    downSjuncNumber=c['downSjunc'])
            
            # Associate Connection with StormPipeNetworkFile
            connection.stormPipeNetworkFile = self
        
    def _createSlink(self, slinks):
        '''
        Create GSSHAPY SuperLink, Pipe, and SuperNode Objects Method
        '''
        
        for slink in slinks:
            # Create GSSHAPY SuperLink object
            superLink = SuperLink(slinkNumber=slink['slinkNumber'],
                                  numPipes=slink['numPipes'])
            
            # Associate SuperLink with StormPipeNetworkFile
            superLink.stormPipeNetworkFile = self
            
            for node in slink['nodes']:
                # Create GSSHAPY SuperNode objects
                superNode = SuperNode(nodeNumber=node['nodeNumber'],
                                      groundSurfaceElev=node['groundSurfaceElev'],
                                      invertElev=node['invertElev'],
                                      manholeSA=node['manholeSA'],
                                      nodeInletCode=node['inletCode'],
                                      cellI=node['cellI'],
                                      cellJ=node['cellJ'],
                                      weirSideLength=node['weirSideLength'],
                                      orificeDiameter=node['orificeDiameter'])
                
                # Associate SuperNode with SuperLink
                superNode.superLink = superLink
                
            for p in slink['pipes']:
                # Create GSSHAPY Pipe objects
                pipe = Pipe(pipeNumber=p['pipeNumber'],
                            xSecType=p['xSecType'],
                            diameterOrHeight=p['diameterOrHeight'],
                            width=p['width'],
                            slope=p['slope'],
                            roughness=p['roughness'],
                            length=p['length'],
                            conductance=p['conductance'],
                            drainSpacing=p['drainSpacing'])
                
                # Associate Pipe with SuperLink
                pipe.superLink = superLink
                    
    def _createSjunc(self, sjuncs):
        '''
        Create GSSHAPY SuperJunction Objects Method
        '''
        
        for sjunc in sjuncs:
            # Create GSSHAPY SuperJunction object
            superJunction = SuperJunction(sjuncNumber=sjunc['sjuncNumber'],
                                          groundSurfaceElev=sjunc['groundSurfaceElev'],
                                          invertElev=sjunc['invertElev'],
                                          manholeSA=sjunc['manholeSA'],
                                          inletCode=sjunc['inletCode'],
                                          linkOrCellI=sjunc['linkOrCellI'],
                                          nodeOrCellJ=sjunc['nodeOrCellJ'],
                                          weirSideLength=sjunc['weirSideLength'],
                                          orificeDiameter=sjunc['orificeDiameter'])
            
            # Associate SuperJunction with StormPipeNetworkFile
            superJunction.stormPipeNetworkFile = self
            
    def _writeConnections(self, connections, fileObject):
        '''
        Write Connections to File Method
        '''
        for connection in connections:
            fileObject.write('CONNECT  %s  %s  %s\n' % (
                             connection.slinkNumber,
                             connection.upSjuncNumber,
                             connection.downSjuncNumber))
        
    def _writeSuperJunctions(self, superJunctions, fileObject):
        '''
        Write SuperJunctions to File Method
        '''
        for sjunc in superJunctions:
            fileObject.write('SJUNC  %s  %.2f  %.2f  %.6f  %s  %s  %s  %.6f  %.6f\n' % (
                             sjunc.sjuncNumber,
                             sjunc.groundSurfaceElev,
                             sjunc.invertElev,
                             sjunc.manholeSA,
                             sjunc.inletCode,
                             sjunc.linkOrCellI,
                             sjunc.nodeOrCellJ,
                             sjunc.weirSideLength,
                             sjunc.orificeDiameter))
    
    def _writeSuperLinks(self, superLinks, fileObject):
        '''
        Write SuperLinks to File Method
        '''
        for slink in superLinks:
            fileObject.write('SLINK   %s      %s\n' %(
                             slink.slinkNumber,
                             slink.numPipes))
            
            for node in slink.superNodes:
                fileObject.write('NODE  %s  %.2f  %.2f  %.6f  %s  %s  %s  %.6f  %.6f\n' %(
                                 node.nodeNumber,
                                 node.groundSurfaceElev,
                                 node.invertElev,
                                 node.manholeSA,
                                 node.nodeInletCode,
                                 node.cellI,
                                 node.cellJ,
                                 node.weirSideLength,
                                 node.orificeDiameter))
            for pipe in slink.pipes:
                fileObject.write('PIPE  %s  %s  %.6f  %.6f  %.6f  %.6f  %.2f  %.6f  %.6f\n' %(
                                 pipe.pipeNumber,
                                 pipe.xSecType,
                                 pipe.diameterOrHeight,
                                 pipe.width,
                                 pipe.slope,
                                 pipe.roughness,
                                 pipe.length,
                                 pipe.conductance,
                                 pipe.drainSpacing))



class SuperLink(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_super_links'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id'))
    
    # Value Columns
    slinkNumber = Column(Integer, nullable=False)
    numPipes = Column(Integer, nullable=False)
    
    # Relationship Properties
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='superLinks')
    superNodes = relationship('SuperNode', back_populates='superLink')
    pipes = relationship('Pipe', back_populates='superLink')
    
    def __init__(self, slinkNumber, numPipes):
        '''
        Constructor
        '''
        self.slinkNumber = slinkNumber
        self.numPipes = numPipes

    def __repr__(self):
        return '<SuperLink: SlinkNumber=%s, NumPipes=%s>' % (
                self.slinkNumber,
                self.numPipes)
    
    
    
    
class SuperNode(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_super_nodes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    superLinkID = Column(Integer, ForeignKey('spn_super_links.id'))
    
    # Value Columns
    nodeNumber = Column(Integer, nullable=False)
    groundSurfaceElev = Column(Float, nullable=False)
    invertElev = Column(Float, nullable=False)
    manholeSA = Column(Float, nullable=False)
    nodeInletCode = Column(Integer, nullable=False)
    cellI = Column(Integer, nullable=False)
    cellJ = Column(Integer, nullable=False)
    weirSideLength = Column(Float, nullable=False)
    orificeDiameter = Column(Float, nullable=False)

    # Relationship Properties
    superLink = relationship('SuperLink', back_populates='superNodes')
    
    def __init__(self, nodeNumber, groundSurfaceElev, invertElev, manholeSA, nodeInletCode, cellI, cellJ, weirSideLength, orificeDiameter):
        '''
        Constructor
        '''
        self.nodeNumber = nodeNumber
        self.groundSurfaceElev = groundSurfaceElev
        self.invertElev = invertElev
        self.manholeSA = manholeSA
        self.nodeInletCode = nodeInletCode
        self.cellI = cellI
        self.cellJ = cellJ
        self.weirSideLength = weirSideLength
        self.orificeDiameter = orificeDiameter

    def __repr__(self):
        return '<SuperNode: NodeNumber=%s, GroundSurfaceElev=%s, InvertElev=%s, ManholeSA=%s, NodeInletCode=%s, CellI=%s, CellJ=%s, WeirSideLength=%s, OrificeDiameter=%s>' % (
                self.nodeNumber,
                self.groundSurfaceElev,
                self.invertElev,
                self.manholeSA,
                self.nodeInletCode,
                self.cellI,
                self.cellJ,
                self.weirSideLength,
                self.orificeDiameter) 
    
    
    
class Pipe(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_pipes'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    superLinkID = Column(Integer, ForeignKey('spn_super_links.id'))
    
    # Value Columns
    pipeNumber = Column(Integer, nullable=False)
    xSecType = Column(Integer, nullable=False)
    diameterOrHeight = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    slope = Column(Float, nullable=False)
    roughness = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    conductance = Column(Float, nullable=False)
    drainSpacing = Column(Float, nullable=False)
    
    # Relationship Properties
    superLink = relationship('SuperLink', back_populates='pipes')
    
    def __init__(self, pipeNumber, xSecType, diameterOrHeight, width, slope, roughness, length, conductance, drainSpacing):
        '''
        Constructor
        '''
        self.pipeNumber = pipeNumber
        self.xSecType = xSecType
        self.diameterOrHeight= diameterOrHeight
        self.width = width
        self.slope = slope
        self.roughness = roughness
        self.length = length
        self.conductance = conductance
        self.drainSpacing = drainSpacing

    def __repr__(self):
        return '<Pipe: PipeNumber=%s, XSecType=%s, DiameterOrHeight=%s, Width=%s, Slope=%s, Roughness=%s, Length=%s, Conductance=%s, DrainSpacing=%s>' % (
                self.pipeNumber,
                self.xSecType,
                self.diameterOrHeight,
                self.width,
                self.slope,
                self.roughness,
                self.length,
                self.conductance,
                self.drainSpacing)
    
    


class SuperJunction(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_super_junctions'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id'))
    
    # Value Columns
    sjuncNumber = Column(Integer, nullable=False)
    groundSurfaceElev = Column(Float, nullable=False)
    invertElev = Column(Float, nullable=False)
    manholeSA = Column(Float, nullable=False)
    inletCode = Column(Integer, nullable=False)
    linkOrCellI = Column(Integer, nullable=False)
    nodeOrCellJ = Column(Integer, nullable=False)
    weirSideLength = Column(Float, nullable=False)
    orificeDiameter = Column(Float, nullable=False)
    
    # Relationship Properties
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='superJunctions')
    
    def __init__(self, sjuncNumber, groundSurfaceElev, invertElev, manholeSA, inletCode, linkOrCellI, nodeOrCellJ, weirSideLength, orificeDiameter):
        '''
        Constructor
        '''
        self.sjuncNumber = sjuncNumber
        self.groundSurfaceElev = groundSurfaceElev
        self.invertElev = invertElev
        self.manholeSA = manholeSA
        self.inletCode = inletCode
        self.linkOrCellI = linkOrCellI
        self.nodeOrCellJ = nodeOrCellJ
        self.weirSideLength = weirSideLength
        self.orificeDiameter = orificeDiameter

    def __repr__(self):
        return '<SuperJunction: SjuncNumber=%s, GroundSurfaceElev=%s, InvertElev=%s, ManholeSA=%s, InletCode=%s, LinkOrCellI=%s, NodeOrCellJ=%s, WeirSideLength=%s, OrificeDiameter=%s>' % (
                self.sjuncNumber,
                self.groundSurfaceElev,
                self.invertElev,
                self.manholeSA,
                self.inletCode,
                self.linkOrCellI,
                self.nodeOrCellJ,
                self.weirSideLength,
                self.orificeDiameter)
        
class Connection(DeclarativeBase):
    '''
    classdocs
    '''
    __tablename__ = 'spn_connections'
    
    # Primary and Foreign Keys
    id = Column(Integer, autoincrement=True, primary_key=True)
    stormPipeNetworkFileID = Column(Integer, ForeignKey('spn_storm_pipe_network_files.id'))
    
    # Value Columns
    slinkNumber = Column(Integer, nullable=False)
    upSjuncNumber = Column(Integer, nullable=False)
    downSjuncNumber = Column(Integer, nullable=False)
    
    # Relationship Properties
    stormPipeNetworkFile = relationship('StormPipeNetworkFile', back_populates='connections')
   
    def __init__(self, slinkNumber, upSjuncNumber, downSjuncNumber):
        '''
        Constructor
        '''
        self.slinkNumber = slinkNumber
        self.upSjuncNumber = upSjuncNumber
        self.downSjuncNumber = downSjuncNumber
        
    def __repr__(self):
        return '<Connection: SlinkNumber=%s, UpSjuncNumber=%s, DownSjuncNumber=%s>' %(
                self.slinkNumber,
                self.upSjuncNumber,
                self.downSjuncNumber)