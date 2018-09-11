import unittest
from mvn_reports_tests import Class_Test


class TestTest_Obj(unittest.TestCase):

    def setUp(self):
        test_doc_1 = 'C:\\Users\\user\\Code\\Python\\BugMiner\\static_files\\TEST-org.apache.tika.cli.TikaCLIBatchCommandLineTest.xml'
        self.test_obj_1 = Class_Test(test_doc_1)

    def tearDown(self):
        pass

    def test_get_name(self):
        expected_name = "org.apache.tika.cli.TikaCLIBatchCommandLineTest"
        self.assertEqual(self.test_obj_1.get_name(), expected_name)

    def test_get_time(self):
        testcases = self.test_obj_1.get_testcases();
        expected_time = 0.0
        for testcase in self.test_obj_1.get_testcases():
            expected_time+=testcase.get_time()
        self.assertEqual(self.test_obj_1.get_time(), expected_time)

    def test_get_testcases(self):
        expected_testcases_names = []
        expected_testcases_names.append("testTwoDirsNoFlags")
        expected_testcases_names.append("testBasicMappingOfArgs")
        expected_testcases_names.append("testOneDirOneFileException")
        expected_testcases_names.append("testTwoDirsVarious")
        expected_testcases_names.append("testConfig")
        expected_testcases_names.append("testJVMOpts")
        for testcase in self.test_obj_1.get_testcases():
            if testcase.get_name() == "testTwoDirsNoFlags":
                self.assertEqual(testcase.get_time(), 0.071)
            elif testcase.get_name() == "testBasicMappingOfArgs":
                self.assertEqual(testcase.get_time(), 0.007)
            elif testcase.get_name() == "testOneDirOneFileException":
                self.assertEqual(testcase.get_time(), 0.007)
            elif testcase.get_name() == "testTwoDirsVarious":
                self.assertEqual(testcase.get_time(), 0.006)
            elif testcase.get_name() == "testConfig":
                self.assertEqual(testcase.get_time(), 0.006)
            elif testcase.get_name() == "testJVMOpts":
                self.assertEqual(testcase.get_time(), 0.007)
            else:
                self.fail("Unexpected testcase name")
        result_testcases_names= []
        for testcase in self.test_obj_1.get_testcases():
            result_testcases_names.append(testcase.get_name())
        for name in expected_testcases_names:
            self.assertTrue(name in result_testcases_names)

    def test_is_associated(self):
        t_associated_name_1 = 'testTwoDirsNoFlags'
        t_associated_name_2 = 'TikaCLIBatchCommandLineTest'
        t_not_associated_name_1 = 'testHeyDirsNoFlags'
        t_not_associated_name_2 = 'TikaBrotherCLIBatchCommandLineTest'
        self.assertTrue(self.test_obj_1.is_associated(t_associated_name_1))
        self.assertTrue(self.test_obj_1.is_associated(t_associated_name_2))
        self.assertFalse(self.test_obj_1.is_associated(t_not_associated_name_1))
        self.assertFalse(self.test_obj_1.is_associated(t_not_associated_name_2))

if __name__ == '__main__':
    unittest.main()