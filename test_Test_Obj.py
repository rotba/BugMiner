import os
import unittest
from mvn_parsers import test_parser


class TestTest_Obj(unittest.TestCase):
    #os.system('mvn install -f C:\\Users\\user\\Code\\Python\\BugMinerTest\\static_files\\GitMavenTrackingProject')

    def setUp(self):
        test_doc_1 = 'C:\\Users\\user\\Code\\Python\\BugMiner\\static_files\\TEST-org.apache.tika.cli.TikaCLIBatchCommandLineTest.xml'
        test_doc_2 = r'C:\Users\user\Code\Python\BugMinerTest\static_files\GitMavenTrackingProject\sub_mod_2\target\surefire-reports\TEST-p_1.AssafTest.xml'
        self.test_obj_1 = test_parser.Class_Test(test_doc_1, '')
        self.test_obj_2 = test_parser.Class_Test(test_doc_2,
                                                 r'C:\Users\user\Code\Python\BugMinerTest\static_files\GitMavenTrackingProject\sub_mod_2')

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
            if "testTwoDirsNoFlags" in testcase.get_name():
                self.assertEqual(testcase.get_time(), 0.071)
            elif "testBasicMappingOfArgs" in testcase.get_name():
                self.assertEqual(testcase.get_time(), 0.007)
            elif "testOneDirOneFileException" in testcase.get_name():
                self.assertEqual(testcase.get_time(), 0.007)
            elif "testTwoDirsVarious" in testcase.get_name():
                self.assertEqual(testcase.get_time(), 0.006)
            elif "testConfig" in testcase.get_name():
                self.assertEqual(testcase.get_time(), 0.006)
            elif "testJVMOpts" in testcase.get_name():
                self.assertEqual(testcase.get_time(), 0.007)
            else:
                self.fail("Unexpected testcase name: "+testcase.get_name())
        result_testcases_names= []
        for testcase in self.test_obj_1.get_testcases():
            result_testcases_names.append(testcase.get_name())
        for name in expected_testcases_names:
            i = 0
            for res_name in result_testcases_names:
                if name in res_name:
                    continue
                else:
                    i += 1
                    if i == len(result_testcases_names):
                        self.fail(name + ' not associated to '+self.test_obj_1.get_name())

    def test_is_associated(self):
            t_associated_name_1 = 'testTwoDirsNoFlags'
            t_associated_name_2 = 'TikaCLIBatchCommandLineTest'
            t_not_associated_name_1 = 'testHeyDirsNoFlags'
            t_not_associated_name_2 = 'TikaBrotherCLIBatchCommandLineTest'
            self.assertTrue(self.test_obj_1.is_associated(t_associated_name_1))
            self.assertTrue(self.test_obj_1.is_associated(t_associated_name_2))
            self.assertFalse(self.test_obj_1.is_associated(t_not_associated_name_1))
            self.assertFalse(self.test_obj_1.is_associated(t_not_associated_name_2))

    def test_src_path(self):
        res = self.test_obj_2.src_path
        self.assertEqual(res, r'C:\Users\user\Code\Python\BugMinerTest\static_files\GitMavenTrackingProject\sub_mod_2\src\test\java\p_1\AssafTest.java')

if __name__ == '__main__':
    unittest.main()