from lxml import etree 
import os
import requests
import shutil

base_url = 'http://img.enews.apabi.com/logo/'
base_path = 'd:/test/logo/'
def download_file(path):  
        url = base_url + path
        filepath = base_path + path
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.69'}
        response = requests.get(url, headers=headers, timeout = 300)  
        if response.status_code == 200:  
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                tmp_filepath = filepath + '.tmp'
                with open(tmp_filepath, 'wb') as f:  
                    for chunk in response.iter_content(chunk_size=8192):  
                        f.write(chunk)  
                shutil.move(tmp_filepath, filepath)
            except:                    
                os.remove(tmp_filepath)
                raise
        else:
            print(f'{response.status_code}, {url}')
        status = response.status_code
        response.close()
        del response
        return status

stub = etree.parse('d:\\test\\mpstub_apabi.xml')
icons = stub.xpath('//LogoIcon/@href')
for icon in icons:
    print(icon)
    for i in range(3):
        try:
            download_file(icon)
            break
        except Exception as e:
            print(e)
print('ok')

