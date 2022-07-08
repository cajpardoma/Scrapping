# Python project for pricing scripping of different sites
# Creado por: Camilo Pardo Macea

# FOR Supplyworks
# ----------------------------------------------------------------------------------------------------------------------
# Libraries import
# ----------------------------------------------------------------------------------------------------------------------
import datetime
import os
import time

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------------------------------------------------------
# Configuration and Global Variables
# ----------------------------------------------------------------------------------------------------------------------
# Path definition of the .csv file
fecha = datetime.datetime.today()
folder = fecha.strftime('%Y-%m')
if not os.path.exists('./XX_Data/' + folder):
    os.makedirs('./XX_Data/' + folder)
output_path_toilet = './XX_Data/' + folder + '/Supplyworks_toilet-' + str(fecha.year) + '_' \
                     + str(fecha.month) + '.csv'

# Path for loading the URL sites
url_path_toilet = './XX_Url/Supplyworks.xlsx'

# Number of retry
NUM_RETRIES = 5

# Waiting time between request
delays = [1, 4, 8, 2, 5, 3]

# Header for beautiful soup
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}


# Function for data extract informacion of product
def supplyworks_data(elem, soup_html):
    """
    Programa que toma la información general de una pagina de producto del market place de Plumbingandelectric
    """
    # Collecting the name and product type
    # brand_name = soup_html.find('div', class_='product-detail__brand-container').text.strip()
    product_name = soup_html.find('h1', class_="margin-top-half-em margin-bottom-half-em").text

    if "bowl" in product_name.lower():
        product_format = "Bowl"
    elif "tank" in product_name.lower():
        product_format = "Tank"
    else:
        product_format = "Toilet"

    # Collecting the sku
    sku_ref = soup_html.find_all('span', class_='num-crumb')[1].text.split('Part #')[1].strip()
    internet_ref = soup_html.find_all('span', class_='num-crumb')[0].text.split('Item #')[1].strip()

    # Collecting the current price
    price_clean = soup_html.find('span', {'data-id': 'currentPrice'}).text.split(' ')[0].split('$')[1]

    # Collecting the image
    # TODO: Get the src using selenium
    url_img = soup_html.find('img', class_='pure-img text-center sku-image').attrs['src']

    # Stock Online
    try:
        stock_flag = soup_html.find('div', class_='availability')\
        .find('span', class_='status instock')
        if stock_flag is None:
            stock = 'No'
        else:
            stock = 'Si'
    except:
        stock = "Na"
    # ------------------------------------------------------------------------------------------------------------------
    # Message display
    print("Recopilando la información de {}".format(elem["Link"]))
    # print("La marca es la: {}".format(brand_name))
    print("El sanitario es el: {}".format(product_name))
    print("El tipo de producto es un: {}".format(product_format))
    print("El sku es el: {}".format(sku_ref))
    print("El sku_internet es el: {}".format(internet_ref))
    print("El precio listado es: {} USD".format(price_clean))
    print(url_img)
    print("\n")
    # ------------------------------------------------------------------------------------------------------------------
    # Appending the item in a list
    information = [datetime.datetime.today().date(), elem["Fabricante"], elem["Sku"],
                   elem["Linea"], product_format, elem["Rough in"], elem["Bowl Height"], elem["Asiento"],
                   elem["Capacidad (Gpl)"], product_name, internet_ref,
                   price_clean, "USD", "supplyworks.com", stock, elem["Link"], url_img]

    return information


# ----------------------------------------------------------------------------------------------------------------------
# Main code
# ----------------------------------------------------------------------------------------------------------------------
for product_type, output_path in [[url_path_toilet, output_path_toilet]]:
    # Reading .xlsx file with url list
    file_df = pd.read_excel(product_type)

    # Keeping just the row with links
    product_df = file_df[file_df['Link'].notna()]

    # Scrapping the information of every url
    data = []
    for index, elem in product_df.iterrows():
        for i in range(NUM_RETRIES):
            # Random Wait between request
            delay = np.random.choice(delays)
            time.sleep(delay)
            try:
                response = requests.get(elem["Link"], headers=headers)

                print("Intento numero {}".format(i))
                print(response)
                if response.status_code in [200, 404]:
                    # escape for loop if the API returns a successful response
                    break
            except requests.exceptions.ConnectionError:
                response = ''
                print("ConnectionError")
        try:
            estate = response.status_code
        except:
            estate = 900

        # parse data if 200 status code (successful response)
        if estate == 200:
            # Parse data with beautifulsoup
            soup: BeautifulSoup = BeautifulSoup(response.content, "html.parser")

            # Getting the information from the website
            toilet_information = supplyworks_data(elem, soup)
            data.append(toilet_information)

    # Creating the dataframe
    df = pd.DataFrame(data, columns=["Fecha", "Fabricante", "SKU", "Linea", "Tipo", "Rough_In",
                                     "Bowl Height", "Asiento", "Capacidad (Gpl)", "Producto",
                                     "Cod_Internet", "Precio", "Moneda",
                                     "Market_Place", "Stock", "URL", "Image_url"])

    # Saving the file in a .csv file
    df.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
