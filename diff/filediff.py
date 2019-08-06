import difflib
from subprocess import Popen, PIPE
import tempfile
import gc

import javalang
from javalang.tree import ConstructorDeclaration


class FileDiff(object):
    REMOVED = '- '
    ADDED = '+ '
    UNCHANGED = '  '
    NOT_IN_INPUT = '? '
    BEFORE_PREFIXES = [REMOVED, UNCHANGED]
    AFTER_PREFIXES = [ADDED, UNCHANGED]

    def __init__(self, diff):
        self.file_name = diff.b_path
        if not self.file_name.endswith(".java"):
            return
        self.before_contents = ['']
        if diff.new_file:
            assert diff.a_blob is None
        else:
            self.before_contents = diff.a_blob.data_stream.stream.readlines()
        self.after_contents = ['']
        if diff.deleted_file:
            assert diff.b_blob is None
        else:
            self.after_contents = diff.b_blob.data_stream.stream.readlines()
        assert self.before_contents != self.after_contents
        self.changed_methods = self.get_changed_methods()
        self.before_indices, self.after_indices = self.get_changed_indices()

    def get_changed_indices(self):
        def get_lines_by_prefixes(lines, prefixes):
            return filter(lambda x: any(map(lambda p: x.startswith(p), prefixes)), lines)

        def get_indices_by_prefix(lines, prefix):
            return map(lambda x: x[0], filter(lambda x: x[1].startswith(prefix), enumerate(lines)))

        diff = list(difflib.ndiff(self.before_contents, self.after_contents))

        diff_before_lines = get_lines_by_prefixes(diff, self.BEFORE_PREFIXES)
        assert map(lambda x: x[2:], diff_before_lines) == self.before_contents
        before_indices = get_indices_by_prefix(diff_before_lines, self.REMOVED)

        diff_after_lines = get_lines_by_prefixes(diff, self.AFTER_PREFIXES)
        assert map(lambda x: x[2:], diff_after_lines) == self.after_contents
        after_indices = get_indices_by_prefix(diff_before_lines, self.ADDED)

        return before_indices, after_indices

    def get_changed_methods(self):
        ans = []
        methods_range = []
        before_methods = {}
        after_methods = {}
        before_content_text = ''.join(self.before_contents)
        after_content_text = ''.join(self.after_contents)
        tree_1 = javalang.parse.parse(before_content_text)
        tree_2 = javalang.parse.parse(after_content_text)
        class_decls = [class_dec for _, class_dec in tree_1.filter(javalang.tree.ClassDeclaration)]
        for class_decl in class_decls:
            for method in class_decl.methods + class_decl.constructors:
                method_start = method.position[0]
                method_end = find_end_line(before_content_text, method.position[0])
                method_sig = generate_method_signiture(method)
                before_methods[method_sig] = []
                for i in range(method_start-1, method_end):
                    before_methods[method_sig].append(self.before_contents[i])
        class_decls = [class_dec for _, class_dec in tree_2.filter(javalang.tree.ClassDeclaration)]
        for class_decl in class_decls:
            for method in class_decl.methods + class_decl.constructors:
                method_start = method.position[0]
                method_end = find_end_line(after_content_text, method.position[0])
                method_sig = generate_method_signiture(method)
                after_methods[method_sig] = []
                for i in range(method_start-1, method_end):
                    after_methods[method_sig].append(self.after_contents[i])
        for method in before_methods.keys():
            if method in after_methods.keys():
                m_before_no_whitespace = list(filter(lambda l: len(l)>0, before_methods[method]))
                m_after_no_whitespace = list(filter(lambda l: len(l) > 0, after_methods[method]))
                if len(m_after_no_whitespace) == len(m_after_no_whitespace):
                    for i in range(0,len(m_after_no_whitespace)):
                        if not m_after_no_whitespace[i] == m_before_no_whitespace[i]:
                            ans.append(str(method))
                            break
                else:
                    ans.append(str(method))
        return ans




def get_methods_lines(contents):
    with tempfile.TemporaryFile() as f:
        f.writelines(contents)
        run_commands = ["java", "-jar", checkStyle68, "-c", methodNameLines, "javaFile", "-o", outPath, workingDir]
        proc = Popen(run_commands, stdout=PIPE, stderr=PIPE, shell=True)
        (out, err) = proc.communicate()


def find_end_line(src_text, line_num):
    brackets_stack = []
    open_position = (-1, -1)
    lines = src_text.split('\n')
    i = 1
    for line in lines:
        if i < line_num:
            i += 1
            continue
        j = 1
        for letter in line:
            if '{' == letter:
                brackets_stack.append('{')
                break
            else:
                j += 1
        if len(brackets_stack) == 1:
            open_position = (i, j)
            break
        i+=1
    if open_position[0] == -1 or open_position[1] == -1:
        return -1
    i = 1
    for line in lines:
        if i < open_position[0]:
            i += 1
            continue
        j = 1
        for letter in line:
            if i == open_position[0] and j <= open_position[1]:
                j += 1
                continue
            if letter == '{':
                brackets_stack.append('{')
            if letter == '}':
                brackets_stack.pop()
            if len(brackets_stack) == 0:
                return i
            j += 1
        i += 1

#Generates string representation of java method signiture
def generate_method_signiture(method):
    if isinstance(method, ConstructorDeclaration):
        ret_type = ''
    elif method.return_type is None:
        ret_type = 'void'
    else:
        ret_type = method.return_type.name
    if len(method.parameters) == 0:
        parameters = '()'
    else:
        parameters = '(' + method.parameters[0].type.name
        if len(method.parameters) > 1:
            param_iter = iter(method.parameters)
            next(param_iter)
            for param in param_iter:
                parameters += ', ' + param.type.name
        parameters += ')'
    #TODO IN ORDER TO DISTUNGUISH BTWEEN METHODS WITH EQUAL NAME THE TRACER SHOULD TAKE IN TO ACCOUNT THE FULL SIGNATURE
    return ret_type + '_' + method.name + parameters
    #return method.name

