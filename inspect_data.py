import pandas as pd

excel_path = 'data/downloads/New folder/wonoayu_pollutants_rolling30_interpolated.xlsx'
df = pd.read_excel(excel_path)
print('File:', excel_path)
print('Shape:', df.shape)
print('Columns:', df.columns.tolist())
print('Head:\n', df.head(3))
print('Null count:\n', df.isnull().sum())

df_poly_tsfel = pd.read_csv('All-Pollutants-wonoayu-polynomial-tsfel.csv')
print('\nAll-Pollutants-wonoayu-polynomial-tsfel.csv shape:', df_poly_tsfel.shape)
