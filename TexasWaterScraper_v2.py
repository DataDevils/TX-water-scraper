# coding: utf-8

# ## Texas Water Scraper
# * Get a list of sites for the year to scrape
# * Loop through each size; generate and pull a report
# * Scrape the report details into a csv file
# ---
# Requires:
# * The selenium package and the geckodriver.exe file (for Mozilla browsers).


#Import libraries
import os, sys
import requests
import unicodedata
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import Select

#Settings
year = 2016
theURL = 'http://www2.twdb.texas.gov/ReportServerExt/Pages/ReportViewer.aspx?%2fWU%2fSumFinal_WUG_Entity_Detail_2016&rs:Command=Render'

print (os.getcwd())

# ### 1. Scrape a list of utilities from the base URL
#Call the page and convert it to 'soup'
response = requests.get(theURL)
soup = BeautifulSoup(response.content,'lxml')

#Extract the control from the 'soup'
tbl = soup.find(id="ReportViewerControl_ctl04_ctl03")

#Create a list of utilities and populate values from each option in the control
utilities = []
values = []
for option in tbl.findAll('option')[1:]: #Skips the first item
    #Remove unicode chars
    utility = unicodedata.normalize("NFKD",option.text)
    utilities.append(utility)
    values.append(option.attrs['value'])
    


# ### 2. Loop through each utility and extract its report
# This step requires the selenium package to open a remotely controlled browser,
# mimic selecting the utility and clicking the View Report button, then waiting 
# for the report to complete and appear. Once that occurs the contents stored as 
# a local HTML file for later scraping.

#Create the selenium browser object
pth = os.path.dirname(sys.argv[0])
os.environ['path'] = os.environ['path'] + ";" + pth + "\\"
gPath = os.path.join(pth,'geckodriver.exe')
browser = webdriver.Firefox(executable_path=gPath)

#Open the page in the selenium browser
browser.get(theURL)

#Loop through each utility
for value,utility in zip(values[50:60],utilities[50:60]):
        
    #Set the output filename from the utility and year values
    outFN = "./Pages/{}_{}.html".format(utility.replace(" ","_"),year)
    
    #Skip if already downloaded
    if os.path.exists(outFN):
        print("{} already processed.".format(utility))
        continue

    #Status
    print("{}:\t".format(utility),end="")

    #Select the item and 'click' it
    utilControl = Select(browser.find_element_by_id('ReportViewerControl_ctl04_ctl03_ddValue'))
    utilControl.select_by_value(value)

    #Select the View Report button to retrieve the report
    browser.find_element_by_xpath('//*[@id="ReportViewerControl_ctl04_ctl00"]').click()

    print("  fetching report",end="... ")
    while True:
        #Copy the page contents to a string
        pageSource = browser.page_source
    
        #Exit the wait loop when the 'Cancel' control disappears:---------------------------------
        #if not browser.find_element_by_id('ReportViewerControl_AsyncWait_Wait').is_displayed():
        #cancelCtrl = browser.find_element_by_id("ReportViewerControl_ctl04_ctl03_ddValue")[0]
        cancelCtrl = browser.find_elements_by_id('ReportViewerControl_AsyncWait_Wait')[0]
        if not cancelCtrl.is_displayed():
            break

    #With the report fetched, write its contents to the file
    print("Complete! Saved to {}".format(outFN))
    with open(outFN,'w') as outfile:
        outfile.write(browser.page_source)
        
    #Check for 2nd page of data
    #soup = BeautifulSoup(pageSource,'lxml') 
    #pageCtrl = soup.find(id='ReportViewerControl_ctl05_ctl00_TotalPages')
    #if '2' in pageCtrl.contents[0]: # There's a 2nd page
    pageCtrl = browser.find_elements_by_id('ReportViewerControl_ctl05_ctl00_TotalPages')[0]
    if pageCtrl.text == '2 ?':
   
        print("   fetching 2nd page",end="... ")
        
        #Click to fetch the 2nd page
        browser.find_element_by_xpath('//*[@id="ReportViewerControl_ctl05_ctl00_Next_ctl00_ctl00"]').click()
        
        #Wait until page loads
        while True:
            print("",end='.')
            page2Source = browser.page_source
            ctrl = BeautifulSoup(page2Source,'lxml').find(id='ReportViewerControl_ctl05_ctl00_TotalPages')
            if "?" not in ctrl.contents[0]:
                break
        print('saving page 2')
        outFN2 = outFN[:-5]+"_pg2.html"
        with open(outFN2,'w') as outFile2: 
            outFile2.write(page2Source)