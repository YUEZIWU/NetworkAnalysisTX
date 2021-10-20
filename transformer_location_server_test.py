import os

# locate to data folder
data_folder_path = '/mnt/nfs/eguide/projects/networkAnalysis/Kenya/networkDesign_results/'
file_names = os.listdir(data_folder_path)

for i, name in enumerate(file_names):
    print(name)
