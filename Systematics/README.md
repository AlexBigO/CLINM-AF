# Systematics

Different sources of systematics:
- calibration
- PID (make variations of `TCutG` objects)
- 

## Calibration systematics

One needs to compute the distribution of the difference between $E_{\rm dep}$ associated to amplitude measurements and Birks fit curve. Once this distribution is obtained, one can define a $\sigma^{\rm Birks}$ parameter and run several calibration procedures using $E_{\rm dep}^{\rm Birks} \pm \alpha \sigma^{\rm Birks}$ where $\alpha $ needs to be chosen (** is 3 enough ? **).


*OQ: the definition interval of $\alpha$ will need to be fine-tuned.*

*OQ: couldn't we use a $\chi^2$-like distribution along the Edep axis?*

Once this is done, one needs to define a "calibration set" for every variation of fit parameters:
- for each fit parameter, apply increments (or decrements) using its uncertainty (given by the calibration fit)
- run through all the combinatorics and keep only the ones respecting the condition** that the Birks curve must lie within the $E_{\rm dep}^{\rm Birks} \pm \alpha \sigma^{\rm Birks}$ band !

*Note: as Birks function is strictly increasing on our energy ranges, this means that the tested Birks curve must be below $E_{\rm dep}^{\rm Birks} + \alpha \sigma^{\rm Birks}$ and above $E_{\rm dep}^{\rm Birks} - \alpha \sigma^{\rm Birks}$ along the whole range of interest.*

The easiest way to do this is to run STIVI decoding without any calibration (\ie retrieve amplitudes) and apply the calibration locally for each "calibration set".

### Brief description of the scripts used for the workflow

- `get_info_4_pars_birks_sets_per_detector.py`: to get all pieces of information needed to generate the sets of Birks parameters (sigma of the calibration, ...), per detector. The sigma of the calibration that is a global indicator of the calibration uncertainty
- `generate_pars_birks_sets_per_detector.py`: to generate triplets of Birks parameters
- `generateParsBirks4Systematics.cxx`: to generate sets of Birks parameters for all detectors (nonuplets) 
- `calibrationSystematics.cxx`: run the nominal workflow with calibration variations (from previous script)


## PID systematics

For nominal PID, we use a cut for each $Z$ value. For a given nominal cut, we vary the area of the graphic cut. For instance, one could define narrower cuts (99\% down to 95\% of the nominal cut area) and wider cuts (101\% upt to 105\% of the nominal cut area).

*OQ: how to automatically define new cut areas?*