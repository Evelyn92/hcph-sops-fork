## Three days before 1<sup>st</sup> session

- [ ] Verify that as part of the [recruitement and screening procedure](../recruitment-scheduling-screening/recruitment.md), you have sent a copy of the MRI Safety and screening form ([EN](../assets/files/safety_form_EN.pdf)|[FR](../assets/files/safety_form_FR.pdf)) to the participant over email and confirm reception by checking the 'First contact email sent' column in [our recruits spreadsheet]({{ secrets.data.recruits_url | default("/redacted.html") }}).
- [ ] Verify that the 'Phone interview done' and 'Participant volunteer and eligible' columns in [our recruits spreadsheet]({{ secrets.data.recruits_url | default("/redacted.html") }}) are checked.
    - [ ] If the phone call interview was more than three days before the first session or the two items immediately above were not checked, call the participant again to reconfirm the following information:
        - [ ] Remind the participant that any jewelry should be removed prior to the scan.
        - [ ] Indicate that they MUST shave the upper area of their chest where the ECG electrodes will be placed, if there is hair because the ECG electrodes MUST directly contact the skin.
        - [ ] Confirm clothing:
            - [ ] if allowed to wear street clothes, remind the participant to avoid clothing with metal or that would uncomfortable to lie in for the duration of the scan; otherwise
            - [ ] remark the participant they will be given a gown and they will need to change before every session.
        - [ ] Repeat at what time and where will you meet the participant.
        - [ ] Verify that the participant has your phone number :fontawesome-solid-square-phone: {{ secrets.phones.study | default("###-###-####") }} to call you in case they gets lost.
        - [ ] **FEMALE PARTICIPANTS ONLY**: Remind the participant that pregnant women cannot undergo our MRI protocols. Therefore, they will take a pregnancy test (which we will have prepared) before the first session.
- [ ] If participant has indicated nervousness or history of claustrophobia, organize a session to use the mock scanner.

## Three days before EVERY session

We MUST verify that *{{ secrets.hosts.psychopy | default("███") }}* correctly runs all *Psychopy* experiments.

- [ ] Connect a secondary screen to the HDMI input of the computer
- [ ] Switch it on and log in into the common user (password: `{{ secrets.login.password_psychopy | default("*****") }}`).
- [ ] Open a terminal

    !!! tip "Shortcut <span class='keypress'>:fontawesome-brands-windows:</span> + <span class='keypress'>t</span>"

- [ ] Update the [HCPh-fMRI-tasks repository](https://github.com/TheAxonLab/HCPh-fMRI-tasks) on *{{ secrets.hosts.psychopy | default("███") }}*:
    ```
    cd ~/workspace/HCPh-fMRI-tasks
    git fetch upstream
    git checkout master
    git rebase upstream/master
    ```

??? important "The following two commands are executed with `sudo`"

    The console will request the common user password (`{{ secrets.login.password_psychopy | default("*****") }}`).

- [ ] Spin up a mock MMBT-S device listening on `/dev/ttyACM0`:
    ``` shell
    sudo socat PTY,link=/tmp/virtual_serial_port PTY,link=/dev/ttyACM0,group-late=dialout,mode=666,b9600
    ```
- [ ] Manually spin up the trigger-forwarding service:
    ``` shell
    sudo python3 code/synchronization/forward-trigger-service.py --disable-mmbt-check
    ```

??? important "Make sure to load the correct environment"

    - [ ] Deactivate conda (if active):
        ``` shell
        conda deactivate
        ```
    - [ ] Load the new virtual environment:
        ``` shell
        source $HOME/psychopyenv/bin/activate
        ```

- [ ] Run the compiled tasks with *Python* directly.
- [ ] Load in the different experiments and check for proper functioning and timing:
    - dMRI (only fixation):
        ``` shell
        python {{ settings.psychopy.tasks.dwi }}.py
        ```
    - QCT:
        ``` shell
        python {{ settings.psychopy.tasks.func_qct }}.py
        ```
    - RSfMRI
        ``` shell
        python {{ settings.psychopy.tasks.func_rest }}.py
        ```
    - BHT:
        ``` shell
        python {{ settings.psychopy.tasks.func_bht }}.py
        ```

    All of the above command lines SHOULD open a modal dialog asking you for the number of trial (automatically calculated, DO NOT modify) and the session number.

    !!! danger "The following steps MUST be executed in this order"

        - [ ] Drag and drop the modal dialog into the scanner's projector screen.
        - [ ] Update the session number with the corresponding number.

- [ ] Check the correct session number is set (use the default 9999 for testing) and hit *OK*.

    ??? danger "The OK button MUST be clicked with this modal dialog on the secondary screen"

        Otherwise, the wrong screen will be selected by *Psychopy*

??? warning "Updating *Ubuntu* or *Psychopy* is not recommended in the proximity of data collection"

    However, you should make sure you are on *Ubuntu* {{ settings.psychopy.ubuntu }}, *Python* {{ settings.psychopy.python }}, and *Psychopy* {{ settings.psychopy.version }}.

## One day before the session

- [ ] Print [the informed consent form](../assets/files/icf_FR.pdf) (**first session only**)
- [ ] Print the MRI safety screener ([EN](../assets/files/safety_form_EN.pdf)|[FR](../assets/files/safety_form_FR.pdf)).
- [ ] Print a receipt form for each participant that will get scanned.
- [ ] Prepare a gas cannula (oxygen mask) by cutting it before the fork and plugging two medication line tubes.
