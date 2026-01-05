# 舆情项目部署指南

## 1. 安装mysql （通过APT存储库安装）
### 1.1 添加MySQL官方APT存储库
下载并安装MySQL的APT配置包，选择版本后(在图形化界面中选择MySQL 8.4版本)更新源：

```bash
sudo apt update && sudo apt upgrade -y  # 更新系统  
wget https://dev.mysql.com/get/mysql-apt-config_0.8.32-1_all.deb  # 下载MySQL APT配置包  
sudo dpkg -i mysql-apt-config_0.8.32-1_all.deb  # 安装配置包（选择MySQL 8.4版本）  
sudo apt update  # 刷新软件包列表 
```

### 1.2 使用APT安装MySQL
```bash
sudo apt install mysql-server -y  # 安装MySQL服务器  
```
安装过程中会提示设置root密码，如果没有提示则会默认配置为使用auth_socket插件进行认证

### 1.3 启动服务与验证
```bash
sudo systemctl start mysql
sudo systemctl status mysql  # 检查运行状态
```
#### 1.3.1 检查当前认证方式
```bash
sudo mysql -u root -e "SELECT user, host, plugin, authentication_string FROM mysql.user WHERE user='root';"
```
如果plugin列显示为auth_socket，则修改root认证插件并设置密码
进入MySQL命令行
```bash
sudo mysql
```
进入MySQL命令行后，依次执行以下SQL语句（请将your_new_strong_password替换为你想要设置的实际密码）：
```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_new_strong_password';
FLUSH PRIVILEGES;
EXIT;
```
完成上述设置后，你就可以使用刚设置的密码以常规方式登录了

### 1.4 登录MySQL并修改配置（可选）​
#### 1.4.1 登录MySQL服务器（在服务器上执行）
```bash
mysql -uroot -p  # 输入密码
```
#### 1.4.2 检查当前允许连接的Host
```sql
SELECT Host, User FROM mysql.user;
```
如果 root 用户的 Host 只有 localhost，则需要添加远程访问权限。
#### 1.4.3 允许特定IP远程访问（推荐）​
-- 允许 100.100.100.100 访问（替换为你的客户端IP）
```sql
CREATE USER 'root'@'192.168.171.1' IDENTIFIED BY 'root';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'192.168.171.1' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```
### 1.5 设置网络监听
#### 1.5.1 修改MySQL配置文件
```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```
在文件中找到 bind-address这一行，默认情况下它很可能是：
bind-address = 127.0.0.1
将其修改为
bind-address = 0.0.0.0           # 监听所有网络接口
修改后，按 Ctrl + O保存，再按 Ctrl + X退出nano。
#### 1.5.2 重启MySQL服务，让配置生效：
```bash
sudo systemctl restart mysql
```
### 1.6 检查防火墙是否放行3306端口
```bash
sudo ufw allow 3306/tcp  # Ubuntu防火墙放行
sudo systemctl restart ufw
```
### 1.7 导入初始表数据 init.sql
#### 1.7.1 图形化工具导入（推荐）
使用任意图形化工具都行。
新建连接，然后选择文件，运行sql文件，选择初始化文件运行即可。
#### 1.7.2 命令行导入
登录数据库：
```bash
mysql -uroot -p  # 输入密码
```
选择数据库：
```sql
USE your_database_name;
```
如果数据库还不存在，你需要先创建它：
```sql
CREATE DATABASE your_database_name;
USE your_database_name;
```
执行导入命令：
```sql
source /path/to/your/init.sql;
```
退出 MySQL 命令行
```sql
exit
```
### 1.8 忘记密码如何修改root密码
首先，修改MySQL的配置文件，使其在启动时不加载权限验证。
```bash
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf
```
在 [mysqld]配置块中，添加下面这行：
skip-grant-tables
:wq 保存并退出编辑器。然后重启MySQL服务使配置生效：
```bash
sudo systemctl restart mysql
```
现在，你可以无需密码直接登录到MySQL服务器：
```bash
mysql -u root
```
设置root用户密码（MySQL 8.0语法）
```sql
use mysql;
UPDATE user SET authentication_string = '', plugin = 'mysql_native_password' WHERE user = 'root' AND host = 'localhost';
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourNewPassword123!';
FLUSH PRIVILEGES;
exit;
```
恢复配置并验证
```bash
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf
```
将 skip-grant-tables 行注释掉（在行首加#）或删除
再次重启MySQL服务：
```bash
sudo systemctl restart mysql
```
你就可以使用新设置的密码以root用户正常登录了：
```bash
mysql -u root -p
```
## 2. 安装Nginx
### 2.1 安装
```bash
sudo apt install nginx -y
```
### 2.2 启动并设置开机自启
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
```
### 2.3 验证安装
```bash
sudo systemctl status nginx
```
### 2.4  防火墙配置（若启用）
允许 HTTP/HTTPS
```bash
sudo ufw allow 'Nginx Full'  # 或单独允许 HTTP/HTTPS
sudo ufw enable
```
### 2.5 上传前端文件至服务器
#### 2.5.1 将client文件夹上传至/home/username/文件夹下
#### 2.5.2 修改目录权限
```bash
sudo chmod o+x /home/username
```
### 2.6 编辑Nginx的配置文件nginx.conf
```conf
server {
    listen 80;
    server_name yourdomain.com;  # 替换为你的域名或IP地址

    # 前端静态文件服务
    location / {
        root /path/to/your/frontend/files;  # 前端文件目录
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 代理API请求到Flask后端
    location /api/ {
        proxy_pass http://127.0.0.1:5000;  # 确保与Flask运行端口一致
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```
### 2.7 修改目录权限
```bash
sudo chown -R 用户名:用户名 /etc/nginx/conf.d
```
### 2.8 上传nginx.conf至服务器/etc/nginx/conf.d目录
### 2.9 重启nginx服务器
```bash
sudo systemctl restart nginx
```
## 3. 安装运行python后台
### 3.1 查看python版本（>=3.10)
```bash
python3 --version
```
### 3.2 安装python（如有必要）
```bash
sudo apt update
sudo apt install python3  # 安装 Python3
sudo apt install python3-pip  # 安装 pip
sudo apt install python3-venv -y  # 安装 venv 模块
```
### 3.3 创建激活虚拟环境
```bash
python3 -m venv ~/myenv  # 创建名为 myenv 的虚拟环境
source myenv/bin/activate  # 激活虚拟环境
```
激活后，终端提示符前会显示 (myenv)
### 3.4 拷贝项目至用户目录，然后运行命令
```bash
pip install -r /path/to/requirements.txt
```
安装依赖包
### 3.5 测试项目应用
```bash
cd /home/~ #项目目录
python3 app.py  # 或你的主文件名称
```
如果正常运行，则使用以下命令运行
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
### 3.6 查看正在运行的Gunicorn进程
```bash
pgrep -a gunicorn
```
### 3.7 终止Gunicorn进程
```bash
pkill gunicorn
```