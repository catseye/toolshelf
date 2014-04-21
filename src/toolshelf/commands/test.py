import os
import subprocess
import sys

def test(shelf, args):
    stats = {
        'sources': 0,
        'no_tests': [],
        'passes': [],
        'fails': []
    }
    def test_it(source):
        stats['sources'] += 1
        if os.path.exists(os.path.join(source.dir, 'test.sh')):
            process = subprocess.Popen(
                './test.sh', shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            (std_output, std_error) = process.communicate()
            if shelf.options.verbose:
                sys.stdout.write(std_output)
                sys.stdout.write(std_error)
            if process.returncode == 0:
                stats['passes'].append(source)
            else:
                stats['fails'].append(source)
        else:
            stats['no_tests'].append(source)

    shelf.foreach_specced_source(
        shelf.expand_docked_specs(args), test_it
    )
    
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
