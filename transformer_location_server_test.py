import os

# locate to data folder
data_folder_path = '/Users/yuezi/Google Drive/LAB/Africa-Model/transfomer_locations/demo_wards_yuezi'
#'/mnt/nfs/eguide/projects/networkAnalysis/Kenya/networkDesign_results/'
file_names = os.listdir(data_folder_path)

for i, name in enumerate(file_names):
    print(name)
