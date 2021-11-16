#!/bin/sh

# 清理网卡
ip link delete virbr0
ip link delete virbr0-nic

# 启动相关后台服务
/etc/init.d/mongodb restart
/etc/init.d/mysql restart
/etc/init.d/virtlogd restart
/etc/init.d/dbus restart
/etc/init.d/libvirtd restart
/etc/init.d/cron restart

if [ ! -f "/.inited" ]; then
  # 启用mysql root远程连接
  /usr/bin/mysql -uroot -proot -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'root' WITH GRANT OPTION; FLUSH PRIVILEGES;"
  # 创建数据库
  /usr/bin/mysql -uroot -proot -e "CREATE DATABASE IF NOT EXISTS cuckoo DEFAULT CHARSET utf8 COLLATE utf8_general_ci;"
  cd /root
  python sysinit.py
  touch /.inited
fi

supervisord -c /root/.cuckoo/supervisord.conf
sleep 5s
tail -f /root/.cuckoo/log/cuckoo.log