import os
import subprocess
import sys

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def setup(self, shelf):
        self.sources = 0
        self.no_tests = []
        self.passes = []
        self.fails = []

    def perform(self, shelf, source):
        self.sources += 1
        test_command = source.hints.get('test_command', None)
        if not test_command:
            if os.path.exists(os.path.join(source.dir, 'test.sh')):
                test_command = './test.sh'
        if test_command:
            process = subprocess.Popen(
                test_command, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            (std_output, std_error) = process.communicate()
            if shelf.options.verbose:
                sys.stdout.write(std_output)
                sys.stdout.write(std_error)
            if process.returncode == 0:
                self.passes.append(source)
            else:
                self.fails.append(source)
        else:
            self.no_tests.append(source)

    def teardown(self, shelf):
        print "Total docked sources tested:      %s" % self.sources
        print "Total without discoverable tests: %s" % len(self.no_tests)
        if shelf.options.verbose:
            print '(%s)' % ' '.join([s.name for s in self.no_tests])
        print "Total passing:                    %s" % len(self.passes)
        if shelf.options.verbose:
            print '(%s)' % ' '.join([s.name for s in self.passes])
        print "Total failures:                   %s" % len(self.fails)
        if self.fails:
            print '(%s)' % ' '.join([s.name for s in self.fails])
