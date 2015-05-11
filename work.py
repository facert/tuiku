# -*- coding: utf-8 -*-
import os
import html2text
import re
from zhihu import Question
from zhihu import Answer
from zhihu import User
from zhihu import Collection
import requests
import shutil
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import redis


def get_redis():
    redis_conf = {
        'host': '127.0.0.1',
        'port': 6379,
        'db': 0
    }

    pool = redis.ConnectionPool(host=redis_conf['host'], port=redis_conf['port'], db=redis_conf['db'])
    return redis.StrictRedis(connection_pool=pool)


class ZhihuToMobi(object):

    def __init__(self, question_id):
        self.question_id = question_id
        self.question_path = None
        self.mobi_path = None

    def question(self, url):

        question = Question(url)

        # 获取该问题的标题
        title = question.get_title()
        # 获取该问题的详细描述
        detail = question.get_detail()
        # 获取回答个数
        answers_num = question.get_answers_num()
        # 获取关注该问题的人数
        followers_num = question.get_followers_num()
        # 获取该问题所属话题
        topics = question.get_topics()
        # 获取排名第一的回答
        # top_answer = question.get_top_answer()
        # 获取排名前十的十个回答
        top_answers = question.get_top_i_answers(10)
        # 获取所有回答
        # answers = question.get_all_answers()

        # print title # 输出：现实可以有多美好？
        # print detail 
        # # 输出：
        # # 本问题相对于“现实可以多残酷？传送门：现实可以有多残酷？
        # # 题主：       昨天看了“现实可以有多残酷“。感觉不太好，所以我
        # # 开了这个问题以相对应，希望能够“中和一下“。和那个问题题主不想
        # # 把它变成“比惨大会“一样，我也不想把这个变成“鸡汤故事会“，或者
        # # 是“晒幸福“比赛。所以大家从“现实，实际”的角度出发，讲述自己的
        # # 美好故事，让大家看看社会的冷和暖，能更加辨证地看待世界，是此
        # # 题和彼题共同的“心愿“吧。
        # print answers_num # 输出：2441
        # print followers_num # 输出：26910
        # for topic in topics:
        #     print topic , # 输出：情感克制 现实 社会 个人经历
        # print top_answer # 输出：<zhihu.Answer instance at 0x7f8b6582d0e0>（Answer类对象）
        # print top_answers # 输出：<generator object get_top_i_answers at 0x7fed676eb320>（代表前十的Answer的生成器）
        # print answers # 输出：<generator object get_all_answer at 0x7f8b66ba30a0>（代表所有Answer的生成器）
        return title, detail, answers_num, followers_num, topics, top_answers

    def answer_to_md(self, answer):
        content = answer.get_content()
        text = html2text.html2text(content.decode('utf-8')).encode("utf-8")
        r = re.findall(r'\*\*(.*?)\*\*', text)
        for i in r:
            if i != " ":
                text = text.replace(i, i.strip())

        r = re.findall(r'_(.*)_', text)
        for i in r:
            if i != " ":
                text = text.replace(i, i.strip())

        r =re.findall(r'!\[\]\((?:.*?)\)', text)
        for i in r:
            text = text.replace(i, i + "\n\n")

        p = re.compile(r'(http:\/\/.*\.zhimg\.com)/(.*)\)')
        r = p.findall(text)
        # r = re.findall(r"(http:\/\/.*\.zhimg\.com)/.*", text)

        def func(m):
            # import pdb;pdb.set_trace()
            url = m.group(1)+"/"+m.group(2)
            r = requests.get(url, stream=True)

            path = os.path.join(os.getcwd(), "images")+"/"+m.group(2)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)    
            return os.path.join(os.getcwd(), "images") +"/"+m.group(2)+")"

        text = p.sub(func, text)
        # for i in r:
        #     import pdb;pdb.set_trace()
        #     text = p.sub()
        #     text = text.replace(i, "./image")
        return text

    def question_to_md(self, url):
        self.title, detail, answers_num, followers_num, topics, top_answers = self.question(url)
        self.question_path = os.path.join(os.path.join(os.getcwd(), "questions"), self.question_id+".md")
        self.mobi_path = os.path.join(os.path.join(os.getcwd(), "mobis"), self.question_id+".mobi")
        f = open(self.question_path, "a")
        f.write("\n")
        f.write("# " + self.title + "\n")
        f.write("## "+ detail + "\n")
        f.write("### 回答数: " + str(answers_num) +" 关注数: "+ str(followers_num)+"\n")
        f.write("——————————————————————————————————————————\n")
        for answer in top_answers:
            f.write("## 作者: " + answer.get_author().get_user_id() + "  赞同: " + str(answer.get_upvote()) + "\n")
            text = self.answer_to_md(answer)
            print text
            f.write(text)
            f.write("#### 原链接: " + answer.answer_url+"\n")
        f.close()

    def md_to_mobi(self):
        question_path = self.question_path
        mobi_path = self.mobi_path
        command1 = "ebook-convert %s %s  --markdown-extensions  --output-profile=kindle_pw --mobi-file-type=old \
            --mobi-ignore-margins --mobi-keep-original-images --no-inline-toc --remove-paragraph-spacing" % (question_path, mobi_path)
        ret1 = subprocess.call(command1, shell=True)
        title = self.title.replace(" ", "")
        command2 = "ebook-meta %s --authors zhihu --title %s " % (mobi_path, title)
        ret2 = subprocess.call(command2, shell=True)
        if ret1 != 0 and ret2 != 0:
            raise Exception("[%s] execute failed." % command1)
        else:
            return self.mobi_path


class MailToKindle(object):

    def __init__(self, mobi_path, email):
        self.mobi_path = mobi_path
        self.email = email

    def send_mail(self):
        #创建一个带附件的实例
        msg = MIMEMultipart()

        #构造附件1
        att1 = MIMEText(open(self.mobi_path, 'rb').read(), 'base64', 'utf-8')
        att1["Content-Type"] = 'application/octet-stream'
        att1["Content-Disposition"] = 'attachment; filename="%s"' % self.mobi_path.split("/")[-1] #这里的filename可以任意写，写什么名字，邮件中显示什么名字
        msg.attach(att1)

        #加邮件头
        msg['to'] = self.email
        msg['from'] = 'zhangcr1992@126.com'
        msg['subject'] = 'kindle'
        #发送邮件
        try:
            server = smtplib.SMTP()
            server.connect('smtp.126.com')
            server.login('zhangcr1992','zxc123')#XXX为用户名，XXXXX为密码
            server.sendmail(msg['from'], msg['to'],msg.as_string())
            server.quit()
            print '发送成功'
        except Exception, e:  
            print str(e) 



def generate(url=None, email=None):
    if not url: 
        url = "http://www.zhihu.com/question/22896560"
    if not email:
        email = "zhangcr1992@kindle.cn"
    question_id = url.split("/")[-1]
    zm = ZhihuToMobi(question_id)
    zm.question_to_md(url)
    mobi_path = zm.md_to_mobi()
    mk = MailToKindle(mobi_path, email)
    mk.send_mail()


# def answer_test(answer_url):

#     answer = Answer(answer_url)
#     # 获取该答案回答的问题
#     question = answer.get_question()
#     # 获取该答案的作者
#     author = answer.get_author()
#     # 获取该答案获得的赞同数
#     upvote = answer.get_upvote()
#     # 把答案输出为txt文件
#     answer.to_txt()
#     # 把答案输出为markdown文件
#     answer.to_md()

#     print question 
#     # <zhihu.Question instance at 0x7f0b25d13f80>
#     # 一个Question对象
#     print question.get_title() # 输出：现实可以有多美好？
#     print author 
#     # <zhihu.User instance at 0x7f0b25425b90>
#     # 一个User对象
#     print author.get_user_id() # 输出：田浩
#     print upvote # 输出：9320


# def user_test(user_url):

#     user = User(user_url)
#     # 获取用户ID
#     user_id = user.get_user_id()
#     # 获取该用户的关注者人数
#     followers_num = user.get_followers_num()
#     # 获取该用户关注的人数
#     followees_num =user.get_followees_num()
#     # 获取该用户提问的个数
#     asks_num = user.get_asks_num()
#     # 获取该用户回答的个数
#     answers_num = user.get_answers_num()
#     # 获取该用户收藏夹个数
#     collections_num = user.get_collections_num()
#     # 获取该用户获得的赞同数
#     agree_num = user.get_agree_num()
#     # 获取该用户获得的感谢数
#     thanks_num = user.get_thanks_num()

#     # 获取该用户关注的人
#     followees = user.get_followees()
#     # 获取关注该用户的人
#     followers = user.get_followers()
#     # 获取该用户提的问题
#     asks = user.get_asks()
#     # 获取该用户回答的问题的答案
#     answers = user.get_answers()
#     # 获取该用户的收藏夹
#     collections = user.get_collections()

#     print user_id # 黄继新
#     print followers_num # 614840
#     print followees_num # 8408
#     print asks_num # 1323
#     print answers_num # 786
#     print collections_num # 44
#     print agree_num # 46387
#     print thanks_num # 11477

#     print followees
#     # <generator object get_followee at 0x7ffcac3af050>
#     # 代表所有该用户关注的人的生成器对象
#     i = 0
#     for followee in followees:
#         print followee.get_user_id()
#         i = i + 1
#         if i == 41:
#             break

#     print followers
#     # <generator object get_follower at 0x7ffcac3af0f0>
#     # 代表所有关注该用户的人的生成器对象
#     i = 0
#     for follower in followers:
#         print follower.get_user_id()
#         i = i + 1
#         if i == 41:
#             break

#     print asks
#     # <generator object get_ask at 0x7ffcab9db780>
#     # 代表该用户提的所有问题的生成器对象
#     print answers
#     # <generator object get_answer at 0x7ffcab9db7d0>
#     # 代表该用户回答的所有问题的答案的生成器对象
#     print collections
#     # <generator object get_collection at 0x7ffcab9db820>
#     # 代表该用户收藏夹的生成器对象


# def collection_test(collection_url):

#     collection = Collection(collection_url)

#     # 获取该收藏夹的创建者
#     creator = collection.get_creator()
#     # 获取该收藏夹的名字
#     name = collection.get_name()
#     # 获取该收藏夹下的前十个答案
#     top_answers = collection.get_top_i_answers(10)
#     # 获取该收藏夹下的所有答案
#     answers = collection.get_all_answers()

#     print creator 
#     # <zhihu.User instance at 0x7fe1296f29e0>
#     # 一个User对象
#     print creator.get_user_id() # 稷黍
#     print name # 给你一个不同的视角
#     print top_answers
#     # <generator object get_top_i_answers at 0x7f378465dc80>
#     # 代表前十个答案的生成器对象
#     print answers 
#     # <generator object get_all_answer at 0x7fe12a29b280>
#     # 代表所有答案的生成器对象

# def test():
#     url = "http://www.zhihu.com/question/24269892"
#     question = Question(url)
#     # 得到排名第一的答案
#     answer = question.get_top_answer()
#     # 得到排名第一的答案的作者
#     user = answer.get_author()
#     # 得到该作者回答过的所有问题的答案
#     user_answers = user.get_answers()
#     # 输出该作者回答过的所有问题的标题
#     for answer in user_answers:
#         print answer.get_question().get_title()
#     # 得到该用户的所有收藏夹
#     user_collections = user.get_collections()
#     for collection in user_collections:
#         # 输出每一个收藏夹的名字
#         print collection.get_name()
#         # 得到该收藏夹下的前十个回答
#         top_answers = collection.get_top_i_answers(10)
#         # 把答案内容转成txt，markdown
#         for answer in top_answers:
#             answer.to_txt()
#             answer.to_md()

if __name__ == '__main__':
    redis = get_redis()
    while True:
        
        data = redis.brpop("kindle")
        if data:
            address = data[1].split(";")[0]
            email = data[1].split(";")[1]
            generate(address, email)
