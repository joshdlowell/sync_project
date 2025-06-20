import unittest
import rest_connector
import integritycheck


class RestConnectorTests(unittest.TestCase):
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
        print("Test a request with a missing required key is rejected\n")
        # Test missing required key
        bad_dict1 = self.valid_min.copy()
        del bad_dict1[self.valid_key]['current_hash']
        response = rest_connector.put_hashtable(bad_dict1)
        self.assertEqual(self.changes, response, "Return values didn't match")
        self.changes['Created'].add(self.valid_key)
        self.assertNotEqual(self.changes, response, "Return values didn't match")

    def test_02_put_hashtable(self):
        print("Test a request with an invalid key is rejected\n")
        # Test included invalid key
        bad_dict1 = self.valid_min.copy()
        bad_dict1[self.valid_key]['bad_key'] = "abcde"
        response = rest_connector.put_hashtable(bad_dict1)
        self.assertEqual(self.changes, response, "Return values didn't match")
        self.changes['Created'].add(self.valid_key)
        self.assertNotEqual(self.changes, response, "Return values didn't match")

    def test_03_put_hashtable(self):
        print("Test a valid request is accepted\n")
        # Check putting a valid entry into the DB
        response = rest_connector.put_hashtable(self.valid_min)
        self.changes['Created'].add(self.valid_key)
        self.assertEqual(self.changes, response, "Return values didn't match")


    def test_get_single_hash(self):
        print("Test retrieving a single hash for valid and invalid file paths\n")
        # Entry in database should return correct hash
        self.assertEqual(rest_connector.get_single_hash(self.valid_key), 'wxyz')
        # Should return None for entry not in database
        self.assertIsNone(rest_connector.get_single_hash(f'{self.valid_key}/newfile'))

    def test_get_hashtable(self):
        print("Test retrieving a full db entry for valid and invalid file paths\n")
        return_dict = db_converter(self.valid_min)
        # Get entire db entry valid
        self.assertEqual(rest_connector.get_hashtable(self.valid_key), return_dict, "Return values didn't match")
        # None for entry not in database
        self.assertIsNone(rest_connector.get_hashtable(f'{self.valid_key}/newfile'))

    def test_get_oldest_updates(self):
        # Test with no dirs in root
        pass

    def test_get_single_timestamp(self):
        print("Test retrieving a 'latest' timestamp for valid and invalid file paths\n")
        # Get entire db entry valid
        self.assertEqual(rest_connector.get_single_timestamp(self.valid_key), float(self.valid_min[self.valid_key]['current_dtg_latest']), "Return values didn't match")

        # None for entry not in database
        self.assertIsNone(rest_connector.get_single_timestamp(f'{self.valid_key}/newfile'))

    def test_get_priority_updates(self):
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
