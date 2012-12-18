'''
Created on 2012-02-10

@author: coteharn
'''
import os
import os.path as path

from tractconverter import TractConverter
import argparse
import logging


def walkAndConvert(p_input, p_conversions, p_output=None, p_anatFile=None, p_isRecursive=False, p_overwrite=False):

    for root, dirs, allFiles in os.walk(p_input):
        logging.info('Processing "{0}"...'.format(root))
        root = root + "/"
        nbFiles = 0
        for k, v in p_conversions.items():
            files = [f for f in allFiles if f[-3:] == k]
            for f in files:
                nbFiles += 1
                inFile = root + f
                logging.info('{0}/{1} files'.format(nbFiles, len(allFiles)))

                if p_output is not None:
                    outfile = p_output + '/' + f[:-3] + v
                else:
                    outfile = inFile[:-3] + v

                if path.exists(outfile) and not p_overwrite:
                    logging.info(f + " : Already Done!!!")
                    continue

                TractConverter.convert(inFile, outfile, p_anatFile)
                logging.info(inFile)

        logging.info('{0} skipped (none track files)'.format(len(allFiles) - nbFiles))
        if not p_isRecursive:
            break

    logging.info("Conversion finished!")

#####
# Script part
###

#Script description
DESCRIPTION = 'Convert track files while walking down a path. ({0})'.format(",".join(TractConverter.FORMATS.keys()))


def buildArgsParser():
    p = argparse.ArgumentParser(description=DESCRIPTION)
    p.add_argument('-i', action='store', dest='input',
                   metavar='DIR', required=True,
                   help='path to walk')
    p.add_argument('-o', action='store', dest='output',
                   metavar='DIR',
                   help='output folder (if omitted, the walking folder is used)')
    p.add_argument('-a', action='store', dest='anat',
                   metavar='FILE', required=False,
                   help='anatomy file ({0})'.format(TractConverter.EXT_ANAT))

    #FIB
    p.add_argument('-fib2tck', action='store_true', dest='fib2tck',
                   help='convert .fib to .tck (anatomy needed)')
    p.add_argument('-fib2trk', action='store_true', dest='fib2trk',
                   help='convert .fib to .trk')
    #TCK
    p.add_argument('-tck2fib', action='store_true', dest='tck2fib',
                   help='convert .tck to .fib (anatomy needed)')
    p.add_argument('-tck2trk', action='store_true', dest='tck2trk',
                   help='convert .tck to .trk (anatomy needed)')
    #TRK
    p.add_argument('-trk2tck', action='store_true', dest='trk2tck',
                   help='convert .trk to .tck (anatomy needed)')
    p.add_argument('-trk2fib', action='store_true', dest='trk2fib',
                   help='convert .trk to .fib')

    p.add_argument('-R', action='store_true', dest='isRecursive',
                   help='make a recursive walk')
    p.add_argument('-f', action='store_true', dest='isForce',
                   help='force (pass extension check; overwrite output file)')
    p.add_argument('-v', action='store_true', dest='isVerbose',
                   help='produce verbose output')

    return p


def main():
    parser = buildArgsParser()
    args = parser.parse_args()

#    args = parser.parse_args(['-i', r'C:\Arnaud_trackConverters_data\trk\\',
#                              '-o', r'C:\Arnaud_trackConverters_data\out\\',
#                              '-a', r'C:\t2.nii.gz',
#                              '-trk2tck',
#                              '-v', '-h',
#                              #'-f', '-v',
#                              ])

    input = args.input
    output = args.output
    anat = args.anat
    fib2tck = args.fib2tck
    fib2trk = args.fib2trk
    trk2tck = args.trk2tck
    trk2fib = args.trk2fib
    tck2trk = args.tck2trk
    tck2fib = args.tck2fib
    isRecursive = args.isRecursive
    isForcing = args.isForce
    isVerbose = args.isVerbose

    if isVerbose:
        logging.basicConfig(level=logging.DEBUG)

    if not os.path.isdir(input):
        parser.error('"{0}" must be a folder!'.format(input))

    if output is not None:
        if not os.path.isdir(output):
            if isForcing:
                logging.info('Creating "{0}".'.format(output))
                os.makedirs(output)
            else:
                parser.error("Can't find the output folder")

    #TODO: Warn if duplicate conversion (i.e. tck2X, tck2Y)
    conversions = {}
    if fib2tck:
        conversions['fib'] = 'tck'
    if fib2trk:
        conversions['fib'] = 'trk'
    if trk2tck:
        conversions['trk'] = 'tck'
    if trk2fib:
        conversions['trk'] = 'fib'
    if tck2trk:
        conversions['tck'] = 'trk'
    if tck2fib:
        conversions['tck'] = 'fib'

    if len(conversions) == 0:
        parser.error('Nothing to convert! Please specify at least one conversion.')

    if anat is not None:
        if not any(map(anat.endswith, TractConverter.EXT_ANAT.split('|'))):
            if isForcing:
                logging.info('Reading "{0}" as a {1} file.'.format(anat.split("/")[-1], TractConverter.EXT_ANAT))
            else:
                parser.error('Anatomy file must be one of {0}!'.format(TractConverter.EXT_ANAT))

        if not os.path.isfile(anat):
            parser.error('"{0}" must be an existing file!'.format(anat))

    walkAndConvert(input, conversions, output, anat, isRecursive, isForcing)

if __name__ == "__main__":
    main()
