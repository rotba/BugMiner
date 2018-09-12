import pickle
import sys


def main(argv):
    cache_file = open('results\\'+argv[0], 'rb')
    bugs = pickle.load(cache_file)
    for bug in bugs:
        print(bug)


if __name__ == '__main__':
    main(sys.argv[1:])