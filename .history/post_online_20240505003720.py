import requests

url = 'https://1mocat.github.io/'  # Flask应用的URL
files = {'file': ('Upload_test_file.txt', open('Upload_test_file.txt', 'rb'), 'text/plain')}  # 要上传的文件
data = {'name': 'maoren', 'email': 'maoren@example.com'}  # 其他表单数据

response = requests.post(url, files=files, data=data)  # 发送POST请求

print(response.text)  # 打印服务器响应的内容
