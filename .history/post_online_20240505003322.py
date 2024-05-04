import requests

url = 'http://127.0.0.1:5000/submit'  # Flask应用的URL
files = {'file': ('Upload_test_file.txt', open('Upload_test_file.txt', 'rb'), 'text/plain')}  # 要上传的文件

response = requests.post(url, files=files)  # 发送POST请求

print(response.text)  # 打印服务器响应的内容
