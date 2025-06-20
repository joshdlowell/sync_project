import unittest
# import rest_connector
import integritycheck

class IntegrityCheckTests(unittest.TestCase):
    # start rest api before these tests
    def setUp(self):
        self.root_path = '/squishy/tests'
        self.files_struc = {'/squishy/tests':
                           {'dirs': ['dir1', 'dir2', 'dir3', 'dir4', 'dir5', 'empty'],
                            'files': ['boot.yaml', 'test_integrity_check.py'],
                            'links': []},
                       '/squishy/tests/dir1':
                           {'dirs': [],
                            'files': ['file1'],
                            'links': []},
                       '/squishy/tests/dir2':
                           {'dirs': [],
                            'files': [],
                            'links': ['lnk1']},
                       '/squishy/tests/dir3':
                           {'dirs': [],
                            'files': ['hlnk1'],
                            'links': []},
                       '/squishy/tests/dir4':
                           {'dirs': ['dir4_1'],
                            'files': [],
                            'links': []},
                       '/squishy/tests/dir4/dir4_1':
                           {'dirs': [],
                            'files': [],
                            'links': []},
                       '/squishy/tests/dir5':
                           {'dirs': ['dir5_1'],
                            'files': ['hlnk2'],
                            'links': ['lnk2', 'lnk3']},
                       '/squishy/tests/dir5/dir5_1':
                           {'dirs': [],
                            'files': ['file2'],
                            'links': []},
                       '/squishy/tests/empty':
                           {'dirs': [],
                            'files': [],
                            'links': []}}
        self.first_run_changes = {'Created':
                                      {'/squishy/tests/dir2', '/squishy/tests/dir5', '/squishy/tests/boot.yaml', '/squishy/tests/dir4', '/squishy/tests/dir3', '/squishy/tests/dir5/lnk3', '/squishy/tests/dir5/dir5_1/file2', '/squishy/tests/test_integrity_check.py', '/squishy/tests/dir2/lnk1', '/squishy/tests/dir1/file1', '/squishy/tests', '/squishy/tests/empty', '/squishy/tests/dir5/hlnk2', '/squishy/tests/dir5/dir5_1', '/squishy/tests/dir1', '/squishy/tests/dir5/lnk2', '/squishy/tests/dir3/hlnk1', '/squishy/tests/dir4/dir4_1'},
                                  'Deleted': set(),
                                  'Modified': set()}
        self.full_hashes = {'/squishy/tests': '7aa7a8ce8dfdb483506ecbead44dd8943c03da07',
                            '/squishy/tests/boot.yaml': 'fb72f2e4e9b5a44650a4dd4ca2c27067ad3a2bc0',
                            '/squishy/tests/test_integrity_check.py': '5c0a6c568d946fd1722cbfe8a06b061c7ea4f870',
                            '/squishy/tests/dir1': '61f13c33c7259df3a8ce09e5f1212aa8ae3e1039',
                            '/squishy/tests/dir1/file1': '15ededa1f314bf445978438ccd6678d1d1a25916',
                            '/squishy/tests/dir2': 'f5dde0002f7b3af2f972ada4c53d0fa959a536c4',
                            '/squishy/tests/dir2/lnk1': 'ab0c4fbdbef08641341580b09da4df151cff6bb3',
                            '/squishy/tests/dir3': '0fabb34c15b2630e51783c0e4483fe43ae7b9b85',
                            '/squishy/tests/dir3/hlnk1': '15ededa1f314bf445978438ccd6678d1d1a25916',
                            '/squishy/tests/dir4': 'd08a432f48451055c7cb850ca0dcc3d09a1805f6',
                            '/squishy/tests/dir4/dir4_1': '347fdd16ff201eb660f3b50036b41bd165a85f9f',
                            '/squishy/tests/dir5': '1b9737868b4bd5ad763bdf65d692df071545a7d0',
                            '/squishy/tests/dir5/hlnk2': '15ededa1f314bf445978438ccd6678d1d1a25916',
                            '/squishy/tests/dir5/dir5_1': '1f577981c04c4a177482203c9a3de80ad313b309',
                            '/squishy/tests/dir5/dir5_1/file2': '2b7dd3feac3508555010e10a8ee00f3e3a0dbba3',
                            '/squishy/tests/empty': 'b93bd91d6f80da4c57215471d70883823c462247'}
        self.test_hash_info = {'/squishy/tests':
                                   {'dirs': ['dir1', 'dir2', 'dir3', 'dir4', 'dir5', 'empty'],
                                    'files': ['boot.yaml', 'test_integrity_check.py'],
                                    'links': [],
                                    'current_hash': '7e85a7fabb5fd2692986a7ac78fb043ee6d4e4a8',
                                    'current_dtg_latest': '1750125976.93499'},
                               '/squishy/tests/dir1':
                                   {'current_hash': '30ec31703247d07b9142f722086416a84704ad53',
                                    'current_dtg_latest': '1750125976.8928897'},
                               '/squishy/tests/dir2':
                                   {'current_hash': '56312a0620d3c21d9beb29ba2df493bf88106601',
                                    'current_dtg_latest': '1750125976.898024'},
                               '/squishy/tests/dir3':
                                   {'current_hash': '30ec31703247d07b9142f722086416a84704ad53',
                                    'current_dtg_latest': '1750125976.904361'},
                               '/squishy/tests/dir4':
                                   {'current_hash': '10a34637ad661d98ba3344717656fcc76209c2f8',
                                    'current_dtg_latest': '1750125976.909718'},
                               '/squishy/tests/dir5':
                                   {'current_hash': 'cd22ff842dfb51981bf96090c52702f4cdc82e4a',
                                    'current_dtg_latest': '1750125976.929444'},
                               '/squishy/tests/empty':
                                   {'current_hash': 'da39a3ee5e6b4b0d3255bfef95601890afd80709',
                                    'current_dtg_latest': '1750125976.931147'},
                               '/squishy/tests/boot.yaml':
                                   {'current_hash': 'fb72f2e4e9b5a44650a4dd4ca2c27067ad3a2bc0',
                                    'current_dtg_latest': '1750125976.9331563'},
                               '/squishy/tests/test_integrity_check.py':
                                   {'current_hash': '5c0a6c568d946fd1722cbfe8a06b061c7ea4f870',
                                    'current_dtg_latest': '1750125976.9349732'}}
        self.test_root_string = '30ec31703247d07b9142f722086416a84704ad5356312a0620d3c21d9beb29ba2df493bf8810660130ec31703247d07b9142f722086416a84704ad5310a34637ad661d98ba3344717656fcc76209c2f8cd22ff842dfb51981bf96090c52702f4cdc82e4ada39a3ee5e6b4b0d3255bfef95601890afd80709fb72f2e4e9b5a44650a4dd4ca2c27067ad3a2bc05c0a6c568d946fd1722cbfe8a06b061c7ea4f870/squishy/tests/links: EMPTY '
        self.test_hash_info2 = {'/squishy/tests/empty':
                                   {'dirs': [],
                                    'files': [],
                                    'links': [],
                                    'current_hash': '7e85a7fabb5fd2692986a7ac78fb043ee6d4e4a8',
                                    'current_dtg_latest': '1750125976.93499'}}
        self.test_string_2 = '/squishy/tests/empty/dirs: EMPTY /squishy/tests/empty/files: EMPTY /squishy/tests/empty/links: EMPTY '

    def test_01_get_walk(self):
        # print(integritycheck._get_walk(self.root_path))

        # Check whole test directory structure
        self.assertEqual(self.files_struc, integritycheck._get_walk(self.root_path), "Return values didn't match")

        # Check several subdirectories
        for path in ['/squishy/tests/empty', '/squishy/tests/dir1', '/squishy/tests/dir2']:
            expected = {path: self.files_struc[path]}
            self.assertEqual(expected, integritycheck._get_walk(path), "Return values didn't match")

        # Subdirectory does not have to be inside root_path, this check is handled in the public "DFS_merkle" func.

    def test_02_get_link_hashable(self):
        # print(integritycheck.get_link_hashable('/squishy/tests/dir2/lnk1'))
        link1 = '/squishy/tests/dir2/lnk1 -> dir1/file1'
        link2 = '/squishy/tests/dir5/lnk2 -> dir5/dir5_1/file2'
        link3 = '/squishy/tests/dir5/lnk3 -> dir1'
        self.assertEqual(link1, integritycheck.get_link_hashable('/squishy/tests/dir2/lnk1'), "Return values didn't match")
        self.assertEqual(link2, integritycheck.get_link_hashable('/squishy/tests/dir5/lnk2'), "Return values didn't match")
        self.assertEqual(link3, integritycheck.get_link_hashable('/squishy/tests/dir5/lnk3'), "Return values didn't match")

    def test_03_get_dir_hashable(self):
        # self.maxDiff = None
        self.assertEqual(self.test_root_string, integritycheck.get_dir_hashable(self.root_path, self.test_hash_info), "Return values didn't match")
        self.assertEqual(self.test_string_2, integritycheck.get_dir_hashable(f"{self.root_path}/empty", self.test_hash_info2), "Return values didn't match")

    def test_04_DFS_merkle(self):
    # THIS TEST NEED TO MOVE TO END TO END INTEGRATION

        #
        # expected_changes = {'Created': set(), 'Deleted': set(), 'Modified': set()}
        # tree_dict = integritycheck._get_walk(self.root_path)
        # dir_path_hash = integritycheck._DFS_merkle(self.root_path, changes, tree_dict)

        # print(changes)

        # Hash the whole test structure and verify the root hash and changes
        root_hash, changes = integritycheck.DFS_merkle(self.root_path, self.root_path)
        self.assertEqual(self.full_hashes[self.root_path], root_hash, "Didn't match")
        self.assertEqual(self.first_run_changes, changes, "Didn't match")

        # Verify all hashes in the db are correct
        for key in self.full_hashes.keys():
            print(f"{key}")
            self.assertEqual(self.full_hashes[key], rest_connector.get_single_hash(key), "Didn't match")

        # Test bad path


        # verify changes

        # verify changes (also verifies recompute root)



if __name__ == '__main__':
    unittest.main()
