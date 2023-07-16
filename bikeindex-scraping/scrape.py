import os
import re
import requests
from bs4 import BeautifulSoup

def extract_bike_urls(html_file):
    with open(html_file, 'r') as file:
        html_content = file.read()

    pattern = r'(https?://bikeindex.org/bikes/[0-9]+)'
    # https://bikeindex.org/bikes/
    bike_urls = re.findall(pattern, html_content)
    return bike_urls

def scrape_bike(url):
    bike = {}
    response = requests.get(url)
    # process!
    soup = BeautifulSoup(response.content, "html.parser")

    # basic info:
    title = soup.find("h1", class_="bike-title").find_all("strong")
    bike_status = title[0].text.strip()
    bike_name = title[1].text.strip()
    bike.update({"BikeName": bike_name})
    bike.update({"BikeStatus": bike_status})

    # theft location long/lat:
    pattern = r"\[([0-9.-]+,\s[0-9.-]+)\];"
    bike_details = soup.find("div", class_="show-bike-details")
    bike_lnglat_scripts = bike_details.find_all("script")
    if len(bike_lnglat_scripts)>=2:
        lnglat = re.findall(pattern, str(bike_lnglat_scripts[1]))[0].split(", ")
        lng = lnglat[0]
        lat = lnglat[1]
        bike.update({"TheftLongitude": lng})
        bike.update({"TheftLatitude": lat})

    # details:
    attr_lis = []
    attr_uls = soup.find_all("ul", class_="attr-list")
    for attr_ul in attr_uls:
        this_attr_lis = attr_ul.find_all("li")
        for attr_li in this_attr_lis:
            attr_lis.append(attr_li)
    for attr in attr_lis:
        attr_name = attr.find("strong").text.replace(':','').replace("\n","").replace("\r","").strip()
        attr_value = attr.text.replace(attr_name, '').replace(':','').replace("\n","").replace("\r","").strip()
        bike.update({attr_name: attr_value})

    return bike


def main(html_file):
    bike_urls = list(set(extract_bike_urls(html_file)))
    bikes = []
    allkey = []

    c = 0
    for url in bike_urls:
        c += 1
        # print(f"Downloading: {url}")
        bike = scrape_bike(url)
        bikes.append(bike)
        # if c > 5: break

    for dictio in bikes:
        for key in dictio:
            allkey.append(key)
    allkey = set(allkey)

    print("\t".join(allkey))
    for bike in bikes:
       bike_row = []
       for key in allkey:
           bike_row.append(bike.get(key, ""))
       print("\t".join(bike_row))


if __name__ == '__main__':
    html_file = './urls.txt'  # Replace with the path to your HTML file
    main(html_file)

