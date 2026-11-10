import requests



headers = {
  "User-Agent": "Mozilla/5.0",
  "Accept": "application/json",
  "Content-Type": "application/json"
}
"""Not used for anything except local testing"""
def open_local_html_for_test(filepath):
    with open(filepath, 'r') as file:
        html = file.read()
    return html

def data_to_coords(data):
    lat = data[0]['lat']
    lon = data[0]['lon']
    return lat, lon

def addr_get_name(data):
    address = data['display_name']
    return address

def addr_to_coords(address):
    params = {
    "q": address,
    "format": "json",
    "polygon": 1,
    "addressdetails": 1
    }

    search_url= "http://nominatim.openstreetmap.org/search"
    response = requests.get(search_url,headers=headers,params=params)
    # print(response.content)
    data = response.json()
    # print(data)
    lat, lon = data_to_coords(data)
    return lat, lon

def coords_to_addr(lat, lon):
    reverse_url = "https://nominatim.openstreetmap.org/reverse?format=json&addressdetails=1&lat="+lat+"&lon="+lon+"&zoom=18&addressdetails=1"
    response = requests.get(reverse_url,headers=headers)
    data = response.json()
    return data