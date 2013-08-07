'''
********************************************************************************
* Name: ORM Tests
* Author: Nathan Swain
* Created On: May 16, 2013
* Copyright: (c) Brigham Young University 2013
* License: BSD 2-Clause
********************************************************************************
'''

import unittest, itertools

from gsshapy.orm.file_object_imports import *
from gsshapy.orm import ProjectFile
from gsshapy.lib import db_tools as dbt

class TestReadMethods(unittest.TestCase):
    def setUp(self):
        # Create Test DB 
        sqlalchemy_url = dbt.init_sqlite_db('db/standard.db')
        
        # Define workspace
        self.readDirectory = 'standard/'
        self.writeDirectory = 'out/'
        self.original = 'standard'
        self.name = 'standard'
        
        # Create DB Sessions
        readSession = dbt.create_session(sqlalchemy_url)
        self.writeSession = dbt.create_session(sqlalchemy_url)
        
        # Instantiate GSSHAPY ProjectFile object
        prjR = ProjectFile(directory=self.readDirectory,
                           filename='standard.prj',
                           session=readSession)
        
        # Invoke read project method
        prjR.readProject()
        
    
    def test_project_write(self):
        '''
        Test ProjectFile write method
        '''
        # Query and invoke write method
        self._query_n_write(ProjectFile)
        
        # Test
        self._compare_files(self.original, self.name, 'prj')

    def test_channel_input_write(self):
        '''
        Test ChannelInputFile write method
        '''
        # Query and invoke write method
        self._query_n_write(ChannelInputFile)
        
        # Test
        self._compare_files(self.original, self.name, 'cif')
        

    def test_map_table_write(self):
        '''
        Test MapTableFile write method
        '''
        # Query and invoke write method
        self._query_n_write(MapTableFile)
        
        # Test
        self._compare_files(self.original, self.name, 'cmt')
        
                
    def test_precip_file_write(self):
        '''
        Test PrecipFile write method
        '''
        # Query and invoke write method
        self._query_n_write(PrecipFile)
        
        # Test
        self._compare_files(self.original, self.name, 'gag')
        
        
    def test_grid_pipe_file_write(self):
        '''
        Test GridPipeFile write method
        '''
        # Query and invoke write method
        self._query_n_write(GridPipeFile)
        
        # Test
        self._compare_files(self.original, self.name, 'gpi')
        
        
    def test_grid_stream_file_write(self):
        '''
        Test GridStreamFile write method
        '''
        # Query and invoke write method
        self._query_n_write(GridStreamFile)
        
        # Test
        self._compare_files(self.original, self.name, 'gst')
        
        
    def test_hmet_file_write(self):
        '''
        Test HmetFile write method
        '''
        # Query and invoke write method
        self._query_n_write_filename(HmetFile, 'hmet_wes.hmt')
        
        # Test
        self._compare_files('hmet_wes', 'hmet_wes', 'hmt')
        
        
    def test_output_location_file_write(self):
        '''
        Test OutputLocationFile write method
        '''
        # Query and invoke write method
        self._query_n_write_multiple(OutputLocationFile, 'ihl')
        
        
        
    def test_link_node_dataset_file_write(self):
        '''
        Test LinkNodeDatasetFile write method
        '''
        # Query and invoke write method
        self._query_n_write_multiple(LinkNodeDatasetFile, 'cdp')
        
        
    def test_raster_map_file_write(self):
        '''
        Test RasterMapFile write method
        '''
        # Query and invoke write method
        self._query_n_write_multiple(RasterMapFile, 'msk')
        
        
        
    def test_projection_file_write(self):
        '''
        Test ProjectionFile write method
        '''
        # Query and invoke write method
        self._query_n_write(ProjectionFile)
        
        
    def test_replace_param_file_write(self):
        '''
        Test ReplaceParamFile write method
        '''
        # Query and invoke write method
        self._query_n_write_filename(ReplaceParamFile, 'replace_param.txt')
        
        
        
    def test_replace_val_file_write(self):
        '''
        Test ReplaceValFile write method
        '''
        # Query and invoke write method
        self._query_n_write_filename(ReplaceValFile, 'replace_val.txt')
        
        
    def test_nwsrfs_file_write(self):
        '''
        Test NwsrfsFile write method
        '''
        # Query and invoke write method
        self._query_n_write_filename(NwsrfsFile, 'nwsrfs_elev.txt')
        
        
    def test_ortho_gage_file_write(self):
        '''
        Test OrthographicGageFile write method
        '''
        # Query and invoke write method
        self._query_n_write_filename(OrthographicGageFile, 'ortho_gages.txt')
        
        
    def test_storm_pipe_network_file_write(self):
        '''
        Test StormPipeNetworkFile write method
        '''
        # Query and invoke write method
        self._query_n_write(StormPipeNetworkFile)
        
        
        
    def test_time_series_file_write(self):
        '''
        Test TimeSeriesFile write method
        '''
        # Query and invoke write method
        self._query_n_write_multiple(TimeSeriesFile, 'ohl')

    def test_index_map_write(self):
        '''
        Test IndexMap write method
        '''
        # Retrieve file from database
        idx = self.writeSession.query(IndexMap).\
                   filter(IndexMap.filename == 'Soil.idx').\
                   one()
        
        # Invoke write method
        idx.write(session=self.writeSession,
                  directory=self.writeDirectory,
                  name='soil_new_name')
        
        
    def test_project_write_all(self):
        '''
        Test ProjectFile write all method
        '''

    def test_project_write_input(self):
        '''
        Test ProjecFile write input method
        '''
        
    def test_project_write_output(self):
        '''
        Test ProjectFile write output method
        '''
    
    def _query_n_write(self, fileIO):
        '''
        Query database and write file method
        '''
        # Retrieve file from database
        instance = self.writeSession.query(fileIO).one()
        
        # Invoke write method
        instance.write(session=self.writeSession,
                       directory=self.writeDirectory,
                       name=self.name)
    
    def _query_n_write_filename(self, fileIO, filename):
        '''
        Query database and write file method
        '''
        # Retrieve file from database
        instance = self.writeSession.query(fileIO).one()
        
        # Invoke write method
        instance.write(session=self.writeSession,
                       directory=self.writeDirectory,
                       filename=filename)
        
    def _query_n_write_multiple(self, fileIO, ext):
        '''
        Query database and write file method
        '''
        # Retrieve file from database
        instance = self.writeSession.query(fileIO).\
                        filter(fileIO.fileExtension == ext).\
                        one()
        
        # Invoke write method
        instance.write(session=self.writeSession,
                       directory=self.writeDirectory,
                       name=self.name)
        
    def _compare_files(self, original, new, ext):
        filePathO = '%s%s.%s' % (self.readDirectory, original, ext)
        filePathN = '%s%s.%s' % (self.writeDirectory, new, ext)
        
        with open(filePathO) as fileO:
            contentsO = fileO.read()
            
        with open(filePathN) as fileN:
            contentsN = fileN.read()
        self.assertEqual(contentsO, contentsN)
        
    def _list_compare(self, listone, listtwo):
        for one, two in itertools.izip(listone, listtwo):
            self.assertEqual(one, two)
        
        
        
    def tearDown(self):
        dbt.del_sqlite_db('db/standard.db')
        
    

if __name__ == '__main__':
    unittest.main()