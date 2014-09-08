import os
import subprocess
import sys

from toolshelf.toolshelf import BaseCommand

class Command(BaseCommand):
    def setup(self, shelf):
        self.stats = {
          'sources': 0,
          'no_tests': [],
          'passes': [],
          'fails': []
        }

    def perform(self, shelf, source):
        self.stats['sources'] += 1
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
                self.stats['passes'].append(source)
            else:
                self.stats['fails'].append(source)
        else:
            self.stats['no_tests'].append(source)

    def teardown(self, shelf):
        stats = self.stats
        print "Total docked sources tested:   %s" % stats['sources']
        print "Total without obvious tests:   %s" % len(stats['no_tests'])
        if shelf.options.verbose:
            print [s.name for s in stats['no_tests']]
        print "Total passing:                 %s" % len(stats['passes'])
        if shelf.options.verbose:
            print [s.name for s in stats['passes']]
        print "Total failures:                %s" % len(stats['fails'])
        if shelf.options.verbose:
            print [s.name for s in stats['fails']]
