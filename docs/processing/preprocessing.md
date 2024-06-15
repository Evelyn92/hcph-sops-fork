## Executing *fMRIPrep*

Because *fMRIPrep* creates a single anatomical reference for all sessions, we generate such reference first by setting the `--anat-only` flag.
If that *fMRIPrep* execution finishes successfully, the anatomical processing outcomes will be stored in the output folder.
We will then run one *fMRIPrep* process for each dataset's session, which is the recommended way for datasets with a large number of sessions (e.g., more than six sessions).
We avert that session-wise *fMRIPrep*'s processes run into race conditions by pre-computing the anatomical reference.

- [ ] Submit the anatomical workflow:
    ``` bash title="Launch each session through fMRIPrep in parallel"
    cd code/fmriprep
    bash ss-fmriprep-anatonly.sh
    ```

    ??? abstract "The sbatch file to run *fMRIPrep* with `--anat-only`"

        ``` bash
{% filter indent(width=8) %}
{% include 'code/fmriprep/ss-fmriprep-anatonly.sh' %}
{% endfilter %}
        ```

- [ ] Once the anatomical workflow ran successfully, submit a *job array* with one scanning session each with the `--bids-filter-file` argument selecting the corresponding session, and point the `--fs-subjects-dir` argument to the folder where *FreeSurfer* results were stored.
    ``` bash title="Launch each session through fMRIPrep in parallel"
    cd code/fmriprep
    bash ss-fmriprep.sh
    ```

    ??? abstract "The sbatch file to run *fMRIPrep* session-wise"

        ``` bash
{% filter indent(width=8) %}
{% include 'code/fmriprep/ss-fmriprep.sh' %}
{% endfilter %}
        ```

### How to proceed if some *fMRIPrep* derivatives are missing

If some derivatives are missing, it is a sign that *fMRIPrep* encountered an error.

- [ ] Check the "Errors" section of the visual report.
- [ ] Check the `log/` folder corresponding to the *fMRIPrep* run, carefully ensuring no errors were missed out on the reports.
- [ ] Search for associated keywords in the [issues on *fMRIPrep*'s GitHub repository](https://github.com/nipreps/fmriprep/issues) if the solution remains unclear after the first assessment; it is likely someone else experienced the same problem before you and reported it.
    The solution might be documented in the issue.
    Don't forget to check closed issues!
- [ ] Search for the issue on [NeuroStars](https://neurostars.org/), if the solution remains unclear.
- [ ] If the solution remains elusive, open an issue in *fMRIPrep*'s GitHub repository to report the problem.
    Your description of the problem needs to be as complete and detailed as possible to help the maintainers identify the problem efficiently.
- [ ] Re-run *fMRIPrep* on that particular subject and session after implementing a solution.

!!! danger "If the error remains despite all efforts, the session MAY be excluded"

## Visualizing *fMRIPrep*'s individual reports

### Anatomical preprocessing assessment

- [ ] Open the *fMRIPrep* anatomical report on a Web Browser.
- [ ] Assess the "Summary" section and apply the [QA/QC criteria](qaqc-criteria-preprocessed.md#summary).
- [ ] Assess the "Anatomical conformation" section and apply the [QA/QC criteria](qaqc-criteria-preprocessed.md#anatomical-conformation).
- [ ] Assess the mosaic showing the calculated brain mask and brain tissue segmentation, and apply the [QA/QC criteria](qaqc-criteria-preprocessed.md#brain-mask-and-brain-tissue-segmentation-of-the-t1w).
- [ ] Visualize the spatial normalization flickering mosaic, and apply the [QA/QC criteria](qaqc-criteria-preprocessed.md#spatial-normalization-of-the-anatomical-t1w-reference).
    Flickering between the subject and the template space is active while your mouse pointer hovers the mosaic area.
- [ ] Assess the surface reconstruction mosaic, and apply the [exclusion criteria](qaqc-criteria-preprocessed.md#surface-reconstruction).
- [ ] Visualize the first section entitled *Summary* and apply the [QA/QC criteria](qaqc-criteria-preprocessed.md#summary).

### Assessment of fMRI Preprocessing

- [ ] Open each *fMRIPrep* functional report on a Web Browser.
- [ ] Go through the section of each fMRI run and proceed as follows:

    ??? important "IMPORTANT — QCT and BHT are assessed first as proxies for the RSfMRI run's quality."

        We employ the QCT (mainly) and the BHT as proxies for the quality of the RSfMRI run.
        Screening the reports in the prescribed order (QCT — BHT — RSfMRI) helps identify issues in the QCT and BHT that may anticipate problems in the RSfMRI.

    - [ ] Assess the textual summary and apply the corresponding [QA/QC criteria](qaqc-criteria-preprocessed.md#textual-summary).
    - [ ] Visualize the T<sub>2</sub><sup>☆</sup> map mosaic, and apply the [QA/QC criteria](qaqc-criteria-preprocessed.md#t2-map).
    - [ ] Check the T<sub>2</sub><sup>☆</sup> gray-matter intensity histogram, and apply the [QA/QC criteria](qaqc-criteria-preprocessed.md#t2-gray-matter-values).
    - [ ] Visualize the co-registration flickering mosaic, apply the [QA/QC criteria](qaqc-criteria-preprocessed.md#alignment-of-functional-and-anatomical-mri-data).
        Flickering between T1w and BOLD images is active while hovering your mouse on the mosaic area.
    - [ ] Visualize the next mosaic displaying regions of interest (ROIs) used to estimate the nuisance regressors, and apply the [QA/QC criteria](qaqc-criteria-preprocessed.md#brain-mask-and-anatomicaltemporal-compcor-rois).
    - [ ] Visualize the carpet plot and nuisance signals panel,
        - [ ] Apply the [exclusion criteria](qaqc-criteria-preprocessed.md#bold-summary-1)
        - [ ] If you are visualizing the carpet plot corresponding to a RSfMRI run, apply [additional QA criteria](qaqc-criteria-preprocessed.md#qa-criteria-specifically-for-rsfmri).
    - [ ] Visualize the confound correlation heatmap and use it to [choose the regressors](qaqc-criteria-preprocessed.md#correlations-between-nuisance-regressors)
        you will include in the nuisance regression model.
    - [ ] Proceed as [indicated above](preprocessing.md#how-to-proceed-if-some-fmriprep-derivatives-are-missing) if errors are reported within the "Errors" section.
    - [ ] Continue with the next fMRI run section
