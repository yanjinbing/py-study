import csv
from datetime import datetime, timedelta  
import requests  
import os
import shutil
from lxml import etree 
from multiprocessing import Pool
'''
第二步、下载mpml和cnml
http://img.enews.apabi.com/xmldb/D110000renmrb/2019-09/01/nq.D110000renmrb_20190901.mpml.xml
http://img.enews.apabi.com/xmldb/D110000renmrb/2019-09/01/nq.D110000renmrb_20190901.cnml.xml
'''

xmldb_url = 'http://img.enews.apabi.com/xmldb/'
image_url = 'http://img.enews.apabi.com/'
base_path = './news'
class NewsDownloader:
    def __init__(self, nid, period) -> None:
        self.nid = nid
        self.period = datetime.strptime(period, '%Y%m%d')
        self.period_path = f"{self.nid}/{self.period.strftime('%Y-%m/%d')}"
        self.session = requests.Session()
        
    def download_file(self, url, path):  
        filepath = os.path.join(base_path, path)
        if os.path.exists(filepath):
            return 200
 
        if url.endswith('/') :
            url = url + path
        else:
            url = url + '/' + path
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.69'}
        with self.session.get(url, headers=headers, timeout = 300) as response:  
            if response.status_code == 200:  
                tmp_filepath = filepath + '.tmp'
                try:
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(tmp_filepath, 'wb') as f:  
                        for chunk in response.iter_content(chunk_size=8192):  
                            f.write(chunk)  
                    shutil.move(tmp_filepath, filepath)
                except Exception as e:               
                    os.remove(tmp_filepath)
                    raise
            else:
                print(f'{response.status_code}, {url}')
        return response.status_code
    
    def retry_download_file(self, url, path):
        ''' 失败了重试三次'''
        for i in range(3):
            try:
                code = self.download_file(url, path)
                if code in [200, 404]:
                    return code
            except Exception as e:
                print(e)
        return 0
    def retry_download_img(self, path):
        url = image_url
        path = self.period_path + '/' + path
        return self.retry_download_file(url, path)

    def do_run(self):
        nqid = f"nq.{self.nid}_{self.period.strftime('%Y%m%d')}"
        mpml = f'{self.period_path}/{nqid}.mpml.xml'
        cnml = f'{self.period_path}/{nqid}.cnml.xml'
        if 200 == self.retry_download_file(xmldb_url, mpml):
            self.parse_mpml(mpml)
        if 200 == self.retry_download_file(xmldb_url, cnml):
            self.parse_cnml(cnml)

    def parse_mpml(self, mpml_file):
        mpml = etree.parse(os.path.join(base_path, mpml_file), etree.XMLParser())
        ns = {
                "mpml":"http://www.apabi.com/2008/MPMLSchema",
                "cnml":"http://www.cnml.org.cn/2005/CNMLSchema",
                "xsi":"http://www.w3.org/2001/XMLSchema-instance"
              }
        pages = mpml.xpath('//mpml:Page', namespaces=ns)
        for page in pages:
            pagebrief = page.xpath(".//mpml:ContentItem[@xsi:type='PageImageCIType']/@href", namespaces=ns)[0]
            self.retry_download_img(pagebrief)

            pdf =  page.xpath(".//mpml:ContentItem[@xsi:type='PdfCIType']/@href", namespaces=ns)
            if len(pdf) == 0 or self.retry_download_img(pdf[0]) != 200:
                ## pdf不存在，下载大图
                real_img = page.xpath(".//mpml:RealImage/@href", namespaces=ns)
                self.retry_download_img(real_img[0])
        pass
    def parse_cnml(self, cnml_file):
        cnml = etree.parse(os.path.join(base_path, cnml_file), etree.XMLParser())
        ns = {
                "mpml":"http://www.apabi.com/2008/MPMLSchema",
                "cnml":"http://www.cnml.org.cn/2005/CNMLSchema",
                "xsi":"http://www.w3.org/2001/XMLSchema-instance"
              }
        images = cnml.xpath(".//cnml:ContentItem[@xsi:type='ImageCIType']/@href", namespaces=ns)
        for image in images:
            self.retry_download_img(image)



def run(id):
    time = datetime.now()  
    prev_time = time - timedelta(days=30)
    while time >= prev_time:   
        period = time.strftime('%Y%m%d') 
        print(f'正在下载{id}-{period}' )    
        time = time - timedelta(days=1)  
        try:
            NewsDownloader(id, period).do_run()            
        except Exception as e:
            print(e)
    return id + '下载完成'
    
def main():
    ids = []
    with open('papers.txt', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            ids.append(row[0])

    with Pool(16) as p:
        results = p.imap_unordered(run, ids)
        for result in results:
            print(f'result {result}')

if __name__ == "__main__":
    main()