import json
from DrissionPage import ChromiumPage,ChromiumOptions
import os
import time
#import ddddocr
import base64
from lxml import etree
import requests
from PIL import Image
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
import pandas as pd
from urllib.parse import quote
import cv2


class Crawl:

    def __init__(self):
        self.headers = {
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://cpquery.cponline.cnipa.gov.cn/detail/index?zhuanlisqh=4x6PdjOKubMxRh7cF5djZQ%253D%253D&anjianbh",
    "Sec-Fetch-Dest": "image",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Google Chrome\";v=\"133\", \"Chromium\";v=\"133\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
        if not os.path.exists("./cnipa/img"):
            os.makedirs("./cnipa/img")
        if not os.path.exists("./cnipa/pdf"):
            os.makedirs("./cnipa/pdf")
        if not os.path.exists("./cnipa/error_pdf"):
            os.makedirs("./cnipa/error_pdf")
        if not os.path.exists("./cnipa/error"):
            os.makedirs("./cnipa/error")
            

    def encrypt(self,t, e="ABCDEF0123456789"):
        # 将密钥和明文编码为UTF-8
        key = e.encode('utf-8')
        data = t.encode('utf-8')
        
        # 初始化AES加密器，使用ECB模式
        cipher = AES.new(key, AES.MODE_ECB)
        
        # 对明文进行填充并加密
        padded_data = pad(data, AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        
        # 将加密后的数据转换为Base64字符串
        encrypted_base64 = base64.b64encode(encrypted_data).decode('utf-8')
        
        return encrypted_base64
    
    
    def get_latest_modified_file(self,folder_path):
    # 获取文件夹下的所有文件和文件夹
        entries = os.listdir(folder_path)
        
        latest_file = None
        latest_time = 0
        
        # 遍历所有条目
        for entry in entries:
            # 获取完整的路径
            full_path = os.path.join(folder_path, entry)
            
            # 检查是否是文件
            if os.path.isfile(full_path):
                # 获取文件的修改时间
                modification_time = os.path.getmtime(full_path)
                
                # 如果当前文件的修改时间比最新的时间更晚，则更新最新文件
                if modification_time > latest_time:
                    latest_time = modification_time
                    latest_file = entry
        
        return latest_file, latest_time

    def identify_gap(self,bg, tp):
        '''
        bg: 背景图片
        tp: 缺口图片
        out:输出图片
        '''
        # 读取背景图片和缺口图片
        bg_img = cv2.imread(bg)  # 背景图片
        tp_img = cv2.imread(tp)  # 缺口图片

        sp1 = tp_img.shape[0]
        sp2 = tp_img.shape[1]
        cropped = bg_img[0:200, sp2:400]

        # 识别图片边缘
        bg_edge = cv2.Canny(cropped, 100, 200)
        tp_edge = cv2.Canny(tp_img, 100, 200)

        # 转换图片格式
        bg_pic = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2RGB)
        tp_pic = cv2.cvtColor(tp_edge, cv2.COLOR_GRAY2RGB)

        # 缺口匹配
        res = cv2.matchTemplate(bg_pic, tp_pic, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)  # 寻找最优匹配

        # 绘制方框
        th, tw = tp_pic.shape[:2]
        tl = max_loc  # 左上角点的坐标
        br = (tl[0] + tw, tl[1] + th)  # 右下角点的坐标
        cv2.rectangle(cropped, tl, br, (0, 0, 255), 2)  # 绘制矩形
        cv2.imwrite('out.png', cropped)  # 保存在本地
        # 返回缺口的X坐标
        return max_loc[0]+sp2
    
    
    def login(self,):
        try:
            if 'https://cpquery.cponline.cnipa.gov.cn/chinesepatent/index' == self.browser.url:
                self.browser.ele('xpath://span[contains(text(),"确定")]').click()
            self.browser.ele('xpath://input[@placeholder="手机号/证件号码"]').input("18800269809")
            self.browser.ele('xpath://input[@placeholder="请输入密码"]').input("Liji2014.")
            self.browser.ele('xpath://button[@class="el-button login-btn el-button--default el-button--medium"]').click()
            while "verify-img-panel" in self.browser.html:
                time.sleep(2)
                bg_src = self.browser.ele('xpath://div[@class="verify-img-panel"]/img').attr("src").replace("data:image/png;base64,", "")
                slice_src = self.browser.ele('xpath://div[@class="verify-sub-block"]/img').attr("src").replace("data:image/png;base64,", "")
                with open("bg_img.jpg","wb") as fp:
                    fp.write(base64.b64decode(bg_src))
                with open("slice_img.jpg","wb") as fp:
                    fp.write(base64.b64decode(slice_src))
                # det = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
                slide = open('slice_img.jpg', 'rb').read()
                bg = open('bg_img.jpg', 'rb').read()
                # distance = det.slide_match(slide, bg, simple_target=True)['target'][0]
                distance = self.identify_gap('./bg_img.jpg','./slice_img.jpg')
                print(distance)
                self.browser.actions.hold('.verify-move-block')
                self.browser.actions.move(offset_x=distance + 50, duration=.1)
                self.browser.actions.release('.verify-move-block')
                time.sleep(2)
            self.browser.get("https://cpquery.cponline.cnipa.gov.cn/chinesepatent/index")
            time.sleep(2)
            self.browser.ele('xpath://span[contains(text(),"确定")]').click()
            time.sleep(2)
            # print()
            # time.sleep(10000)
        except Exception as e:
            pass
        
    def get_scxx(self,zhuanlisqh,encrypt_param):
        headers = {
            "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Authorization": "Bearer " + self.access_token,
    "Connection": "keep-alive",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://cpquery.cponline.cnipa.gov.cn",
    "Referer": f"https://cpquery.cponline.cnipa.gov.cn/detail/index?zhuanlisqh={encrypt_param}&anjianbh",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": self.ua,
    "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "userType": "USER_RZ_ZIRANREN",
        }
        url = "https://cpquery.cponline.cnipa.gov.cn/api/view/gn/scxx"
        data = {
            "zhuanlisqh": zhuanlisqh,
            "nodeId": "aj_gk_scxx",
            "anjianbh": None
        }
        cookies = self.get_cookies()
        code_401_count = 0
        while True:
            try:
                if code_401_count >= 10:
                    self.access_token = self.browser.run_js("return localStorage.ACCESS_TOKEN")
                    headers["Authorization"] = "Bearer " + self.access_token
                    code_401_count = 0
                response = requests.post(url, headers=headers,cookies=cookies, data=json.dumps(data, separators=(',', ':')),timeout=20)
                print("scxx",response)
                if response.status_code == 401:
                    code_401_count += 1
                if response.status_code != 200:
                    cookies = self.get_cookies()
                    continue
                break
            except Exception as e:
                print("error:",str(e))
        return response.json()

    def get_tzs(self,zhuanlisqh):
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Authorization": "Bearer " + self.access_token,
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://cpquery.cponline.cnipa.gov.cn",
            "Referer": "https://cpquery.cponline.cnipa.gov.cn/detail/index?zhuanlisqh=Jgo%2BEM66xoh0Cy5SGswg7Q%3D%3D&anjianbh",
            "userType": "USER_RZ_ZIRANREN",
            "User-Agent":self.ua
        }
        url = "https://cpquery.cponline.cnipa.gov.cn/api/view/gn/scxx/tzs"
        data = {"zhuanlisqh":zhuanlisqh,"nodeId":"aj_gk_scxx_tzs"}
        cookies = self.get_cookies()
        code_401_count = 0
        while True:
            try:
                if code_401_count >= 10:
                    self.access_token = self.browser.run_js("return localStorage.ACCESS_TOKEN")
                    headers["Authorization"] = "Bearer " + self.access_token
                    code_401_count = 0
                    # self.login()
                response = requests.post(url, headers=headers,cookies=cookies, data=json.dumps(data, separators=(',', ':')),timeout=20)
                print("tzs",response)
                if response.status_code == 401:
                    code_401_count += 1
                if response.status_code != 200:
                    cookies = self.get_cookies()
                    continue
                break
            except Exception as e:
                print("error:",str(e))
        return response.json()

    def get_fileinfo(self,zhuanlisqh,rid,wenjiandm):
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Authorization": "Bearer " + self.access_token,
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://cpquery.cponline.cnipa.gov.cn",
            "Referer": "https://cpquery.cponline.cnipa.gov.cn/detail/index?zhuanlisqh=Jgo%2BEM66xoh0Cy5SGswg7Q%3D%3D&anjianbh",
            "userType": "USER_RZ_ZIRANREN",
            "User-Agent":self.ua
        }
        url = "https://cpquery.cponline.cnipa.gov.cn/api/view/gn/fetch-file-infos"
        data = {"zhuanlisqh":zhuanlisqh,"rid":rid,"ds":"TZS","wenjiandm":wenjiandm}
        cookies = self.get_cookies()
        code_401_count = 0
        while True:
            try:
                if code_401_count >= 10:
                    self.access_token = self.browser.run_js("return localStorage.ACCESS_TOKEN")
                    headers["Authorization"] = "Bearer " + self.access_token
                    code_401_count = 0
                response = requests.post(url, headers=headers,cookies=cookies, data=json.dumps(data, separators=(',', ':')),timeout=20)
                print("fileinfo",response)
                if response.status_code == 401:
                    code_401_count += 1
                if response.status_code != 200:
                    cookies = self.get_cookies()
                    continue
                response.json()["data"]
                break
            except Exception as e:
                print("error:",str(e))
        return response.json()

        
        
    def get_cookies(self):
        if "https://tysf.cponline.cnipa.gov.cn/am/#/user/login" == self.browser.url:
            self.login()
        self.browser.listen.start(self.browser.url)
        self.browser.refresh()
        
        # time.sleep(2.5)
        if "https://cpquery.cponline.cnipa.gov.cn/chinesepatent/index" == self.browser.url:
            tree = etree.HTML(self.browser.html)
            if len(tree.xpath('//span[contains(text(),"确定")]')) != 0:
                self.browser.ele('xpath://span[contains(text(),"确定")]').click()
            time.sleep(2)
            self.browser.get(self.url)
        res = self.browser.listen.wait(timeout=10)
        _cookies = self.browser.cookies()
        cookies = {}
        for _cookie in _cookies:
            key = _cookie["name"]
            value = _cookie["value"]
            cookies[key] = value
        return cookies

    def main(self):
        df = pd.read_csv("./after_2010.csv",encoding="utf-8")[1000000:1050000]
        keyword_nos = df["ida"].values.tolist()
        records = pd.read_csv("./after_2010.csv",encoding="utf-8").to_dict(orient="records")
        self.browser = browser = ChromiumPage(10)
        browser.get("https://tysf.cponline.cnipa.gov.cn/am/#/user/login")
        self.login()
        
        error_fp = open("./cnipa/error/error.txt","a",encoding="utf-8")
        # latest_file, latest_time = self.get_latest_modified_file("./cnipa/pdf")
        # self.access_token = browser.run_js("return localStorage.ACCESS_TOKEN")

        for record_index,record in enumerate(records):
            print("第",record_index,"个:",record)
            # if  record_index < _index:
            #     continue
            # record["ida"] = "201010121746X"
            keyword_no = record["ida"]
            if os.path.exists(f"./cnipa/pdf/CN{keyword_no}_第一次.pdf") or os.path.exists(f"./cnipa/error_pdf/CN{keyword_no}.pdf"):
                continue
       
            response = {
                "data":{
                    "records":[{"zhuanlisqh":record["ida"]}]
                }
            }
            for _record in response["data"]["records"]:
                encrypt_param = quote(self.encrypt(_record["zhuanlisqh"]))
                # https://cpquery.cponline.cnipa.gov.cn/detail/index?zhuanlisqh=Jgo%252BEM66xoh0Cy5SGswg7Q%253D%253D&anjianbh
                self.url = f"https://cpquery.cponline.cnipa.gov.cn/detail/index?zhuanlisqh={encrypt_param}&anjianbh"
                browser.get(self.url)
                self.access_token = browser.run_js("return localStorage.ACCESS_TOKEN")
                # 
                while self.access_token == "null":
                    if "https://cpquery.cponline.cnipa.gov.cn/chinesepatent/index" == self.browser.url:
                        try:
                            self.browser.ele('xpath://span[contains(text(),"确定")]').click()
                            self.access_token = browser.run_js("return localStorage.ACCESS_TOKEN")
                        except Exception as e:
                            print("error:",str(e))
                self.ua = browser.run_js("return navigator.userAgent")
                refresh_count = 0
                error_count = 0
                status = "审查信息"
                
                scxx_response = json.dumps(self.get_scxx(_record["zhuanlisqh"],encrypt_param),ensure_ascii=False)
                print("审查信息")
                if "通知书" not in scxx_response:
                    with open(f"./cnipa/error_pdf/CN{keyword_no}.pdf","w",) as fp:
                        fp.write("")
                    continue
                tzs_response = self.get_tzs(_record["zhuanlisqh"])
                print("通知书")
                if "审查意见通知书" not in json.dumps(tzs_response,ensure_ascii=False):
                    with open(f"./cnipa/error_pdf/CN{keyword_no}.pdf","w",) as fp:
                        fp.write("")
                    continue
                            
                if refresh_count >= 5:
                    error_fp.write(str(_record["zhuanlisqh"]) + "\n")
                    error_fp.flush()
                    continue
                if error_count >= 2:
                    with open(f"./cnipa/error_pdf/CN{keyword_no}.pdf","w",) as fp:
                        fp.write("")
                    continue
                # res = browser.listen.wait()
                count = 1
                for tzs in tzs_response["data"]:
                    if "审查意见通知书" not in  tzs["name"]:
                        continue
                    _response = self.get_fileinfo(_record["zhuanlisqh"],tzs["additionalData"]["rid"],tzs["additionalData"]["wenjiandm"])
                    cookies = self.get_cookies()
                    print(_response)
                    if _response["data"]["wenjianhzm"] == "pdf":
                        for index,item in enumerate(_response["data"]["ossLujingList"]):
                            pdf_url = f"https://cpquery.cponline.cnipa.gov.cn/api/pcshoss/view/fetch-file?osslujing={item['osslujing']}&wenjianhzm={_response['data']['wenjianhzm']}&timestamp={item['timestamp']}&sign={item['sign']}&isDN={item['isDN']}&ds={_response['data']['ds']}&wenjiandm={_response['data']['wenjiandm']}"
                            while True:
                                try:
                                    pdf_response = requests.get(pdf_url,headers=self.headers,cookies=cookies,timeout=40)
                                    if pdf_response.status_code != 200:
                                        cookies = self.get_cookies()
                                        continue
                                    content = pdf_response.content
                                    break
                                except:
                                    pass
                            _date = tzs["name"].split()[0]
                            _name = tzs["name"].split()[-1].replace("审查意见通知书", "")
                            if "第N次" in _name:
                                output_pdf = f"./cnipa/pdf/CN{keyword_no}_{_name}_{_date}.pdf"  # 输出的 PDF 文件名
                            else:
                                output_pdf = f"./cnipa/pdf/CN{keyword_no}_{_name}.pdf"  # 输出的 PDF 文件名
                            with open(output_pdf,"wb") as fp:
                                fp.write(content)  
                            
                        
                    else:
                        image_files = []
                        img_error_count = 0
                        for index,item in enumerate(_response["data"]["ossLujingList"]):
                            print(f"正在采集第{index + 1}个pdf图片","总共",len(_response["data"]["ossLujingList"]),"个...")
                            img_url = f"https://cpquery.cponline.cnipa.gov.cn/api/pcshoss/view/fetch-file?osslujing={item['osslujing']}&wenjianhzm={_response['data']['wenjianhzm']}&timestamp={item['timestamp']}&sign={item['sign']}&isDN={item['isDN']}&ds={_response['data']['ds']}&wenjiandm={_response['data']['wenjiandm']}"
                            while True:
                                try:
                                    if img_error_count >= 5:
                                        break
                                    img_response = requests.get(img_url,headers=self.headers,cookies=cookies,timeout=30)
                                    if img_response.status_code != 200:
                                        cookies = self.get_cookies()
                                        continue
                                    if len(img_response.content) != 0:
                                        content = img_response.content
                                        break
                                    else:
                                        img_error_count += 1
                                except:
                                    pass
                            if img_error_count >= 5:
                                break
                            with open("./cnipa/img/" + str(index) + ".jpg","wb") as fp:
                                fp.write(content)  
                            image_files.append("./cnipa/img/" + str(index) + ".jpg")     
                        if img_error_count >= 5:
                            error_fp.write(str(_record["zhuanlisqh"]) + "\n")
                            error_fp.flush()
                            continue
                        _date = tzs["name"].split()[0]
                        _name = tzs["name"].split()[-1].replace("审查意见通知书", "")
                        if "第N次" in _name:
                            output_pdf = f"./cnipa/pdf/CN{keyword_no}_{_name}_{_date}.pdf"  # 输出的 PDF 文件名
                        else:
                            output_pdf = f"./cnipa/pdf/CN{keyword_no}_{_name}.pdf"  # 输出的 PDF 文件名
                        
                        images = [Image.open(image).convert('RGB') for image in image_files]  # 将所有图片转换为 RGB 模式

                        # 保存为 PDF
                        images[0].save(output_pdf, save_all=True, append_images=images[1:])
        browser.close()



def shop_login_main():
    Crawl().main()

if __name__ == '__main__':
    Crawl().main()
