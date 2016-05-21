import pandas as pd
from bs4 import BeautifulSoup
import urllib2
import matplotlib.pylab as plt
import re
import sqlite3
import numpy as np
wpage= 'https://www.london.gov.uk/about-us/greater-london-authority-gla/spending-money-wisely/our-spending'

req = urllib2.Request(wpage)
page = urllib2.urlopen(req)
soup = BeautifulSoup(page, 'html5lib')

table = soup.find_all('table')     # Find all <table> tags
thelist = []                       # An empty list

for t in table:
    if len(t.find_all('th')) > 0:  # Only select tables with csv files

        for a in t.find_all('a', href=True):   
            thelink = 'https:' + a['href']     # Find all hyperlinks in the table
            
            if len(thelink) < 40:        # If True, thelink is a link to another webpage
                                         # containing the csv file

               req = urllib2.Request(thelink)    # Scrap thelink wepage
               page = urllib2.urlopen(req)
               soup = BeautifulSoup(page, 'html5lib')

               aa = soup.find_all(href = re.compile('.csv'))[0] # Extract the only csv file
               thelink = aa['href']
               thelist.append(thelink)   # Append results to the list
            else:
               thelist.append(thelink)   # If the link is a link to the csv file, append the
                                         # results straight away



from __future__ import print_function

df = pd.DataFrame()
print('Running')
for num, thefile in enumerate(thelist):
     print(num, end="  "),
     tmp = pd.read_csv(thefile, header=None) 

     # Drop rows with all missing values
     tmp.dropna(inplace=True, how='all',axis=1, thresh=10)
     
     # Find the row with the column names     
     ix = np.where(tmp.values == 'Vendor ID')[0][0]
     column_names = tmp.loc[ix]
     
     # Remove summary from file header
     tmp = tmp[(ix + 1) :]
     tmp.columns = column_names
     
     # Drop columns with all missing values
     tmp.dropna(inplace=True, how='all', axis=0)
     tmp.dropna(inplace=True, axis = 0)
     
     # Append results to dataframe
     df = df.append(tmp, ignore_index = True)
print('Done')


def clean_par(text):
    # transform '(123)' -> -123 
    if '(' in text:
        output = ('-' + re.sub('[()]','',text))
    else:
        output = text
    return output

df['Amount'] = df['Amount'].map(lambda x: clean_par(x))
df['Amount'] = df['Amount'].map(lambda x: x.replace(',','')).astype(float)

df['Clearing Date'] = df['Clearing Date'].map(lambda x: pd.Timestamp(x))
df['Expenditure Account Code Description'] = df['Expenditure Account Code Description'].map(lambda x: x.upper())

mask = ~df['Directorate'].isnull()
df.loc[mask,'Directorate'] = df.loc[mask,'Directorate'].map(lambda x: x.upper())
df.loc[mask,'Directorate'] = df.loc[mask,'Directorate'].map(lambda x: x.replace('&','AND'))
df.loc[mask,'Directorate'] = df.loc[mask,'Directorate'].map(lambda x: x.rstrip())

con = sqlite3.connect('/Users/vincenzo/Science/GLA/data.db')
con.text_factory = str
df.to_sql('table',con, flavor='sqlite',index=False, if_exists='replace')

# Plot Amount vs date
df_sorted = df.sort_values('Clearing Date') 
df_sorted.plot(x = 'Clearing Date', y = 'Amount',legend=None,
    grid=True,lw=1.2)
plt.ylabel('Amount')

# Plot Amount vs date

grouped = df.groupby('Expenditure Account Code Description')
total = grouped.sum().sort_values('Amount',ascending=False)

# Pie chart
grouped = df[~df['Directorate'].isnull()].groupby('Directorate')
total = grouped.sum().sort_values('Amount',ascending=False)

plt.figure(figsize=(7,4))
labels = total.index.values
labels[5:] = ''

cmap = plt.cm.jet
colors = cmap(np.linspace(0., 2., len(total)))
explode = tuple(np.linspace(0,0.8,len(total)))

patches, texts = plt.pie(total['Amount'], radius=0.9, startangle=0,
    colors=colors,explode=explode,labels=labels)
_ = [texts[i].set_fontsize(10) for i in range(0,len(total))]

plt.axis('equal')
plt.title('Total Spendings (2013-2016)')
plt.tight_layout()

#plt.legend(labels=labels, loc="best",fontsize=9,bbox_to_anchor=(0.43, 0.6))





