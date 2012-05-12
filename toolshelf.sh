# `source`d by the alias `toolshelf` which `bootstrap-toolshelf.sh` adds to
# your `.bashrc`

F=$TOOLSHELF/tmp-toolshelf-result.sh
python $TOOLSHELF/toolshelf/toolshelf.py $* >$F
source $F
rm -f $F
