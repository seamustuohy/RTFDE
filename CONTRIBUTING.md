# Contributing

Hi there! I'm thrilled that you want to contribute to this project. Your help is essential for allowing it to work across the flood of inconsistency found in RTF encapsulation.

Contributions to this project are [released](https://docs.github.com/github/site-policy/github-terms-of-service#6-contributions-under-repository-license) to the public under the [project's open source license](./LICENSE).


### Dependencies

All dependencies can be found in the [`setup.py`](./setup.py) file.

# Getting Started

**To download and install this library do the following.**

1. Clone from Github.
```bash
git clone https://github.com/seamustuohy/RTFDE.git
cd RTFDE
```

2. Setup a virtual environment
```bash
python3 -m venv .venv.dev
source .venv.dev/bin/activate
```

3. Install RTFDE with development dependencies

```bash
pip3 install -e .[dev]
```

4. Change the code and reinstall
```
pip3 install -e .[dev]
```

5. Create and run tests
```
python3 -m unittest discover -v
```

# Documentation

This project uses [Google style docstrings](catch_common_validation_issues) which allows us to auto-generate the pdoc documentation.


# Advanced Logging

Any logging (including how verbose the logging is) can be handled by configuring logging.

You can enable RTFDE's primary logging by getting and setting the "RTFDE" logger. Any logging that is needed for basic triage will be turned on by this logger.

```
log = logging.getLogger("RTFDE")
log.setLevel(logging.DEBUG)
```

**Here is an example run on one of the test cases.**

```
import logging
import RTFDE

log = logging.getLogger("RTFDE")
log.setLevel(logging.DEBUG)


path = 'tests/test_data/plain_text/quoted_printable_01.rtf'
with open(path, 'r') as fp:
    raw = fp.read()
output = RTFDE.DeEncapsulator(rtf)
output = RTFDE.DeEncapsulator(raw)
output.deencapsulate()
```

## Developer Debugging

You should read this section if the normal logging set to DEBUG didn't give you enough information to understand an error or weird behavior of RTFDE. I've added a variety of levels of debug logging to help you dig in and understand these problems.

### RTF Validation Errors

You have, what you believe to be, a valid RTF file which RTFDE is rejecting and telling you is invalid. You can see what each of the validators is parsing by setting the `RTFDE.validation_logger`. If set to DEBUG it will output the data being validated so you can evaluate it yourself to track down the issue.

```
log = logging.getLogger("RTFDE.validation_logger")
log.setLevel(logging.DEBUG)
```

### HTMLRTF Stripping Logging

If you want to log all text and RTF control words that are suppressed by HTMLRTF control words you can use the `RTFDE.HTMLRTF_Stripping_logger` logger. If set to DEBUG it will output the Tokens which have been removed and the line the token starts on, the line it ends on, the starting position of that token in the line, and the end position of that token. The log uses the following format `HTMLRTF Removed: {value}, {line}, {end_line}, {start_pos}, {end_pos}`

Here is how you enable this log.
```
log = logging.getLogger("RTFDE.HTMLRTF_Stripping_logger")
log.setLevel(logging.DEBUG)
```

### HTMLRTF Stripping Logging

If you are having difficulty tracking down some sort of text-transformation/decoding issue then you can use the text_extraction logging to show you FAR more information about what is occuring during text extraction. WARNING: This log is a flood of information!

Here is how you enable this log.
```
log = logging.getLogger("RTFDE.text_extraction")
log.setLevel(logging.DEBUG)
```




### Grammar Debugging

RTFDE



### Lark Debug Logs
If you want to see underlying Lark language parsing toolkit's logging you can activate its logger like this.

```
log = logging.getLogger("lark")
log.setLevel(logging.DEBUG)
```
