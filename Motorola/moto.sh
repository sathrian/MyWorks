#!/bin/sh
PATH="/usr/lib/jvm/java-8-openjdk-amd64/bin:~/bin:$PATH"
export PATH="/usr/lib/jvm/java-8-openjdk-amd64/bin:~/bin:$PATH"
script_dir=$(dirname $(readlink -f $0))
echo $(pwd)
cd $script_dir
echo $(pwd)
/usr/bin/python $script_dir/Moto.py -c $script_dir/moto.yaml;
