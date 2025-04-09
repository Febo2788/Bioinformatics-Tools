import os
import pandas as pd

input_directory = r'C:\Users\thora\Downloads\TT12AB'
output_directory = r'C:\Users\thora\Downloads\TT12AB\converted_files'

os.makedirs(output_directory, exist_ok=True)

for filename in os.listdir(input_directory):
    if filename.endswith('.csv'):
        file_path = os.path.join(input_directory, filename)
        
        df = pd.read_csv(file_path)
        
        df.rename(columns={
            'Plate File': 'Data File',
            'Field 1': 'Strain Type',
            'Field 2': 'Sample Number',
            'Field 3': 'Strain Name',
            'Field 4': 'Strain Number'
        }, inplace=True)
        
        df['Data File'] = 'file'
        
        hour_index = df.columns.get_loc('Hour')
        df.insert(hour_index, 'Other', '')
        
        output_file_path = os.path.join(output_directory, filename)
        df.to_csv(output_file_path, index=False)
        
        print(f"File '{filename}' has been converted and saved to '{output_file_path}'.")
