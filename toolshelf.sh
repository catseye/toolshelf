# `source`d by the alias `toolshelf` which `bootstrap-toolshelf.sh` adds to
# your `.bashrc`

F=$TOOLSHELF/toolshelf/tmp-toolshelf-result.sh
python $TOOLSHELF/toolshelf/toolshelf.py $*
if [ -e $F ]; then
    source $F
    rm -f $F
fi
