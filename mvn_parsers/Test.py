import os
import unittest
import test_parser


class TestTest_Obj(unittest.TestCase):

    # os.system('mvn clean install -f '+os.getcwd() + r'\static_files\GitMavenTrackingProject')
    # os.system('mvn clean install -f ' + os.getcwd() + r'\static_files\tika_1')
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
        self.test_2 = test_parser.TestClass(
            os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_1\src\test\java\p_1\AmitTest.java')
        self.test_3 = test_parser.TestClass(
            os.getcwd() + r'\static_files\tika_1\src\test\java\org\apache\tika\parser\AutoDetectParserTest.java')
        self.test_4 = test_parser.TestClass(
            os.getcwd() + r'\static_files\tika_1\src\test\java\org\apache\tika\sax\AppendableAdaptorTest.java')
        self.test_5 = test_parser.TestClass(
            os.getcwd() + r'\static_files\tika_1\src\test\java\org\apache\tika\sax _1\AppendableAdaptorTest.java')
        self.testcase_1 = [t for t in self.test_3.testcases if t.id.endswith('None_testExcel()')][0]
        self.testcase_2 = [t for t in self.test_4.testcases if t.id.endswith('None_testAppendChar()')][0]
        self.testcase_3 = [t for t in self.test_5.testcases if t.id.endswith('None_testAppendChar()')][0]
        self.testcase_4 = [t for t in self.test_5.testcases if t.id.endswith('None_testAppendString()')][0]

    def tearDown(self):
        pass

    def test_get_path(self):
        expected_name = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_2\src\test\java\NaimTest.java'
        self.assertEqual(self.test_1.src_path, expected_name)

    def test_get_module(self):
        expected_module_1 = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_2'
        expected_module_2 = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_1'
        self.assertEqual(self.test_1.module, expected_module_1,
                         str(self.test_1) + ' module should be ' + expected_module_1)
        self.assertEqual(self.test_2.module, expected_module_2,
                         str(self.test_2) + ' module should be ' + expected_module_2)

    def test_mvn_name(self):
        expected_name = 'p_1.AmitTest'
        expected_method_name = 'p_1.AmitTest#hoo'
        self.assertEqual(self.test_2.mvn_name, expected_name)
        self.assertTrue(expected_method_name in list(map(lambda m: m.mvn_name, self.test_2.testcases)))

    def test_get_testcases(self):
        expected_testcase_id = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_1\src\test\java\p_1\AmitTest.java#AmitTest#None_hoo()'
        self.assertTrue(expected_testcase_id in list(map(lambda tc: tc.id, self.test_2.testcases)))
        self.assertEqual(len(self.test_2.testcases), 2, "p_1.AmitTest should have only one method")

    def test_get_report_path(self):
        expected_report_path = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_1\target\surefire-reports\TEST-p_1.AmitTest.xml'
        self.assertEqual(self.test_2.get_report_path(), expected_report_path)

    def test_report_get_src_file_path(self):
        expected_src_file_path = os.getcwd() + r'\static_files\GitMavenTrackingProject\sub_mod_2\src\test\java\p_1\AssafTest.java'
        self.assertEqual(self.test_report_2.src_path, expected_src_file_path)

    def test_report_get_time(self):
        testcases = self.test_report_1.testcases;
        expected_time = 0.0
        for testcase in self.test_report_1.testcases:
            expected_time += testcase.time
        self.assertEqual(self.test_report_1.time, expected_time)

    def test_report_get_testcases(self):
        expected_testcases_names = []
        expected_testcases_names.append("testTwoDirsNoFlags")
        expected_testcases_names.append("testBasicMappingOfArgs")
        expected_testcases_names.append("testOneDirOneFileException")
        expected_testcases_names.append("testTwoDirsVarious")
        expected_testcases_names.append("testConfig")
        expected_testcases_names.append("testJVMOpts")
        for testcase in self.test_report_1.testcases:
            if "testTwoDirsNoFlags" in testcase.name:
                self.assertEqual(testcase.time, 0.071)
            elif "testBasicMappingOfArgs" in testcase.name:
                self.assertEqual(testcase.time, 0.007)
            elif "testOneDirOneFileException" in testcase.name:
                self.assertEqual(testcase.time, 0.007)
            elif "testTwoDirsVarious" in testcase.name:
                self.assertEqual(testcase.time, 0.006)
            elif "testConfig" in testcase.name:
                self.assertEqual(testcase.time, 0.006)
            elif "testJVMOpts" in testcase.name:
                self.assertEqual(testcase.time, 0.007)
            else:
                self.fail("Unexpected testcase name: " + testcase.name)
        result_testcases_names = []
        for testcase in self.test_report_1.testcases:
            result_testcases_names.append(testcase.name)
        for name in expected_testcases_names:
            i = 0
            for res_name in result_testcases_names:
                if name in res_name:
                    continue
                else:
                    i += 1
                    if i == len(result_testcases_names):
                        self.fail(name + ' not associated to ' + self.test_report_1.name)

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

    def test_star_line_end_line(self):
        self.assertTrue(self.testcase_1.start_line == 130, 'result - start_line : '+str(self.testcase_1.start_line))
        self.assertTrue(self.testcase_1.end_line == 132, 'result - end_line : '+str(self.testcase_1.end_line))

    def test_has_the_same_code(self):
        self.assertTrue(self.testcase_2.has_the_same_code_as(self.testcase_3))
        self.assertFalse(self.testcase_2.has_the_same_code_as(self.testcase_4))

    def test_change_surefire_ver(self):
        module = self.test_4.module
        test_parser.change_surefire_ver(module,'2.22')
        with open(self.test_4.get_xml_path(), 'r') as xml_file:
            lines = xml_file.readlines()
            self.assertTrue(lines[262] =='          <version>2.22</version>')



    @unittest.skip("Important test but will require some time to validate")
    def test_get_compilation_error_testcases(self):
        print('test_get_compilation_error_testcases')
        with open(os.getcwd() + r'\static_files\test_get_compilation_error_testcases_report.txt', 'r') as report_file:
            report = report_file.read()
        commit = [c for c in Main.all_commits if c.hexsha == 'a71cdc161b0d87e7ee808f5078ed5fefab758773'][0]
        parent = commit.parents[0]
        module_path = os.getcwd() + r'\tested_project\GitMavenTrackingProject\sub_mod_1'
        Main.repo.git.reset('--hard')
        Main.repo.git.checkout(commit.hexsha)
        commit_tests = Main.test_parser.get_tests(module_path)
        commit_testcases = Main.test_parser.get_testcases(commit_tests)
        expected_not_compiling_testcase = [t for t in commit_testcases if 'MainTest#gooTest' in t.mvn_name][0]
        Main.prepare_project_repo_for_testing(parent, module_path)
        commit_new_testcases = Main.get_commit_created_testcases(commit_testcases)
        compolation_error_testcases = Main.get_compilation_error_testcases(report, commit_new_testcases)
        self.assertTrue(expected_not_compiling_testcase in compolation_error_testcases,
                        "'MainTest#gooTest should have been picked as for compilation error")


if __name__ == '__main__':
    unittest.main()
