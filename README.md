# docker版cuckoo

启动方式
```
docker run -idt \
--name=u1 \
--net=host \
--privileged=true \
-e "avas_cuckoo_win7x64_vm_num=3" \
-v /root/cuckoo_kvm/images:/root/images \
cuckoo
```