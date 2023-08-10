#!/bin/bash
# runs the Ct value prediction script pipeline

# sets the arguments to the appropriate variables
while getopts p:l:d:o:m:c:f:n:u:e:r:i:t: flag
do
    case "${flag}" in
        p) pileups_dir=${OPTARG};;
        l) lists_dir=${OPTARG};;
        d) metadata_path=${OPTARG};;
        o) out_dir=${OPTARG};;
        m) mat_name=${OPTARG};;
        c) ct_name=${OPTARG};;
        f) out_file=${OPTARG};;
        n) model_name=${OPTARG};;
        u) num_trees=${OPTARG};;
        e) tree_depth=${OPTARG};;
        r) row_sub=${OPTARG};;
        i) pileup_path=${OPTARG};;
        t) tmp_dir=${OPTARG};;
    esac
done

# checks if any required arguments are null
if [ -z "$metadata_path" ] || [ -z "$pileup_path" ]
then
    space="                                  "
    echo usage: "$0  [-p pileups_dir] [-l lists_dir] [-d metadata_path - required]"
    echo "$space[-o out_dir] [-m mat_name] [-c ct_name]"
    echo "$space[-f out_file] [-n model_name] [-u num_trees]"
    echo "$space[-e tree_depth] [-r row_sub] [-i pileup_path - required]"
    echo "$space[-t tmp_dir]"
    echo " "
    echo "one or more required arguments missing: "
    echo "    -d: metadata_path"
    echo "    -i: pileup_path"
    exit 1
fi


# getting the directory where the bash script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# checking all the arguments and creating the commands for each script:
base="python3 "
base+="$SCRIPT_DIR"
base+="/"
c1="$base"
c1+="parsePileups.py"
c2="$base"
c2+="createMat.py"
c3="$base"
c3+="trainModel.py"
c4="$base"
c4+="predictCt.py"

c4+=" -i $pileup_path"
if ! [ -z "$tmp_dir" ]; then c4+=" -t $tmp_dir"; fi
if ! [ -z "$pileups_dir" ]; then c1+=" -p $pileups_dir"; fi
if ! [ -z "$lists_dir" ]; then c1+=" -l $lists_dir"; c2+=" -l $lists_dir"; fi
c1+=" -d $metadata_path"
if ! [ -z "$out_dir" ]; then c2+=" -o $out_dir"; c3+=" -o $out_dir"; c4+=" -o $out_dir"; fi
if ! [ -z "$mat_name" ]; then c2+=" -m $mat_name"; c3+=" -m $mat_name"; c4+=" -m $mat_name"; fi
if ! [ -z "$ct_name" ]; then c2+=" -c $ct_name"; c3+=" -c $ct_name"; fi
if ! [ -z "$out_file" ]; then c3+=" -f $out_file"; fi
if ! [ -z "$model_name" ]; then c3+=" -n $model_name"; c4+=" -n $model_name"; fi
if ! [ -z "$num_trees" ]; then c3+=" -nt $num_trees"; fi
if ! [ -z "$tree_depth" ]; then c3+=" -td $tree_depth"; fi
if ! [ -z "$row_sub" ]; then c3+=" -rs $row_sub"; fi




# running the scripts:
echo "$c1"
$c1
echo "$c2"
$c2
echo "$c3"
$c3
echo "$c4"
$c4


s="stored all output as: "
if [ -z "$out_file" ]
then
    s+="pileup_model_output"
else
    s+="$out_file"
fi
s+="  in: "

if [ -z "$out_dir" ]
then
    s+="./output/"
else
    s+="$out_dir"
fi
echo "$s"
