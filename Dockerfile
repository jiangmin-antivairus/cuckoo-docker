FROM ubuntu:18.04
LABEL maintainer="jiangmin xuruoyu@jiangmin.com"

# 初始化环境
RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list
# RUN echo "deb http://security.debian.org/debian-security stretch/updates main" >> /etc/apt/sources.list
RUN apt-get clean
RUN apt-get update

# 安装依赖
RUN apt-get install -y htop net-tools vim
RUN apt-get install -y python python-pip python-dev libffi-dev libssl-dev python-setuptools
# RUN apt-get install -y python-virtualenv
RUN apt-get install -y libjpeg-dev zlib1g-dev
RUN apt-get install -y mongodb

#修改pip源
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip -U
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装mysql-5.7(账号密码均为root, docker build时会出错)
RUN echo "mysql-server mysql-server/root_password password root" | debconf-set-selections
RUN echo "mysql-server mysql-server/root_password_again password root" | debconf-set-selections
RUN apt-get -y install mysql-server-5.7 && \
  mkdir -p /var/lib/mysql && \
  mkdir -p /var/run/mysqld && \
  mkdir -p /var/log/mysql && \
  chown -R mysql:mysql /var/lib/mysql && \
  chown -R mysql:mysql /var/run/mysqld && \
  chown -R mysql:mysql /var/log/mysql

RUN apt-get install -y python-mysqldb

# 修改my.cnf开启远程连接
#RUN sed -i 's/^bind-address/#bind-address/g' /etc/mysql/my.cnf
# UTF-8 and bind-address
RUN sed -i -e "$ a [client]\n\n[mysql]\n\n[mysqld]"  /etc/mysql/my.cnf && \
  sed -i -e "s/\(\[client\]\)/\1\ndefault-character-set = utf8/g" /etc/mysql/my.cnf && \
  sed -i -e "s/\(\[mysql\]\)/\1\ndefault-character-set = utf8/g" /etc/mysql/my.cnf && \
  sed -i -e "s/\(\[mysqld\]\)/\1\ninit_connect='SET NAMES utf8'\ncharacter-set-server = utf8\ncollation-server=utf8_unicode_ci\nbind-address = 0.0.0.0/g" /etc/mysql/my.cnf

# 安装KVM
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y qemu-kvm libvirt-daemon-system
RUN apt-get install -y python-libvirt
RUN sed -i "s/#user = \"root\"/user = \"root\"/" /etc/libvirt/qemu.conf
RUN sed -i "s/#group = \"root\"/group = \"root\"/" /etc/libvirt/qemu.conf

# # 安装kvm管理工具webvirtmgr
# RUN apt-get install -y git python-libvirt python-libxml2 novnc supervisor nginx
# ADD webvirtmgr /opt/webvirtmgr

# 配置libvirt
#RUN setcap cap_net_raw,cap_net_admin=eip /usr/sbin/tcpdump
#RUN apt-get install -y tcpdump apparmor-utils

# 安装tcpdump
RUN apt-get install -y tcpdump apparmor-utils
RUN setcap cap_net_raw,cap_net_admin=eip /usr/sbin/tcpdump

RUN apt-get install -y libcap2-bin

# tcpdump相关配置
# RUN adduser cuckoo
# RUN groupadd pcap
# RUN usermod -a -G pcap cuckoo
# RUN chgrp pcap /usr/sbin/tcpdump
# RUN usermod -a -G libvirtd cuckoo
RUN mv /usr/sbin/tcpdump /usr/bin/tcpdump

# 安装内存dump工具
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y volatility

# 安装m2crypto
RUN apt-get install -y swig
RUN apt-get install -y libssl1.0-dev
RUN pip install m2crypto==0.24.0

RUN apt-get install -y libguac-client-rdp0 libguac-client-vnc0 libguac-client-ssh0 guacd

RUN pip install -U cuckoo
RUN pip install pyOpenSSL==18.0.0

RUN apt-get install -y iputils-ping
RUN apt-get install -y supervisorctl

COPY community-master.tar.gz /root
COPY sysinit.py /root
COPY sysinit.sh /sysinit.sh
COPY win7x64.xml /root
RUN chmod +x /entrypoint.sh

# CMD [ "/sbin/init" ]
CMD [ "bash" ]

# 安装布谷鸟
#RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple jsonschema==2.6.0
#RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -U cuckoo