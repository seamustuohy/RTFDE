# Private Data Test Folder

Use this folder to include files to test against a private folder full of RTF files exported from .msg files. The `TestPrivateMsgTestCases` unittest in `test_de_encapsulate.py` will run against this, or any other, folder full of raw encapsulated .rtf files.

This test will first try to run against whatever path is set in the RTFDE_PRIVATE_MSG_FOLDER environment variable.

If you do not set this environment variable this test will look for .rtf files in the `tests/test_data/personal_rtf_test_files` folder. If it finds none there it will exit without any error.

```
> export RTFDE_PRIVATE_MSG_FOLDER="/path/to/folder/with/messages/"
> python3 -m unittest discover -v
```

If you want to run tests that check the contents of the original HTML file against the encapsulated version you can use the RTFDE_PRIVATE_MSG_OUTPUT_FOLDER environment variable. If you do not set this environment variable this test will look for .html files in the `tests/test_data/personal_rtf_test_output_files` folder. If it does not find a file with the same name as the .rtf file that it is testing it will not attempt to compare it to anything. (`file.rtf` needs a corresponding `file.html`).

```
    > export RTFDE_PRIVATE_MSG_OUTPUT_FOLDER="/path/to/folder/with/html/outputs/"
    > python3 -m unittest discover -v --locals
```

It is important to use the --locals variable for unittest since it will expose the filename where an error occurs alongside the unittest failure. Look for the variable named `FAILING_FILENAME`

This folder `tests/test_data/personal_rtf_test_files` has been included in the .gitignore to allow developers to safely use it for this purpose.


# Populating the private test folder
See code in `scripts/prep_private_rtf_test_folder.sh` for guidance on how to populate a private test folder with RTF files extracted from a folder full of .msg files.

Run this script to extract .rtf msg bodies from .msg files. Can be run in multiple ways.

1) extract the .rtf bodies from a folder of .msg files into another folder.
```
./prep_private_rtf_test_folder.sh \
    -i /tmp/msg_files/ \
    -o /tmp/extracted_rtf/
```

2) exract the .rtf body from a single .msg file into a folder
```
./prep_private_rtf_test_folder.sh \
    -i /tmp/msg_files/email.msg \
    -o /tmp/extracted_rtf/
```

2) exract the .rtf body from a single .msg file to a specific filename
```
./prep_private_rtf_test_folder.sh \
    -i /tmp/msg_files/email.msg \
    -o /tmp/extracted_rtf/extracted_msg.rtf
```


# Example test files to include

```
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/input/chinese-exotic-test.rtf'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/input/complex-test.rtf'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/input/hebrew-test.rtf'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/input/mixed-charsets-test.rtf'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/input/newlines-test.rtf'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/input/russian-test.rtf'
wget 'https://github.com/bbottema/rtf-to-html/raw/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/input/simple-test.rtf'
```
