class SourceLine(object):
    def __init__(self, line, line_number, is_changed):
        self.line = line
        self.line_number = line_number
        self.is_changed = is_changed

    def __repr__(self):
        start = "  "
        if self.is_changed:
            start = "* "
        return "{0}{1}: {2}".format(start, str(self.line_number), self.line)

    @staticmethod
    def get_source_lines(start_line, end_line, contents, changed_indices, method_used_lines):
        source_lines = []
        for line_number in range(start_line - 1, end_line):
            if line_number not in method_used_lines:
                continue
            line = contents[line_number]
            is_changed = line_number in changed_indices
            source_lines.append(SourceLine(line, line_number, is_changed))
        return source_lines


class MethodData(object):
    def __init__(self, method_name, start_line, end_line, contents, changed_indices, method_used_lines, parameters, file_name):
        self.method_name = method_name
        self.start_line = int(start_line)
        self.end_line = int(end_line)
        self.implementation = contents[self.start_line - 1: self.end_line]
        self.method_used_lines = method_used_lines
        self.parameters = parameters
        self.file_name = file_name
        self.id = self.file_name + "@" + self.method_name + "(" + ",".join(self.parameters) + ")"
        self.source_lines = SourceLine.get_source_lines(start_line, end_line, contents, changed_indices, method_used_lines)
        self.changed = self._is_changed()

    def _is_changed(self):
        # return len(set(self.method_used_lines).intersection(set(indices))) > 0
        return any(filter(lambda line: line.is_changed, self.source_lines))
        # return any(filter(lambda ind: ind >= self.start_line and ind <= self.end_line, indices))

    def __eq__(self, other):
        assert isinstance(other, type(self))
        return self.method_name == other.method_name and self.parameters == other.parameters

    def __repr__(self):
        return self.id

    def get_changed_lines(self):
        return filter(lambda line: line.is_changed, self.source_lines)