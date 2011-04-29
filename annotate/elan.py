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

import xml.etree.ElementTree as ET
from time import strftime
from annotate import Annotation

class ElanAnnotation(Annotation):
    """
    Annotator for writing files for MPI's Elan.
    http://www.lat-mpi.eu/tools/elan/
    """
    def write_annotation(self):
        annotation_id = 1
        root = ET.Element('ANNOTATION_DOCUMENT',
                          {'AUTHOR': 'HLP Lab Automatic Aligner',
                           'DATE': strftime('%FT%R%z'),
                           'FORMAT': '2.6',
                           'VERSION': '2.6',
                           'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                           'xsi:noNamespaceSchemaLocation': 'http://www.mpi.nl/tools/elan/EAFv2.6.xsd'})
        header = ET.SubElement(root, 'HEADER',
                               {'MEDIA_FILE': '',
                                'TIME_UNITS': 'milliseconds'})
        media = ET.SubElement(header, 'MEDIA_DESCRIPTOR',
                              {'MEDIA_URL': 'file://{0}'.format(self.annotation_data['filename']),
                               'MIME_TYPE': 'audio/x-wav',
                               'RELATIVE_MEDIA_URL': 'file:{0}'.format(self.annotation_data['filename'])})
        prop = ET.SubElement(header, 'PROPERTY', {'NAME': 'lastUsedAnnotationId'})
        prop.text = str(len(self.annotation_data['words']) + len(self.annotation_data['phones']) + 2)
        timeorder = ET.SubElement(root, 'TIME_ORDER')
        for i,t in enumerate(self.annotation_data['time_slots'], 1):
            ts = ET.SubElement(timeorder, 'TIME_SLOT',
                               {'TIME_SLOT_ID': 'ts{0}'.format(i),
                                'TIME_VALUE': t})

        word_tier = ET.SubElement(root, 'TIER',
                                  {'ANNOTATOR': 'Auto',
                                   'DEFAULT_LOCALE': 'en',
                                   'LINGUISTIC_TYPE_REF': 'Word',
                                   'PARTICIPANT': self.annotation_data['participant'],
                                   'TIER_ID': 'Word'})
        for word in self.annotation_data['words']:
            start = word['xmin'] * 1000
            end = word['xmax'] * 1000
            ts1, ts2 = ('','')
            for i, t in enumerate(self.annotation_data['tsids']):
                if t['time'] == start:
                    ts1 = self.annotation_data['tsids'].pop(i)
                    break
            for i, t in enumerate(self.annotation_data['tsids']):
                if t['time'] == end:
                    ts2 = self.annotation_data['tsids'].pop(i)
                    break
            annot = ET.SubElement(root, 'ANNOTATION')
            annotation_id += 1
            alanot = ET.SubElement(annot, 'ALIGNABLE_ANNOTATION',
                                   {'ANNOTATION_ID': 'a{0}'.format(annotation_id),
                                    'TIME_SLOT_REF1': ts1,
                                    'TIME_SLOT_REF2': ts2})
            anval = ET.SubElement(alanot, 'ANNOTATION_VALUE')
            anval.text = word

        phone_tier = ET.SubElement(root, 'TIER',
                                   {'ANNOTATOR': 'Auto',
                                    'DEFAULT_LOCALE': 'en',
                                    'LINGUISTIC_TYPE_REF': 'Phoneme',
                                    'PARTICIPANT': self.annotation_data['participant'],
                                    'TIER_ID': 'Phoneme'})
        for phone in self.annotation_data['phones']:
            start = phone['xmin'] * 1000
            end = phone['xmax'] * 1000
            ts1, ts2 = ('','')
            for i, t in enumerate(self.annotation_data['tsids']):
                if t['time'] == start:
                    ts1 = self.annotation_data['tsids'].pop(i)
                    break
            for i, t in enumerate(self.annotation_data['tsids']):
                if t['time'] == end:
                    ts2 = self.annotation_data['tsids'].pop(i)
                    break
            annot = ET.SubElement(root, 'ANNOTATION')
            annotation_id += 1
            alanot = ET.SubElement(annot, 'ALIGNABLE_ANNOTATION',
                                   {'ANNOTATION_ID': 'a{0}'.format(annotation_id),
                                    'TIME_SLOT_REF1': ts1,
                                    'TIME_SLOT_REF2': ts2})
            anval = ET.SubElement(alanot, 'ANNOTATION_VALUE')
            anval.text = phone


        # These tags are cargo culted. I hand aligned a file in Elan and used the output
        # from that to determine what the structure of a file should look like
        ling_type1 = ET.SubElement(root, 'LINGUISTIC_TYPE',
                                   {'GRAPHIC_REFERENCES': 'false',
                                    'LINGUISTIC_TYPE_ID': 'default-lt',
                                    'TIME_ALIGNABLE': 'true'})
        ling_type2 = ET.SubElement(root, 'LINGUISTIC_TYPE',
                                   {'GRAPHIC_REFERENCES': 'false',
                                    'LINGUISTIC_TYPE_ID': 'Word',
                                    'TIME_ALIGNABLE': 'true'})
        ling_type3 = ET.SubElement(root, 'LINGUISTIC_TYPE',
                                   {'GRAPHIC_REFERENCES': 'false',
                                    'LINGUISTIC_TYPE_ID': 'Phoneme',
                                    'TIME_ALIGNABLE': 'true'})
        locale = ET.SubElement(root, 'LOCALE',
                               {'COUNTRY_CODE': 'US',
                                'LANGUAGE_CODE': 'en'})
        constraint1 = ET.SubElement(root, 'CONSTRAINT',
                      {'DESCRIPTION': "Time subdivision of parent annotation's time interval, no time gaps allowed within this interval",
                      'STEREOTYPE': 'Time_Subdivision'})
        constraint2 = ET.SubElement(root, 'CONSTRAINT',
                      {'DESCRIPTION': "Symbolic subdivision of a parent annotation. Annotations refering to the same parent are ordered",
                      'STEREOTYPE': 'Symbolic_Subdivision'})
        constraint3 = ET.SubElement(root, 'CONSTRAINT',
                      {'DESCRIPTION': "1-1 association with a parent annotation",
                      'STEREOTYPE': 'Symbolic_Association'})
        constraint4 = ET.SubElement(root, 'CONSTRAINT',
                      {'DESCRIPTION': "Time alignable annotations within the parent annotation's time interval, gaps are allowed",
                      'STEREOTYPE': 'Included_In'})

        tree = ET.ElementTree(root)
        tree.write('annotation.eaf', encoding = 'utf-8', xml_declaration = True, method = "xml")
