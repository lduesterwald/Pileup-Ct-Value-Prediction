import sys
import os
import pickle

import pandas as pd
import numpy as np
from os.path import exists

# this function parses paramaters passed in through the command line or sets them to a default vakue
# paramaters:
#   args: the list of arguments passed in through the command line
#   start_dir: the directory from which the script was run
# returns:
#   pileups_dir: the directory containing pileup files (in .gz or .pileup format) to be parsed
#   lists_dir: the output directory to which to store the lists outputted by this script
#   metadata_path: the path to the .csv metadata file containing information about each pileup file in pileups_dir
def parseParams(args, start_dir):
    # setting default values for each parameter
    pileups_dir = start_dir + "/" # (-p)
    lists_dir = start_dir + "/pileup_lists/" # (-l)
    # required parameter:
    metadata_path = "" # (-d)

    for i in range(len(args)):
        if(args[i] == "-h" or args[i] == "--help"):
            print(helpOption())
            sys.exit()
        if (i == len(args) - 1):
            break
        elif (args[i] == "-p" or args[i] == "--pileups_dir"):
            pileups_dir = args[i + 1]
            if (pileups_dir.endswith("/") == False):
                pileups_dir+="/"
        elif (args[i] == "-l" or args[i] == "--lists_dir"):
            lists_dir = args[i + 1]
            if (lists_dir.endswith("/") == False):
                lists_dir+="/"
        elif (args[i] == "-d" or args[i] == "--metadata_path"):
            metadata_path = args[i + 1]

    # creating output_dir if it does not already exist:
    if (exists(lists_dir) == False):
        os.system("mkdir " + lists_dir)

    # exitting the script if the required parameter was not passed in
    if (metadata_path == ""):
        print("Error: metadata_path (-m) required parameter not entered")
        sys.exit()

    return pileups_dir, lists_dir, metadata_path

# returns a string of all the options for the script if the script was called with -h or --help
def helpOption():
    s = "-p --pileups_dir:\tthe directory containing the .gz or .pileup pileup files to train the model. The default is './'"
    s+= "\n-l --lists_dir:\tthe directory for storing the parsed output lists created by the script. The default is ./pileup_lists/"
    s+= "\n-d --metadata_path:\tthe path to the metadata .csv file with the genome_id, testing instrument, and Ct value of all pileup files. There is no default for this option."
    return s


#finds the position in the tuple of the character
def findPos(c):
    if (c == "A" or c == "a"):
        return 0
    if (c == "C" or c == "c"):
        return 1
    if (c == "G" or c == "g"):
        return 2
    if (c == "T" or c == "t"):
        return 3
    if (c == "I"): #insertion
        return 4
    if (c == "D"): #deletion
        return 5
    return None

# checks whether the inputed charcter (s) is a nucleotide base
# returns:
#   True if s is A, C, T, G, a, c, t, or g or False otherwise
def isBase(s):
    if (((((s == "A") or (s == "C")) or (s == "G")) or s == "T")):
        return True
    if (((((s == "a") or (s == "c")) or (s == "g")) or s == "t")):
        return True
    return False


# gets the instrument and ct value of the given genome_id from the csv file
# gets the Ct value and instrument of the a specific genome
# parameters:
#    csv_path: the path to the metadata csv file containing the information about the genome
#    genome_id: the genome id of the genome for which to find the Instrument and Ct value
# returns: a list of the instrument and Ct value or None if the genome_id was not in the csv file
def getInfo(csv_file, genome_id):
    for index, row in csv_file.iterrows():
        if (row["ID"] == genome_id):
            ct = row["Ct Value"]

            if np.isnan(ct):
                return None
            else:
                return ct
    return None  # the genome_id was not found in the metadata file

# calculates if a position is masked
# first and last 100 are masked and the low depth positions
#   22029-22033, 22340-22367, 22897, 22899-22905, and 23108-23122,
def isMasked(pos):
    if ((pos <= 100) or (pos > 29803)):
        return True
    # checking the low depth positions
    elif ((pos >= 22029) and (pos <= 22033)):
        return True
    elif ((pos >= 22340) and (pos <= 22367)):
        return True
    elif (pos == 22897):
        return False
    elif ((pos >= 22899) and (pos <= 22905)):
        return True
    elif ((pos >= 23108) and (pos <= 23122)):
        return True
    # otherwise, it is not masked:
    return False


# normalizes the inputted tuple
# parameters:
#   t: a tuple of counts
# returns:
#   the input tuple as a normalized tuple of frequencies
def normalizeTup(t):
    t2 = []
    tot = float(sum(t))
    if (tot == 0): #checking that there are read results for this tuple, if not returning a tuple of 0s
        return [0, 0, 0, 0, 0, 0]
    for j in range(len(t)):
        v = float(t[j])
        v = v / tot
        t2.append(v)
    return t2


# parses the read results of the string passed in, reading in results one character at a time
# parameters:
#   s: string of read results
#   ref: the reference nucleotide (major allele)
# returns:
#   tuple: a tuple of the parsed read results for a given nucleotide position
#   for this position, tuple contains the frequencies of [A, C, T, G, insertion, deletion]
def parseResults(s, ref):
    # initializing the tuple to keep track of frequencies
    tup = [0, 0, 0, 0, 0, 0]

    i = 0 # keep track of the index in the string
    # iterate through s (read results)
    while (i < len(s)):
        c = s[i] # character at index i of string s

        if (c == "." or c == ","): # same as the reference nucleotide (ref)
            pos = findPos(ref) # this is the position in the tuple of the reference nucleotide
            tup[pos] = tup[pos] + 1
            i = i + 1

        elif (isBase(c)): # nucleotide base
            pos = findPos(c) # this is the position in the tuple of the current nucleotide base
            tup[pos] = tup[pos] + 1
            i = i + 1

        elif (c == "+" or c == "-"): # insertion or deletion
            if (c == "+"):
                tup[4] = tup[4] + 1 # increasing the insertion tuple
            else:
                tup[5] = tup[5] + 1 # increasing the deletion tuple
            if (i != (len(s) - 1)):
                num = int(s[i + 1]) # the number of bases that were inserted/deleted
                i = i + (2 + num) # move i to ahead of the inserted/deleted sequence
            else:
                i = i + 1

        elif (c == "^"): # caret (start of a segment)
            # ignore the start and the character after it (gives sequence quality)
            i = i + 2

        elif (c == "*"): # deletion:
            tup[5] = tup[5] + 1 # increasing the deletion tuple
            i = i + 1

        else: # end character ($) or ambiguous nucleotide N (</>) or character wasn't recognized
            i = i + 1

    # normalize the tuple to frequencies
    tuple = normalizeTup(tup)
    return tuple


# returns the number of positions masked before a nucleotide position passed in
# paramaters:
#   p: the nucleotide position
def getMasked(p):
    if (p < 22029):
        return 100
    if (p < 22340):
        return 105
    if (p < 22897):
        return 133
    if (p < 22899):
        return 134
    if (p < 23108):
        return 141
    return 156

# returns the positon that the given nucleotide position should be at in the list
def getPos(nuc_pos):
    return (nuc_pos - getMasked(nuc_pos))*6

def parseFile(pileup_dir, pileup_file, met, meta_file, lists_dir, genome_id):
    # reading through the pileup files
    fi = open((pileup_dir + pileup_file), "r")
    if (met == True):
        ct  = getInfo(meta_file, genome_id)
    else:
        ct = None # no metadata info

    lst = []
    for aline in fi:
        vals = aline.split("\t")

        if (len(vals) >= 5): #checking that the line has all the information needed
            seq = vals[0] # the sequence
            pos = int(vals[1]) # the nucleotide position

            if (isMasked(pos) == False): #checking whether the position was masked
                nuc = vals[2] # the nucleotide at the position
                dep = vals[3] # the read depth
                res = vals[4] # the read results

                # parsing the read results, tup is a tuple of frequencies of [A, C, T, G, insertion, deletion] for this nucleotide position
                tup = parseResults(res, nuc)

                # adding -1 (the position was not in the pileup file) to the list so that the list indexes correspond correeclty to nucleotide positions
                diff = getPos(pos) - len(lst)
                for i in range(diff): # adding diff -1s  to the list so that the position is right
                    lst.append(-1)

                # adding the tuple of frequencies to the list
                for item in tup:
                    lst.append(item)

    # add the Ct value at the beginning of the list
    lst.insert(0, ct)
    # storing the list in the output directory
    out_f = (lists_dir + genome_id + ".pkl")
    os.system("touch " + out_f)
    f_opn = open(out_f, "wb")
    pickle.dump(lst, (f_opn))
    f_opn.close()

# main functions
# parses all the pileup files in a directory and stores the parsed results as lists
def main(argv):
    args = sys.argv
    start_dir = os.getcwd() # current directory:

    # set parameters:
    pileups_dir, lists_dir, metadata_path = parseParams(args, start_dir)

    if (metadata_path == "None"): # Do not store any metadata with the pileup lists
        met = False
        meta_file = None
    else:
        met = True
        meta_file = pd.read_csv(metadata_path)
    c = 0 # track the number of files parsed

    print("--parsePileups.py-- started script, beginning to parse files")
    for filename in os.scandir(pileups_dir):
        f = str(filename).strip("<DirEntry ' ''>")
        # checking that the file is the right format
        if (f.endswith(".gz")):
            genome_id = f.replace(".gz", "")
   
           if (genome_id.endswith(".pileup") == False):
                pileup_file = genome_id + ".pileup"
    
           # unzip the file
            os.system("gzip -d " + (pileups_dir + f))

            parseFile(pileups_dir, pileup_file, met, meta_file, lists_dir, genome_id)
            # printing updates every 100 files:
            if (c % 100 == 0):
                print("\tparsed file: ", c)
            c = c + 1

        elif (f.endswith(".pileup")):
            genome_id = f.replace(".pileup", "")
            parseFile(pileups_dir, (genome_id + ".pileup"), met, meta_file, lists_dir, genome_id)
            # printing updates every 100 files:
            if (c % 100 == 0):
                print("\tparsed file: ", c)
            c = c + 1



    print("--parsePileups.py-- finished script, stored output lists in: ", lists_dir)

# if this is the script called by python, run main function
if __name__ == '__main__':
    main(sys.argv)

