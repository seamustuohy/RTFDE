# RTFDE: RTF De-Encapsulator

A python3 library for extracting encapsulated `HTML` & `plain text` content from the `RTF` bodies of .msg files.

De-encapsulation enables previously encapsulated HTML and plain text content to be extracted and rendered as HTML and plain text instead of the encapsulating RTF content. After de-encapsulation, the HTML and plain text should differ only minimally from the original HTML or plain text content.

# Features

- De-encapsulate HTML from RTF encapsulated HTML.
- De-encapsulate plain text from RTF encapsulated text.

# Known Issues

- This library *fully* unquotes text it de-encapsulates because it does not know which text was quoted in the RTF conversion process and which text was quoted in the original html/text. So, for instance escaped [Quoted-Printable](https://en.wikipedia.org/wiki/Quoted-printable) text will be returned un-escaped.
- This library currently can't [combine attachments](https://docs.microsoft.com/en-us/openspecs/exchange_server_protocols/ms-oxrtfex/b518f0bc-468c-4218-87a7-8f8859bf5773) from a .MSG Message object with the de-encapsulated HTML. This is mostly because I could not get a good set of examples of encapsulated HTML which had attachment objects that needed to be integrated back into the body of the HTML.

# Anti-Features (I don't intend to have this library do this.)

- Extract plain text from RTF encapsulated HTML. If you want this, then you will have to parse the HTML using another library.

# Installation

**To install from the pip package.**

```
pip3 install RTFDE

```

# Usage

## De-encapsulating HTML or TEXT

```python
from RTFDE.deencapsulate import DeEncapsulator

with open('rtf_file', 'rb') as fp:
    raw_rtf  = fp.read()
    rtf_obj = DeEncapsulator(raw_rtf)
    rtf_obj.deencapsulate()
    if rtf_obj.content_type == 'html':
        print(rtf_obj.html)
    else:
        print(rtf_obj.text)
```



# Enabling Logging

Any logging (including how verbose the logging is) can be handled by configuring logging. You can enable RTFDE's logging at the highest level by getting and setting the "RTFDE" logger.

```
log = logging.getLogger("RTFDE")
log.setLevel(logging.INFO)
```






To see how to enable more in-depth logging for debugging check out the CONTRIBUTING.md file.

```
# Now, get the log that you want
# The main logger is simply called RTFDE. That will get you all the *normal* logs.
requests_log = logging.getLogger("RTFDE")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```


# Contribute

Please check the [contributing guidelines](./CONTRIBUTING.md)

# License

Please see the [license file](./LICENSE) for license information on RTFDE. If you have further questions related to licensing PLEASE create an issue about it on github.
