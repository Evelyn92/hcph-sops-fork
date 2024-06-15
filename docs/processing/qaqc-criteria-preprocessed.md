# QA criteria for preprocessed data

## Summary
- [ ] Check that the anatomical processing is based on the number of T1w images you expected and that no excluded T1w was mistakenly included in the processing.
  If that is not the case, use the *fMRIPrep* `--bids-filter-file` flag to exclude unwanted T1w from the processing and re-run *fMRIPrep*.
- [ ] Verify that the standard output space corresponds to the one you want.
  If that is not the case, assign the correct output space to the `--output-spaces` flag of *fMRIPrep* and re-run *fMRIPrep*.

## QA criteria for *fMRIPrep* anatomical preprocessing

### Brain mask and brain tissue segmentation of the T1w

- [ ] Assess the quality of the segmentation:
    - [ ] Check that the blue line correctly outlines the boundary between GM and WM.
    - [ ] Check that the magenta line outlines ventricles.
    - [ ] Check that the contours do not exclude single voxels within piecewise-smooth regions (generally more identifiable in the WM and inside the ventricles).
      Be careful if those single excluded voxels only appear close to tissue boundaries.
      They are likely misclassified because of the partial volume effect, and as such, they do not constitute an exclusion criteria.
    - [ ] Check that the contours do not include other tissues than the tissue of interest (GM; magenta, WM; blue).
    - [ ] **Do not** use the CompCor confounds for nuisance regression if you find any of the issues above.

### Spatial normalization of the anatomical T1w reference

- [ ] In order of importance, the following structures should be correctly aligned: (i) ventricles, (ii) subcortical regions, (iii) corpus callosum, (iv) cerebellum, (v) cortical GM.
    Tweak the spatial normalization and re-run *fMRIPrep* in case of a misalignment of the ventricles, subcortical regions, or the corpus callosum.
    You can, however, be more lenient with GM alignment.
- [ ] Check for severe stretching or distortion of the T1w.

## QA criteria for *fMRIPrep* functional preprocessing

### Textual summary

- [ ] Check that the repetition time is the expected 1.6s.
  If not:
    - [ ] Investigate whether the TR metadata in the sidecar JSON file is wrong.
      Fix it and re-run *fMRIPrep*.
    - [ ] [Exclude the whole session](#textual-summary-1) if it was acquired with the wrong TR.
- [ ] Verify that susceptibility distortion correction was applied.
  If not, check that fieldmaps were present in the unprocessed data, that there are no typos in their filename, and that the fields `B0FieldSource` and `B0FieldIdentifier` have been correctly set in the JSON sidecars.
- [ ] Verify that registration was applied.
  If not, fix the problem and re-run *fMRIPrep*.
- [ ] Check that four echoes are detected in the field `Multi-echo EPI sequence`.
  If not, check that four echoes were present in the unprocessed data and that they are no typos in their filename.
  [Exclude the session if those issues cannot be fixed](#textual-summary-1).
- [ ] If the four echoes are not detected in the field `Multi-echo EPI sequence` even after checking their presence in the unprocessed data and that they are no
  typos in their filename, exclude the session.

### Alignment of functional and anatomical MRI data

- [ ] Check that the BOLD and the T1w image are well aligned:
    - [ ] Verify that the image boundaries as well as the anatomical landmarks, such as the ventricles and the corpus callosum, appear in the same place when toggling between images.
    - [ ] Verify that the white and pial surface outline (red and blue lines) correspond well to the tissues boundaries in the BOLD image.
    - [ ] Increase the degrees of freedom of the co-registration transform setting `--bold2t1w-dof 9` to the *fMRIPrep* call, and re-run *fMRIPrep* if issues are observed at any point above.
    - [ ] If that did not solve the co-registration problem, set `--bold2t1w-init header` instead and re-run *fMRIPrep*.
    - [ ] [Exclude this session](#alignment-of-functional-and-anatomical-mri-data) if the co-registration performance remains insufficient.
<!-- https://github.com/TheAxonLab/hcph-sops/issues/453
- [ ] Check that no large residual susceptibility distortion affects the BOLD image.
  Susceptibility distortion manifests as signal drop-outs or brain distortions.
    - [ ] Check the [susceptibility distortion estimation](#textual-summary) if large susceptibility distortion remains.
    - [ ] If this issue cannot be fixed, [exclude the session](#alignment-of-functional-and-anatomical-mri-data-1).-->

### Brain mask and (anatomical/temporal) CompCor ROIs

- [ ] Verify that the brain mask does not clip GM areas out.
    Note that a hole in the middle of the brain mask is not a problem, as this will not disrupt co-registration.
    Note also that it is not a problem that the brain mask is loose around the brain.
    If the brain mask does clip GM areas out, do not use nuisance regressors as they likely contain signal of interest.
- [ ] Verify that the temporal CompCor mask appears as a collection of points scattered around the brain (with typically higher density in the outer rim of the frontal lobe and close to the brainstem) and does not form suspiciously aggregated shapes (an indicator of an underlying artifact).
    If the mask does not appear as it should, make sure to not use temporal CompCor confounds in the nuisance regression.

### Correlations between nuisance regressors

- [ ] Note down the regressors that are highly correlated and take care of not including more than one per correlated group in the nuisance regression model.

## QA criteria specifically for RSfMRI

### BOLD summary

The carpet plot MUST appear homogeneous:

- [ ] Check that the carpet plot is unaffected by strong dark deflections (signal drops) associated with motion peaks (particularly in the brain edge).
- [ ] Check that no periodic modulation is visible throughout the plot.

If any of the latter patterns is observed, flag the session and double check that the carpetplot appears homogeneous after denoising.

# Exclusion criteria for preprocessed data

## Exclusion criteria *fMRIPrep* anatomical processing

### Brain mask and brain tissue segmentation of the T1w

- [ ] Check for residual intensity non-uniformity (INU).
  If the INU is strongly visible, exclude the data.
- [ ] Check that the brain mask does not cut off part of the brain and/or contain holes surrounding signal drop-out regions.
  If it is not the case, exclude the data.
- [ ] Check that the brain mask does not include parts that are clearly NOT brain.
  Typically, this appears as bumps surrounding high-intensity areas of signal outside the brain (e.g dura or skull).
  If it is not the case, exclude the data.

### Surface reconstruction

- [ ] Check that the WM-GM boundary outlines (blue line) matches the boundary observed in the underlying image.
- [ ] Verify that the WM and pial surface do not cross or overlap each other.
- [ ] Verify that the pial surface (red line) does not extend past the actual pial boundary.

## Exclusion criteria for preprocessed fMRI

### Textual summary

- [ ] If the fMRI run has been acquired with a TR different from 1.6s, exclude that scan.
  It is likely the other fMRI scans have been mistakenly acquired with the wrong TR, so double-check the other fMRI run of the same session.
- [ ] If the four echoes are not detected in the field `Multi-echo EPI sequence` even after checking their presence in the unprocessed data and that they are no  typos in their filename, exclude the session.

### Alignment of functional and anatomical MRI data

- [ ] If the BOLD to T1w image alignment cannot be fixed by [tweaking the co-registration](#alignment-of-functional-and-anatomical-mri-data), the fMRI scan has to be excluded.
- [ ] If large susceptibility distortion remains [despite previous measures](#alignment-of-functional-and-anatomical-mri-data), exclude the fMRI scan.

### BOLD summary

- [ ] Check for outstanding signal drops that may reveal a coil failure.
  If such a pattern is observed, exclude the fMRI scan.
