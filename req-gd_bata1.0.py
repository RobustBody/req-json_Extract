import requests
import pandas as pd
import json
from datetime import datetime
import pytz
import re
import os
import math
import time

# 全局变量
now_timestamp=str(time.time()).split('.')[0]
gdList_file='gdList_file_'+str(now_timestamp)+'.json' #查询到的工单列表数据
gdurl_txt='gdurl_'+str(now_timestamp)+'.txt' #生成的工单详情url，一行一个url
gdxq_data_his='gdxq_data_his_'+str(now_timestamp)+'.json' #记录所有请求到的工单详情json，一行一个
outfile='output_'+str(now_timestamp)+'.csv' # 结果输出文件
gd_count=0 #记录查询列表的总条数

#gd_select_url="http://127.0.0.1:8080/xxx/xx?orderBy=creatorTime&sortRule=ascend&create_time=2023-01-01 00:00:00&create_time=2023-12-30 23:59:59&pageNum=1&pageSize=100&_t=1715588213"

# 工单查询的时间范围，及工单查询的url
start_time="2023-01-01 00:00:00"
end_time="2023-12-30 23:59:59"
base_url="http://127.0.0.1:8080/xxx/xx/?orderBy=creatorTime&sortRule=ascend&create_time="
# 合成查询的url
gd_select_url=base_url+start_time+"&create_time="+end_time+"&pageNum=1&pageSize=100&_t="+str(now_timestamp)

# 粘贴获取到的cookie，http格式，a=123, b=456
cookie_str=" "

# 处理cookie格式为python3 requests格式
cookies = {item.split('=')[0]: item.split('=')[1] for item in cookie_str.split('; ')}

# 自定义请求头的referer和user-agent
headers={
    'Referer':'http://127.0.0.1:8080/xxx/',
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.160 Safari/537.36'
}

# HTTP请求获取工单列表,及请求工单详情,公用方法
def get_json_list(url,cookies,headers):
    response = requests.get(url,cookies=cookies,headers=headers)
    if response.status_code == 200:
        #print(response.text)
        return response.json()
    else:
        print(response)
        return None

# 正则表达式，匹配系统名称从title中
def regex_sysname(s):
    # 匹配直到'系统'或'平台'之前的所有非'|'和非'-'字符
    pattern = r'([^-|]*?)(系统|平台)'
    matches = re.search(pattern, s)
    if matches:
        # 直接返回捕获的组，即'系统'或'平台'之前的部分
        return matches.group(1) + matches.group(2)
    else:
        return None # 如果没有找到匹配项，返回None

# 工单状态转为中文
def gd_status(s):
    #print(s)
    #print(bool(s==3))
    #print(bool(s=='3'))
    if s==1:
        return "待处理"
    if s==2:
        return "处理中"
    if s==3:
        return "已完成"
    if s==7:
        return "已关闭"
    if s==10:
        return "挂起"
    if s==11:
        return "已废除"

'''
1.通过请求获取工单行数，并通过请求获取所有工单列表信息，存入文件中gdList_file.json
'''
def get_gdList_pages(gd_select_url):
    #先获取有多少个工单，再根据页数生成查询url
    jsonlist_data = get_json_list(gd_select_url,cookies,headers)
    global gd_count
    gd_count=jsonlist_data["data"]["count"]
    print("gd_count:"+str(gd_count))
    page_count=math.ceil(gd_count/100)
    print("page_count:"+str(page_count))
    for i in range(1,page_count+1):
        gd_select_url=base_url+start_time+"&create_time="+end_time+"&pageNum="+str(i)+"&pageSize=100&filterType=myPartIn&_t="+str(now_timestamp)
        print("gd_select_url:"+gd_select_url)
        get_gdList_out_file(gd_select_url) #调用方法获取工单列表并存入文件
    print("gdList_file:"+gdList_file)

# 获取工单列表数据，并存到文件中
def get_gdList_out_file(gd_select_url):
    #通过http请求，获取到工单列表的json数据
    jsonlist_data = get_json_list(gd_select_url,cookies,headers)
    filename=gdList_file
 #每行一页数据
    with open(filename,'a',encoding='utf-8') as json_file:
        json_file.write(json.dumps(jsonlist_data,ensure_ascii=False)+"\n")

'''
2.通过读取data.json文件，获取到工单id，生成工单详情URL，存入文件gdurl.txt
'''
def gdx_url(gdList_file):
    filename=gdList_file
    file_line_count=0
    with open(filename,'r',encoding='utf-8') as json_file:
        for line in json_file:
            line=line.strip()
            if not line.strip():
                continue
            jsonlist_data=json.loads(line) # 按行输入json使用loads(),按文件输入使用load()
            gd_list=jsonlist_data["data"]["list"]
            for item in gd_list:
                gdurl=gdurl_txt
                gdxq_url="http://127.0.0.1:8080/xxx/xx/x/"+item["ticketId"]+"\n"
                with open(gdurl,'a',encoding='utf-8') as file:
                    file.write(gdxq_url)
                    file_line_count=file_line_count+1
    print("file_line_count:"+str(file_line_count))
    print("gdurl_txt:"+gdurl_txt)

'''
3.通过读取gdurl.txt文件，循环获取单条工单详情URL，并追加写入gdxq_data_his.json
    并在循环中调用get_field_out_file()方法提取指定字段到csv文件中
'''
def gdxqdata(gdurl_txt):
    gdurl=gdurl_txt
    with open(gdurl,'r',encoding='utf-8') as url_file:
        jsq=0
        for line in url_file:
            line=line.strip()
            if not line.strip():
                continue
            jsq+=1
            print(str(jsq)+"\t\t"+line)
            gdxq_json=get_json_list(line,cookies,headers)
            # 先在此处把所有获取到的工单信息，每行一个存在文件中
            with open(gdxq_data_his,'a',encoding='utf-8') as file:
                file.write(json.dumps(gdxq_json,ensure_ascii=False)+"\n")
            get_field_out_file(gdxq_json)
        print("gd_count-jsq:"+str(gd_count-jsq))

"""
4.通过读取gdxq_data_his.json文件，循环获取单行工单详情json，获取指定字段并写入out_file.csv
"""
def get_field_out_file(gdxq_json):
    new_dict={}
    new_dict['ticketNum']=gdxq_json['data']['ticketNum']
    new_dict['title']=gdxq_json['data']['title']
    utc_time=datetime.fromisoformat(gdxq_json['data']['createTime'].replace("Z","+00:00"))
    beijing_tz=pytz.timezone("Asia/Shanghai")
    beijing_time=utc_time.astimezone(beijing_tz)
    formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    new_dict['createTime']=formatted_time
    new_dict['creatorName']=gdxq_json['data']['creatorName']
    new_dict['updateTimgLong']=datetime.fromtimestamp(gdxq_json['data']['updateTimgLong']/1000)
    new_dict['modelName']=gdxq_json['data']['modelName']
    new_dict['tacheName']=gdxq_json['data']['tacheName']
    new_dict['status']=gd_status(gdxq_json['data']['status'])
    new_dict['month']=beijing_time.strftime("%m")+"月"
    new_dict['系统名称']=regex_sysname(gdxq_json['data']['title'])
    #根据name遍历寻找具体字段
    for form_layout in gdxq_json['data']['formLayoutVos']:
        for field in form_layout['fieldList']:
            if field['name']=="事件描述" or field['name']=="漏洞描述":
                new_dict['事件描述/漏洞描述']=field['defaultValue']
            if field['name']=="分析结论":
                new_dict['分析结论']=field['defaultValue']
            if field['name']=="处置方法":
                new_dict['处置方法']=field['defaultValue']
            new_dict['处理计划']=''
            if field['name']=="处理结果":
                new_dict['处理结果']=field['defaultValue']
            if field['name']=="事后影响确认" or field['name']=="派发说明":
                new_dict['事后影响确认/派发说明']=field['defaultValue']
            if field['name']=="发生环境":
                new_dict['发生环境']=field['defaultValue']
            if field['name']=="事件初步定级" or field['name']=="漏洞定级":
                new_dict['事件初步定级/漏洞定级']=field['defaultValue']
    column_order=['ticketNum','title','creatorName','createTime','updateTimgLong','事件描述/漏洞描述','分析结论','处置方法','处理计划','处理结果','事后影响确认/派发说明','tacheName','status','modelName','month','系统名称','发生环境','事件初步定级/漏洞定级']
    #工单ID	工单标题	建单人	建单时间	关闭时间	工单描述	分析结论	处置方法	处理计划	处理结果	事后影响确认/派发说明	处理状态	工单状态	类型	月份	系统名称	所属环境	漏洞级别
    df=pd.DataFrame(new_dict,columns=column_order,index=[0])
    if not os.path.isfile(outfile):
        header=True
    else:
        header=False
    df.to_csv(outfile,mode='a',header=header,index=False)

# 可单独调用get_field_out_file()方法，从文件中读取多行工单详情json数据，并提取指定字段输出到csv
def loop_gdxqFile(gdxq_data_his):
    filename=gdxq_data_his
    with open(filename,'r',encoding='utf-8') as json_file:
        for line in json_file:
            line=line.strip()
            if not line.strip():
                continue
            gdxq_json=json.loads(line) # 按行输入json使用loads(),按文件输入使用load()
            get_field_out_file(gdxq_json)


def main():
#1.通过请求获取工单行数，并通过请求获取所有工单列表信息，存入文件中gdList_file.json
    #get_gdList_pages(gd_select_url)
#2.通过读取gdList_file.json文件，获取到工单id，生成工单详情URL，存入文件gdurl.txt
    #gdx_url(gdList_file)
    #gdx_url("可指定文件名称")
#3.通过读取gdurl.txt文件，循环获取单条工单详情URL，并追加写入gdxq_data_his.json
    #gdxqdata(gdurl_txt)
    #gdxqdata("可指定文件名称")
#4.通过读取gdxq_data_his.json文件，循环获取单行工单详情json，获取指定字段并写入out_file.csv
    #此步骤通过gdxqdata()方法,在每次工单详情请求后，会直接提取字段并写入csv
    #如需单独调用，可直接调用loop_gdxqFile()，此方法遍历多行工单详情，并获取指定字段写入csv文件
    #loop_gdxqFile("指定文件gdxq_data_his")


if __name__=="__main__":
    main()