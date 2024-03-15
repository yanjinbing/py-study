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

'''
检查版面图是否存在，检查顺序
pdf -> jpg -> ceb/cebx ，如果不存在，尝试下载
'''
source_dir = "E:\\News\\news\\"
image_url = 'http://img.enews.apabi.com/'

session = requests.Session()
def download_file(url, filepath):  
    if os.path.exists(filepath):
            return 200

    url = url.replace('\\', '/')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.69'}
    with session.get(url, headers=headers, timeout = 300) as response:
        if response.status_code == 200:  
            tmp_filepath = filepath + '.tmp'
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)                
                with open(tmp_filepath, 'wb') as f:  
                        for chunk in response.iter_content(chunk_size=8192):  
                            f.write(chunk)  
                shutil.move(tmp_filepath, filepath)
                print(url)
            except:             
                if os.path.exists(tmp_filepath):
                    os.remove(tmp_filepath)
                raise
   
    return response.status_code

def retry_page_img(path, file):
    url = image_url + path + '/' + file
    ''' 失败了重试三次'''
    for i in range(3):
        try:
            code = download_file(url, os.path.join(source_dir, path, file))
            if code in [200, 404]:
                    return code
        except Exception as e:
            print(e)
    return 0
    
def parse_mpml(path, mpml_file):
    mpml = etree.parse(os.path.join(source_dir, path, mpml_file), etree.XMLParser())
    ns = {
                "mpml":"http://www.apabi.com/2008/MPMLSchema",
                "cnml":"http://www.cnml.org.cn/2005/CNMLSchema",
                "xsi":"http://www.w3.org/2001/XMLSchema-instance"
              }
    pages = mpml.xpath('//mpml:Page', namespaces=ns)
    for page in pages:
        pagebrief = page.xpath(".//mpml:ContentItem[@xsi:type='PageImageCIType']/@href", namespaces=ns)[0]
        retry_page_img(path, pagebrief)

        pdf =  page.xpath(".//mpml:ContentItem[@xsi:type='PdfCIType']/@href", namespaces=ns)
        if len(pdf) == 0 or pdf[0] == '' or retry_page_img(path, pdf[0]) != 200:
            ## pdf不存在，下载大图
            real_img = page.xpath(".//mpml:RealImage/@href", namespaces=ns)
            if len(real_img) == 0 or retry_page_img(path, real_img[0]) != 200:
                 ceb = page.xpath(".//mpml:ContentItem[@xsi:type='CebCIType']/@href", namespaces=ns)
                 if len(ceb) > 0 and ceb != '':
                    retry_page_img(path, ceb[0])

def get_last_paper(target_dir):
    file_name = os.path.join(target_dir, 'download.log')
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            lines = file.readlines()
            return lines[0].strip()
    return ""

def save_last_paper(target_dir, paper_path):
    file_name = os.path.join(target_dir, 'download.log')
    with open(file_name, 'w') as file:
        file.write(paper_path)
def walk_dir(nid):
    print(nid)
    '''，遍历期次，解析mpml，查看pdf是否存在
    '''
    if 'ok' == get_last_paper(os.path.join(source_dir, nid)):
        return 0
    
    for month in os.listdir(os.path.join(source_dir, nid)): 
        print('\tmonth = ' + month)
        for day in os.listdir(os.path.join(source_dir, nid, month)):
            mpml_file = f"nq.{nid}_{month}{day}.mpml.xml"
            mpml_file = mpml_file.replace('-', '')
            try:
                parse_mpml(os.path.join(nid, month, day), mpml_file)
            except Exception as e:
                print(e)   
    save_last_paper(os.path.join(source_dir, nid), "ok")   

def run(nid):
    walk_dir(nid)
    return 0
    
def main():
    paper_dirs = os.listdir(source_dir)
    with Pool(8) as p:
        results = p.imap_unordered(run, paper_dirs)
        for result in results:
            print(f'result {result}')

if __name__ == "__main__":
    main()
   