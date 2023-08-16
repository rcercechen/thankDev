# ThankDev

```

  _         _   _       _____ _                 _      ____             
 | |    ___| |_( )___  |_   _| |__   __ _ _ __ | | __ |  _ \  _____   __
 | |   / _ \ __|// __|   | | | '_ \ / _` | '_ \| |/ / | | | |/ _ \ \ / /
 | |__|  __/ |_  \__ \   | | | | | | (_| | | | |   <  | |_| |  __/\ V / 
 |_____\___|\__| |___/   |_| |_| |_|\__,_|_| |_|_|\_\ |____/ \___| \_/  
                                                                        
```

根据提供的`域名/目标`从Github中搜索开发测试过程中泄漏的`信息, 资产`等, 包括:
* 测试域名, ip
* 人员信息: email, username等
* 可能的影子资产
* 配置信息
* 等

> Create at 2023 hw, hw工具~

> 师傅们留个 🌟🌟🌟 呗~


## Usage

```
usage: main.py [-h] -k KEYWORD -s SESSION [-p PAGE] [-m MIN]

Let's Thank Dev!

options:
  -h, --help            show this help message and exit
  -k KEYWORD, --keyword KEYWORD
                        域名/目标
  -s SESSION, --session SESSION
                        github session
  -p PAGE, --page PAGE  github search page nums
  -m MIN, --min MIN     filter minimum score
```

安装依赖:
```
pip3 install -r requirements.txt
```

首先需要提取出github的`token`才能进行`code`类型的搜索. 只需要cookie中的`user_session`即可.
```
python3 main.py -k pingan.com.cn -s "xxxxx-xxxxx"
```

结果:
* 分数从高到底排序输出
* 在results下保存assets.txt, emails.txt, result.json

> 例子就不贴了,都是马赛克...


### config.yml

在这里可以自己定义一些关键词及其权重, 调整出合适自己的值. 配置项说明:

* extra_keywords: 额外的关键词, 在域名后加上的, 适合自定义
* weights: 自己想要的关键词权重, 自己凭经验调整

> 首次运行时会自动生成, 这个配置不会加入git跟踪文件


### 一些问题

1. 写得比较糙, 很多都是拍脑袋想到的参数...
2. github上搜出来Code列有几千个, 但页数才5页, 目前还不知道怎么回事, 建议增加额外的关键词来获取更多结果

### TODO

- [] 存活探测
- [] 网页截图
- [] 欢迎补充~