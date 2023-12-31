# Pileup Ct-Value-Prediction
This repository contains scripts to train and score a Random Forest regression model to predict the Ct values as a proxy for viral load of input SARS-CoV-2 genome data from pileup files. For more detail on the pileup format [go here](https://en.wikipedia.org/wiki/Pileup_format)
This repo contains the following Python scripts:
* *parsePileups.py* - parsing all pileup files in a directory and storing the parsed results as lists
* *createMat.py* - concatenating the pileup lists created by *parsePileups.py* to create and store a matrix representing all pileup files
* *trainModel.py* - training a model on the pileup matrix created by *createMat.py* and evaluating its accuracy using R2 score and RMSE across 5 fold cross validation
* *predictCt.py* - parsing an inputted pileup file and using the model created by *trainModel.py* to predict its Ct value 

This repo also includes the *'sample'* directory containing the metadata file and model for testing and running the scripts.



## Requirements
### 1. Python Packages
This repo is designed to be run with python3 (version 3.9.12) and Anaconda version 2022.05 which can be downloaded [here](https://repo.anaconda.com/archive/).   
This repo requires the following packages to be installed:
* numpy (version 1.21.5)
* pandas (version 1.4.2)
* sklearn (version 1.0.2)

### 2. Genome Data Directory
This repo requires a directory containing genome data as pileup files. The name of the directory can be passed into the scripts (option -p). The pileup  files should have *.gz* or *.pileup* extension and be named \<genome_id>.gz or \<genome_id>.pileup.

The script *parsePileups.py* also requires a comma-separated (*.csv*) metadata file with information about each genome. This file should contain at least the genome_id (corresponding to the file names) and Ct value for each pileup file. The column titles in the metadata file should be "ID" and "Ct Value" for the genome IDs and Ct values. If the file includes additional columns, they will be ignored by the scripts. The path to this file must be passed into the script (option -d). 

The column titles in the metadata file should be formatted in the same was as the example metadata file provided in */sample/metadata_file.csv*.


## Running the Scripts
The scripts in this repo implement a pipeline and should be run in the following order: 
1. *parsePileups.py*
2. *createMat.py*
3. *trainModel.py*
4. *predictCt.py*

This repo also contains the *ct_value_prediction.sh.sh* bash script to run the entire pipeline.

### *parsePileups.py*
The *parsePileups.py* script is used to parse the pileup read results of every *.gz* or *.pileup* pileup file in the pileup directory and to store the output lists in a specified output directory. 
For efficient execution with a large number of pileup files, we recommend splitting the pileup directory into several sub directories and running the script concurrently across the sub directories.

An example run would be:
~~~
python3 parsePileups.py -p <pileup_directory> -l <pileup_list_directory> -d <metadata_file_path>
~~~

This script takes in the following options:
* -p --pileups_dir: Specify the directory containing the *.gz* or *.pileup* pileup files to parse. The default is './'  
* -l --lists_dir: Specify the directory to which to store the lists created by the script. The default is './pileup_lists/'. If the directory does not already exist, it will be created by the script.
* -d --metadata_path: Specify the path to the comma-separated (*.csv*) metadata file containing the genome_id and Ct value of each pileup file in the pileup directory. There is no default for this option.


### *createMat.py*
The *createMat.py* script is used to create and store the pileup matrix used to train the model. The matrix represents the features consisting of the frequency of: A, C, T, and G bases, and insertion or deletion, for every nucleotide position in the genomes. Every row represents one genome. The script also creates 2 metadata lists to record the order of the genome IDs and Ct values according to the order of the rows in the matrix.

An example run would be:
~~~
python3 createMat.py -l <pileup_list_directory> -o <output_directory>
~~~

The script takes in the following options:
* -l --lists_dir: Specify the directory containing the parsed pileup lists to make the matrix. This should be the same directory used for *parsePileups.py*. The default is './pileup_lists/'
* -o --out_dir:  Specify the directory in which to store the outputs created by this script. The default is './output'. If the output directory does not already exist, it will be created by the script.
* -m --mat_name: Specify the name that the pileup matrix created by the script will be stored as. The default is 'pileup_matrix.npy'. The matrix will be stored as a numpy array in the output directory.
* -c --ct_name: Specify the name that the ordered list of Ct values created by the script will be stored as. The default is 'pileup_cts.pkl'. This list will be stored in the output directory


### *trainModel.py*
The *trainModel.py* script is used to train a model on the pileup matrix created by *createMat.py* and evaluate its accuracy across 5 folds. The accuracy is evaluated using two metrics: the R2 score and RMSE. The average accuracy across 5 folds with 95% confidence intervals is calculated and written to an output file. The script also stores the model trained in the first fold.

An example run would be:
~~~
python3 trainModel.py -o <output_directory>
~~~

The script takes in the following options:
* -o --out_dir:  Specify the directory in which to store the outputs created by this script. This should be the same directory used for *createMat.py*. The default is './output'. 
* -m --mat_name: Specify the name of the pileup matrix. This should be the same name used for *createMat.py*. The default is 'pileup_matrix.npy'.
* -c --ct_name: Specify the name of the ordered list of Ct values. This should be the same name used for *createMat.py*. The default is 'pileup_cts.pkl'.
* -f --out_file: Specify the name of the file to which to write the output of the script. The default is 'pileup_model_output'. This file will be created in the output directory.
* -n --model_name: Specify the name that the model trained in the first fold will be stored as. The default is 'pileup_model.pkl'. The model will be saved in the output directory
* -ts --test_size: Specify the size of the test set to be used in the train_test_split during model training and evaluation. The default is 0.2.
* -nt --num_trees: Specify the ‘n_estimators’ (number of trees) parameter in the Random Forest regression model. The default was established through hyperparameter tuning and is 400.
* -td --tree_depth: Specify the ‘max_depth’ (tree depth) parameter in the Random Forest regression model. The default was established through hyperparameter tuning and is None.
* -rs --row_subsampling: Specify the ‘max_samples’ (row subsampling) parameter in the Random Forest regression model. The default was established through hyperparameter tuning and is 0.25.


An example output file would be as follows:
~~~
Model Accuracy:

Accuracy per Fold:
    R2s: [0.729874745744207, 0.719702747256483, 0.7288074666296775, 0.7296017448665342, 0.7291816997605967]
    RMSEs: [4.361144821234152, 4.470131007299943, 4.329620825861739, 4.3193577395235, 4.366280458601157]

Averages:
    R2: 0.727 ± 0.003 
    RMSE: 4.369 ± 0.047
~~~


### *predictCt.py*

The *predictCt.py* script takes in one *.gz* or *.pileup* pileup file and predicts its Ct value using the model created by *trainModel.py*. The script runs *parsePileups.py* and *createMat.py* to parse the pileup file before making the prediction.

An example run would be:
~~~
python3 predictCt.py -i <pileup_file_path> 
~~~

The script takes in the following options:
* -i --pileup_path: Specify the path to the pileup file to predict the Ct value of. This should be a *.gz* or *.pileup* file. There is no default for this option.
* -t --tmp_dir: Specify the temporary directory to be created by the script in order to parse the pileup file. This directory will be removed later so it must not exist when the script is called. The default is “./tmp”.
* -o --out_dir:  Specify the directory in which the matrix and model are stored. This should be the same directory used for *createMat.py* and *trainModel.py*. The default is './output'. 
* -n --model_name: Specify the path to the pileup model to use to predict the Ct value. This should be the same as used for *trainModel.py*. The default is 'pileup_model.pkl'


### *ct_value_prediction.sh*
The *ct_value_prediction.sh* script runs all 4 scripts in a sequence. This script takes in the union of the arguments of the individual component scripts. Running the script with the -h option will list all optional and required arguments. 

An example run would be:
~~~
bash ct_value_prediction.sh -p <pileup_directory> -d <metadata_file_path>  -i <pileup_file_path>
~~~
