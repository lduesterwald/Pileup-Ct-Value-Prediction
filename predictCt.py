import sys
import os
from os.path import exists
import pickle
import numpy as np

# this function parses paramaters passed in through the command line or sets them to a default vakue
# paramaters:
#   args: the list of arguments passed in through the command line
#   start_dir: the directory from which the script was run
# returns:
#   pileups_path: the path to the pileup file to predict the Ct value of
#   tmp_dir: the path to the temporary directory to be created by the script
#   model_name: the path to the pileup model to use to predict the Ct value
def parseParams(args, start_dir):
    # required parameter:
    pileup_path = "" # (-i)
    # setting default values for each parameter:
    tmp_dir = start_dir + "/tmp/" # (-t)
    out_dir = start_dir + "/output/" # (-o) # the ouput directory containing the matrix and model
    model_name = out_dir + "pileup_model.pkl" # (-n)

    for i in range(len(args)):
        if(args[i] == "-h" or args[i] == "--help"):
            print(helpOption())
            sys.exit()
        if (i == len(args) - 1):
            break
        elif (args[i] == "-i" or args[i] == "--pileup_path"):
            pileup_path = args[i + 1]
        elif (args[i] == "-t" or args[i] == "--tmp_dir"):
            tmp_dir = args[i + 1]
            if (tmp_dir.endswith("/") == False):
                tmp_dir+="/"
        elif (args[i] == "-o" or args[i] == "--out_dir"):
            out_dir = args[i + 1]
            if (out_dir.endswith("/") == False):
                out_dir = out_dir + "/"
            model_name = out_dir + "pileup_model.pkl"
        elif (args[i] == "-n" or args[i] == "--model_name"):
            model_name = out_dir + args[i + 1]


    # exitting the script if the required parameter was not passed in
    if (pileup_path == ""):
        print("Error: pileup_path (-i) required parameter not entered")
        sys.exit()

    # exitting the script if the tmp_dir already exists
    if (exists(tmp_dir)):
        print("Error: tmp_dir (-t) already exists")
        sys.exit()

    return pileup_path, tmp_dir, model_name

# returns a string of all the options for the script if the script was called with -h or --help
def helpOption():
    s="-i --pileup_path:\tthe path to the pileup file to predict the Ct value of"
    s+="-t --tmp_dir:\tthe path to the temporary directory to be created by the script"
    s+="-n --model_path:\tthe path to the pileup model to use to predict the Ct value"
    return s


# adjusts the length of the array representing the current pileup file to match the matrix the model was trained on
#   by either adding -1 (the base isn't present in this genome) to the end or removing extra rows
# parameters:
#   row: the array of this current row
#   cols: the number of columns in the matrix the model was trained on
# returns:
#   row: the new array with the correct length
def evenLength(row, cols):
    if (cols == len(row)):
        return row
    if (cols > len(row)): # add -1 to end of row
        diff = cols - len(row)
        for i in range(diff):
            row = np.append(row, -1)
        return row
    # delete extra values from row
    diff = len(row) - cols
    return row[:-diff]


# main function
# parses the passed in pileup file and predicts its Ct value using the pileup model
def main(argv):
    args = sys.argv
    start_dir = os.getcwd() # current directory
    script_path = os.path.dirname(os.path.realpath(argv[0])) # directory of the script
    if (script_path.endswith("/") == False):
        script_path+="/"

    # set parameters:
    pileup_path, tmp_dir, model_name  = parseParams(args, start_dir)
    print("--predictCt.py-- set parameters")

    # creating the temporary directory to store the pileup file
    os.system("mkdir " + tmp_dir)
    os.system("cp " + pileup_path + " " + tmp_dir)

    # parse the pileup file and create an array to represent the genome:
    arr_name = "this_row.npy"
    os.system("python3 " + script_path + "parsePileups.py -p " + tmp_dir + " -l " + tmp_dir + " -d None")
    os.system("python3 " + script_path + "createMat.py -l " + tmp_dir + " -o " + tmp_dir + " -m " + arr_name)

    # loading the model
    model = pickle.load(open(model_name, "rb"))

    # get the number of features in the model:
    num_ft = model.n_features_in_ 

    # open array representing this pileup
    arr = (np.load((tmp_dir + arr_name), allow_pickle=True))[0]
    this_row = evenLength(arr, num_ft) # evening the length
    print("--predictCt.py-- parsed pileup file")

    # removing the temporary directory:
    os.system("rm -r " + tmp_dir)

    # making prediction:
    p = (model.predict(this_row.reshape(1, -1)))[0]
    print("--predictCt.py-- got prediction")

    # printing prediction:
    print("\nPredicted Ct value: ", p)


# if this is the script called by python, run main function
if __name__ == '__main__':
	main(sys.argv)
