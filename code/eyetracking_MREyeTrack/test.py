# https://www.axonlab.org/hcph-sops/data-management/edf-to-bids/
from pyedfread import read_edf
from pathlib import Path

DATA_PATH = Path("D:\\Eye_Dataset\\Sub001\\230928_anatomical_MREYE_study\\ET_EDF")
edf_name = "JB1.EDF"
file_path = str(DATA_PATH / edf_name)
# file_path = "D:\\Eye_Dataset\\Sub001\\230928_anatomical_MREYE_study\\ET_EDF\\Bold_GR4.edf"

print(file_path)
recording, events, messages = read_edf(file_path)
print(messages)
print('part 1 finished!')