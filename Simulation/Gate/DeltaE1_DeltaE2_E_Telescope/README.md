# $\Delta E_1 - \Delta E_2 - E$ telescope

## Apply coincidence

One needs to merge data per Run and per Event. The data are imported and converted from `TTree` to `pandas.DataFrame` type.
One can also select a threshold for each detector.

*Bonus: we look for the Z value of the particle detected in the first detector (Plastic 1). This will be the Z value of the event even if the particle fragments dowstream.*

This work is done by the `reshape_data.py` script that "reshapes" MC data so that they have the same architecture as real data.

```
python3 reshape_sim_data.py ConfigFiles/PostProdSimData/<to_complete>
```

*NB: the reshape_sim_data.py script is work in progress, the new version (with PDGCode selection on Plastic 1) still needs to be tested.*

## Handle nuclear reactions between detectors
As we are interested in the production of secondary particles via fragmentation processes within the target, the $Z$ value of interest is the one of the particle coming out of the target. 

There are basically two scenarios for a secondary particle coming out of the target:

1) the particle does not undergo any nuclear reaction and keeps its identity through the whole measurement process (\ie it is still the same when it deposits energy in the final detector of the telescope)

This first scenario does not cause any issue PID-wise.

2) the particle undergoes nuclear reaction (\eg fragmentation). It can happen between:

    a) target and Plastic 1;

    b) Plastic 1 and Plastic 2;

    c) Plastic 2 and CeBr.

Let's focus on the second scenario.

The case a) is the trickiest. At the simulation level, thanks to MC truth, no issue appears, but experimentally, one does not have any mean to recognize this behaviour as no detector can give information before Plastic 1. So, this case cannot be addressed at the experimental level and goes in the category of "systematic conatimnation".

*Idea: try to assess its relative importance thanks to MC studies.*

So, putting aside case a), we are left with cases b) and c) that are quite similar as it is a "daughter" particle that deposits energy in the next detector. So the $Z$ value of the particle detected in Plastic 2 and/or CeBr is not the $Z$ value of the mother (\ie the value of interest).

How to handle this?

- At the MC level, once again, MC truth comes to the rescue thanks to `PDGCode` and `ParentID` variables registered for each detector.

- At the experimental level. Going from the principle that one has absolutely no way of knowing if it is a secondary particle of interest (`ParentID == 1`) or a daughter (`ParentID > 1`), and having no possible input on case a), the only possibility left is to suppose that the $Z$ value of interest is the one of the particle detected by Plastic 1.
But, the PID method used here requires to also have information on Plastic 2 (and/or CeBr), so the case a) could impact the point position in the $(E_2, E_1)$ plane. 

*We consider that fragmentation in Plastic 1 that is 2mm wide is less probable than in Plastic 2. So we suppose that PID on both Plastic detectors gives the $Z$ value of interest in a great majority of events.*


