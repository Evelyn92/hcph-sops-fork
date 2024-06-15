After data collection, a significant amount of post-scanner steps remain to reach the point where all data and derivatives have been processed, making sure they are BIDS compliant and ready for release.

The flowchart below shows an overview of the post-scanner data workflow:

``` mermaid
flowchart TB
    classDef imp stroke:#f00,stroke-width:2px;

    subgraph PACS[PACS]
    end

    subgraph physio["Physio-recording Laptop ({{ secrets.hosts.acqknowledge | default("███") }})"]
    end

    subgraph et_pc[Eye-tracker Computer]
    end

    subgraph psychopy_pc["Stimuli Presentation Laptop ({{ secrets.hosts.psychopy | default("███") }})"]
    end

    subgraph local_data[<b>Local Storage</b>]
        raw_mri[Raw MRI]
        bids_mri[BIDS MRI]
        bids_phys[BIDS Physio]
        bids_edf[BIDS edf]
        bids_events[BIDS Events]
    end

    subgraph dropbox[<b>Dropbox</b>]
        raw_phys[Raw Physio]
        raw_edf[Raw edf]
        raw_events[<i>Psychopy</i> Logs]
    end
    
    subgraph datalad[<b>DataLad</b>]
        bids_mri_datalad[BIDS MRI]
        bids_phys_datalad[BIDS Physio]
        bids_edf_datalad[BIDS edf]
        bids_events_datalad[BIDS Events]

        mriqc_out[Visual reports]
        preproc_fMRI[Preprocessed fMRI]
        preproc_dMRI[Preprocessed dMRI]

        FC

        dti_out[dMRI Derivatives]
        SC
    end
    
    subgraph openneuro[<b>Open Neuro Datasets</b>]
        unprocessed[Unprocessed Dataset]
        processed[Preprocessed Dataset]
        connectivity[SC, FC]

        rel_1[HCPh Release 1]
        rel_2[HCPh Release 2]
        rel_3[HCPh Release 3]
    end

    PACS --->|<i>pacsman</i> Script| raw_mri
    physio -->|Dropbox Sync| raw_phys
    et_pc -->|Psychopy| psychopy_pc
    psychopy_pc --> |Dropbox Sync| raw_edf
    psychopy_pc --> |Dropbox Sync| raw_events
    
    raw_mri -->|<i>HeudiConv</i> Script| bids_mri
    raw_phys --->|<i>physio-to-bids.ipynb</i> Script| bids_phys
    raw_edf ---> |<i>edf2bids</i> Script| bids_edf
    raw_events ---> |<i>psychopy2events.py</i> Script| bids_events

    bids_mri -->|FIRST Session Only !| med[Clinical Screening]
    med -->|"Incidental(s)"| alert[Alert Participant]
    class alert imp

    local_data --->|<i>datalad save</i>| datalad
    local_data --->|<i>cron</i> Job| HOrUs
    HOrUs ---> datalad
    bids_mri_datalad -->|MRIQC| mriqc_out[Visual Reports]

    mriqc_out -->|Q'Kay| mri_qc_screen[Screening]
    mri_qc_screen -->|Exclusion Criterium Met| Reschedule
    class Reschedule imp

    bids_mri_datalad -->|fMRIPrep| preproc_fMRI[Preprocessed fMRI]
    bids_mri_datalad -->|dMRIPrep| preproc_dMRI[Preprocessed dMRI]
    
    bids_mri_datalad -->|<i>pydeface</i> Script| unprocessed
    %%mriqc_out --> unprocessed

    preproc_dMRI --> processed
    preproc_fMRI --> processed

    %% fMRI pipeline
    %%preproc_fMRI --- mot_censor
    %%mot_censor --- regressed
    %%regressed --- filtered
    %%bids_phys_datalad --- filtered
    %%filtered --> FC
    preproc_fMRI --->|<i>compute_fc</i> Script| FC

    %% dMRI pipeline
    %%preproc_dMRI --- dti_dki
    %%dti_dki --> dti_out
    preproc_dMRI --->|DTI and DKI| dti_out

    dti_out --> processed

    %%preproc_dMRI --- dwi_odf
    %%dwi_odf --- tract
    %%tract --> SC
    preproc_dMRI --->|CSD and Tractography| SC

    SC --> connectivity
    FC --> connectivity

    unprocessed --> rel_1
    processed --> rel_2
    connectivity --> rel_3
```

The above graph can be detailed into two main data workflows:

1. **MRI data**.
    Stored on the CHUV PACS, the raw MRI data should first be locally [converted to BIDS](post-session.md/#convert-imaging-data-to-bids-with-heudiconv). Then both the raw and BIDS compliant data are to be synchronized with the [*Datalad* dataset](preliminary.md/#adding-data-or-metadata). From there, the BIDS compliant data can be [quality controlled](./mriqc.md) and [pre-processed](../processing/preprocessing.md) using the corresponding packages (e.g. *MRIQC*, *fMRIPrep*, *dMRIPrep*) to allow computation of analysis-grade derivatives (e.g. [functional](../processing/functional-connectivity.md) or structural connectivity).
2. **Physiological data**.
    Physiological data stored in the *stimuli presentation laptop* ({{ secrets.hosts.psychopy | default("███") }}) and the *physio-recording laptop* ({{ secrets.hosts.acqknowledge | default("███") }}) are synchronized with a cloud storage using *Dropbox*.
    The physiological signals (*AcqKnowledge*) and ET's recordings are converted to BIDS using [*phys2bids*](physio-to-bids.ipynb) and *etf2bids*, respectively.
    The logs from *Psychopy* are converted into BIDS' *events* files with the [*psychopy2events.py*](./post-session.md/#generate-bids-events-files) script.
    **Further processing steps, such as denoising, should be defined soon.**