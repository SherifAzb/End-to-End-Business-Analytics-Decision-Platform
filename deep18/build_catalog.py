import sys
import pandas as pd

data_path = sys.argv[1] if len(sys.argv) > 1 else 'data.csv'
d = pd.read_csv(data_path, usecols=['Product_ID', 'Product_Name_y', 'Category_y', 'Brand', 'Date', 'Unit_Price'], parse_dates=['Date'])
last = d[d['Date'] >= d['Date'].max() - pd.Timedelta(days=30)]
price = last.groupby('Product_ID')['Unit_Price'].median().rename('Price')
cat = d.drop_duplicates('Product_ID').set_index('Product_ID')[['Product_Name_y', 'Category_y', 'Brand']]
cat.columns = ['Product', 'Category', 'Brand']
out = cat.join(price).reset_index().sort_values(['Category', 'Product'])
out['Price'] = out['Price'].round(2)
out.to_csv('products_catalog.csv', index=False, encoding='utf-8-sig')
print(len(out), 'products,', out['Category'].nunique(), 'categories')
