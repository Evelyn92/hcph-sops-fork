# QA criteria for functional connectivity

!!! warning "Contradictory QA counter-measures"
    In the following two subsections, the suggested counter-measures when QA criteria are not met propose changing the cut-off frequency of the low-pass filter in opposed directions, and therefore, *solutions compete*.
    Although challenging, finding a trade-off cut-off that meets all QA criteria across all three group visualizations is necessary.

## FC distributions

- [ ] Check that the FC distributions appear similar across sessions and are Gaussian centered approximately around zero with a small positive mean<sup>[1]</sup>.
    Two deviations from this scenario are possible:

    1. The FC distributions of most sessions appear shifted towards positive values, skewed, flat, or bimodal. 
        It indicates the denoising was either too aggressive for the number of functional frames available or the BOLD signal is still contaminated with residual noise.
        As such, the denoising needs to be revised as follows:

        - [ ] Decrease the cut-off frequency of the low-pass filtering using the `--low-pass` flag of `funconn.py`
        - [ ] If that modification is insufficient, remove high-pass filtering by removing "high-pass" from the denoising strategy list.
              Do so by precising the flag `--confounds "motion" "scrubs"` to `funconn.py`.
        - [ ] Decrease the cut-off frequency until the FC distributions of most subjects are Gaussian centered approximately around zero with a small positive mean if the above modifications are still insufficient.

        ??? note "Alternatively, increasing the motion censoring threshold would be a possibility to address this issue."
            However, in our study, we pre-registered that we would perform the analysis with three different motion censoring thresholds.
            Therefore, rather than optimizing the value of the motion censoring threshold, we will perform a *mulitverse* analysis and report the results for the three threshold levels we pre-registered.

    2. Only a few sessions' FC distribution are shifted towards positive values, skewed, flat or bimodal: then apply the [exclusion criteria detailed below](#fc-distributions-1)

## QC-FC distributions

Now we will assess that QC-FC distribution<sup>[2]</sup> and the null distribution represented by the red dotted line are approximately equivalent for all IQMs. 

- [ ] Verify that QC-FC% &ge; 95% for all IQM, where the QC-FC% value corresponds to the distance between the observed and the null distributions for each IQM.

    ??? note "Why QC-FC% &ge; 95%, in particular?"
        QC-FC% &ge; 95% for all IQM is considered indicative of negligible modulations in the BOLD signal correlation structure<sup>[2]</sup>.

    However, if QC-FC% &lt; 95% for at least one IQM, then the preprocessing of the data requires revisiting as follows:

    - [ ] Include more motion regressors by switching motion regression strategy using the `--motion "full"` flag when running `funconn.py`.
    - [ ] Increase the cut-off frequency of the low-pass filtering using the `--low-pass` flag of `funconn.py` if the QC-FC distribution still does not meet the 95% cutoff.
    - [ ] Exclude additional sessions following [the exclusion criteria detailed below](#qc-fc-distributions-1) if revising the preprocessing does not suffice to reach the threshold QC-FC% &ge; 95%.
    
## QC-FC versus Euclidean distance

- [ ] Check that, for all IQM, there is no significant correlation between QC-FC correlations and Euclidean distance separating the nodes<sup>[2]</sup>.
    If the correlation is significant for one IQM or more, it indicates that connectivity estimates are biased in a distance-dependent manner, with many long-distance correlations decreased by motion and many short-distance correlations increased by motion<sup>[4]</sup>.
    As such, motion correction needs to be revised as follows:
    - [ ] Include more motion regressors by switching motion regression strategy using the `--motion "full"` flag when running `funconn.py`.
    - [ ] If tweaking the preprocessing does not suffice, revise [the exclusion criteria by excluding additional sessions](qaqc-criteria-FC.md#qc-fc-versus-euclidean-distance-1).

# Exclusion criteria based on functional connectivity

## Censoring

- [ ] Exclude the sessions for which the RSfMRI scan does not meet the QC cutoff of 5 minutes of fMRI remaining after censoring. Indeed, less than 5 minutes of RSfMRI is not enough to reliably estimate functional connectivity <sup>[5],[6]</sup>.

## FC distributions

- [ ] Exclude the sessions for which the FC distribution appears shifted towards positive values, skewed, flat, or bimodal.
    Those sessions's BOLD is still contaminated with residual noise, despite the preprocessing being adequate for the acquisition protocol. 
    A likely scenario is that the subject moved a lot during this particular session.

## QC-FC distributions

- [ ] Exclude sessions associated with extreme IQM outliers if the 95% cutoff is still not met after revising the preprocessing.
- [ ] Iteratively exclude the session with the highest `fd_perc` until that cutoff is met, if the 95% cutoff is still not met.

## QC-FC versus Euclidean distance

- [ ] Iteratively exclude the session with the highest `fd_perc` until that cutoff is met, if the correlation between QC-FC and the euclidean distance is not significant.

[1]: https://doi.org/10.3389/fnins.2023.1092125 "Morfini, F., Whitfield-Gabrieli, S., and Nieto-Castañón, A. “Functional Connectivity MRI Quality Control Procedures in CONN.” Front Neurosci 17 (2023). doi:10.3389/fnins.2023.1092125"
[2]: https://doi.org/10.1016/j.neuroimage.2017.03.020 "Ciric, R. et al. “Benchmarking of Participant-Level Confound Regression Strategies for the Control of Motion Artifact in Studies of Functional Connectivity. (2017)” NeuroImage, doi:10.1016/j.neuroimage.2017.03.020"
[3]: https://doi.org/10.1016/j.neuroimage.2017.03.056 "Bright, M. & Murphy, K., Cleaning up the fMRI time series: Mitigating noise with advanced acquisition and correction strategies. (2017) NeuroImage. doi:10.1016/j.neuroimage.2017.03.056"
[4]: https://doi.org/10.1016/j.neuroimage.2011.10.018 "Power, Jonathan D., Kelly A. Barnes, Abraham Z. Snyder, Bradley L. Schlaggar, and Steven E. Petersen. “Spurious but Systematic Correlations in Functional Connectivity MRI Networks Arise from Subject Motion.” NeuroImage 59, no. 3 (February 2012): 2142–54, doi:10.1016/j.neuroimage.2011.10.01"
[5]: https://doi.org/10.1152/jn.00783.2009 "Van Dijk, K. R., Hedden, T., Venkataraman, A., Evans, K. C., Lazar, S. W., Buckner, R. L., et al. (2010). Intrinsic functional connectivity as a tool for human connectomics: theory, properties, and optimization. J. Neurophysiol. 103, 297–321. doi: 10.1152/jn.00783.2009"
[6]: https://doi.org/10.3389/fnimg.2023.1072927 "Birn, Rasmus M. “Quality Control Procedures and Metrics for Resting-State Functional MRI.” Frontiers in Neuroimaging 2 (2023), doi:10.3389/fnimg.2023.1072927"
 

