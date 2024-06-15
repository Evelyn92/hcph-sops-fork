!!! danger "*DataLad* must be version 1.0 or later"

This project maintains data under version control thanks to *DataLad*<sup>[1]</sup>.
For instructions on how to setup *DataLad* on your PC, please refer to the [official documentation](https://handbook.datalad.org/en/latest/intro/installation.html).
When employing high-performance computing (HPC), we provide [some specific guidelines](#hpc-users-instructions-to-install-datalad).

!!! important "Please read the [*DataLad Handbook*](https://handbook.datalad.org/en/latest/index.html), especially if you are new to this tool"

## Creating a *DataLad* dataset

- [ ] Designate a host and folder where data will be centralized.
    In the context of this study, the primary copy of data will be downloaded into {{ secrets.hosts.oesteban | default('&lt;hostname&gt;') }}, under the path `{{ settings.paths.pilot_sourcedata }}` for the piloting acquisitions and `{{ settings.paths.sourcedata }}` for the experimental data collection.
- [ ] Install the `bids` *DataLad procedure* provided from this repository to facilitate the correct intake of data and metadata:

    ``` shell
    PYTHON_SITE_PACKAGES=$( python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])' )
    ln -s {{ secrets.data.sops_clone_path | default('<path>') }}/code/datalad/cfg_bids.py ${PYTHON_SITE_PACKAGES}/datalad/resources/procedures/
    ```

    ??? bug "*DataLad*'s documentation does not recommend this approach"

        For safety, you can prefer to use *DataLad*'s recommendations and place the `cfg_bids.py` file in some of the suggested paths.

- [ ] Check the new *procedure* is available as `bids`:

    ``` {.shell hl_lines="2"}
    $ datalad run-procedure --discover
    cfg_bids (/home/oesteban/.miniconda/lib/python3.9/site-packages/datalad/resources/procedures/cfg_bids.py) [python_script]
    cfg_yoda (/home/oesteban/.miniconda/lib/python3.9/site-packages/datalad/resources/procedures/cfg_yoda.py) [python_script]
    cfg_metadatatypes (/home/oesteban/.miniconda/lib/python3.9/site-packages/datalad/resources/procedures/cfg_metadatatypes.py) [python_script]
    cfg_text2git (/home/oesteban/.miniconda/lib/python3.9/site-packages/datalad/resources/procedures/cfg_text2git.py) [python_script]
    cfg_noannex (/home/oesteban/.miniconda/lib/python3.9/site-packages/datalad/resources/procedures/cfg_noannex.py) [python_script]
    ```

    !!! tip "Learn more about the [YODA principles (*DataLad Handbook*)](https://handbook.datalad.org/en/latest/basics/101-127-yoda.html)"

- [ ] Create a *DataLad* dataset for the original dataset:

    ``` shell
    cd /data/datasets/
    datalad create -c bids hcph-dataset
    ```
<!--
- [ ] Create a *DataLad* subdataset called `sourcedata`

    ``` bash title="bash oneliner to link sessions"
{% filter indent(width=4) %}
{% include 'code/pacsman/softlinks-trick.sh' %}
{% endfilter %}
    ```
-->

- [ ] Configure a [RIA store](https://handbook.datalad.org/en/latest/beyond_basics/101-147-riastores.html), where large files will be pushed (and pulled from when installing the dataset in other computers)
    ``` shell title="Creating a RIA sibling to store large files"
    cd hcph-dataset
    datalad create-sibling-ria -s ria-storage --alias hcph-dataset \
            --new-store-ok --storage-sibling=only \
            "ria+ssh://{{ secrets.data.curnagl_backup | default('<username>@<hostname>:<path>') }}/dataset/"
    ```

- [ ] Configure a [GitHub sibling](https://handbook.datalad.org/en/0.15/basics/101-139-hostingservices.html), to host the Git history and the annex metadata:
    ``` shell title="Creating a GitHub sibling to store DataLad's infrastructure and dataset's metadata"
    datalad siblings add --dataset . --name github \
            --pushurl git@github.com:{{ secrets.data.gh_repo | default('<organization>/<repo_name>') }}.git \
            --url https://github.com/{{ secrets.data.gh_repo | default('<organization>/<repo_name>') }}.git \
            --publish-depends ria-storage
    ```

## *Client* side operations (when *consuming* the data)

### Installing the *DataLad* dataset

Wherever you want to process the data, you'll need to `datalad install` it before you can pull down (`datalad get`) the data.
To access the metadata (e.g., sidecar JSON files of the BIDS structure), you'll need to have access to the git repository that corresponds to the data (https://github.com/{{ secrets.data.gh_repo | default('&lt;organization&gt;/&lt;repo_name&gt;') }}.git)
To fetch the dataset from the RIA store, you will need your SSH key be added to the authorized keys.

??? important "Getting access to the RIA store"

    These steps must be done just once before you can access the dataset's data:

    - [ ] [Create a secure SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent) on the system(s) on which you want to install the dataset.
    - [ ] Send the SSH **public** key you just generated (e.g., `~/.ssh/id_ed25519.pub`) over email to Oscar at {{ secrets.email.oscar | default('*****@******') }}.


- [ ] Install and get the dataset normally:

    === "Installing the dataset without fetching data from annex"

        ``` shell
        datalad install https://github.com/{{ secrets.data.gh_repo | default('<organization>/<repo_name>') }}.git
        ```

    === "Installing the dataset and fetch all data from annex, with 8 parallel threads"

        ``` shell
        datalad install -g -J 8 https://github.com/{{ secrets.data.gh_repo | default('<organization>/<repo_name>') }}.git
        ```

### Synchronizing your *DataLad* dataset

Once the dataset is installed, new sessions will be added as data collection goes on.
When a new session is added, your *DataLad* dataset will remain at the same point in history (meaning, it will become out-of-date).

- [ ] Pull new changes in the git history.
    *DataLad* will first fetch Git remotes and merge for you.

    ``` shell
    cd hcph-dataset/  # <--- cd into the dataset's path
    datalad update -r --how merge
    ```

- [ ] If you need the data, now you can get the data as usual:

    ``` shell
    find sub-001/ses-pilot019 -name "*.nii.gz" | xargs datalad get -J 8
    ```

### Adding data or metadata

- [ ] Use `datalad save` indicating the paths you want to add, and include `--to-git` if the file contains only metadata (e.g., JSON files).

    === "Adding data files (e.g., NIfTI and compressed TSV files)"

        ``` shell
        find sub-001/ses-pilot019 -name "*.nii" -or -name "*.nii.gz" -or -name "*.tsv.gz" | \
            xargs datalad save -m '"add(pilot019): new session data (NIfTI and compressed TSV)"'
        ```

    === "Adding metadata files"

        ``` shell
        find sub-001/ses-pilot019 -name "*.json" -or -name "*.tsv" -or -name "*.bvec" -or -name "*.bval" | \
            xargs datalad save -m '"add(pilot019): new session metadata (JSON, TSV, bvec/bval)"'
        ```

### Registering containers

We use *DataLad containers-run* to execute software while keeping track of provenance.
Prior to first use, containers must be added to *DataLad* as follows (example for *MRIQC*):

- [ ] Register the *MRIQC* container to the dataset

    === "Registering a *Singularity* container"

        ``` shell
        datalad containers-add \
            --call-fmt 'singularity exec --cleanenv -B {% raw %}{{${HOME}/tmp/}}:/tmp {img} {cmd}{% endraw %}' \
            mriqc \
            --url docker://nipreps/mriqc:{{ settings.versions.mriqc }}
        ```

        ??? important "Insert relevant arguments to the `singularity` command line with `--call-fmt`"

            In the example above, we configure the container's call to automatically *bind* (`-B` flag to mount the filesystem) the temporary folder.
            *MRIQC* will store the working directory there by default.
            Please replace the path with the appropriate path for your settings (i.e., laptop, cluster, etc.).

    === "Registering a *Docker* container"

        ``` shell
        datalad containers-add \
            --call-fmt 'docker run -u $( id -u ) -it -v {% raw %}{{${HOME}/tmp/}}:/tmp {img} {cmd}{% endraw %}' \
            mriqc \
            --url docker://nipreps/mriqc:{{ settings.versions.mriqc }}
        ```

    ??? info "Pinning a particular version of *MRIQC*"

        If a different version of *MRIQC* should be executed, replace the *Docker* image's tag (`{{ settings.versions.mriqc }}`) with the adequate version tag within the above command line.

### HPC users - instructions to install *DataLad*

When HPC is planned for processing, *DataLad* will be required on that system(s).

- [ ] Start an interactive session on the HPC cluster

    ??? warning "Do not run the installation of *Conda* and *DataLad* in the login node"

        HPC systems typically recommend using their login nodes only for tasks related to job submission, data management, and preparing jobscripts.
        Therefore, the execution of resource-intensive tasks such as *fMRIPrep* or building containers on login nodes can negatively impact the overall performance and responsiveness of the system for all users.
        Interactive sessions are a great alternative when available and **should** be used when creating the *DataLad* dataset.
        For example, in the case of systems operating SLURM, the following command would open a new interactive session:
        ```
        srun --nodes=1 --ntasks-per-node=1 --time=01:00:00 --pty bash -i
        ```

- [ ] Install *DataLad*.
    Generally, the most convenient and user-sandboxed installation (i.e., without requiring elevated permissions) can be achieved by using *Conda*, but other alternatives (such as *lmod*) can be equally valid:

    === "Install *DataLad* with *Conda*"

        - [ ] Get and install *Conda* if it is not already deployed in the system:

            ``` shell
            wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
            bash Miniconda3-latest-Linux-x86_64.sh
            ```

        - [ ] Install *DataLad*:

            ``` shell
            conda install -c conda-forge -y "datalad>=1.0" datalad-container
            ```

    === "Install *DataLad* in HPC with *lmod* enabled"

        - [ ] Check the availability and dependencies for a specific Python version (here we check 3.8.2):

            ``` bash
            module spider Python/3.8.2
            ```

        - [ ] Load Python (please note `ml` below is a shorthand for `module load`)

            ``` bash
            ml GCCcore/9.3.0 Python/3.8.2
            ```

        - [ ] Update *pip*:

            ``` bash
            python -m pip --user -U pip
            ```

        - [ ] Install *DataLad*:

            ``` bash
            python -m pip install --user "datalad>=1.0" datalad-container
            ```

- [ ] Check datalad is properly installed, for instance:

    ``` shell
    $ datalad --version
    datalad 1.0.0
    ```

    ??? bug "*DataLad* crashes (*Conda* installations)"

        *DataLad* may fail with the following error:
        ``` py
        ImportError: cannot import name 'getargspec' from 'inspect' (/home/users/cprovins/miniconda3/lib/python3.11/inspect.py)
        ```

        In such a scenario, create a *Conda* environment with a lower version of Python, and re-install datalad
        ``` shell
        conda create -n "datalad" python=3.10
        conda activate datalad
        conda install -c conda-forge datalad datalad-container
        ```

- [ ] Configure your Git identity settings.

    ``` shell
    cd ~
    git config --global --add user.name "Jane Doe"
    git config --global --add user.email doe@example.com
    ```

[1]: https://doi.org/10.5281/zenodo.808846 "Hanke, Michael, et al. “Datalad.” Open Source Software, 2021. doi:10.5281/zenodo.808846"
