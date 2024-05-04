import requests

url = 'https://1mocat.github.io/' 
files = {'file': ('Upload_test_file.txt', open('Upload_test_file.txt', 'rb'), 'text/plain')}  # 要上传的文件

response = requests.post(url, files=files) 
