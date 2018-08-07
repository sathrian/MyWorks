#!/bin/sh
PATH=~/bin:$PATH
script_dir=$(dirname $(readlink -f $0))
echo $(pwd)
cd $script_dir
echo $(pwd)
/usr/bin/python $script_dir/Moto.py -c $script_dir/moto.yaml;
