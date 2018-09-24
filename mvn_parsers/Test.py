import os
import unittest
import test_parser


class TestTest_Obj(unittest.TestCase):

    #os.system('mvn clean install -f '+os.getcwd() + r'\static_files\GitMavenTrackingProject')
    def setUp(self):
        test_doc_1 = os.getcwd() + r'\static_files\TEST-org.apache.tika.cli.TikaCLIBatchCommandLineTest.xml'
        test_doc_2 = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_2\target\surefire-reports\TEST-p_1.AssafTest.xml'
        self.test_report_1 = test_parser.TestClassReport(test_doc_1, '')
        self.test_report_2 = test_parser.TestClassReport(test_doc_2,
                                                         os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_2')
        self.test_1 = test_parser.TestClass(
            os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_2\src\test\java\NaimTest.java')
        self.test_2 = test_parser.TestClass(
            os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_1\src\test\java\p_1\AmitTest.java')

    def tearDown(self):
        pass

    def test_get_path(self):
        expected_name = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_2\src\test\java\NaimTest.java'
        self.assertEqual(self.test_1.get_path(), expected_name)

    def test_get_module(self):
        expected_module_1 = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_2'
        expected_module_2 = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_1'
        self.assertEqual(self.test_1.get_module(), expected_module_1,
                         str(self.test_1) + ' module should be ' + expected_module_1)
        self.assertEqual(self.test_2.get_module(), expected_module_2,
                         str(self.test_2) + ' module should be ' + expected_module_2)

    def test_mvn_name(self):
        expected_name = 'p_1.AmitTest'
        expected_method_name = 'p_1.AmitTest#hoo'
        self.assertEqual(self.test_2.get_mvn_name(), expected_name)
        self.assertTrue(expected_method_name in list(map(lambda m: m.get_mvn_name(), self.test_2.get_testcases())))

    def test_get_testcases(self):
        expected_testcase_id = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#hoo'
        self.assertTrue(expected_testcase_id in list(map(lambda tc: tc.get_id(), self.test_2.get_testcases())))
        self.assertEqual(len(self.test_2.get_testcases()), 2, "p_1.AmitTest should have only one method")

    def test_get_report_path(self):
        expected_report_path = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_1\target\surefire-reports\TEST-p_1.AmitTest.xml'
        self.assertEqual(self.test_2.get_report_path(), expected_report_path)

    def test_report_get_src_file_path(self):
        expected_src_file_path = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_2\src\test\java\p_1\AssafTest.java'
        self.assertEqual(self.test_report_2.get_src_file_path(), expected_src_file_path)

    def test_report_get_time(self):
        testcases = self.test_report_1.get_testcases();
        expected_time = 0.0
        for testcase in self.test_report_1.get_testcases():
            expected_time += testcase.get_time()
        self.assertEqual(self.test_report_1.get_time(), expected_time)

    def test_report_get_testcases(self):
        expected_testcases_names = []
        expected_testcases_names.append("testTwoDirsNoFlags")
        expected_testcases_names.append("testBasicMappingOfArgs")
        expected_testcases_names.append("testOneDirOneFileException")
        expected_testcases_names.append("testTwoDirsVarious")
        expected_testcases_names.append("testConfig")
        expected_testcases_names.append("testJVMOpts")
        for testcase in self.test_report_1.get_testcases():
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
                self.fail("Unexpected testcase name: " + testcase.get_name())
        result_testcases_names = []
        for testcase in self.test_report_1.get_testcases():
            result_testcases_names.append(testcase.get_name())
        for name in expected_testcases_names:
            i = 0
            for res_name in result_testcases_names:
                if name in res_name:
                    continue
                else:
                    i += 1
                    if i == len(result_testcases_names):
                        self.fail(name + ' not associated to ' + self.test_report_1.get_name())

    def test_report_is_associated(self):
        t_associated_name_1 = 'testTwoDirsNoFlags'
        t_associated_name_2 = 'TikaCLIBatchCommandLineTest'
        t_not_associated_name_1 = 'testHeyDirsNoFlags'
        t_not_associated_name_2 = 'TikaBrotherCLIBatchCommandLineTest'
        self.assertTrue(self.test_report_1.is_associated(t_associated_name_1))
        self.assertTrue(self.test_report_1.is_associated(t_associated_name_2))
        self.assertFalse(self.test_report_1.is_associated(t_not_associated_name_1))
        self.assertFalse(self.test_report_1.is_associated(t_not_associated_name_2))

    def test_report_is_associated(self):
        t_associated_name_1 = 'testTwoDirsNoFlags'
        t_associated_name_2 = 'TikaCLIBatchCommandLineTest'
        t_not_associated_name_1 = 'testHeyDirsNoFlags'
        t_not_associated_name_2 = 'TikaBrotherCLIBatchCommandLineTest'
        self.assertTrue(self.test_report_1.is_associated(t_associated_name_1))
        self.assertTrue(self.test_report_1.is_associated(t_associated_name_2))
        self.assertFalse(self.test_report_1.is_associated(t_not_associated_name_1))
        self.assertFalse(self.test_report_1.is_associated(t_not_associated_name_2))

    @unittest.skip("Test nor ready")
    def test_star_line_end_line(self):
        testcases_1 = self.test_1.get_testcases()
        testcases_2 = self.test_2.get_testcases()

    @unittest.skip("Important test but will require some time to validate")
    def test_get_compilation_error_testcases(self):
        print('test_get_compilation_error_testcases')
        with open(os.getcwd()+r'\static_files\test_get_compilation_error_testcases_report.txt','r') as report_file:
            report = report_file.read()
        commit = [c for c in Main.all_commits if c.hexsha == 'a71cdc161b0d87e7ee808f5078ed5fefab758773'][0]
        parent = commit.parents[0]
        module_path = os.getcwd()+r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.repo.git.reset('--hard')
        Main.repo.git.checkout(commit.hexsha)
        commit_tests = Main.test_parser.get_tests(module_path)
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_not_compiling_testcase = [t for t in commit_testcases if 'MainTest#gooTest' in t.get_mvn_name()][0]
        Main.prepare_project_repo_for_testing(parent, module_path)
        commit_new_testcases = Main.get_commit_created_testcases(commit_testcases)
        compolation_error_testcases = Main.get_compilation_error_testcases(report, commit_new_testcases)
        self.assertTrue(expected_not_compiling_testcase in compolation_error_testcases,
                        "'MainTest#gooTest should have been picked as for compilation error")

if __name__ == '__main__':
    unittest.main()
