#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Project: cuckoo_docker 
@File: sysinit.py.py
@Author: XuRuoYu
@Describe: 
@Date: 2021/11/16 10:18 上午 
"""
# coding:utf-8
import json
from configparser import ConfigParser
import xml.etree.ElementTree as ET
import os
import time


# 通过基础镜像增量生成各个虚拟机磁盘文件
def generate_vm_disk(base_disk_path, vm_disk_path):
    print('qemu-img create -f qcow2 -b ' + base_disk_path + ' ' + vm_disk_path)
    if os.path.exists(vm_disk_path):
        os.remove(vm_disk_path)
    os.system('qemu-img create -f qcow2 -b ' + base_disk_path + ' ' + vm_disk_path)


# 通过虚拟机配置文件模板生成虚拟机配置文件
def generate_vm_xml(vm_name, vm_template_path, vm_disk_path, vm_xml_path, mac, vcpu=2, vmem=2):
    # 读取虚拟机配置文件模板
    tree = ET.parse(vm_template_path)
    root = tree.getroot()
    # 设置虚拟机名称
    root.find('./name').text = vm_name
    # 设置网卡mac
    root.find('./devices/interface/mac').attrib['address'] = mac
    # 设置cpu数量
    root.find('./vcpu').text = str(vcpu)
    # 设置内存大小
    root.find('./memory').text = str(vmem)
    # 设置镜像路径
    root.find('./devices/disk/source').attrib['file'] = vm_disk_path
    # 保存虚拟机配置文件
    tree.write(vm_xml_path)


# 通过配置文件创建虚拟机实例
def create_vm_by_xml(vm_xml_path):
    os.system('virsh define ' + vm_xml_path)


# 创建num个虚拟机
def create_vm(num, vm_os, vm_template_path, vm_xml_dir='./vm_xml', vm_disk_dir='./images'):
    if num > 255:
        print('虚拟机数量不能超过255个')
        return
    vm_xml_dir = os.path.abspath(vm_xml_dir)
    vm_disk_dir = os.path.abspath(vm_disk_dir)
    print(vm_xml_dir)
    print(vm_disk_dir)
    # 创建虚拟机配置文件目录
    if not os.path.exists(vm_xml_dir):
        os.mkdir(vm_xml_dir)
    # 创建虚拟机磁盘文件目录
    if not os.path.exists(vm_disk_dir):
        os.mkdir(vm_disk_dir)
    # 创建虚拟机
    for i in range(num):
        vm_name = vm_os + '_' + str(i + 1)
        vm_disk_path = vm_disk_dir + '/' + vm_name + '.qcow2'
        vm_xml_path = vm_xml_dir + '/' + vm_name + '.xml'
        generate_vm_xml(vm_name=vm_name, vm_template_path=vm_template_path, vm_disk_path=vm_disk_path,
                        vm_xml_path=vm_xml_path, mac='52:54:00:00:00:' + "%02x" % (i + 1))
        generate_vm_disk(vm_disk_dir + '/' + vm_os + '.qcow2', vm_disk_path)
        create_vm_by_xml(vm_xml_path)
        # 修改dhcp分配静态IP
        os.system('virsh net-update default add ip-dhcp-host --xml \'<host mac="52:54:00:00:00:' + "%02x" % (
                i + 1) + '" name="' + vm_name + '" ip="192.168.122.' + str(i + 2) + '" />\'')
        # 启动虚拟机
        os.system('virsh start ' + vm_name)
        # 检查windows虚拟机是否成功启动
        while True:
            if os.system('ping -c 1 192.168.122.' + str(i + 2)) == 0:
                break
            else:
                print('等待虚拟机' + vm_name + '启动')
                time.sleep(1)
        # 等待系统初始化完成（预估量）
        time.sleep(30)
        # 创建default快照
        os.system('virsh snapshot-create-as ' + vm_name + ' ' + 'default')
        # 关闭虚拟机
        os.system('virsh shutdown ' + vm_name)


# 初始化cuckoo
def cuckoo_init():
    os.system('cuckoo init')


# 修改cuckoo kvm配置文件(配置文件只采用默认路径/root/.cuckoo)
def modify_cuckoo_kvm_conf(num, vm_os, resultserver_ip):
    platform = {
        'win7x64': 'windows',
        'win7x86': 'windows',
        'centos': 'linux',
    }
    config = ConfigParser()
    if os.path.exists('/root/.cuckoo/conf/kvm.conf'):
        config.read('/root/.cuckoo/conf/kvm.conf')
    config.add_section('kvm')
    config.set('kvm', 'dsn', 'qemu:///system')
    config.set('kvm', 'machines', ','.join([vm_os + '_' + str(i) for i in range(1, num + 1)]))
    config.set('kvm', 'interface', 'virbr0')

    for i in range(1, num + 1):
        lable = vm_os + '_' + str(i)
        config.add_section(lable)
        config.set(lable, 'label', lable)
        config.set(lable, 'platform', platform[vm_os])
        config.set(lable, 'ip', '192.168.122.' + str(i + 1))
        config.set(lable, 'snapshot', 'default')
        config.set(lable, 'resultserver_ip', resultserver_ip)
        config.set(lable, 'resultserver_port', '2042')
        config.set(lable, 'tags', '')
        config.set(lable, 'osprofile', '')
        config.set(lable, 'interface', '')

    if not os.path.exists('/root/.cuckoo/conf'):
        os.mkdir('/root/.cuckoo/conf')
    if os.path.exists('/root/.cuckoo/conf/kvm.conf'):
        os.remove('/root/.cuckoo/conf/kvm.conf')
    config.write(open('/root/.cuckoo/conf/kvm.conf', 'w'))
    pass


# 修改cuckoo其他配置文件
def modify_cuckoo_conf():
    config = ConfigParser()
    config.read('/root/.cuckoo/conf/cuckoo.conf')
    config.set('cuckoo', 'version_check', 'no')
    config.set('cuckoo', 'api_token', 'ijq2sXmQroZf7H5x6lKBOg')
    config.set('cuckoo', 'machinery', 'kvm')
    config.set('database', 'connection', 'mysql://root:root@localhost:3306/cuckoo')
    config.set('resultserver', 'ip', '0.0.0.0')
    config.write(open('/root/.cuckoo/conf/cuckoo.conf', 'w'))

    config = ConfigParser()
    config.read('/root/.cuckoo/conf/auxiliary.conf')
    config.set('sniffer', 'tcpdump', '/usr/bin/tcpdump')
    config.write(open('/root/.cuckoo/conf/auxiliary.conf', 'w'))

    config = ConfigParser()
    config.read('/root/.cuckoo/conf/reporting.conf')
    config.set('mongodb', 'enabled', 'yes')
    config.write(open('/root/.cuckoo/conf/reporting.conf', 'w'))

    pass


# 导入cuckoo社区
def import_cuckoo_community():
    os.system('cuckoo community --file /root/community-master.tar.gz')
    pass


if __name__ == '__main__':
    print('avas.:::::',os.environ.get('avas.cuckoo.win7x64.vm_num'))
    print('avas_:::::',os.environ.get('avas_cuckoo_win7x64_vm_num'))
    # 读取avas.cuckoo.win7x64.vm_num环境变量
    if os.getenv('avas.cuckoo.win7x64.vm_num') is None:
        win7x64_vm_num = 2
    else:
        win7x64_vm_num = int(os.getenv('avas.cuckoo.win7x64.vm_num'))
    print('win7x64虚拟机数量：' + str(win7x64_vm_num))
    # create_vm(win7x64_vm_num, 'win7x64', vm_template_path='win7x64.xml')
    # cuckoo_init()
    # import_cuckoo_community()
    # # 删除已有kvm.conf
    # os.remove('/root/.cuckoo/conf/kvm.conf')
    # modify_cuckoo_kvm_conf(win7x64_vm_num, 'win7x64', '192.168.122.1')
    # modify_cuckoo_conf()
    # os.system('cp supervisord.conf /root/.cuckoo/supervisord.conf')
