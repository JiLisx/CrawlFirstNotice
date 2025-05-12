import json
from DrissionPage import ChromiumPage,ChromiumOptions
import os
import time
import ddddocr
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

#   2025/02/14 15:49


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
    
    
    def login(self,browser):
        try:
            if 'https://cpquery.cponline.cnipa.gov.cn/chinesepatent/index' == "":
                browser.ele('xpath://span[contains(text(),"确定")]').click()
            browser.ele('xpath://input[@placeholder="手机号/证件号码"]').input("")
            browser.ele('xpath://input[@placeholder="请输入密码"]').input("")
            browser.ele('xpath://button[@class="el-button login-btn el-button--default el-button--medium"]').click()
            while "verify-img-panel" in browser.html:
                time.sleep(2)
                bg_src = browser.ele('xpath://div[@class="verify-img-panel"]/img').attr("src").replace("data:image/png;base64,", "")
                slice_src = browser.ele('xpath://div[@class="verify-sub-block"]/img').attr("src").replace("data:image/png;base64,", "")
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
                browser.actions.hold('.verify-move-block')
                browser.actions.move(offset_x=distance + 50, duration=.1)
                browser.actions.release('.verify-move-block')
                time.sleep(2)
            browser.get("https://cpquery.cponline.cnipa.gov.cn/chinesepatent/index")
            time.sleep(2)
            browser.ele('xpath://span[contains(text(),"确定")]').click()
            time.sleep(2)
            # print()
            # time.sleep(10000)
        except Exception as e:
            pass

    def main(self):
        records = pd.read_csv("./after_2010.csv",encoding="utf-8").to_dict(orient="records")[30001:]
        browser = ChromiumPage(5001)
        browser.get("https://tysf.cponline.cnipa.gov.cn/am/#/user/login")
        self.login(browser)
        
        error_fp = open("./cnipa/error/error.txt","a",encoding="utf-8")
        # latest_file, latest_time = self.get_latest_modified_file("./cnipa/pdf")

        # if latest_file:
        #     print(f"Latest modified file: {latest_file}")
        #     print(f"Last modified time: {latest_time}")
        #     _index = keyword_nos.index(latest_file.replace("CN", "").replace(".pdf", ""))
        # else:
        #     print("No files found in the folder.")
        #     _index = 0
        for record_index,record in enumerate(records):
            print("第",record_index,"个:",record)
            # if  record_index < _index:
            #     continue
            keyword_no = record["ida"]
            if os.path.exists(f"./cnipa/pdf/CN{keyword_no}.pdf") or os.path.exists(f"./cnipa/error_pdf/CN{keyword_no}.pdf"):
                continue
            # browser.get("https://cpquery.cponline.cnipa.gov.cn/chinesepatent/index")
            # _cookies = browser.cookies()
            # cookies = {}
            # for _cookie in _cookies:
            #     key = _cookie["name"]
            #     value = _cookie["value"]
            #     cookies[key] = value
            # browser.listen.start("/api/search/undomestic/publicSearch")
            
            # browser.ele('xpath://input[@placeholder="例如: 2010101995057"]').input(keyword_no)
            # try:
            #     browser.ele('xpath://button[@class="q-btn q-btn-item non-selectable no-outline q-mx-xs q-btn--standard q-btn--rectangle bg-primary text-white q-btn--actionable q-focusable q-hoverable q-btn--wrap"]').click()
            
            #     res = browser.listen.wait(timeout=5)
            #     response = json.loads(res._raw_body)
            # except Exception as e:
            #     print("error:",str(e))
            response = {
                "data":{
                    "records":[{"zhuanlisqh":record["ida"]}]
                }
            }
            for _record in response["data"]["records"]:
                encrypt_param = quote(self.encrypt(_record["zhuanlisqh"]))
                # https://cpquery.cponline.cnipa.gov.cn/detail/index?zhuanlisqh=Jgo%252BEM66xoh0Cy5SGswg7Q%253D%253D&anjianbh
                browser.get(f"https://cpquery.cponline.cnipa.gov.cn/detail/index?zhuanlisqh={encrypt_param}&anjianbh")
                
                
                refresh_count = 0
                error_count = 0
                status = "审查信息"
                
                while True:
                    try:
                        if "verify-img-panel" in browser.html or "确定" in browser.html:
                            self.login(browser)
                            browser.get(f"https://cpquery.cponline.cnipa.gov.cn/detail/index?zhuanlisqh={encrypt_param}&anjianbh")
                        if refresh_count >= 5:
                            break
                        #     # self.login(browser)
                        #     # print("重新登录...")
                        #     refresh_count = 0
                        if error_count >= 2:
                            break
                        if status == "审查信息":
                            browser.listen.start("/api/view/gn/scxx")
                        # status = "审查信息"
                        browser.ele('xpath://span[@class="custom-tree-node"]//span[contains(text(),"审查信息")]',timeout=5).click()
                        if status == "审查信息":
                            res = browser.listen.wait(timeout=10)
                            sc_response = res._raw_body
                            if "url" in sc_response and "/api/view/gn/scxx/tzs" in sc_response:
                                browser.listen.start("/api/view/gn/scxx/tzs")
                                status = "通知书"
                            else:
                                error_count = 2
                        
                        print("审查信息")
                        browser.ele("xpath://span[@class='custom-tree-node']//span[contains(text(),'通知书')]",timeout=5).click()
                        print("点击通知书")
                        if status == "通知书":
                            res = browser.listen.wait(timeout=10)
                            tzs_response = res._raw_body
                            if "url" in tzs_response and "第一次审查意见通知书" in tzs_response:
                                status = "第一次审查意见通知书"
                                browser.listen.start("/api/view/gn/fetch-file-infos")
                            else:
                                error_count = 2
                        browser.ele("xpath://span[@class='custom-tree-node']//span[contains(text(),'第一次审查意见通知书')]",timeout=5).click()
                        browser.ele("xpath://span[@class='custom-tree-node']//span[contains(text(),'第一次审查意见通知书')]",timeout=5).click()
                        print("点击第一次审查意见通知书")
                        if status == "第一次审查意见通知书":
                            res = browser.listen.wait(timeout=10)
                            _response = json.loads(res._raw_body)
                            _response["data"]["ossLujingList"]
                            break
                    except Exception as e:
                        print("error:",str(e),status)
                        # if ("第一次审查意见通知书" in str(e) and "第一次审查意见通知书" not in browser.html):
                        #     error_count += 1
                        if "第一次审查意见通知书" == status and '_raw_body' in str(e):
                            browser.refresh()
                            refresh_count += 1
                            time.sleep(5)
                            
                if refresh_count >= 5:
                    error_fp.write(str(_record["zhuanlisqh"]) + "\n")
                    error_fp.flush()
                    continue
                if error_count >= 2:
                    with open(f"./cnipa/error_pdf/CN{keyword_no}.pdf","w",) as fp:
                        fp.write("")
                    continue
                # res = browser.listen.wait()
                _cookies = browser.cookies()
                cookies = {}
                for _cookie in _cookies:
                    key = _cookie["name"]
                    value = _cookie["value"]
                    cookies[key] = value
                _response = json.loads(res._raw_body)
                print(_response)
                if _response["data"]["wenjianhzm"] == "pdf":
                    for index,item in enumerate(_response["data"]["ossLujingList"]):
                        pdf_url = f"https://cpquery.cponline.cnipa.gov.cn/api/pcshoss/view/fetch-file?osslujing={item['osslujing']}&wenjianhzm={_response['data']['wenjianhzm']}&timestamp={item['timestamp']}&sign={item['sign']}&isDN={item['isDN']}&ds={_response['data']['ds']}&wenjiandm={_response['data']['wenjiandm']}"
                        while True:
                            try:
                                pdf_response = requests.get(pdf_url,headers=self.headers,cookies=cookies)
                                if pdf_response.status_code != 200:
                                    print("")
                                content = pdf_response.content
                                break
                            except:
                                pass
                        with open(f"./cnipa/pdf/CN{keyword_no}.pdf","wb") as fp:
                            fp.write(content)  
                         
                    
                else:
                    image_files = []
                    img_error_count = 0
                    for index,item in enumerate(_response["data"]["ossLujingList"]):
                        img_url = f"https://cpquery.cponline.cnipa.gov.cn/api/pcshoss/view/fetch-file?osslujing={item['osslujing']}&wenjianhzm={_response['data']['wenjianhzm']}&timestamp={item['timestamp']}&sign={item['sign']}&isDN={item['isDN']}&ds={_response['data']['ds']}&wenjiandm={_response['data']['wenjiandm']}"
                        while True:
                            try:
                                if img_error_count >= 5:
                                    break
                                img_response = requests.get(img_url,headers=self.headers,cookies=cookies)
                                if img_response.status_code != 200:
                                    print("")
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
                    output_pdf = f"./cnipa/pdf/CN{keyword_no}.pdf"  # 输出的 PDF 文件名
                    
                    images = [Image.open(image).convert('RGB') for image in image_files]  # 将所有图片转换为 RGB 模式

                    # 保存为 PDF
                    images[0].save(output_pdf, save_all=True, append_images=images[1:])
        browser.close()



def shop_login_main():
    Crawl().main()

if __name__ == '__main__':
    Crawl().main()
