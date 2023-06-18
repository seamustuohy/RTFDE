# Private Data Test HTML output Folder

Use this folder to include HTML files which correspond to the to RTF files in the private test folder. It is used in the `TestPrivateMsgTestCases` unittest in `test_de_encapsulate.py`.

See the README.md in the `tests/test_data/personal_rtf_test_files` directory for more info on the primary .rtf files.

If you want to run tests that check the contents of the original HTML file against the encapsulated version you can use the RTFDE_PRIVATE_MSG_OUTPUT_FOLDER environment variable. If you do not set this environment variable this test will look for .html files in the `tests/test_data/personal_rtf_test_output_files` folder. If it does not find a file with the same name as the .rtf file that it is testing it will not attempt to compare it to anything. (`file.rtf` needs a corresponding `file.html`).

```
    > export RTFDE_PRIVATE_MSG_OUTPUT_FOLDER="/path/to/folder/with/html/outputs/"
    > python3 -m unittest discover -v --locals
```

It is important to use the --locals variable for unittest since it will expose the filename where an error occurs alongside the unittest failure. Look for the variable named `FAILING_FILENAME`

This folder `tests/test_data/personal_rtf_test_outputfiles` has been included in the .gitignore to allow developers to safely use it for this purpose.


# Example test files to include

```
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/output/rfcompliant/chinese-exotic-test.html'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/output/rfcompliant/complex-test.html'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/output/rfcompliant/hebrew-test.html'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/output/rfcompliant/mixed-charsets-test.html'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/output/rfcompliant/newlines-test.html'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/output/rfcompliant/russian-test.html'
wget 'https://raw.githubusercontent.com/bbottema/rtf-to-html/9e4c42dbd7a8505d862aaf905739c5b6fc5e3be9/src/test/resources/test-messages/output/rfcompliant/simple-test.html'
```
