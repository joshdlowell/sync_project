import unittest
import bootstrap
import dbapi


class BootStrapTests(unittest.TestCase):
    def setUp(self):

        # ADD reading yaml verification
        self.values = {'local_db': 'http://127.0.0.1:5000',
                       'root_path': '/tests/testfiles'}
        self.db = {'local_db': 'http://127.0.0.1:5000'}

    def test_init_bootstrap_all(self):
        self.assertEqual(bootstrap.init_bootstrap(['local_db', 'root_path']), self.values, "Return values didn't match")  # add assertion here

    def test_init_bootstrap_one(self):
        self.assertEqual(bootstrap.init_bootstrap(['local_db']), self.db, "Return values didn't match")  # add assertion here

    def test_init_bootstrap_with_invalid(self):
        test_dict = self.db.copy()
        test_dict['other_db'] = None
        self.assertEqual(bootstrap.init_bootstrap(['local_db', 'other_db']), test_dict, "Return values didn't match")  # add assertion here

    def test_init_bootstrap_only_invalid(self):
        test_dict = {'other_db': None, "other_path": None}
        self.assertEqual(bootstrap.init_bootstrap(test_dict.keys()), test_dict)  # add assertion here


class DbApiTests(unittest.TestCase):
    # start rest api before these tests
    def setUp(self):
        self.valid_min = {
            "/tests/testfiles":
            {
                'current_hash': 'wxyz',
                'current_dtg_latest': str(1749982108.5355163)
            }
        }
        self.valid_key = list(self.valid_min.keys())[0]
        self.changes = {'Created': set(), 'Deleted': set(), 'Modified': set()}

    def test_01_put_hashtable(self):
        # Test missing required key
        bad_dict1 = self.valid_min.copy()
        del bad_dict1[self.valid_key]['current_hash']
        response = dbapi.put_hashtable(bad_dict1)
        self.assertEqual(self.changes, response, "Return values didn't match")
        self.changes['Created'].add(self.valid_key)
        self.assertNotEqual(self.changes, response, "Return values didn't match")

    def test_02_put_hashtable(self):
        # Test included invalid key
        bad_dict1 = self.valid_min.copy()
        bad_dict1[self.valid_key]['bad_key'] = "abcde"
        response = dbapi.put_hashtable(bad_dict1)
        self.assertEqual(self.changes, response, "Return values didn't match")
        self.changes['Created'].add(self.valid_key)
        self.assertNotEqual(self.changes, response, "Return values didn't match")

    def test_03_put_hashtable(self):
        # Check putting a valid entry into the DB
        response = dbapi.put_hashtable(self.valid_min)
        self.changes['Created'].add(self.valid_key)
        self.assertEqual(self.changes, response, "Return values didn't match")


    def test_get_single_hash(self):
        # Entry in database
        self.assertEqual(dbapi.get_single_hash(self.valid_key), 'wxyz')
        # None for entry not in database
        self.assertIsNone(dbapi.get_single_hash(f'{self.valid_key}/newfile'))

    def test_get_hashtable(self):
        return_dict = db_converter(self.valid_min)
        # Get entire db entry valid
        self.assertEqual(dbapi.get_hashtable(self.valid_key), return_dict, "Return values didn't match")
        # None for entry not in database
        self.assertIsNone(dbapi.get_hashtable(f'{self.valid_key}/newfile'))

    def test_get_oldest_updates(self):
        # Test with no dirs in root
        pass

    def test_get_single_timestamp(self):
        # Get entire db entry valid
        self.assertEqual(dbapi.get_single_timestamp(self.valid_key), float(self.valid_min[self.valid_key]['current_dtg_latest']), "Return values didn't match")

        # None for entry not in database
        self.assertIsNone(dbapi.get_single_timestamp(f'{self.valid_key}/newfile'))

    def test_get_priority_updates(self):
        pass


class IntegrityCheckTests(unittest.TestCase):
    # start rest api before these tests
    def setUp(self):
        self.valid_min = {
            "/tests/testfiles":
            {
                'current_hash': 'wxyz',
                'current_dtg_latest': str(1749982108.5355163)
            }
        }

    def test_DFS_merkle(self):

        # takes root_path: str, dir_path: str):

        # Test bad path

        # verify root hash

        # verify changes

        # verify sub-dir hash

        # verify changes (also verifies recompute root)


        # return dir_path_hash, changes
        pass

    def test_get_walk(self):

            # takes parent_path

            # tree_dict[dir_path] = {"dirs": sorted(clean_dirs),
            #                        "files": sorted(clean_files),
            #                        "links": sorted(clean_links)}
        pass

    def test_get_link_hashable(self):
           # takes link_path

        # returns string representing link
        pass

    def test_get_dir_hashable(self):

        # Takes dir_path, hash_info) -> concatenated hex hash str:
        pass


def db_converter(data):
    converted = {'dirs': None, 'files': None, 'links': None}

    for path in data.keys():
        converted['path'] = path
        for key, value in data[path].items():
            converted[key] = value
    return converted


if __name__ == '__main__':
    unittest.main()
