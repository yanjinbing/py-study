import csv
from datetime import datetime, timedelta  
import requests  
import os
import shutil
from lxml import etree 
import zipfile
import os  
import shutil
from multiprocessing import Pool

source_dir = 'D:\\test\\news\\'
target_dir = "D:\\test\\news_unzip\\"
backup_dir = 'D:\\test\\backup\\'

def download_file(url, target_file):  
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.69'}
        response = requests.get(url, headers=headers, timeout = 300)  
        if response.status_code == 200:  
            try:
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                tmp_filepath = target_file + '.tmp'
                with open(tmp_filepath, 'wb') as f:  
                    for chunk in response.iter_content(chunk_size=8192):  
                        f.write(chunk)  
                shutil.move(tmp_filepath, target_file)
            except:                    
                os.remove(tmp_filepath)
                raise
        else:
            print(f'{response.status_code}, {url}')
        return response.status_code

def download_content_item(cnml_file):
    # 下载文章插图
    cnml = etree.parse(cnml_file, etree.XMLParser())
    ns = {
        "mpml":"http://www.apabi.com/2008/MPMLSchema",
                "cnml":"http://www.cnml.org.cn/2005/CNMLSchema",
                "xsi":"http://www.w3.org/2001/XMLSchema-instance"
        }
    images = cnml.xpath(".//cnml:ContentItem[@xsi:type='ImageCIType']/@href", namespaces=ns)
    base_url = '/'.join(s for s in cnml_file.split(os.sep)[-4:-1])
      
    # 组合成新的路径  
    for image in images:
        image_url = 'http://img.enews.apabi.com/' + base_url + '/' + image
        for i in range(3):
            try:
                code = download_file(image_url, os.path.join(os.path.dirname(cnml_file), image))
                if code in [200, 404]:
                    break
                else:
                    return False
            except Exception as e:
                print(e)
                return False
    return True


def walk_dir(source, target):
    print(source)
    for name in os.listdir(source): 
        path_name = os.path.join(source, name) 
        if os.path.isdir(path_name):
            walk_dir(path_name, os.path.join(target, name))
        else:
            file_name, ext = os.path.splitext(path_name)
            if ext == '.zip':       
                try:
                    ## 目标已经存在
                    target_path = os.path.join(target, file_name[-2:])
                    with zipfile.ZipFile(path_name, 'r') as file :
                        file.extractall(target_path)
                    for file in os.listdir(target_path):
                        if file.endswith('.cnml.xml'):
                            break
                    # 下载文章插图
                    if download_content_item(os.path.join(target_path, file)):
                        # 移动到备份目录
                        source_file = os.path.join(backup_dir, path_name.replace(':',''))
                        parent_dir = os.path.dirname(source_file)  
                        if not os.path.exists(parent_dir):  
                            os.makedirs(parent_dir)
                        shutil.move(path_name, source_file)
                except Exception as e:
                    print(e)


def run(path_name):
    walk_dir(os.path.join(source_dir, path_name), os.path.join(target_dir, path_name))
    pass
    
def main():
    paper_dirs = os.listdir(source_dir)
    with Pool(16) as p:
        results = p.imap_unordered(run, paper_dirs)
        for result in results:
            print(f'result {result}')

if __name__ == "__main__":
    main()
    