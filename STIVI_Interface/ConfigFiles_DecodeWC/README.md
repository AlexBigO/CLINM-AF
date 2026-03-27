# Helper BASH script

Use the BASH script as follows:

```
./get_list_of_bin_files.sh DIR RUN_NUMBER
```

where `DIR` is the directory containing all the `.bin` files (from WaveCatcher) and `RUN_NUMBER` is the number of the considered Run.

This script will produce a `.txt` file with the list of all the `.bin` files in `DIR`. Then, one just needs to copy-paste this list in the `.yml` config file of `decode_wc.py`.