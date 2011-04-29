#!/usr/bin/env python

#Author: Andrew Watts
#
#    Copyright 2009-2011 Andrew Watts and
#        the University of Rochester BCS Department
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License version 2.1 as
#    published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.
#    If not, see <http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>.
#

# Based almost entirely on the make-ctl.pl script written by
# various people in the CS department at the University of Rochester
# Pythonified by Andrew Watts

from __future__ import division, print_function
import re
import os

class Ctl(object):
    """
    Reads in a Sphinx3 boundaries file and generates a Sphinx3 CTL file.
    """

    def __init__(self, path):
        self.path = path

    def load_manual_boundaries(self):
        boundaries = []
        os.chdir(self.path)
        with open('boundaries', 'r') as boundfile:
            for line in boundfile:
                boundaries.append(line)
        return boundaries

    def load_automatic_endpoints(self):
        """
        Write some docstringage
        """
        uttstart = re.compile(r'^Utt_Start#\d+, Leader: ([\d\.]+),')
        uttcanc = re.compile(r'^Utt_Cancel')
        uttend = re.compile(r'^Utt_End#(\d+), End: [\d\.]+,  Trailer: ([\d\.]+)')

        intervals = []
        with open('ep', 'r') as ep:
            for line in ep:
                start, end = None, None
                usm = uttstart.search(line)
                ucm = uttcanc.search(line)
                uem = uttend.search(line)
                if usm:
                    start = int(usm.groups()[0]) * 100
                elif ucm:
                    start = None
                elif uem:
                    end = int(uem.groups()[1]) * 100
                intervals.append({'start': start, 'end': end})
        return intervals

    def find_control_intervals(self, boundaries, intervals):
        """
        Write some docstringage
        """
        next_interval = 1
        control = []
        for uttid in boundaries:
            while (next_interval < len(intervals) and intervals[next_interval]['end']< boundaries[uttid-1] + self.epsilon):
                nextInterval += 1

            new_control = {'start': control[-1]['end'] + 1 if len(control) > 0 else 0,
                           'end': next_interval-1,
                           'uttid': "utt{0}".format(uttid)}

            if (intervals[newControl['end']]['end'] < boundaries[uttid-1] - self.epsilon):
                # too much of a difference, snap to the manual boundary
                intervals[newControl['end']]['end'] = boundaries[uttid-1]

            if (new_control['start'] <= new_control['end']):
                control.append(new_control)
            else:
                control[-1]['uttid'] = re.sub(r'^utt(\d+)(?:\-\d+)?$',r'utt\1-'+ str(uttid), control[-1]['uttid'])

        #snap interval pointers
        for c in control:
            c['start'] = intervals[c['start']]['start']
            c['end'] = intervals[c['end']]['end']

        # fix overlapping intervals by setting both to their average
        for i,c in enumerate(control, 1):
            if (control[i-1]['end'] > control[i]['start']):
                control[i-1]['end'] = control[i]['start'] = int((control[i-1]['end'] + control[i]['start']) / 2);

        return control

    # write control file
    def write_control_file(self):
        boundaries = self.load_manual_boundaries()
        intervals = self.load_automatic_endpoints()
        control = self.find_control_intervals(boundaries, intervals)

        with open('ctl', 'w') as ctl:
            for line in control:
                if line['start'] == None:
                    line['start'] = 0
                print('./ {0} {1} {2}'.format(line['start'], line['end'], line['uttid']), file=ctl)
