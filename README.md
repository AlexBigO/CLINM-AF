# <font color="darkmagenta">**CLINM Analysis Framework (CLINM-AF)**</font>

A set of python modules and scripts to:
- analyse experimental data from CLINM measurements
- produce simulated data (only GATE10 for the moment)


# <font color="blue">**Installation**</font>

## Download this Github repository

You can use `git clone` command as follows:

```
git clone --branch main <github repo>
```

## Create a virtual environment

One can use a `conda` environment:
- create a new environement:
```
conda env create -f environment.yml
```
- update an existing environment (named `clinmaf_env`):
```
conda env update --name clinamf_env --file environment.yml --prune
```

## Create an alias for this repository

In your `~/.bashrc` or `~/.bash_profile` add

```
export CLINMAF="<put the path to your local copy of this repo>"
```

So you can directly run the command lines below and be sure that they are ran from the right directory.

# <font color="blue">**Choices**</font>

We decide to work with the following environment:
- Python scripts (python + PyROOT)
- the scripts shall remain generic and work with YAML configuration files as input
- we develop utils that will be put in the dedicated folder to get lighter "main scripts"


# <font color="blue">**Architecture**</font>

*IDEA*: reformat all the input data so that each config (each data taking) gets associated to a repository

- `Utils`: a directory with some utilities used in several scripts across the framework
- `DataImport`: a directory with the necessary tools to retrieve data from remote server
- `Fitter`: (not implemented yet) a directory with the tools used to fit energy distributions


# <font color="blue">**Import data from remote server**</font>

We want to retrieve data from a server (e.g. `sbgui11`). These data can either be:
- data that already that underwent STIVI reconstruction (with flatTree option enabled!)
- data from the Wave Catcher (so `.bin` files) that would then require some STIVI treatment

To import data, do:
```
cd $CLINMAF/DataImport/
python3 import_data_from_server.py config_import_data.yml
```

*Notes*:
- One can decide to print the copy and rename command lines, or run them directly
- The file(s) or directory than should be copied from remote to local disc need to be specified in the config file
- One can copy:
    - a single file
    - a list of files
    - a single directory
    - a list of directories

    and rename them if desired

- It is also possible to create a SSH Control Master and add it directly to the `~/.ssh/` config file


*Caveat*: if one does not use SSH Control Master, this script only works when already connected to IPHC server.


# <font color="blue">**STIVI interface**</font>

## <font color="darkgreen">**Decode Wave Catcher data**</font>

To run the `DecodeWC` action of STIVI, run:
```
cd $CLINMAF/STIVI_Interface/
python3 decode_wc.py config_decode_wc.yml
```

*Notes*:
- one needs an installation of STIVI (within SHOE) for this script to work
- one can run the `DecodeWC` action for a single file or a list of files and specify the desired options inside the YAML file:
    - one can use the `output/name = auto` option to automatically generate the output file name (in the SHOE Reconstruction directory) according to the input file name
    - or, one can select the desired output file(s) name(s) with the possibility to automatically merge the output files into a single `.root` file and remove the temporary root files.

## <font color="darkgreen">**Handle data from STIVI output**</font>

For each `.root` file we want to analyse:
- we compute kinetic energies before Plastic 1 and before Plastic 2, and store them in new branches;
- we create new `.root` files containing only the original `TTree` and some QA plots (the 2D plots).

To do so, we run:

```
cd $CLINMAF/STIVI_Interface/
python3 convert_stivi_output.py config_convert_stivi_output.yml
```

where:
- `convert_stivi_output.py` is a generic python script that should not be modified;
- `config_convert_stivi_output.ymll` is a configuration file that must me modified to adapt the input and output to the use-case.

*Note*: there are two ways of saving the output files:
- enable the `output/sub_dir/activate` option: this will automatically produce a directory for each input file with a name associated to the Run details contained in the input `.root` file. The location of this sub directory is given by `output/dir`.
- do not enable the `output/sub_dir/activate` option: one needs to fill the `output/file` option with the given output file names that will be created in `output/dir`.

*Note*: it can be easier to work with a directory per input file (i.e. per Run) because of the many files that might be produced during the next steps of the analysis.



# <font color="blue">**Calibration of the detectors [WORK IN PROGRESS]**</font>

Three scintillation detectors are used in this set:
- a "thin" plastic (2 mm)
- a "thicker" plastic (4mm)
- an organic CeBr3 detector used as a calorimeter

We measure (notably) the amplitude of the signal generated by these detectors during an event. Yet we need to link this amplitude (or the charge, defined as the amplitude intergrated over the measurement time window) to the energy deposited by the detected particle. Hence, the need of a calibration that shall provide a dictionary allowing for the translation of measured amplitude into deposited energy.


One needs to perform this calibration in two steps:
- real data analysis to fit amplitude/charge distributions, retrieve mean and standard deviation of the gaussian
- simulation via GATE to fit deposited energy distribution, retrieve mean and standard deviation of the gaussian


## <font color="darkgreen">**The simulation**</font>

```
cd $CLINMAF/Calibration/Simulation/
python3 simulation.py config_simu.py
```

*Notes*:
- we use Gate to perform this simulation
- one can modify some aspects of the configuration, namely the source energy (in MeV/u) and number of particles produced, the name of the measurement campaign along with the Run number, and of course the output directory.
- the output file names are generated automatically according to the elements of the configuration.

## <font color="darkgreen">**The fit**</font>

```
cd $CLINMAF/Calibration/
```

These two steps require a common tool: fit data with a gaussian function. So, we decide to work with a common script called `fit.py` that shall be used as follows:

```python3 fit.py config_fit.yml```

and that can retrieve an amplitude, a charge or a deposited energy distribution from a `TTree`, convert it into a histogram, fit it and save fit results along with original distribution and QA plot of the fit in an output `.root` file.

### <font color="black">**Get amplitude/charge from real data**</font>

In `config_fit.yml`, one needs to set an input file that is the output of `decode_wc.py` script.


### <font color="black">**Get deposited energy from simulation**</font>



In `config_fit.yml`, one needs to set an input file that is an output of a GATE simulation (matching the configuration of a real Run).

### <font color="black">**Make pretty fit plots**</font>

One can run

```python3 plot_fit.py config_plot_fit.yml ```

to produce a 'prettier' plot of the fit result.

# <font color="blue">**Fitting tool [WORK IN PROGRESS]**</font>

*Note*: We decide to use a ROOT-based approach as ROOT is more well known by the team members (than some *flarefly* package for instance). Besides, this is a versatile option as one could work with ROOT or pyROOT, making it "internship-compatible".

*Note*: I would like to do some unbinned fits, hence RooFit :)

*Note*: the fitter should run on a whole tree, because it would need the information of the whole phase space to improve fitting parameters...

*Idea*: the base structure of flarefly could be re-used.

This tool would be used to perform fit in 2D plan (Delta E - E) and extract nsigma values for each point in this plan (i.e. do PID).

It would be nice to go deep in the fit theory to extract some p-value info, nll info and so on...

## <font color="darkgreen">**Tests**</font>

I decided to perform tests on data from Run 06 located in `/Users/abigot/CLINM/Data/CNAO/spt2025/rootfiles/Run_06_Data_9_13_2025_Binary_config2_carbon120MeVu_FlatTree` folder.

The goal is to write a script that will allow to scan the data in order to check the distributions per energy bin.

## <font color="darkgreen">**Components**</font>

- data handler
- fitter
- store results
- quality assurance

## <font color="darkgreen">**Data handler**</font>

Handle input (.root) files with TTrees and perform the discretisation of space along x axis.

It will store these new distributions into a dedicated `.root`file.

To run this process, do:
```
python3 projector.py config_projector.yml
```

*Question*: how to choose the energy binning ? We decide to do it by eye at first but we are developing a more clever and automatised way to do it.

### Energy pre-binning


So, we first try a dummy scan of the bins and then adapt it by adding a constraint on the minimal number of points that should be inside a bin. **NEED TO FIND THIS NUMBER: a percentage of the total amount of data maybe ?**

### Extrema of the distributions

The point is that for the fits, we'll need to have some insight on the initial values of the parameters (e.g. mean, standard deviation, fitting range) and we also need to be sure that there is enough data inside am energy bin to be fitted. So, once the pre-binning is done, we perform a scan of the distribution in every bin in order to retrieve estimations of local minima and maxima:
- the maxima would be associated to a peak hence will feed the initial value of the fit functions means;
- the minima would give information on the fitting range (between two minima for a given peak).

We run this scan and store the informations on the same file as the `TTree`s with the energy distributions.


## <font color="darkgreen">**The fitter itself**</font>

### Initialisation

We use `RooFit` to fit data in each energy bin. As mentioned above, we shall use the information retrieved on extrema to give a starting point to the fit parameters and also constrain the fitting ranges (one peak for each value of $Z$).

### The fit

We perform the fit and store all relevant information (related to the fit result) into a new file.

### ?

It must be able to perform fits in energy bins for a whole 2D plot, and then do an iterative work to improve the global fit with Bethe-Bloch.