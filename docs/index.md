# The Human Connectome PHantom (HCPh) study: Standard Operating Procedures

!!! abstract "These SOPs correspond to a pre-registered report"

    These documents correspond to a pre-registration<sup>[1]</sup>.
    Please check the corresponding [registered report](https://osf.io/fh8mc) ([direct download](assets/files/HCPh_RR_1.4.pdf)) to get a better understanding of what these SOPs implement.

    The experiments and hypotheses were pre-registered to further guarantee research rigor and seek early scrutiny and feedback from experts in the field, thereby generating consensus on data collection and analysis.
    Researchers increasingly perceive pre-registration as a tool to maximize research transparency, improve study planning, and eliminate incentives conducive to dubious practices in the search for positive outcomes.
    By pre-registering the study, we will maximize the impact and usefulness of this work.

    Future reports and public communications of results of this project will be pre-registered whenever that is possible.

??? thanks "Thanks to César Caballero-Gaudés and Stefano Moia"

    We highly appreciate the decisive help we have received from César and Stefano to bring together the physiology component of this project.

    César provided very valuable feedback at the earliest stages of the design of the project and has also facilitated it with key feedback (including a visit to show their settings at BCBL).

    Stefano helped edit our registered report, and traveled to Lausanne twice to help us on the spot with the BIOPAC and calibration.

??? thanks "Thanks to Garikoitz Lerma-Usabiaga"

    Gari filmed several versions of the *Mundaka clip*, that allowed us to edit the final clip that is presented during the resting state fMRI.

??? thanks "Thanks to Inès de Riedmatten and Arthur Spencer"

    Inès has contributed with excellent materials to the initial versions of these SOPs, and re-enabled the trigger issuing by our dMRI sequence (which had disappeared after a scanner's software upgrade...)
    Arthur helped us with more recent aspects regarding the gas analyzer calibration and has supported us in other meaningful ways.

| ![](assets/images/cohort1.png) |
|:--:|
| ***Figure 1. Experimental design of Cohort I.*** *The first section of the study involves acquiring 72 sessions across three scanners of a single subject.* |

## Summary

Unveiling how the brain's structure defines its distributed function and modulates the dynamics of processing holds the promise of triggering a revolution in neuroscience and applications to mental health and neurodegenerative diseases.
Magnetic resonance imaging (MRI) has proven a valuable, non-invasive way of probing both the architecture and activity of the brain in-vivo, with sufficient spatial and temporal resolution to understand many aspects of its function.
Although a large body of literature has shown strong correlations between structural and functional networks at the larger scales<sup>[2],[3],[4],[5]</sup>, the accumulated unreliability of MRI measurements from the scanner and through further steps of the research workflow impedes the link between structure, function, and dynamics at clinically relevant spatial and temporal scales.
In particular, the measurements obtained with MRI are highly indirect, spatiotemporally uncertain, and confounded by other sources of MR signal.
This complexity provides an immense informatics challenge that crosses multiple imaging modalities, including structural, functional, and dynamic connectivity approaches to understanding the human brain.
Nonetheless, functional and structural networks extracted from MRI have proven sufficient levels of reliability to discriminate between individuals<sup>[5],[6],[7],[8]</sup>, and such reliability has proven stable from months to years<sup>[9]</sup>.
Therefore, it is critical to characterize the reliability of this network’s phenotyping before these analytical approaches may be applied clinically<sup>[10],[11]</sup>.
In this project, we will first optimize the research workflow of MR network analyses to maximize the reliability of functional and structural connectivity matrices (so-called connectomes).
Indeed, these matrices have been shown to contain large ratios of false positives and false negatives in both the functional [12] and the structural<sup>[13],[14]</sup> cases.
 We hypothesize that such improvements in sensitivity and specificity of functional and structural networks generalize across scanners and subjects, allowing the univocal identification of individuals from their brain’s networks ("fingerprinting").
In order to be able to statistically separate and characterize the sources of signal variation, the project involves acquiring large amounts of repeated data on a small number of individuals.
This approach has recently been dubbed "precision MRI"<sup>[15]</sup> and focuses on individual differences rather than group differences.
The data acquisition approach is structured in three efforts with varying numbers of subjects, repetitions, and scanning devices.
The first two, called "Cohort I" and "Cohort II" are sequential in time, and collected on three different devices.
Cohort I involves a single individual who will undergo a total of 60 scanning sessions.
Subsequently, Cohort II involves six (6) individuals and a total of twelve (12) sessions each.
Finally, "Cohort III" is a quality control set involving 18 individuals and a total of two sessions each in a single scanner.
In total, the project plans for repeated MRI acquisition on 25 healthy, adult human subjects, across three different 3.0 Tesla (T) MRI scanners available at CHUV.
In addition to the new data, the project will reuse existing, open-access data to pilot various aspects of the MRI processing and analysis workflow to further support the overall reliability of the findings.

## Impact

Overall, this project will equip researchers with a framework for the extraction of reliable and precise structural, functional and dynamic networks that permit their joint modeling and analysis with interpretable and reproducible methods.
The project will publicly release two highly valuable datasets necessary for the improvement of the workflow for structural and functional network extraction under open access and reuse terms.
Upon conclusion, this study will mark a turning point for MRI research as a fundamental resource for academic training and a necessary assessment to unlock clinical applications in the long-term with the improvement of the reliability of MRI-network analyses.
At a local scale, the project will substantially contribute to ensuring the reliability of the MRI clinical workflow that routinely aids medical decisions at CHUV.


[1]: https://doi.org/10.17605/OSF.IO/VAMQ6 "C. Provins et al., Reliability characterization of MRI measurements for analyses of brain networks on a single human, OSF-Standard Pre-Data Collection Registration, 2023, doi:10.17605/OSF.IO/VAMQ6."

[2]: https://doi.org/10.1016/j.jneumeth.2010.01.014 "P. Hagmann et al., MR connectomics: Principles and challenges., J. Neurosci. Methods 194(1):34–45, 2010, doi:10.1016/j.jneumeth.2010.01.014."

[3]: https://doi.org/10.1073/pnas.0811168106 "C. J. Honey et al., Predicting human resting-state functional connectivity from structural connectivity., PNAS 106(6):2035–40, 2009, doi:10.1073/pnas.0811168106."

[4]: https://doi.org/10.1073/pnas.1219562110 "A. M. Hermundstad et al., Structural foundations of resting-state and task-based functional connectivity in the human brain, PNAS 110(15):6169–6174, 2013, doi:10.1073/pnas.1219562110."

[5]: https://doi.org/10.1038/s41467-018-04614-w "G. Rosenthal et al., Mapping higher-order relations between brain structure and function with embedded vector representations of connectomes, Nat. Comm. 9(1):2178, 2018, doi:10.1038/s41467-018-04614-w."

[6]: https://doi.org/10.1371/journal.pbio.0060159 "P. Hagmann et al., Mapping the structural core of human cerebral cortex, PLoS Biol. 6(7):e159, 2008, doi:10.1371/journal.pbio.0060159."

[7]: https://doi.org/10.1038/nn.4135 "E. S. Finn et al., Functional connectome fingerprinting: identifying individuals using patterns of brain connectivity, Nat. Neurosci. 18(11):1664–1671, 2015, doi:10.1038/nn.4135."

[8]: https://doi.org/10.1038/s41598-018-25089-1 "E. Amico and J. Goñi, The quest for identifiability in human functional connectomes*, Sci. Rep. 8(1):8254, 2018, doi:10.1038/s41598-018-25089-1."

[9]: https://doi.org/10.1016/j.neuroimage.2019.02.002 "C. Horien et al., The individual functional connectome is unique and stable over months to years, NeuroImage 189:676–687, 2019, doi:10.1016/j.neuroimage.2019.02.002."

[10]: https://doi.org/10.1038/s41562-019-0655-x "X.-N. Zuo et al., Harnessing reliability for neuroscience research, Nat. Hum. Behav. 3(8):8, 2019, doi:10.1038/s41562-019-0655-x."

[11]: https://doi.org/10.1001/jamapsychiatry.2020.4272 "M. P. Milham, J. Vogelstein, and T. Xu, Removing the Reliability Bottleneck in Functional Magnetic Resonance Imaging Research to Achieve Clinical Utility, JAMA Psychiatry 78(6):587–588, 2021, doi:10.1001/jamapsychiatry.2020.4272."

[12]: https://doi.org/10.1016/j.neuroimage.2011.10.018 "J. D. Power et al., Spurious but systematic correlations in functional connectivity MRI networks arise from subject motion, NeuroImage 59(3):2142–2154, 2012, doi:10.1016/j.neuroimage.2011.10.018."

[13]: https://doi.org/10.1016/j.neuroimage.2016.06.035 "A. Zalesky et al., Connectome sensitivity or specificity: which is more important?, NeuroImage 142:407–420, 2016, doi:10.1016/j.neuroimage.2016.06.035."

[14]: https://doi.org/10.1038/s41467-017-01285-x "K. H. Maier-Hein et al., The challenge of mapping the human connectome based on diffusion tractography, Nat. Comm. 8(1):1349, 2017, doi:10.1038/s41467-017-01285-x."

[15]: https://doi.org/10.1016/j.neuron.2017.07.011 "E. M. Gordon et al., Precision Functional Mapping of Individual Human Brains, Neuron 95(4):791-807.e7, 2017, doi:10.1016/j.neuron.2017.07.011."
