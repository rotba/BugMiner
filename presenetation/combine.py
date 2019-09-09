import csv
import os
import shutil
import sys
from functools import reduce
from openpyxl import load_workbook
from mvnpy.bug import Bug_data_handler

maxInt = sys.maxsize

while True:
	# decrease the maxInt value by factor 10
	# as long as the OverflowError occurs.

	try:
		csv.field_size_limit(maxInt)
		break
	except OverflowError:
		maxInt = int(maxInt / 10)

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'combined')


class Combiner(object):
	PROJ_HEADER = 'project name'
	def __init__(self, results_dir, combined_path=DEFAULT_PATH):
		def is_project_dir(path):
			return 'data' in os.listdir(path)

		self._projects = map(
			lambda x: Project_Factory.create(x),
			filter(lambda y: is_project_dir(y), map(lambda z: os.path.join(results_dir, z), os.listdir(results_dir)))
		)
		self._combined_path = combined_path
		if not os.path.isdir(self._combined_path):
			os.mkdir(self._combined_path)

	def combine(self, table_name):
		f_path = os.path.join(self._combined_path, table_name+'.csv')
		if os.path.isfile(f_path):
			os.remove(f_path)
		with open(f_path, 'a+') as csv_output:
			writer = csv.DictWriter(csv_output, fieldnames=self.infer_fields(table_name), lineterminator='\n')
			writer.writeheader()
			for row in self.reduce_combined_table(table_name):
				writer.writerow(row)

	def reduce_combined_table(self, table_name):
		return reduce(
			lambda acc, curr: acc + curr,
			map(lambda x: map(lambda y: self.wrap_project_row(y, x), x.get_rows(table_name)), self._projects),
			[]
		)

	def wrap_project_row(self, row, proj):
		return self.push_project_name(row, proj)

	def push_project_name(self, row, proj):
		row.update({Combiner.PROJ_HEADER:proj.name})
		return row

	def infer_fields(self, table_name):
		return [Combiner.PROJ_HEADER] + reduce(lambda acc, curr: curr.get_headers(table_name) if acc == None else acc,
		                                 self._projects, None)


class Project_Factory(object):

	@classmethod
	def create(self, path):
		return Project(path)


class Project(object):

	def __init__(self, path):
		def is_table(path):
			return path.endswith('.csv')

		self._path = path
		self._data_path = os.path.join(self._path, 'data')
		self._name = os.path.basename(path)
		self._tables = filter(lambda x: is_table(x),
		                      map(lambda y: os.path.join(self._data_path, y), os.listdir(self._data_path)))

	@property
	def name(self):
		return self._name

	def get_rows(self, table_name):
		return self.csv_to_rows(self.get_table_path(table_name))

	def csv_to_rows(self, table_file):
		with open(table_file, 'r') as f:
			reader = csv.DictReader(f)
			return list(reader)

	def get_table_path(self, table_name):
		return reduce(
			lambda acc, curr: curr if acc == None and os.path.basename(curr) == table_name + '.csv' else acc,
			self._tables,
			None
		)

	def get_headers(self, table_name):
		with open(self.get_table_path(table_name), "rb") as f:
			reader = csv.reader(f)
			return reader.next()


if __name__ == '__main__':
	Combiner(sys.argv[1]).combine(sys.argv[2])
