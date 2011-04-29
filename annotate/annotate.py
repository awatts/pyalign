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

from __future__ import division, print_function
import re
import os
import sys

class Annotation(object):
    """
    Base class for all annotion writers. Reads in all of the files needed to
    generated an annotation. Subclasses must provide their own "write_annotation"
    method.
    """

    def __init__(self, path):
        self.path = path
        self.epsilon = 75
        self.frames_per_second = 100
        self.xmax = 0
        self.annotation_data = {'participant': 'NA',
                                'filename': 'audio.wav',
                                'words': [],
                                'phones': [],
                                'elems': [],
                                'tsids': []}

    def add_interval(self, arr, interval):
        """
        Document me.
        """
        seconds_per_frame = 1 / self.frames_per_second
        eps = seconds_per_frame / 100

        if len(arr) > 0:
            diff = interval['xmin'] - arr[-1]['xmax']
            if diff > (seconds_per_frame + eps):
                arr.append({'xmin': arr[-1]['xmax'], 'xmax': interval['xmin'], 'text': ''})
            elif diff > 0:
                arr[-1]['xmax'] = interval['xmin']
        elif interval['xmin'] > 0:
            arr.append({'xmin': 0, 'xmax': interval['xmin'], 'text': ''})

        arr.append(interval)
        if (interval['xmax'] > xmax):
            xmax = interval['xmax']

    def read_control_file(self):
        """
        Read in the 'ctl' and 'insent' files, then the 'wdseg' and 'phseg' files
        for each line of ('ctl', 'insent') and return arrays of start times, end
        times, and word(s)/phone for each utterance, plus the word segments, and
        the phone segments of the utterances
        """
        # utterances, words, and phones
        utts, wds, phs = [[] for x in range(4)]

        ctlfmt = re.compile(r'^\s*\S+\s+(\d+)\s+(\d+)\s+(\S+)\s*$')
        insentfmt = re.compile(r'\(([^\)]+)\)$')

        os.chdir(self.path)
        with open('ctl', 'r') as ctl:
            with open('insent') as insent:
                start_frame, end_frame, ctl_utt_id, insent_utt_id = [None for x in range(5)]

                while 1:
                    ctline = ctl.readline()
                    insentline = insent.readline()

                    ctlmatch = ctlfmt.match(ctline)
                    if ctlmatch:
                        start_frame, end_frame, ctl_utt_id = ctlmatch.groups()
                    else:
                        print("Invalid CTL line: {0}".format(ctline), file=sys.stderr)

                    insentmatch = insentfmt.search(insentline)
                    if insentmatch:
                        insent_utt_id = insentmatch.groups()[0]
                    else:
                        print("Invalid insent line: {0}".format(insentline), file=sys.stderr)

                    if not (ctl_utt_id == insent_utt_id):
                        print("utt id mismatch between ctl ({0}) and insent ({1})".format(ctl_utt_id, insent_utt_id) , file=sys.stderr)

                    # create utterance interval
                    self.add_interval(utts, {'xmin': int(start_frame) / self.frames_per_second,
                                             'xmax': int(end_frame) / self.frames_per_second,
                                             'text': re.sub('\([^\)]+\)$', '', insentline)})

                    # get word intervals in utterance
                    try:
                        with open('wdseg/{0}.wdseg'.format(ctl_utt_id), 'r') as wdseg:
                            wdsfmt = re.compile(r'^\s*(\d+)\s+(\d+)\s+(?:-)?\d+\s+(\S+)\s*$')
                            for line in wdseg:
                                start_frame, end_frame, word = [None for x in range(4)]
                                wdsmatch = wdsfmt.match(line)
                                if wdsmatch:
                                    start_frame, end_frame, word = wdsmatch.groups()
                                    word = re.sub('\([^\)]+\)$','', word)
                                    add_interval(wds, {'xmin': start_frame / self.frames_per_second + utts[-1]['xmin'],
                                                      'xmax': end_frame / self.frames_per_second + utts[-1]['xmin'],
                                                      'text': word})
                    except IOError:
                        print("warning: couldn't open wdseg/{0}.wdseg; using utt as word".format(ctl_utt_id), file=sys.stderr)
                        add_interval(wds, {'xmin': start_frame / self.frames_per_second,
                                          'xmax': end_frame / self.frames_per_second,
                                          'text': insentline})

                    # get phoneme intervals in utterance
                    try:
                        with open('phseg/{0}.phseg'.format(ctl_utt_id), 'r') as phseg:
                            phfmt = re.compile(r'^\s*(\d+)\s+(\d+)\s+(?:-)?\d+\s+(\S+)\s*$')
                            for line in phseg:
                                start_frame, end_frame, phone = [None for x in range(4)]
                                phmatch = phfmt.match(line)
                                if phmatch:
                                    start_frame, end_frame, phone = phmatch.groups()
                                    phone = re.sub('\([^\)]+\)$','', phone)
                                    add_interval(phs, {'xmin': start_frame / self.frames_per_second + utts[-1]['xmin'],
                                                      'xmax': end_frame / self.frames_per_second + utts[-1]['xmin'],
                                                      'text': phone})
                    except IOError:
                        print("warning: couldn't open phseg/{0}.phseg; using utt as phones".format(ctl_utt_id), file=sys.stderr)
                        add_interval(phs, {'xmin': start_frame / self.frames_per_second,
                                          'xmax': end_frame / self.frames_per_second,
                                          'text': insentline})
        return (utts, wds, phs)

    def generate_annotation_data(self):
        """
        Generate the data that will be fed to write_annotation
        """
        utts, wds, phs = self.read_control_file()
        time_slots, words, phones, tsids, elems = [[] for x in range(5)]
        sil = re.compile('^(<sil>|SIL|<s>|<\/s>|)$')

        for w in wds:
            if not sil.match(w['text']):
                self.annotation_data['time_slots'].append(w['xmin'] * 1000)
                self.annotation_data['time_slots'].append(w['xmax'] * 1000)
                self.annotation_data['words'].append(w['text'])
                self.annotation_data['elems'].append(w)

        for p in phs:
            if not sil.match(p['text']):
                self.annotation_data['time_slots'].append(p['xmin'] * 1000)
                self.annotation_data['time_slots'].append(p['xmax'] * 1000)
                self.annotation_data['phones'].append(p['text'])
                self.annotation_data['elems'].append(p)

        timeslots.sort()
        for i, t in enumerate(timeslots):
            ts = {'slot': 'ts{0}'.format(i+1),
                  'time': t}
            self.annotation_data['tsids'].append(ts)

    def write_annotation(self):
        raise NotImplementedError
