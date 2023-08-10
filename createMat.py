import sys
import os
import pickle
import numpy as np
from os.path import exists

# this function parses paramaters passed in through the command line or sets them to a default vakue
# paramaters:
#   args: the list of arguments passed in through the command line
#   start_dir: the directory from which the script was run
# returns:
#   lists_dir: the directory containing pileup files (in .gz format) to be parsed
#   out_dir: the directory in which to store outputs from the script
#   mat_name: the name that the matrix created by the script will be stored as
#   ct_name: the name that the ordered list of Ct values created by the script will be stored as
def parseParams(args, start_dir):
    # setting default values for each parameter:
    lists_dir = start_dir + "/pileup_lists/" # (-l)
    out_dir = start_dir + "/output/" # (-o)
    mat_name = out_dir + "pileup_matrix.npy" # (-m)
    ct_name = out_dir + "pileup_cts.pkl" # (-c)


    for i in range(len(args)):
        if(args[i] == "-h" or args[i] == "--help"):
            print(helpOption())
            sys.exit()
        if (i == len(args) - 1):
            break
        elif (args[i] == "-l" or args[i] == "--lists_dir"):
            lists_dir = args[i + 1]
            if (lists_dir.endswith("/") == False):
                lists_dir+="/"
        elif (args[i] == "-o" or args[i] == "--out_dir"):
            out_dir = args[i + 1]
            if (out_dir.endswith("/") == False):
                out_dir = out_dir + "/"
            mat_name = out_dir + "pileup_matrix.npy"
            ct_name = out_dir + "pileup_cts.pkl"
        elif (args[i] == "-m" or args[i] == "--mat_name"):
            mat_name = out_dir + args[i + 1]
        elif (args[i] == "-c" or args[i] == "--ct_name"):
            ct_name = out_dir + args[i + 1]

    # creating output_dir if it does not already exist:
    if (exists(out_dir) == False):
        os.system("mkdir " + out_dir)

    return lists_dir, out_dir, mat_name, ct_name


# returns a string of all the options for the script if the script was called with -h or --help
def helpOption():
    s= "-l --lists_dir:\tthe directory containing the parsed pileup lists as .npy files created by parsePileups.py. The default is ./pileup_lists/"
    s+="\n-o --out_dir:\tthe directory in which to store outputs from the script. The default is ./output"
    s+="\n-m --mat_name:\tthe name that the pileup matrix created by the script will be stored as. The default is 'pileup_matrix.npy'"
    s+="\n-c --ct_name:\tthe name that the ordered list of Ct values created by the script will be stored as. The default is 'pileup_cts.pkl'"
    return s


# reads every parsed list file in the lists_dir directory and appends it to an array
# parameters:
#   lists_dir: the directory of pileup lists
# returns:
#   cts: the list of Ct values corresponding to the order of rows in the array
#   arr: the array created by appending all the pileup lists in the directory
#   max_len: the length of the longest row in the array
def makeArray(lists_dir):
    arr = [] # initialize array
    # initialize Ct value list
    cts = []
    max_len = 0 # keep track of the longest list
    ind = 0

    for filename in os.scandir(lists_dir):
        f = str(filename).strip("<DirEntry ' ''>")
        genome_id = str(f).replace(".pkl", "")

        fi = open((lists_dir + f), "rb")  # open the list
        lst = pickle.load(fi)

        if (len(lst) > max_len):
            max_len = len(lst)

        # updating every 250 lists read
        if (ind % 250 == 0):
            print("\tread list: ", ind)
        ind = ind + 1

        # updating the metadata lists:
        cts.append(lst[0])
        # removing the Ct value from this list and adding it to the array
        del lst[0]
        arr.append(lst)

    return cts, arr, max_len


# evens the lengths of all of the rows in the array
# adds -1 (representing the absence of this nucleotide position in the genome) to the end of all shorter lists so that every row has the same length
# parameters:
#   arr: the array to even
#   max_len: the length of the longest row of the array
def evenLength(arr, max_len):
    for i in range(len(arr)):
        l = arr[i] # get current row (list)
        if (len(l) < max_len):
            for j in range((max_len - len(l))):
                arr[i].append(-1) # adding -1 until the length of this row is max_len
    return arr


# main functions
# creates and stores a matrix to represent the pileup files with columns
#   of the frequency of A, C, T, G, ins, del or every nucleotide positon in the genomes
# every genome is one row in the matrix
def main(argv):
    args = sys.argv
    start_dir = os.getcwd() # current directory

    # set parameters:
    lists_dir, strt, mat_name, ct_name = parseParams(args, start_dir)
    print("--createMat.py-- set parameters")

    # read in the parsed lists created by parsePileups.py to create the matrix
    cts, arr, max_len = makeArray(lists_dir)
    print("--makePileupMat.py-- made matrix")

    # even the lengths of all rows by adding -1 to the ends of shorter genomes
    even_arr = evenLength(arr, max_len)
    print("--makePileupMat.py-- evened array lengths")

    # storing the matrix as a numpy array
    mat = np.array(even_arr, dtype=np.float64)
    np.save(mat_name, mat)

    # save the Ct value list:
    f_opn = open(ct_name, "wb")
    pickle.dump(cts, f_opn)

    print("--createMat.py-- saved matrix as: ", mat_name, " and Ct value list as: ", ct_name)


# if this is the script called by python (vs being called by another)
# script, run main().
if __name__ == '__main__':
        main(sys.argv)
