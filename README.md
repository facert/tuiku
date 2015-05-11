# tuiku
将知乎问答转换成电子书推送到kindle的web服务

1.  web 服务基于 flask, mongodb, redis
2.  其中 zhihu.py 参考 https://github.com/egrcc/zhihu-python 

INSTALL

1. 安装 python 库

          pip install flask pymongo redis

2. 安装 calibre: http://calibre-ebook.com/

3. 将 config.ini 中的 email 和 password 换成 自己的 知乎账号和密码

RUN

        python manage.py runserver   
  访问： http://0.0.0.0:8080/
