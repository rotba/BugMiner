import xml.etree.ElementTree as ET
import re
import os
import csv

import javalang


class TestClass:
    def __init__(self, file_path):
        self.path = os.path.realpath(file_path)
        self.module = self.find_module(self.path)
        self.testcases = []
        with open(self.path, 'r') as src_file:
            self.tree = javalang.parse.parse(src_file.read())
        class_decls = [class_dec for _, class_dec in self.tree.filter(javalang.tree.ClassDeclaration)]
        for class_decl in class_decls:
            for method in class_decl.methods:
                self.testcases.append(TestCase(method, class_decl,self))

    def get_mvn_name(self):
        relpath = os.path.relpath(self.path, self.module+'\\src\\test\\java').replace('.java', '')
        return relpath.replace('\\', '.')
    def get_path(self):
        return self.path
    def get_testcases(self):
        return self.testcases
    def get_module(self):
        return self.module
    def parse_src_path(self):
        ans = self.module_path
        ans+='\\src\\test\\java'
        packages = self.name.split('.')
        for p in packages:
            ans+='\\'+p
        return ans+'.java'
    def get_report_path(self):
        return self.module+'\\target\\surefire-reports\\'+'TEST-'+self.get_mvn_name()+'.xml'
    def __repr__(self):
        return str(self.get_path())
    def __eq__(self, other):
        if not isinstance(other, TestClass):
            return False
        else:
            return self.get_path()==other.get_path()

    def find_module(self, file_path):
        parent_dir = os.path.abspath(os.path.join(file_path, os.pardir))
        while parent_dir!=None:
            if os.path.isfile(parent_dir+'//pom.xml'):
                return parent_dir
            else:
                parent_dir = os.path.abspath(os.path.join(parent_dir, os.pardir))
        raise Exception(file_path+' is not part of a maven module')

class TestCase(object):
    def __init__(self, method, class_decl,parent):
        self.parent = parent
        self.method = method
        self.class_decl = class_decl
        self.id = parent.get_path()+'#'+self.class_decl.name+'#'+method.name
    def get_mvn_name(self):
        return self.parent.get_mvn_name()+'#'+self.method.name
    def get_path(self):
        return self.parent.get_path
    def get_id(self):
        return self.id
    def get_module(self):
        return self.parent.get_module()
    def get_parent(self):
        return self.parent
    def __repr__(self):
        return str(self.get_path())
    def __eq__(self, other):
        if not isinstance(other, TestCase):
            return False
        else:
            return self.get_path()==other.get_path()

class TestClassReport:
    def __init__(self, xml_doc_path, modlue_path):
        self.xml_path = xml_doc_path
        self.success_testcases = []
        self.failed_testcases = []
        self.testcases = []
        self.time = 0.0
        self.maven_multiModuleProjectDirectory = ''
        self.module_path = modlue_path
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        self.name = root.get('name')
        self.src_file_path = self.parse_src_path()
        for testcase in root.findall('testcase'):
            m_test =TestCaseReport(testcase, self)
            if m_test.test_passed:
                self.success_testcases.append(m_test)
            else:
                self.failed_testcases.append(m_test)
            self.testcases.append(m_test)
            self.time += m_test.get_time()
        properties_root = root.find('properties')
        properties = properties_root.findall('property')
        for property in properties:
            if property.get('name') == 'maven.multiModuleProjectDirectory':
                self.maven_multiModuleProjectDirectory = property.get('value')
    def get_time(self):
        return self.time
    def get_name(self):
        return self.name
    def get_testcases(self):
        return self.testcases
    def passed(self):
        return len(self.failed_testcases)==0
    def get_module(self):
        return self.module_path

    #Returns true if the given test name is this test or it's one of its testcases
    def is_associated(self, test):
        if test =='test' or test =='TEST' or test =='Test':
            return False
        if test in self.get_name():
            return True
        for testcase in self.get_testcases():
            if test in testcase.get_name():
                return True
        return False

    def __repr__(self):
        return str(self.get_name())

    def get_src_file_path(self):
        return self.src_file_path

    def parse_src_path(self):
        test_name = os.path.basename(self.xml_path).replace('TEST-','').replace('.java', '').replace('.xml', '')
        test_name = test_name.replace('.', '\\')
        test_name += '.java'
        return self.module_path + '\\src\\test\\java\\' + test_name


class TestCaseReport(object):
    def __init__(self, testcase, parent):
        self.parent = parent
        self.testcase_tag = testcase
        self.name = self.testcase_tag.get('name')
        self.time = float(re.sub('[,]', '', self.testcase_tag.get('time')))
        self.test_passed = True
        failure = self.testcase_tag.find('failure')
        if not failure is None:
            self.test_passed = False
        failure = self.testcase_tag.find('error')
        if not failure is None:
            self.test_passed = False

    def get_time(self):
        return self.time
    def get_name(self):
        return self.parent.get_name()+'#'+self.name
    def passed(self):
        return self.test_passed
    def get_src_path(self):
        return self.parent.src_path
    def get_module(self):
        return self.parent.get_module()
    def get_parent(self):
        return self.parent
    def __repr__(self):
        return str(self.get_name())



#Return parsed tests of the reports dir
def parse_tests_reports(path_to_reports, project_dir):
    ans = []
    for filename in os.listdir(path_to_reports):
        if filename.endswith(".xml"):
            ans.append(TestClass(os.path.join(path_to_reports, filename), project_dir))
    return ans

#Gets path to maven project directory and returns parsed
def get_tests(project_dir):
    ans = []
    if os.path.isdir(project_dir+'\\src\\test\java'):
        ans.extend(parse_tests(project_dir+'\\src\\test\java'))
    for filename in os.listdir(project_dir):
        file_abs_path = os.path.join(project_dir, filename)
        if os.path.isdir(file_abs_path):
            if not (filename=='src' or  filename=='.git'):
                ans.extend(get_tests(file_abs_path))
    return ans

#Parses all the test java classes in a given directory
def parse_tests(tests_dir):
    ans = []
    for filename in os.listdir(tests_dir):
        abs_path =os.path.join(tests_dir,filename)
        if os.path.isdir(abs_path):
            ans.extend(parse_tests(abs_path))
        elif filename.endswith(".java"):
            ans.append(TestClass(abs_path))
    return ans


# Gets path to maven project directory and returns parsed
def get_tests_reports(project_dir):
    ans = []
    path_to_reports = os.path.join(project_dir, 'target\\surefire-reports')
    if os.path.isdir(path_to_reports):
        ans.extend(parse_tests_reports(path_to_reports, project_dir))
    for filename in os.listdir(project_dir):
        file_abs_path = os.path.join(project_dir, filename)
        if os.path.isdir(file_abs_path):
            if not (filename=='src' or  filename=='.git'):
                ans.extend(get_tests_reports(file_abs_path))
    return ans


#Gets path to maven project directory and returns parsed
def get_cached_tests_reports(cached_proj_dir ,project_dir):
    ans = []
    path_to_reports = os.path.join(cached_proj_dir, 'target\\surefire-reports')
    if os.path.isdir(path_to_reports):
        ans.extend(parse_tests_reports(path_to_reports, project_dir))
    for filename in os.listdir(cached_proj_dir):
        file_abs_path = os.path.join(cached_proj_dir, filename)
        project_dir_abs_path = os.path.join(project_dir, filename)
        if os.path.isdir(file_abs_path):
            if not (filename=='src' or  filename=='.git'):
                ans.extend(get_cached_tests_reports(file_abs_path, project_dir_abs_path))
    return ans


#Returns all testcases of given test classes
def get_testcases(test_classes):
    ans = []
    for test_class in test_classes:
        ans+= test_class.get_testcases()
    return ans

def export_as_csv(tests):
    with open('all_tests.csv', 'a', newline='') as csvfile:
        fieldnames = ['test_name', 'time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for test in tests:
            writer.writerow({'test_name': test.get_name(), 'time': str(test.get_time())})

def get_mvn_exclude_tests_list(tests,time):
    count = 0
    ans ='-Dtest='
    for test in tests:
        if test.get_time()>time:
            if ans[len(ans)-1]!='=':
                ans+=','
            ans+='!'+test.get_name()
            count+=1
    return ans




