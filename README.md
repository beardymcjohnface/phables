<p align="center">
  <img src="https://raw.githubusercontent.com/Vini2/phables/master/phables_logo.png" width="600" title="phables logo" alt="phables logo">
</p>

Phables: Phage bubbles resolve bacteriophage genomes in viral metagenomic samples
===============

[![CI](https://github.com/Vini2/phables/actions/workflows/testing.yml/badge.svg)](https://github.com/Vini2/phables/actions/workflows/testing.yml)
![GitHub](https://img.shields.io/github/license/Vini2/phables)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Anaconda-Server Badge](https://anaconda.org/vijinim/phables/badges/version.svg)](https://anaconda.org/vijinim/phables)
[![PyPI version](https://badge.fury.io/py/phables.svg)](https://badge.fury.io/py/phables)
[![Documentation Status](https://readthedocs.org/projects/phables/badge/?version=latest)](https://phables.readthedocs.io/en/latest/?badge=latest)

Phables is a tool developed using [Snaketool](https://github.com/beardymcjohnface/Snaketool) to resolve bacteriophage genomes using phage bubbles in viral metagenomic data. It models cyclic phage-like components in the viral metagenomic assembly as flow networks, models as a minimum flow decomposition problem and resolves genomic paths corresponding to flow paths determined. Phables uses the [Minimum Flow Decomposition via  Integer Linear Programming](https://github.com/algbio/MFD-ILP) implementation to obtain the flow paths.

For detailed instructions on installation and usage, please refer to the [**documentation hosted at Read the Docs**](https://phables.readthedocs.io/en/latest/).

**NEW:** Phables is now available on Anaconda.org at [https://anaconda.org/vijinim/phables](https://anaconda.org/vijinim/phables) and on PyPI at [https://pypi.org/project/phables/](https://pypi.org/project/phables/). Feel free to pick your package manager.

<p align="center">
  <img src="https://raw.githubusercontent.com/Vini2/phables/master/Phables_workflow.png" title="phables workflow" alt="phables workflow">
</p>

## Setting up Phables

### Option 1: Installing Phables from Anaconda.org

You can install Phables from Anaconda.org at [https://anaconda.org/vijinim/phables](https://anaconda.org/vijinim/phables). Make sure you have [`conda`](https://docs.conda.io/en/latest/) installed.

```bash
# add channels
conda config --add channels defaults
conda config --add channels bioconda
conda config --add channels conda-forge
conda config --add channels gurobi

# create conda environment and install phables
conda create -n phables -c vijinim phables

# activate environment
conda activate phables
```

Now you can go to [Setting up Gurobi](#setting-up-gurobi) to configure Gurobi.

### Option 2: Installing Phables from PyPi

You can install Phables from PyPI at [https://pypi.org/project/phables/](https://pypi.org/project/phables/). Make sure you have [`pip`](https://pip.pypa.io/en/stable/) installed.

```bash
pip install phables
```

Now you can go to [Setting up Gurobi](#setting-up-gurobi) to configure Gurobi.

### Setting up Gurobi

The MFD implementation uses the linear programming solver [Gurobi](https://www.gurobi.com/). We chose Gurobi over open source solvers as Gurobi is fast and can solve large models (check the performance comparison at [https://www.gurobi.com/resources/open-source-linear-and-mixed-integer-programming-software-and-solvers/](https://www.gurobi.com/resources/open-source-linear-and-mixed-integer-programming-software-and-solvers/)).

The `phables` conda environment and pip setup already include Gurobi. To handle large models without any model size limitations, you have to activate the (academic) license and add the key using the following command.

```bash
grbgetkey <KEY>
```

You can refer to further instructions at [https://www.gurobi.com/academia/academic-program-and-licenses/](https://www.gurobi.com/academia/academic-program-and-licenses/). Please note that this academic lisence is a file-based host-locked license, meaning that you can only run Gurobi on the machine that the license was obtained for. If you want to run on a cluster, you will have to contact your system admin and setup a floating network license. You can find more details at [https://support.gurobi.com/hc/en-us/articles/360013195412-How-do-I-obtain-a-free-academic-license-for-a-cluster-or-a-shared-computer-lab-](https://support.gurobi.com/hc/en-us/articles/360013195412-How-do-I-obtain-a-free-academic-license-for-a-cluster-or-a-shared-computer-lab-).

### Test the setup

After setting up, run the following command to print out the Phables help message.

```bash
phables --help
```

Then run the following command to launch the test run and ensure that Phables is working.
```bash
phables test
```

## Quick Start Guide

### Setup databases

Run the following command to download and setup the required databases.

```bash
phables install
```

### Preprocess data

Next, run the following command to preprocess your data. You have to provide the output from [Hecatomb](https://hecatomb.readthedocs.io/en/latest/) and the path to the directory containing the raw paired-end reads.

```bash
phables preprocess --input hecatomb.out/ --reads reads_dir/ --threads 16
```

### Run Phables

Now you can run Phables as follows.

```bash
phables --input hecatomb.out/
```

Please refer to the [**documentation hosted at Read the Docs**](https://phables.readthedocs.io/en/latest/) for further information on how to run Phables.


## Reporting Issues

Phables is still under testing. If you want to test (or break) Phables give it a try and report any issues and suggestions under [Phables Issues](https://github.com/Vini2/phables/issues).


## Acknowledgement

Phables uses the Gurobi implementation of [MFD-ILP](https://github.com/algbio/MFD-ILP) and code snippets from [STRONG](https://github.com/chrisquince/STRONG), [METAMVGL](https://github.com/ZhangZhenmiao/METAMVGL), [GraphBin](https://github.com/metagentools/GraphBin) and [MetaCoAG](https://github.com/metagentools/MetaCoAG).
