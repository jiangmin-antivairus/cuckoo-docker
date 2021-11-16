#!/bin/sh

# 获取git版本号
git_version=$(git rev-parse --short HEAD)
echo 'git_version:' $git_version
# 写入版本号至version文件
echo $git_version > version

# 制作docker镜像
docker build --no-cache -t cuckoo:$git_version .
docker tag cuckoo:$git_version cuckoo:latest

# 导出docker镜像
# docker save -o cuckoo.tar cuckoo:$git_version