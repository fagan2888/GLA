import pandas as pd
from bs4 import BeautifulSoup
import urllib2
import matplotlib.pylab as plt
import re

wpage= 'https://www.london.gov.uk/about-us/greater-london-authority-gla/spending-money-wisely/our-spending'

def give_me_soup(wpage):
    req = urllib2.Request(wpage)
    page = urllib2.urlopen(req)
    soup = BeautifulSoup(page, 'html5lib')
    print 'souping', wpage
    return soup

def list_of_links(wpage):
    soup = give_me_soup(wpage)
    table = soup.find_all('table')[0]

    thelist = []
    for a in table.find_all('a', href=True):
        thelink = 'https:' + a['href']
        
        if len(thelink) < 40:
           soup = give_me_soup(thelink)
           aa = soup.find_all(href = re.compile('.csv'))[0]
           thelink = aa['href']
           thelist.append(thelink)
        else:
           thelist.append(thelink)

    return thelist 

def stack_dataframes(thelist):
    df = pd.DataFrame()

    for num,thefile in enumerate(thelist):
        print thefile
        tmp = pd.read_csv(thefile, header=None) 
        tmp.dropna(inplace=True, how='all',axis=1, thresh=10)
        
        #cols = tmp.where(tmp[1] == 'Vendor ID').dropna(how='all')
        #column_names = tmp.iloc[cols.index].values.flatten()
        try:
           ix = tmp.loc[tmp[0] == 'Vendor ID'].index[0]
        except KeyError:
           ix = tmp.loc[tmp[1] == 'Vendor ID'].index[0]
        
        column_names = tmp.loc[ix]
        tmp = tmp[(ix + 1) :]
        tmp.columns = column_names
        tmp.dropna(inplace=True, how='all',axis=0)
        tmp.dropna(inplace=True, axis = 0)

        df = df.append(tmp, ignore_index = True)

    return df

thelist = list_of_links(wpage)
df = stack_dataframes(thelist)
df = df[df.columns[2:]]

def clean_par(text):
	if '(' in text:
		output = ('-' + re.sub('[()]','',text))
	else:
		output = text
	return output

df['Amount'] = df['Amount'].map(lambda x: clean_par(x))
df['Amount'] = df['Amount'].map(lambda x: x.replace(',','')).astype(float)
df['Clearing Date'] = df['Clearing Date'].map(lambda x: pd.Timestamp(x))
df['Expenditure Account Code Description'] = df['Expenditure Account Code Description'].map(lambda x: x.upper())

# Plot Amount vs date
df_sorted = df.sort_values('Clearing Date') 
df_sorted.plot(x = 'Clearing Date', y = 'Amount',legend=None,ylim=(-10**5,10**8),grid=True)
plt.ylabel('Amount')

grouped = df.groupby('Expenditure Account Code Description')
total = grouped.sum().sort_values('Amount',ascending=False)

#total[0:4].plot.pie(subplots=True, legend=False, autopct='%.2f')






