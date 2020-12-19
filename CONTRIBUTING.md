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
