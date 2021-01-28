# -*- coding = utf-8 -*-
# @Time : 2021/1/28 9:56
# @Auther : Jefsky
# @File : mix_iamges.py
# @Software : PyCharm
# 文件上传
import base64
import urllib
import json
import requests
import flask, os, sys, time
from flask import request

interface_path = os.path.dirname(__file__)
sys.path.insert(0, interface_path)  # 将当前文件的父目录加入临时系统变量

server = flask.Flask(__name__, static_folder='static')


@server.route('/', methods=['get'])
def index():
    return '<form action="/upload" method="post" enctype="multipart/form-data">上传前景图<input type="file" ' \
           'name="img1">上传背景景图<input type="file" name="img2"><input type="text" name="rate"><button ' \
           'type="submit">上传</button></form> '


@server.route('/upload', methods=['post'])
def upload():
    fname1 = request.files['img1']  # 获取上传的文件
    fname2 = request.files['img2']  # 获取上传的文件
    rate = request.values['rate']
    if fname1 and fname2:
        t = time.strftime('%Y%m%d%H%M%S')
        new_fname1 = r'static/upload_images/' + t + '_' + fname1.filename
        new_fname2 = r'static/upload_images/' + t + '_' + fname2.filename
        outputimage = r'static/combine_images/' + t + '.png'
        fname1.save(new_fname1)  # 保存文件到指定路径
        fname2.save(new_fname2)  # 保存文件到指定路径
        travel_image(new_fname1, new_fname2, outputimage, float(rate))
        src = '<img src=' + outputimage + '><img src='+new_fname1+'>'
        return src
    else:
        return '{"msg": "请上传文件！"}'


def save_base_image(img_str, filename):
    img_data = base64.b64decode(img_str)
    with open(filename, 'wb') as f:
        f.write(img_data)


# 人像分割
# filename:原图片名（本地存储包括路径）；dehazedfilename:处理后的文件保存名称
def body_seg_fore(filename, resultfilename):
    request_url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/body_seg"

    # 二进制方式打开图片文件
    f = open(filename, 'rb')
    img = base64.b64encode(f.read())

    params = {"image": img}
    # params = json.dumps(params).encode('utf-8')

    access_token = '填你的'
    request_url = request_url + "?access_token=" + access_token

    sss = ''
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.post(request_url, data=params, headers=headers)
    if response:
        print(response.json())
        print(type(response.json()))
        sss = response.json()['foreground']
    save_base_image(sss, resultfilename)


# 图片整合
# foreimage：前景照片，baseimage：景区照片,outputimage：数据结果,rate：前景照片缩放比例
def combine_image(foreimage, baseimage, outputimage, rate):
    from PIL import Image
    base_img = Image.open(baseimage)
    BL, BH = base_img.size
    # 读取要粘贴的图片 RGBA模式
    # 当需要将一张有透明部分的图片粘贴到一张底片上时，如果用Python处理，可能会用到PIL，
    # 但是PIL中 有说明，在粘贴RGBA模式的图片是，alpha通道不会被帖上，也就是不会有透明的效果，
    # 当然也给出了解决方法，就是粘贴的时候，将RGBA的的alpha通道提取出来做为mask传入。
    fore_image = Image.open(foreimage)
    L, H = fore_image.size
    # 缩放
    fore_image = fore_image.resize((int(L * rate), int(H * rate)))
    L, H = fore_image.size
    # 分离通道
    r, g, b, a = fore_image.split()  # 粘贴

    box = (int(BL / 2 - L / 2), BH - H, int(BL / 2 + L / 2), BH)

    base_img.paste(fore_image, box, mask=a)
    base_img.save(outputimage)  # 保存图片


# 输出程序
def travel_image(originimage, baseimage, outputimage, rate):
    body_seg_fore(originimage, originimage)
    combine_image(originimage, baseimage, outputimage, rate)


server.run(port=8000)
