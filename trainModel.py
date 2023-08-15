import sys
import os
import pickle
import random
import numpy as np

from sklearn.ensemble import RandomForestRegressor

# for model evaluation:
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
import statistics
import math

# sets the parameters for the script:
# paramaters:
#   args: the list of arguments passed in through the command line
#   start_dir: the directory from which the script was run
# returns:
#   out_dir: the directory in which to store outputs from the script
#   mat_name: the name of the pileup matrix
#   ct_name: the name of the ordered list of Ct values
#   out_file: the name of the file to which to write the output of the script
#   model_name: the name that the model trained in the first fold will be stored as
#   num_trees: the number of trees ('n_estimators' parameter for the model)
#   tree_depth: the value for tree depth  ('max_depth parameter for the model)
#   row_subsampling: the value for row subsampling ('max_samples' parameter for the model)
def parseParams(args, start_dir):
    # setting default values for each parameter:
    out_dir = start_dir + "/output/" # (-o)
    mat_name = out_dir + "pileup_matrix.npy" # (-m)
    ct_name = out_dir + "pileup_cts.pkl" # (-c)
    out_file = out_dir + "pileup_model_output" # (-f)
    model_name = out_dir + "pileup_model.pkl"# (-n)
    # parameters for the model, default values are the optimal ones found during prameter tuning
    num_trees = 400 # (-nt)
    tree_depth = None # (-td)
    row_subsampling = 0.25 # (-rs)


    for i in range(len(args)):
        if(args[i] == "-h" or args[i] == "--help"):
            print(helpOption())
            sys.exit()
        if (i == len(args) - 1):
            break
        elif (args[i] == "-o" or args[i] == "--out_dir"):
            out_dir = args[i + 1]
            if (out_dir.endswith("/") == False):
                out_dir = out_dir + "/"
            mat_name = out_dir + "pileup_matrix.npy"
            ct_name = out_dir + "pileup_cts.pkl"
            out_file = out_dir + "pileup_model_output"
            model_name = out_dir + "pileup_model.pkl"
        elif (args[i] == "-m" or args[i] == "--mat_name"):
            mat_name = out_dir + args[i + 1]
        elif (args[i] == "-c" or args[i] == "--ct_name"):
            ct_name = out_dir + args[i + 1]
        elif (args[i] == "-f" or args[i] == "--out_file"):
            out_file = out_dir + args[i + 1]
        elif (args[i] == "-n" or args[i] == "--model_name"):
            model_name = out_dir + args[i + 1]
        elif( args[i] == "-nt" or args[i] == "--num_trees"):
            num_trees = args[i + 1]
        elif( args[i] == "-td" or args[i] == "--tree_depth"):
            tree_depth = args[i + 1]
        elif( args[i] == "-rs" or args[i] == "--row_subsampling"):
            row_subsampling = args[i + 1]

    os.system("touch " + out_file)

    return out_dir, mat_name, ct_name, out_file, model_name, num_trees, tree_depth, row_subsampling


# returns a string of all the options for the script if the script was called with -h or --help
def helpOption():
    s="-o --out_dir:\tthe directory in which to store outputs from the script. The default is './output'"
    s= "\n-m --mat_name:\tthe name of the pileup matrix. The default is 'pileup_matrix.npy'"
    s+="\n-c --ct_name:\tthe name of the ordered list of Ct values. The default is 'pileup_cts.pkl'"
    s+="\n-f --out_file:\tthe name of the file to which to write the output of the script. The default is 'pileup_model_output'"
    s+="\n-n --model_name:\tthe name that the model trained in the first fold will be stored as. The default is 'pileup_model.pkl'"
    s+="\n-nt --num_trees:\tthe 'n_estimators' (number of trees) parameter in the Random Forest regressor. The default is 400"
    s+="\n-td --tree_depth:\tthe 'max_depth' (tree depth) parameter in the Random Forest regressor. The default is None"
    s+="\n-rs --row_subsampling:\tthe 'max_samples' parameter in the Random Forest regressor. the default is 0.25"

    return s



# splits the matrix into train and test sets
# splits using indices based on the fold so that test sets across folds are non-overlapping
# parameters:
#   mat: the matrix to split into train and test sets
#   ct_lst: the ordered list of Ct values corresponding to the order of rows in the matrix
#   inds: the randomly shuffled list of all indices in the matrix
#   num_folds: the total number of num_folds
#   i: the index of the current fold
# returns:
#   train_set and test_set: the train and test sections of the matrix
#   train_cts and test_cts: the train and test sections of the Ct value list corresponding to the rows of the train and test sets

def splitMat(mat, ct_lst, inds, num_folds, i):
    r, c = mat.shape

    # getting the test and train indices for this fold
    ts = int(r/num_folds)
    if (i == 4):
        test_inds = inds[(i*ts):]
    else:
        test_inds = inds[(i*ts):((i + 1)*ts)]
    if (i == 0):
        train_inds = inds[(ts):]
    else:
        train_inds = inds[0:(i*ts)] + inds[((i + 1)*ts):]

    # sorting the indices so that they correspond to the same order in the ct and mcov lists
    train_inds.sort()
    test_inds.sort()

    # selecting the correct rows of the matrix for the train and test sets based on the indices
    train_set = mat[train_inds, :]
    test_set = mat[test_inds, :]
    # selecting the correct items of the Ct value list for the train and test labels based on the indices
    train_cts = [ct_lst[i] for i in train_inds]
    test_cts = [ct_lst[i] for i in test_inds]

    return train_set, train_cts, test_set, test_cts



# calculates the average and 95% confidence interval for a lists
# parameters:
#   lst: the list to calculate the average of
# returns:
#   ci_s: a string of the average and confidence interval of a list
def getCI(lst):
    z= 1.96 #For 95% confidnce interval
    mean = sum(lst)/len(lst)
    stdv = statistics.pstdev(lst)
    sqrtlen = math.sqrt(len(lst))
    confidence_interval = z*(stdv/sqrtlen)
    # rounding:
    mean = ("%.3f" % (mean))
    confidence_interval = ("%.3f" % (confidence_interval))
    ci_s = str(mean) + " ± " + str(confidence_interval)
    return ci_s


# main functions
# trains a model on a pileup matrix evaluates the model via 5 fold cross validation
def main():
    args = sys.argv
    start_dir = os.getcwd() # current directory

    # set parameters:
    out_dir, mat_name, ct_name, out_file, model_name, num_trees, tree_depth, row_subsampling = parseParams(args, start_dir)
    print("--trainModel.py-- set parameters")

    # initializing the model
    model =  RandomForestRegressor(n_estimators=num_trees, max_depth=tree_depth, random_state=42, max_samples=row_subsampling)

    # opening matrix:
    mat_open = np.load(mat_name, allow_pickle=True)
    # opening the Ct value list:
    fi = open(ct_name, "rb")
    ct_lst = pickle.load(fi)

    # initializing lists to store the results
    r2s = []
    rmses = []

    # Generating a randomly shuffled list of matrix indices for the cross validation
    r, c = mat_open.shape
    inds = list(range(r))
    random.Random(42).shuffle(inds)

    # starting the cross validation
    num_folds = 5
    for i in range(num_folds):
        print("\tStarted fold ", (i + 1))

        # splitting the matrix and metadata lists into train and test sets
        train_set, train_lab, test_set, test_lab = splitMat(mat_open, ct_lst, inds, num_folds, i)

        # training model:
        model.fit(train_set, train_lab)

        # store the model from the first fold:
        if (i == 0):
            with open(model_name,'wb') as f:
                pickle.dump(model,f)

        predictions = model.predict(test_set) # getting predictions
        # evaluating model accuracy:
        rmse = math.sqrt(mean_squared_error(test_lab, predictions))
        rmses.append(rmse)
        r2 = r2_score(test_lab, predictions)
        r2s.append(r2)
        print("\tResults from this fold: R2: ", r2, "  RMSE: ", rmse)

    # getting averages with confidence intervals from  folds:
    r2_ci = getCI(r2s)
    rmse_ci = getCI(rmses)

    # writing the results to the output file:
    s = "Model Accuracy:\n\nAccuracy per Fold:\n\tR2s:  ["
    for i in range(len(r2s)):
        if (i != 4):
            s+=str(r2s[i]) + ", "
        else:
            s+=str(r2s[i]) + "]"
    s+="\n\tRMSEs:  ["
    for i in range(len(rmses)):
        if (i != 4):
            s+=str(rmses[i]) + ", "
        else:
            s+=str(rmses[i]) + "]"
    s+="\n\nAverages:\n\tR2: " + r2_ci + "\n\tRMSE: " + rmse_ci
    f = open(out_file, "a")
    f.write(s)
    f.close()

    print("\n\n--trainModel.py-- finished script. Stored all output as: ", out_file, "\nResults:\n\tR2: ", r2_ci, "\n\tRMSE: ", rmse_ci)

# if this is the script called by python (vs being called by another)
# script, run main().
if __name__ == '__main__':
        main()
