# Python project for pricing scripping of different sites
# Creado por: Juan Felipe Monsalvo Salazar

# FOR AmericanStandard-US
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
fecha = datetime.datetime.today()# Checking and creating the folder
folder = fecha.strftime('%Y-%m')
if not os.path.exists('./XX_Data/' + folder):
    os.makedirs('./XX_Data/' + folder)
output_path_toilet = './XX_Data/' + folder + '/American_wholesaler-' + str(fecha.year) + '_' + str(fecha.month) + '.csv'

# Path for loading the URL sites
url_path_toilet = './XX_Master_database/Wholesaler_Database.xlsx'
fabricante = 'American Standard'

# Number of retry
NUM_RETRIES = 5

# Waiting time between request
delays = [1, 4, 8, 2, 5, 3]

# Header for beautiful soup
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 '
                         '(KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}


# Function for data extract informacion of product
def american_data(elem, soup_html):
    """
    Programa que toma la información general de una página de producto del market place de AmericanStandard-us
    """
    # Collecting the name and product type
    brand_name = elem["Fabricante"]
    product_name = elem["Description"]
    product_subcategory = elem["Subcategory"]
    product_format = elem["Tipo"]
    linea_name = elem["Linea"]
    price_type = elem["Price Type"]
    multiplier = elem['Multiplicador']

    # Collecting the sku
    # sku_ref = soup_html.find('div', class_='product-number').find('span', class_='itemNumber').text
    # internet_ref = soup_html.find('div', class_='w-25 tr f6').text.split(' ')[2]

    # Collecting the current price
    price_clean = soup_html.find('div', class_='component-content price-info')['listprice'].strip('$ ')

    # Collecting the image
    url_img = soup_html.find('div', class_='product-carousel').find('div', class_='item productimage')\
        .find("img")['src']

    # Stock Online
    unstock_flag = soup_html.find('div', class_='component cxa-addtocart-component')\
        .find('div', class_='component-content out-stock-sv')
    if unstock_flag is None:
        stock = 'Si'
        consumer_price_clean = soup_html.find('div', class_='component-content price-info')['adjustedprice'].strip('$ ')
    else:
        stock = 'No'
        consumer_price_clean = None

    # ------------------------------------------------------------------------------------------------------------------
    # Message display
    print("Recopilando la información de {}".format(elem["Link"]))
    print("La marca es la: {}".format(brand_name))
    print("El sanitario es el: {}".format(product_name))
    print("El tipo de producto es un: {}".format(product_format))
    print("El sku es el: {}".format(elem["Sku"]))
    print("El precio listado es: {} USD".format(price_clean))
    print("El precio consumidor es: {} USD".format(consumer_price_clean))
    print(url_img)
    print("\n")
    # ------------------------------------------------------------------------------------------------------------------
    # Appending the item in a list
    information = [datetime.datetime.today().date(), brand_name, elem["Sku"], linea_name, product_subcategory,
                   product_format, elem["Rough in"], elem["Bowl Height"], elem["Asiento"],
                   elem["Capacidad"], product_name, price_type, multiplier, price_clean,
                   consumer_price_clean, "USD", "americanstandard-us.com", stock, elem["Link"], url_img]

    return information

# ----------------------------------------------------------------------------------------------------------------------
# Main code
# ----------------------------------------------------------------------------------------------------------------------
for product_type, output_path in [[url_path_toilet, output_path_toilet]]:
    # Reading .xlsx file with url list
    file_df = pd.read_excel(product_type, sheet_name='Competitors')
    file_df = file_df[file_df['Fabricante'] == fabricante]

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
            if elem["Scrap"] == 'Si':
                toilet_information = american_data(elem, soup)
                data.append(toilet_information)

    # ------------------------------------------------------------------------------------------------------------------
    # Keeping just the row without links
    product_df_notlink = file_df[file_df['Link'].isna()]
    for index, elem in product_df_notlink.iterrows():
        brand_name = elem["Fabricante"]
        product_name = elem["Description"]
        product_subcategory = elem["Subcategory"]
        product_format = elem["Tipo"]
        linea_name = elem["Linea"]
        price_type = elem["Price Type"]
        multiplier = elem['Multiplicador']
        url_img = elem['URL_Img']

        # Appending the item in a list
        information = [datetime.datetime.today().date(), brand_name, elem["Sku"], linea_name, product_subcategory,
                       product_format, elem["Rough in"], elem["Bowl Height"], elem["Asiento"],
                       elem["Capacidad"], product_name, price_type, multiplier, elem['List Price'],
                       None, "USD", "americanstandard-us.com", None, None, url_img]
        data.append(information)
    # ------------------------------------------------------------------------------------------------------------------

    # Creating the dataframe
    df = pd.DataFrame(data, columns=["Fecha", "Fabricante", "SKU", "Linea", 'Subcategoria', "Tipo", "Rough_In",
                                     "Bowl_Height", "Asiento", "Capacidad_(Gpl)", "Producto",
                                     "Price_Type", "Multiplicador", "Precio_Lista", "Precio_Consumidor", "Moneda",
                                     "Market_Place", "Stock", "URL", "Image_url"])

    # Saving the file in a .csv file
    df.to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
